"""Settings loading and the production safety guard (docs/PLAN.md Phase 1)."""

import pytest
from pydantic import ValidationError

from app.config import BASE_DIR, DEV_JWT_SECRET, Settings

STRONG_SECRET = "s" * 40


def test_defaults_resolve_paths_against_backend_root(clean_env: pytest.MonkeyPatch) -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.model_path == BASE_DIR.parent / "ml" / "model.joblib"
    assert settings.model_path.is_absolute()
    assert settings.metadata_path == BASE_DIR.parent / "ml" / "metadata.json"


def test_cors_origins_accept_comma_separated_kwarg(clean_env: pytest.MonkeyPatch) -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_accept_comma_separated_env(clean_env: pytest.MonkeyPatch) -> None:
    """A plain comma list must not blow up on pydantic-settings' JSON decoding."""
    clean_env.setenv("CORS_ORIGINS", "http://a.test,http://b.test")

    assert Settings().cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_accept_json_list_env(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("CORS_ORIGINS", '["http://a.test"]')

    assert Settings().cors_origins == ["http://a.test"]


def test_production_rejects_default_jwt_secret(clean_env: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production")


def test_production_rejects_empty_jwt_secret(clean_env: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="")


def test_production_rejects_wildcard_cors(clean_env: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(environment="production", jwt_secret=STRONG_SECRET, cors_origins="*")


def test_production_accepts_hardened_config(clean_env: pytest.MonkeyPatch) -> None:
    settings = Settings(
        environment="production",
        jwt_secret=STRONG_SECRET,
        cors_origins="https://app.example.com",
    )

    assert settings.is_production
    assert settings.jwt_secret == STRONG_SECRET
    assert DEV_JWT_SECRET not in settings.cors_origins
