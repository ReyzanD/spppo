"""Prediction endpoint: classify a message as Penipuan or Bukan Penipuan."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.services.ml_service import load_active_model
from app.utils.errors import AppError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predict"])

MAX_MESSAGE_LENGTH = 1000


class PredictRequest(BaseModel):
    """Input for a fraud prediction."""

    message: str = Field(
        ...,
        max_length=MAX_MESSAGE_LENGTH,
        description="The SMS/WhatsApp message text to classify",
        examples=["Selamat! Anda memenangkan hadiah. Hubungi 081234567890 sekarang."],
    )

    @field_validator("message")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Pesan tidak boleh kosong")
        return stripped


class PredictResponse(BaseModel):
    """Prediction result with per-class probabilities."""

    label: Literal["Penipuan", "Bukan Penipuan"]
    probabilities: dict[str, float] = Field(
        description="Probability for each class; values sum to approximately 1"
    )
    processed_text: str = Field(description="Text after cleaning and stopword removal")


@router.post(
    "",
    summary="Classify a message as Penipuan or Bukan Penipuan",
    status_code=status.HTTP_200_OK,
    response_model=PredictResponse,
)
async def predict(request: Request, payload: PredictRequest) -> PredictResponse:
    """Classify one message using the trained TF-IDF + Naive Bayes model."""
    ml_service = getattr(request.app.state, "ml_service", None)
    if ml_service is None:
        settings = getattr(request.app.state, "settings", None) or get_settings()
        ml_service = load_active_model(settings)
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "MODEL_UNAVAILABLE: artifact model belum tersedia. "
                "Jalankan `python ml/train_model.py` terlebih dahulu."
            ),
        )

    try:
        return PredictResponse(**ml_service.predict(payload.message))
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Prediction failed for a %d-character message", len(payload.message))
        raise AppError(
            status_code=500,
            code="PREDICTION_ERROR",
            message="Gagal melakukan prediksi. Silakan coba lagi.",
        ) from exc
