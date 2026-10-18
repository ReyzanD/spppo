"""FastAPI entry point: run with `uvicorn app.main:app --reload` from `backend/`."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import Settings, get_settings
from app.routers import health, model_info, predict
from app.services.ml_service import load_active_model
from app.utils.errors import register_exception_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load shared resources once per process, not per request (NFR-05)."""
    settings: Settings = get_settings()
    app.state.settings = settings
    app.state.ml_service = load_active_model(settings)
    logger.info(
        "Startup complete: env=%s version=%s model_loaded=%s",
        settings.environment,
        __version__,
        app.state.ml_service is not None,
    )
    yield
    app.state.ml_service = None


def create_app() -> FastAPI:
    """Build the application. Kept as a factory so tests can build one per run."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API deteksi pesan penipuan dengan TF-IDF + Multinomial Naive Bayes "
            "pada dataset SMS Indonesia."
        ),
        lifespan=lifespan,
    )

    cors_kwargs = {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if not settings.is_production:
        cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    app.add_middleware(
        CORSMiddleware,
        **cors_kwargs,
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(predict.router)
    app.include_router(model_info.router)

    return app


app = create_app()
