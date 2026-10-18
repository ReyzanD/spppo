"""Liveness/readiness probe."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health(request: Request) -> dict[str, object]:
    """Report process health.

    Unlike every other endpoint this one is intentionally *not* wrapped in the
    `{status, data}` envelope (see docs/FRD.md §4.12); it matches the exact shape
    documented there so uptime probes can read it directly.
    """
    ml_service = getattr(request.app.state, "ml_service", None)
    return {"status": "ok", "model_loaded": ml_service is not None}
