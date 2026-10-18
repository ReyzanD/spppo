"""Train TF-IDF + Multinomial Naive Bayes (docs/FRD.md §3.4).

Run as a module so the shared preprocessing package is importable:

    cd backend
    python -m training.train_model

Why a CV step exists
--------------------
The first baseline (`alpha=1.0`, word unigram+bigram) reached 97.10% accuracy but
only 77.86% spam recall, failing NFR-01: with a 12.6% positive class, accuracy is
easy to win by predicting "ham". Hyperparameters (and the choice of features) are
therefore selected by 5-fold cross-validation **on the training split only**, and
the held-out test split is evaluated exactly once at the end. Tuning against the
test split would leak it and make the reported number meaningless.

Selection rule, fixed before the test split was scored:

    feasible  = CV accuracy >= 90, CV recall(spam) >= 90, CV precision(spam) >= 85
    objective = maximise CV F1(spam)

with a deliberate safety margin (SELECTION_MIN_RECALL = 92 rather than 90), because
a config that sits at exactly 90 on CV has fallen to ~88 on a single 1,035-row
test split before.

Produces, in `backend/models/`:

    naive_bayes.pkl, tfidf_vectorizer.pkl   the fitted pipeline pieces
    metrics.json                            test-split metrics (percent)
    top_features.json                       most indicative word features
    training_run.json                       config, CV table, split provenance
"""

import argparse
import csv
import json
import pickle
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion

from app.config import get_settings
from app.services.preprocessing import clean

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA = BASE_DIR / "data" / "sms_spam_collection.csv"

HAM = "ham"
SPAM = "spam"
LABELS = (HAM, SPAM)

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
TOP_N = 20

# NFR-01 (docs/PRD.md §6).
TARGET_ACCURACY = 90.0
TARGET_RECALL_SPAM = 90.0

# Selection constraints. The recall floor is deliberately above the target so the
# chosen model keeps a margin on data it has never seen.
SELECTION_MIN_RECALL = 92.0
SELECTION_MIN_PRECISION = 85.0
SELECTION_MIN_ACCURACY = 90.0

# Word n-grams are interpretable; char n-grams catch obfuscation ("Fr33", "w0n")
# and misspellings. The union tested best under the selection rule.
FEATURE_KINDS = ("word12", "word12_md1", "char35", "word12+char35")
ALPHAS = (1.0, 0.5, 0.1, 0.05)


def build_vectorizer(kind: str) -> TfidfVectorizer | FeatureUnion:
    """Build an unfitted vectorizer for the named feature configuration."""
    word = TfidfVectorizer(min_df=2, ngram_range=(1, 2), sublinear_tf=True)
    match kind:
        case "word12":
            return word
        case "word12_md1":
            return TfidfVectorizer(min_df=1, ngram_range=(1, 2), sublinear_tf=True)
        case "char35":
            return TfidfVectorizer(
                analyzer="char_wb", min_df=2, ngram_range=(3, 5), sublinear_tf=True
            )
        case "word12+char35":
            return FeatureUnion(
                [
                    ("w", word),
                    (
                        "c",
                        TfidfVectorizer(
                            analyzer="char_wb", min_df=2, ngram_range=(3, 5), sublinear_tf=True
                        ),
                    ),
                ]
            )
        case _:
            raise ValueError(f"unknown feature kind: {kind}")


def load_dataset(path: Path) -> tuple[list[str], list[str]]:
    """Read the cleaned CSV written by training/clean_dataset.py."""
    if not path.is_file():
        raise SystemExit(f"Cleaned dataset not found: {path}\nRun training/clean_dataset.py first.")

    texts: list[str] = []
    labels: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            texts.append(row["teks_pesan"])
            labels.append(row["label"])
    return texts, labels


