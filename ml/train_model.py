"""Train the SMS fraud detector: TF-IDF + Multinomial Naive Bayes.

Usage (from the repository root)::

    python ml/train_model.py
    python ml/train_model.py --data backend/data/raw/SMSSpamCollection

The script follows the requested pipeline in order:

1. load the UCI SMS Spam Collection (5,574 tab-separated, labelled messages)
2. check for missing values and duplicates, remove them and print the counts
3. preprocess with the shared ``ml.preprocessing.preprocess`` function
4. build TF-IDF features (word 1-2 grams + character 3-5 grams)
5. map ``spam`` -> ``Penipuan`` and ``ham`` -> ``Bukan Penipuan``
6. split 80/20, stratified, random_state=42
7. train MultinomialNB on the training split
8. evaluate on the held-out test split and print accuracy/precision/recall/F1
   and the confusion matrix (accuracy is measured, never hardcoded)
9. write ``model.joblib``, ``vectorizer.joblib`` and ``metadata.json``

The dataset is read from an existing local copy when available; otherwise it is
downloaded from the dataset's GitHub repository to ``ml/data/`` and verified
against a pinned SHA-256 before training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion

if __package__ in (None, ""):
    # Allow `python ml/train_model.py` as well as `python -m ml.train_model`.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.preprocessing import preprocess  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = Path(__file__).resolve().parent

DEFAULT_DATA_CANDIDATES = (
    ML_DIR / "data" / "indonesian_sms_spam.csv",
    REPO_ROOT / "backend" / "data" / "raw" / "indonesian_sms_spam.csv",
    REPO_ROOT / "backend" / "data" / "raw" / "SMSSpamCollection",
    ML_DIR / "data" / "SMSSpamCollection",
)

DATASET_NAME = "Indonesian SMS Spam Collection"
SOURCE_URL = (
    "https://raw.githubusercontent.com/Andikazidanef15/"
    "Sentiment-Analysis-on-Indonesian-SMS-Dataset/main/dataset_sms_spam_v1.csv"
)
DATASET_SHA256 = "206e8cb15de401b499df4323c58527e9e6eb9e70608bafabeec3516a6d0d717c"

# Configuration already selected by 5-fold CV on the training split during the
# web-app phase, and kept here so training and the existing service agree.
# Character n-grams catch obfuscated wording ("Fr33", "w0n"); alpha=0.1 raises
# spam recall, which matters more than raw accuracy on a 12.6% positive class.
ALPHA = 0.1
RANDOM_STATE = 42
TEST_SIZE = 0.2
SPAM = "spam"
HAM = "ham"
LABEL_MAP = {SPAM: "Penipuan", HAM: "Bukan Penipuan"}
LABELS = ("Bukan Penipuan", "Penipuan")

MODEL_FILE = "model.joblib"
VECTORIZER_FILE = "vectorizer.joblib"
METADATA_FILE = "metadata.json"


def sha256_of(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_dataset(destination: Path) -> Path:
    """Download the dataset CSV and verify it against the pinned SHA-256."""
    data_dir = destination.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")

    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "penipuan-ml/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
            while chunk := response.read(64 * 1024):
                out.write(chunk)
    except BaseException:
        # Never leave a half-written file behind for the next run to trust.
        partial.unlink(missing_ok=True)
        raise

    actual = sha256_of(partial)
    if actual != DATASET_SHA256:
        partial.unlink(missing_ok=True)
        raise SystemExit(
            "Dataset checksum mismatch.\n"
            f"  expected {DATASET_SHA256}\n"
            f"  actual   {actual}\n"
            "Refusing to train on an unverified file."
        )

    os.replace(partial, destination)
    print(f"Downloaded {DATASET_NAME} -> {destination}")
    return destination


def resolve_dataset(explicit: Path | None) -> Path:
    """Return an existing dataset path, downloading it when necessary."""
    if explicit is not None:
        if not explicit.is_file():
            raise SystemExit(f"Dataset not found: {explicit}")
        return explicit

    for candidate in DEFAULT_DATA_CANDIDATES:
        if candidate.is_file():
            return candidate

    return download_dataset(ML_DIR / "data" / "indonesian_sms_spam.csv")


def load_messages(path: Path) -> tuple[list[str], list[str], str, str]:
    """Parse messages and labels from CSV or TSV dataset file."""
    texts: list[str] = []
    labels: list[str] = []
    dataset_name = "UCI SMS Spam Collection"
    source_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"

    if path.suffix.lower() == ".csv":
        dataset_name = "Indonesian SMS Spam Collection"
        source_url = "https://github.com/Andikazidanef15/Sentiment-Analysis-on-Indonesian-SMS-Dataset"
        with path.open(encoding="utf-8", errors="replace") as handle:
            import csv

            reader = csv.reader(handle)
            header = next(reader, None)
            text_idx = 0
            label_idx = 1
            if header:
                lower_header = [h.strip().lower() for h in header]
                if "label" in lower_header:
                    label_idx = lower_header.index("label")
                if "teks" in lower_header:
                    text_idx = lower_header.index("teks")
                elif "text" in lower_header:
                    text_idx = lower_header.index("text")

            for row in reader:
                if not row or len(row) <= max(text_idx, label_idx):
                    continue
                raw_label = row[label_idx].strip().lower()
                text = row[text_idx].strip()
                if not text:
                    continue
                if raw_label in ("1", "penipuan", "spam"):
                    labels.append(SPAM)
                    texts.append(text)
                elif raw_label in ("0", "2", "bukan penipuan", "ham", "normal", "promo"):
                    labels.append(HAM)
                    texts.append(text)

        return texts, labels, dataset_name, source_url

    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            label, separator, text = line.partition("\t")
            if not separator:
                raise SystemExit(f"{path}:{lineno}: expected 'label<TAB>message'")
            label = label.strip().lower()
            if label not in (SPAM, HAM):
                raise SystemExit(f"{path}:{lineno}: unexpected label {label!r}")
            texts.append(text)
            labels.append(label)

    return texts, labels, dataset_name, source_url


def remove_missing_and_duplicates(
    texts: list[str], labels: list[str]
) -> tuple[list[str], list[str], dict[str, int]]:
    """Drop empty messages and duplicate messages, reporting each count.

    Deduplication is by message text: keeping the same message twice (possibly
    with two different labels) would leak rows across the train/test split.
    """
    missing = 0
    duplicates = 0
    seen: set[str] = set()
    kept_texts: list[str] = []
    kept_labels: list[str] = []

    for text, label in zip(texts, labels, strict=True):
        if not text.strip():
            missing += 1
            continue
        if text in seen:
            duplicates += 1
            continue
        seen.add(text)
        kept_texts.append(text)
        kept_labels.append(label)

    removed = {"missing": missing, "duplicates": duplicates, "total": missing + duplicates}
    return kept_texts, kept_labels, removed


def build_vectorizer() -> FeatureUnion:
    """TF-IDF over word unigrams/bigrams and character 3-5 grams."""
    return FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True
                ),
            ),
        ]
    )


def evaluate(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    """Compute the requested classification metrics for the Penipuan class."""
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)) * 100, 2),
        "precision": round(
            float(precision_score(y_true, y_pred, pos_label="Penipuan", zero_division=0)) * 100,
            2,
        ),
        "recall": round(
            float(recall_score(y_true, y_pred, pos_label="Penipuan", zero_division=0)) * 100,
            2,
        ),
        "f1": round(
            float(f1_score(y_true, y_pred, pos_label="Penipuan", zero_division=0)) * 100,
            2,
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(LABELS)).tolist(),
        "confusion_matrix_labels": list(LABELS),
        "positive_class": "Penipuan",
    }


def print_metrics(metrics: dict[str, Any], n_test: int) -> None:
    """Print the evaluation report in a readable table."""
    matrix = metrics["confusion_matrix"]
    print(f"\nEvaluation on held-out test set ({n_test} messages)")
    print(f"  Accuracy   : {metrics['accuracy']:.2f}%")
    print(f"  Precision  : {metrics['precision']:.2f}%  (positive class: Penipuan)")
    print(f"  Recall     : {metrics['recall']:.2f}%")
    print(f"  F1-score   : {metrics['f1']:.2f}%")
    print("\nConfusion matrix (rows = actual, columns = predicted):")
    print(f"  {'':>16} {'Bukan Penipuan':>16} {'Penipuan':>12}")
    print(f"  {'Bukan Penipuan':>16} {matrix[0][0]:>16} {matrix[0][1]:>12}")
    print(f"  {'Penipuan':>16} {matrix[1][0]:>16} {matrix[1][1]:>12}")


def train(
    data_path: Path | None = None, out_dir: Path | None = None
) -> tuple[Path, Path, Path, dict[str, Any]]:
    """Run the full pipeline and return the paths of the written artifacts."""
    data = resolve_dataset(data_path)
    output = out_dir or ML_DIR
    output.mkdir(parents=True, exist_ok=True)

    raw_texts, raw_labels, dataset_name, source_url = load_messages(data)
    print(f"Dataset            : {data} ({dataset_name})")
    print(f"Raw rows           : {len(raw_texts)}")

    texts, labels, removed = remove_missing_and_duplicates(raw_texts, raw_labels)
    print(f"Missing removed    : {removed['missing']}")
    print(f"Duplicates removed : {removed['duplicates']}")
    print(f"Rows removed total : {removed['total']}")
    print(f"Rows after cleaning: {len(texts)}")

    processed = [preprocess(text) for text in texts]
    empty_after = sum(1 for value in processed if not value)
    mapped_labels = [LABEL_MAP[label] for label in labels]
    counts = Counter(mapped_labels)
    fraud_count = counts["Penipuan"]
    ham_count = counts["Bukan Penipuan"]
    print(f"Class distribution : {fraud_count} Penipuan / {ham_count} Bukan Penipuan")
    if empty_after:
        print(f"Empty after text preprocessing: {empty_after} (classified from the prior)")

    x_train, x_test, y_train, y_test = train_test_split(
        processed,
        mapped_labels,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=mapped_labels,
    )
    print(f"Train/test split   : {len(x_train)} / {len(x_test)} (stratified, seed {RANDOM_STATE})")

    vectorizer = build_vectorizer()
    x_train_vectorized = vectorizer.fit_transform(x_train)
    model = MultinomialNB(alpha=ALPHA)
    model.fit(x_train_vectorized, y_train)

    predictions = model.predict(vectorizer.transform(x_test)).tolist()
    metrics = evaluate(y_test, predictions)
    print_metrics(metrics, len(y_test))

    model_path = output / MODEL_FILE
    vectorizer_path = output / VECTORIZER_FILE
    metadata_path = output / METADATA_FILE
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    metadata: dict[str, Any] = {
        "project": "Sistem Pendeteksi Pesan Penipuan Online",
        "algorithm": "Multinomial Naive Bayes",
        "vectorizer": "TF-IDF (word 1-2 grams + char_wb 3-5 grams, sublinear tf)",
        "accuracy": metrics["accuracy"],
        "accuracy_unit": "percent",
        "dataset": {
            "name": dataset_name,
            "source_url": source_url,
            "raw_size": len(raw_texts),
            "size": len(texts),
            "spam": counts["Penipuan"],
            "ham": counts["Bukan Penipuan"],
            "removed": removed,
        },
        "dataset_size": len(texts),
        "train_size": len(x_train),
        "test_size": len(x_test),
        "split": {
            "test_size": TEST_SIZE,
            "train_size": len(x_train),
            "test_size_rows": len(x_test),
            "random_state": RANDOM_STATE,
            "stratified": True,
        },
        "labels": {"spam": "Penipuan", "ham": "Bukan Penipuan"},
        "metrics": metrics,
        "hyperparameters": {"alpha": ALPHA},
        "preprocessing": {
            "steps": [
                "case folding",
                "URL/phone/number placeholders",
                "remove punctuation",
                "remove Indonesian & English stopwords",
            ],
            "numbers": "normalized to <num>, <phone>, <url> (kept as fraud signal)",
            "stopwords_file": "stopwords_id.txt, stopwords_en.txt",
        },
        "training_date": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_file": MODEL_FILE,
        "vectorizer_file": VECTORIZER_FILE,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"\nSaved model      : {model_path}")
    print(f"Saved vectorizer : {vectorizer_path}")
    print(f"Saved metadata   : {metadata_path}")
    return model_path, vectorizer_path, metadata_path, metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the Naive Bayes fraud detector.")
    parser.add_argument("--data", type=Path, default=None, help="path to SMSSpamCollection")
    parser.add_argument("--out-dir", type=Path, default=ML_DIR, help="artifact directory")
    args = parser.parse_args(argv)

    try:
        _, _, _, metadata = train(args.data, args.out_dir)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"\nFinal measured accuracy: {metadata['accuracy']:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
