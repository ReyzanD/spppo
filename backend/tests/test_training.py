"""Tests for training/train_model.py.

Hermetic: synthetic data only, no dataset download, no network. The real corpus
is exercised by running `python -m training.train_model`, not by CI.
"""

import csv
import json
import pickle
from pathlib import Path

import pytest
from sklearn.pipeline import FeatureUnion
from training.train_model import (
    ALPHAS,
    FEATURE_KINDS,
    RunRecord,
    build_vectorizer,
    cross_validate,
    fit_model,
    is_feasible,
    load_dataset,
    metrics_of,
    save_artifacts,
    select_config,
    top_features,
)

SPAM_WORDS = ["free", "prize", "claim", "win", "urgent", "txt", "call", "cash"]
HAM_WORDS = ["lunch", "meeting", "tomorrow", "later", "thanks", "dinner", "film", "home"]


def synthetic_dataset() -> tuple[list[str], list[str]]:
    """20 spam + 20 ham messages with strongly separable vocabulary."""
    texts, labels = [], []
    for i in range(20):
        words = SPAM_WORDS[i % len(SPAM_WORDS) :] + SPAM_WORDS[: i % len(SPAM_WORDS)]
        texts.append(" ".join(words) + f" offer {i}")
        labels.append("spam")
        words = HAM_WORDS[i % len(HAM_WORDS) :] + HAM_WORDS[: i % len(HAM_WORDS)]
        texts.append(" ".join(words) + f" plan {i}")
        labels.append("ham")
    return texts, labels


def write_cleaned_csv(path: Path, texts: list[str], labels: list[str]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["label", "teks_pesan"])
        writer.writerows(zip(labels, texts, strict=True))
    return path


# --- metric computation ---------------------------------------------------


def test_metrics_are_percentages_with_ham_first_confusion() -> None:
    y_true = ["ham", "ham", "spam", "spam"]
    y_pred = ["ham", "spam", "spam", "spam"]

    metrics = metrics_of(y_true, y_pred)

    assert metrics["accuracy"] == 75.0
    # [[TN, FP], [FN, TP]] with labels ['ham', 'spam']
    assert metrics["confusion_matrix"] == [[1, 1], [0, 2]]
    assert metrics["recall_spam"] == 100.0
    assert metrics["precision_spam"] == 66.67


def test_metrics_survive_no_predicted_spam() -> None:
    """zero_division=0 keeps a misspelled model from crashing the run."""
    metrics = metrics_of(["spam", "ham"], ["ham", "ham"])

    assert metrics["recall_spam"] == 0.0
    assert metrics["precision_spam"] == 0.0
    assert metrics["f1_spam"] == 0.0


# --- dataset loading ------------------------------------------------------


def test_load_dataset_reads_the_cleaner_output_contract(tmp_path: Path) -> None:
    path = write_cleaned_csv(tmp_path / "clean.csv", ["free prize", "lunch"], ["spam", "ham"])

    texts, labels = load_dataset(path)

    assert texts == ["free prize", "lunch"]
    assert labels == ["spam", "ham"]


def test_load_dataset_fails_loudly_when_missing(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="clean_dataset"):
        load_dataset(tmp_path / "absent.csv")


# --- vectorizer factory ---------------------------------------------------


@pytest.mark.parametrize("kind", FEATURE_KINDS)
def test_build_vectorizer_supports_every_kind(kind: str) -> None:
    assert build_vectorizer(kind) is not None


def test_union_kind_combines_word_and_char_features() -> None:
    vectorizer = build_vectorizer("word12+char35")

    assert isinstance(vectorizer, FeatureUnion)
    assert [name for name, _ in vectorizer.transformer_list] == ["w", "c"]


def test_build_vectorizer_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown feature kind"):
        build_vectorizer("nonsense")


# --- the selection rule ---------------------------------------------------


def test_is_feasible_requires_the_recall_margin() -> None:
    """90.0 recall is the NFR target but selection demands 92 for safety."""
    assert is_feasible({"accuracy": 95.0, "recall_spam": 92.0, "precision_spam": 85.0})
    assert not is_feasible({"accuracy": 95.0, "recall_spam": 91.9, "precision_spam": 90.0})
    assert not is_feasible({"accuracy": 95.0, "recall_spam": 95.0, "precision_spam": 84.9})
    assert not is_feasible({"accuracy": 89.9, "recall_spam": 95.0, "precision_spam": 90.0})


