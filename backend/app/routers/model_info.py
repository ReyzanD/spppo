"""Model information endpoint backed by ml/metadata.json."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.services.ml_service import load_active_model

router = APIRouter(tags=["model"])


@router.get("/model-info", summary="Metadata of the trained model")
async def model_info(request: Request) -> dict[str, Any]:
    """Return algorithm, accuracy, dataset and split information."""
    ml_service = getattr(request.app.state, "ml_service", None)
    if ml_service is None:
        settings = getattr(request.app.state, "settings", None) or get_settings()
        ml_service = load_active_model(settings)
    if ml_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MODEL_UNAVAILABLE: jalankan `python ml/train_model.py` terlebih dahulu.",
        )

    metadata = ml_service.load_metadata()
    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MODEL_METADATA_UNAVAILABLE: metadata.json tidak ditemukan.",
        )
    return metadata
