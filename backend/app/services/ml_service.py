"""Model artifact loading and inference."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib

from app.config import Settings
from app.services.preprocessing import preprocess

logger = logging.getLogger(__name__)

LABEL_FRAUD = "Penipuan"
LABEL_HAM = "Bukan Penipuan"
LABELS = (LABEL_FRAUD, LABEL_HAM)


@dataclass
class MlService:
    """Handle to the loaded model, vectorizer and metadata."""

    model_path: Path
    vectorizer_path: Path
    metadata_path: Path
    _model: Any | None = field(default=None, repr=False)
    _vectorizer: Any | None = field(default=None, repr=False)
    _metadata: dict[str, Any] | None = field(default=None, repr=False)

    def _load_prediction_artifacts(self) -> None:
        if self._model is None:
            self._model = joblib.load(self.model_path)
        if self._vectorizer is None:
            self._vectorizer = joblib.load(self.vectorizer_path)

    def load_metadata(self) -> dict[str, Any] | None:
        """Read ``metadata.json`` once; return ``None`` when it is missing."""
        if self._metadata is None:
            if not self.metadata_path.is_file():
                return None
            self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return self._metadata

    def predict(self, message: str) -> dict[str, Any]:
        """Preprocess, vectorize and classify a single message."""
        self._load_prediction_artifacts()
        assert self._model is not None and self._vectorizer is not None

        processed_text = preprocess(message)
        features = self._vectorizer.transform([processed_text])
        scores = self._model.predict_proba(features)[0]
        classes = [str(name) for name in self._model.classes_]
        by_class = {name: float(score) for name, score in zip(classes, scores, strict=True)}

        probabilities = {label: round(by_class.get(label, 0.0), 4) for label in LABELS}
        label = max(probabilities, key=probabilities.__getitem__)
        return {
            "label": label,
            "probabilities": probabilities,
            "processed_text": processed_text,
        }


def load_active_model(settings: Settings) -> MlService | None:
    """Return an ``MlService`` when the prediction artifacts exist, else ``None``.

    A missing model is a normal state during development: the process still
    starts so ``/health`` and ``/docs`` are reachable, and prediction endpoints
    report 503 MODEL_UNAVAILABLE.
    """
    if not settings.model_path.is_file() or not settings.vectorizer_path.is_file():
        logger.warning(
            "Model artifacts not found (%s, %s). Run `python ml/train_model.py`.",
            settings.model_path,
            settings.vectorizer_path,
        )
        return None

    logger.info(
        "Model artifacts found: %s, %s, metadata=%s",
        settings.model_path,
        settings.vectorizer_path,
        settings.metadata_path.is_file(),
    )
    return MlService(
        model_path=settings.model_path,
        vectorizer_path=settings.vectorizer_path,
        metadata_path=settings.metadata_path,
    )