def metrics_of(y_true: list[str], y_pred: list[str]) -> dict:
    """Metrics in percent (0-100), matching `model_info.akurasi` in docs/ERD.md."""
    return {
        "accuracy": round(accuracy_score(y_true, y_pred) * 100, 2),
        "precision_spam": round(
            precision_score(y_true, y_pred, pos_label=SPAM, zero_division=0) * 100, 2
        ),
        "recall_spam": round(
            recall_score(y_true, y_pred, pos_label=SPAM, zero_division=0) * 100, 2
        ),
        "f1_spam": round(f1_score(y_true, y_pred, pos_label=SPAM, zero_division=0) * 100, 2),
        # labels=[ham, spam] gives [[TN, FP], [FN, TP]]
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(LABELS)).tolist(),
        "confusion_matrix_labels": [f"actual_{name}" for name in LABELS],
    }


def cross_validate(
    texts: list[str],
    labels: list[str],
    *,
    folds: int = CV_FOLDS,
    random_state: int = RANDOM_STATE,
    feature_kinds: tuple[str, ...] = FEATURE_KINDS,
    alphas: tuple[float, ...] = ALPHAS,
) -> list[dict]:
    """Score every (features, alpha) config on the training split only.

    The vectorizer is refit inside each fold, so no fold's validation rows ever
    influence the features used to score it. `feature_kinds`/`alphas` exist so a
    test can run a one-cell grid instead of the full search.
    """
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_state)
    collected: dict[tuple[str, float], dict[str, list[float]]] = {}

    for train_ix, valid_ix in splitter.split(texts, labels):
        fold_texts = [texts[i] for i in train_ix]
        fold_labels = [labels[i] for i in train_ix]
        valid_texts = [texts[i] for i in valid_ix]
        valid_labels = [labels[i] for i in valid_ix]

        for kind in feature_kinds:
            vectorizer = build_vectorizer(kind)
            x_fold = vectorizer.fit_transform(fold_texts)
            x_valid = vectorizer.transform(valid_texts)

            for alpha in alphas:
                model = MultinomialNB(alpha=alpha).fit(x_fold, fold_labels)
                predicted = list(model.predict(x_valid))
                scores = metrics_of(valid_labels, predicted)
                bucket = collected.setdefault(
                    (kind, alpha),
                    {"accuracy": [], "precision_spam": [], "recall_spam": [], "f1_spam": []},
                )
                for key in bucket:
                    bucket[key].append(scores[key])

    table = [
        {
            "features": kind,
            "alpha": alpha,
            "accuracy": round(mean(values["accuracy"]), 2),
            "precision_spam": round(mean(values["precision_spam"]), 2),
            "recall_spam": round(mean(values["recall_spam"]), 2),
            "f1_spam": round(mean(values["f1_spam"]), 2),
        }
        for (kind, alpha), values in collected.items()
    ]
    table.sort(key=lambda row: row["f1_spam"], reverse=True)
    return table


def is_feasible(row: dict) -> bool:
    """Hard constraints plus the recall margin, per the rule in the module docstring."""
    return (
        row["accuracy"] >= SELECTION_MIN_ACCURACY
        and row["recall_spam"] >= SELECTION_MIN_RECALL
        and row["precision_spam"] >= SELECTION_MIN_PRECISION
    )


def select_config(cv_table: list[dict]) -> dict:
    """Highest CV F1 among feasible configs; loud failure when none qualifies."""
    feasible = [row for row in cv_table if is_feasible(row)]
    if not feasible:
        best = cv_table[0] if cv_table else {}
        raise SystemExit(
            "No configuration met the selection constraints "
            f"(accuracy>={SELECTION_MIN_ACCURACY}, recall>={SELECTION_MIN_RECALL}, "
            f"precision>={SELECTION_MIN_PRECISION}). Best CV F1 was {best}. "
            "Relax the rule deliberately and document why, do not silently retune."
        )
    return max(feasible, key=lambda row: row["f1_spam"])


def split_dataset(
    texts: list[str],
    labels: list[str],
    *,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[list[str], list[str], list[str], list[str]]:
    return train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )


