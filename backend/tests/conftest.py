"""Shared pytest fixtures."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _test_environment() -> Iterator[None]:
    """Force ENVIRONMENT=test and drop any cached settings built before it."""
    previous = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "test"

    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

    if previous is None:
        os.environ.pop("ENVIRONMENT", None)
    else:
        os.environ["ENVIRONMENT"] = previous


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Remove app-related variables so a test sees only its own inputs."""
    for name in (
        "ENVIRONMENT",
        "JWT_SECRET",
        "CORS_ORIGINS",
        "ML_MODEL_DIR",
        "ML_MODEL_FILE",
        "ML_VECTORIZER_FILE",
        "ML_METADATA_FILE",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """A TestClient with the app's lifespan executed (so startup logic is covered)."""
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
