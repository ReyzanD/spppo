"""Export training metrics to the SQLite database via SQLAlchemy.

This module writes the training run metrics (accuracy, recall, precision, F1,
confusion matrix, and artifact paths) to the `training_runs` table so that
Phase 5 can later query them via SQLAlchemy models.

Usage:
    from app.services.export_metrics import export_training_run
    export_training_run(
        version="v1",
        accuracy=97.87,
        precision_spam=89.21,
        recall_spam=94.66,
        f1_spam=91.85,
        confusion_matrix=[[889, 15], [7, 124]],
        vectorizer_path="models/tfidf_vectorizer.pkl",
        classifier_path="models/naive_bayes.pkl",
        dataset_size=5171,
        spam_count=653,
        ham_count=4518,
        train_test_split=0.2,
    )
"""

from datetime import UTC, datetime

from sqlalchemy import (
    MetaData,
    create_engine,
    insert,
)

# Engine configured to use the same DB as Alembic
_engine = create_engine("sqlite:///./app.db")

_meta = MetaData()
# Reflect existing tables so we don't re-create them
_meta.reflect(bind=_engine)
_training_runs_table = _meta.tables["training_runs"]


def _get_connection():
    """Return a SQLAlchemy connection bound to the engine."""
    return _engine.connect()


def export_training_run(
    *,
    version: str,
    accuracy: float,
    precision_spam: float,
    recall_spam: float,
    f1_spam: float,
    confusion_matrix: list,
    vectorizer_path: str,
    classifier_path: str,
    dataset_size: int,
    spam_count: int,
    ham_count: int,
    train_test_split: float,
    precision_ham: float | None = None,
    recall_ham: float | None = None,
) -> None:
    """Insert a new training run row into the database.

    The confusion_matrix should be a 2×2 list [[TN, FP], [FN, TP]].
    All numeric values are expected as Python native types (int/float).
    """
    tn, fp = confusion_matrix[0]
    fn, tp = confusion_matrix[1]

    now = datetime.now(UTC)

    with _get_connection() as conn:
        stmt = (
            insert(_training_runs_table)
            .values(
                version=version,
                accuracy=accuracy,
                precision_spam=precision_spam,
                recall_spam=recall_spam,
                f1_spam=f1_spam,
                precision_ham=precision_ham,
                recall_ham=recall_ham,
                confusion_tn=tn,
                confusion_fp=fp,
                confusion_fn=fn,
                confusion_tp=tp,
                vectorizer_config='{"vectorizer": "tfidf", "ngram_range": [1, 2]}',
                classifier_config='{"classifier": "multinomial_nb", "alpha": 0.1}',
                vectorizer_path=vectorizer_path,
                classifier_path=classifier_path,
                dataset_size=dataset_size,
                spam_count=spam_count,
                ham_count=ham_count,
                train_test_split=train_test_split,
                created_at=now,
            )
            .on_conflict_do_update(
                index_elements=["version"],
                set_={
                    "accuracy": accuracy,
                    "precision_spam": precision_spam,
                    "recall_spam": recall_spam,
                    "f1_spam": f1_spam,
                    "confusion_tn": tn,
                    "confusion_fp": fp,
                    "confusion_fn": fn,
                    "confusion_tp": tp,
                    "vectorizer_config": '{"vectorizer": "tfidf", "ngram_range": [1, 2]}',
                    "classifier_config": '{"classifier": "multinomial_nb", "alpha": 0.1}',
                    "vectorizer_path": vectorizer_path,
                    "classifier_path": classifier_path,
                    "dataset_size": dataset_size,
                    "spam_count": spam_count,
                    "ham_count": ham_count,
                    "train_test_split": train_test_split,
                    "created_at": now,
                },
            )
        )
        conn.execute(stmt)
        conn.commit()
    print(f"Training run {version} exported to DB successfully.")


def list_training_runs() -> list[dict]:
    """Return all training runs as dictionaries (for Phase 5 API)."""
    with _get_connection() as conn:
        result = conn.execute(
            _training_runs_table.select().order_by(_training_runs_table.c.created_at.desc())
        ).fetchall()
    return [dict(row) for row in result]