def fit_model(
    x_train: list[str], y_train: list[str], config: dict
) -> tuple[TfidfVectorizer | FeatureUnion, MultinomialNB]:
    """Fit vectorizer and classifier on the training rows with the chosen config."""
    vectorizer = build_vectorizer(config["features"])
    x_vectorized = vectorizer.fit_transform(x_train)
    model = MultinomialNB(alpha=config["alpha"]).fit(x_vectorized, y_train)
    return vectorizer, model


def top_features(
    vectorizer: TfidfVectorizer | FeatureUnion, model: MultinomialNB, n: int = TOP_N
) -> dict:
    """Most indicative *word* features, two ways.

    `log_prob` — highest log P(feature | class): frequent wording per class.
    `log_odds` — largest log P(f|spam) - log P(f|ham): discriminative features,
                 which is what actually explains a prediction.

    For a FeatureUnion the char n-grams are excluded from the ranking (they come
    out as fragments like "cl ") so the table stays readable; the vocabulary size
    still counts everything.
    """
    all_names = list(vectorizer.get_feature_names_out())
    log_prob = model.feature_log_prob_
    classes = list(model.classes_)
    spam_ix, ham_ix = classes.index(SPAM), classes.index(HAM)

    def readable(name: str) -> str:
        prefix, sep, rest = name.partition("__")
        return rest if sep and prefix in {"w", "c"} else name

    indices = [i for i, name in enumerate(all_names) if not name.startswith("c__")]
    log_odds = {i: float(log_prob[spam_ix][i] - log_prob[ham_ix][i]) for i in indices}

    def top_by(scores: dict[int, float], count: int) -> list[dict]:
        ordered = sorted(scores, key=lambda i: scores[i], reverse=True)[:count]
        return [{"feature": readable(all_names[i]), "score": round(scores[i], 4)} for i in ordered]

    return {
        "vocabulary_size": len(all_names),
        "word_features_ranked": len(indices),
        "alpha": float(model.alpha),
        "ranking_scope": "word-level features only; char n-grams excluded for readability",
        "top_by_log_prob": {
            SPAM: top_by({i: float(log_prob[spam_ix][i]) for i in indices}, n),
            HAM: top_by({i: float(log_prob[ham_ix][i]) for i in indices}, n),
        },
        "top_by_log_odds": {
            SPAM: top_by(log_odds, n),
            HAM: top_by({i: -value for i, value in log_odds.items()}, n),
        },
    }


@dataclass
class RunRecord:
    config: dict
    cv_table: list[dict]
    split: dict
    metrics: dict
    dataset: dict
    extra: dict = field(default_factory=dict)