def test_select_config_maximises_f1_among_feasible_rows() -> None:
    table = [
        {
            "features": "a",
            "alpha": 1.0,
            "accuracy": 99.0,
            "precision_spam": 99.0,
            "recall_spam": 80.0,
            "f1_spam": 99.0,
        },  # not feasible: recall
        {
            "features": "b",
            "alpha": 0.1,
            "accuracy": 98.0,
            "precision_spam": 90.0,
            "recall_spam": 94.0,
            "f1_spam": 92.0,
        },
        {
            "features": "c",
            "alpha": 0.1,
            "accuracy": 97.0,
            "precision_spam": 88.0,
            "recall_spam": 93.0,
            "f1_spam": 90.0,
        },
    ]

    assert select_config(table)["features"] == "b"


def test_select_config_refuses_to_silently_retune() -> None:
    """If nothing qualifies the run must stop, not pick the least bad option."""
    table = [
        {
            "features": "a",
            "alpha": 1.0,
            "accuracy": 99.0,
            "precision_spam": 99.0,
            "recall_spam": 60.0,
            "f1_spam": 75.0,
        }
    ]

    with pytest.raises(SystemExit, match="No configuration met"):
        select_config(table)


def test_cross_validate_returns_one_row_per_config() -> None:
    texts, labels = synthetic_dataset()

    table = cross_validate(texts, labels, folds=3, feature_kinds=("word12",), alphas=(1.0, 0.1))

    assert len(table) == 2
    assert {row["alpha"] for row in table} == {1.0, 0.1}
    assert all(row["features"] == "word12" for row in table)
    for row in table:
        assert 0.0 <= row["accuracy"] <= 100.0
        assert 0.0 <= row["recall_spam"] <= 100.0


# --- fitting and the artifact contract -----------------------------------


def test_pickle_round_trip_predicts_identically(tmp_path: Path) -> None:
    """The Phase 4 determinism requirement, tested without the real corpus."""
    texts, labels = synthetic_dataset()
    vectorizer, model = fit_model(texts, labels, {"features": "word12+char35", "alpha": 0.1})

    model_path = tmp_path / "m.pkl"
    vec_path = tmp_path / "v.pkl"
    model_path.write_bytes(pickle.dumps(model))
    vec_path.write_bytes(pickle.dumps(vectorizer))

    reloaded_model = pickle.loads(model_path.read_bytes())
    reloaded_vectorizer = pickle.loads(vec_path.read_bytes())

    samples = ["free prize claim win", "lunch meeting tomorrow later"]
    first = reloaded_model.predict(reloaded_vectorizer.transform(samples))
    second = reloaded_model.predict(reloaded_vectorizer.transform(samples))

    assert list(first) == list(second)
    assert list(first) == list(model.predict(vectorizer.transform(samples)))


def test_save_artifacts_writes_the_names_phase_6_will_load(tmp_path: Path) -> None:
    texts, labels = synthetic_dataset()
    vectorizer, model = fit_model(texts, labels, {"features": "word12", "alpha": 1.0})
    features = top_features(vectorizer, model, n=5)
    run = RunRecord(
        config={"features": "word12", "alpha": 1.0},
        cv_table=[],
        split={"test_size": 0.2, "random_state": 42, "n_train": 30, "n_test": 10},
        metrics=metrics_of(labels, labels),
        dataset={"path": "synthetic", "rows": len(texts), "spam": 20, "ham": 20},
    )

    paths = save_artifacts(tmp_path, vectorizer=vectorizer, model=model, run=run, features=features)

    assert {path.name for path in paths.values()} == {
        "naive_bayes.pkl",
        "tfidf_vectorizer.pkl",
        "metrics.json",
        "top_features.json",
        "training_run.json",
    }
    assert all(path.is_file() for path in paths.values())
    record = json.loads(paths["training_run"].read_text())
    assert record["selected_config"]["features"] == "word12"
    assert "selection_rule" in record


def test_top_features_ranks_words_and_excludes_char_ngrams(tmp_path: Path) -> None:
    texts, labels = synthetic_dataset()
    vectorizer, model = fit_model(texts, labels, {"features": "word12+char35", "alpha": 0.1})

    features = top_features(vectorizer, model, n=5)

    assert features["vocabulary_size"] > 0
    assert features["word_features_ranked"] < features["vocabulary_size"]
    ranked = features["top_by_log_odds"]["spam"]
    assert len(ranked) == 5
    assert all(not item["feature"].startswith("c__") for item in ranked)
    # The synthetic spam words should dominate the spam end of the ranking.
    assert any(item["feature"] in SPAM_WORDS for item in ranked)


def test_feature_grid_is_non_empty() -> None:
    assert FEATURE_KINDS
    assert ALPHAS