def save_artifacts(
    out_dir: Path,
    *,
    vectorizer: TfidfVectorizer | FeatureUnion,
    model: MultinomialNB,
    run: RunRecord,
    features: dict,
) -> dict[str, Path]:
    """Write the pickles and the JSON reports."""
    settings = get_settings()
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "model": out_dir / settings.model_file,
        "vectorizer": out_dir / settings.vectorizer_file,
        "metrics": out_dir / "metrics.json",
        "top_features": out_dir / "top_features.json",
        "training_run": out_dir / "training_run.json",
    }

    with paths["model"].open("wb") as handle:
        pickle.dump(model, handle)
    with paths["vectorizer"].open("wb") as handle:
        pickle.dump(vectorizer, handle)

    paths["metrics"].write_text(json.dumps(run.metrics, indent=2) + "\n", encoding="utf-8")
    paths["top_features"].write_text(
        json.dumps(features, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    record = {
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "dataset": run.dataset,
        "split": run.split,
        "selected_config": run.config,
        "selection_rule": {
            "method": f"{CV_FOLDS}-fold stratified CV on the training split only",
            "constraints": {
                "accuracy_min": SELECTION_MIN_ACCURACY,
                "recall_spam_min": SELECTION_MIN_RECALL,
                "precision_spam_min": SELECTION_MIN_PRECISION,
            },
            "objective": "maximise CV f1_spam",
            "cv_table": run.cv_table,
        },
        "vectorizer": {
            "features": run.config["features"],
            "vocabulary_size": features["vocabulary_size"],
        },
        "classifier": {"name": "MultinomialNB", "alpha": run.config["alpha"]},
        "metrics": run.metrics,
        **run.extra,
    }
    paths["training_run"].write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the Naive Bayes detector.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="cleaned CSV")
    parser.add_argument("--out-dir", type=Path, default=None, help="artifact directory")
    parser.add_argument("--notes", default="", help="free-text note stored in the run record")
    args = parser.parse_args(argv)

    settings = get_settings()
    out_dir = args.out_dir or settings.model_path.parent

    raw_texts, labels = load_dataset(args.data)
    texts = [clean(text) for text in raw_texts]
    x_train, x_test, y_train, y_test = split_dataset(texts, labels)

    print(f"dataset   {len(texts)} messages ({labels.count(SPAM)} spam / {labels.count(HAM)} ham)")
    print(f"split     {len(x_train)} train / {len(x_test)} test  (seed {RANDOM_STATE})")
    print(f"\nselecting on {CV_FOLDS}-fold CV over the training split only:")

    cv_table = cross_validate(x_train, y_train)
    print(f"  {'features':>15} {'alpha':>6} {'acc':>7} {'P':>7} {'R':>7} {'F1':>7}  feasible")
    for row in cv_table:
        print(
            f"  {row['features']:>15} {row['alpha']:>6} {row['accuracy']:>7.2f} "
            f"{row['precision_spam']:>7.2f} {row['recall_spam']:>7.2f} {row['f1_spam']:>7.2f}  "
            f"{'yes' if is_feasible(row) else 'no'}"
        )

    config = select_config(cv_table)
    print(
        f"\nselected  features={config['features']} alpha={config['alpha']} "
        f"(CV f1 {config['f1_spam']:.2f}, recall {config['recall_spam']:.2f})"
    )

    vectorizer, model = fit_model(x_train, y_train, config)
    y_pred = list(model.predict(vectorizer.transform(x_test)))
    metrics = metrics_of(y_test, y_pred)
    features = top_features(vectorizer, model)

    run = RunRecord(
        config=config,
        cv_table=cv_table,
        split={
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "n_train": len(y_train),
            "n_test": len(y_test),
            "n_spam_test": y_test.count(SPAM),
        },
        metrics=metrics,
        dataset={
            "path": str(args.data),
            "rows": len(texts),
            "spam": labels.count(SPAM),
            "ham": labels.count(HAM),
        },
        extra={"notes": args.notes} if args.notes else {},
    )

    paths = save_artifacts(out_dir, vectorizer=vectorizer, model=model, run=run, features=features)

    print(f"\nheld-out test split ({len(y_test)} messages), evaluated once:")
    print(f"  accuracy       {metrics['accuracy']:>6.2f}%   (target >= {TARGET_ACCURACY:.0f}%)")
    print(f"  precision spam {metrics['precision_spam']:>6.2f}%")
    print(
        f"  recall spam    {metrics['recall_spam']:>6.2f}%   (target >= {TARGET_RECALL_SPAM:.0f}%)"
    )
    print(f"  f1 spam        {metrics['f1_spam']:>6.2f}%")
    print(f"  confusion      {metrics['confusion_matrix']}  [[TN, FP], [FN, TP]]")

    accuracy_ok = metrics["accuracy"] >= TARGET_ACCURACY
    recall_ok = metrics["recall_spam"] >= TARGET_RECALL_SPAM
    print()
    print(
        f"NFR-01         accuracy {'PASS' if accuracy_ok else 'FAIL'}, "
        f"recall {'PASS' if recall_ok else 'FAIL'}"
    )

    print()
    for name, path in paths.items():
        print(f"  wrote {name:14s} {path}")

    # Training succeeded either way; a missed target is a finding to report, not a crash.
    return 0 if (accuracy_ok and recall_ok) else 2


if __name__ == "__main__":
    sys.exit(main())
