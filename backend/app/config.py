"""Application settings, loaded from environment variables and/or a .env file."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# The directory that contains the `app` package (i.e. `backend/`).
BASE_DIR = Path(__file__).resolve().parent.parent

# Development default. The app refuses to start in production while this is in use.
DEV_JWT_SECRET = "dev-insecure-secret-change-me"


def parse_origins(value: str) -> list[str]:
    """Accept either a JSON array or a comma-separated list of origins.

    `.env` users write `CORS_ORIGINS=http://a,http://b`; container/CI config often
    supplies a JSON array instead. Both are accepted.
    """
    text = value.strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"CORS_ORIGINS is not valid JSON: {exc}") from exc
        if not isinstance(parsed, list):
            raise ValueError("CORS_ORIGINS JSON value must be an array")
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


class Settings(BaseSettings):
    """Runtime configuration. Every field can be provided via environment variable."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ------------------------------------------------------
    app_name: str = "Sistem Pendeteksi Pesan Penipuan Online"
    environment: Literal["development", "test", "production"] = "development"

    # --- Security ---------------------------------------------------------
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 7

    # Comma-separated in the environment, e.g. CORS_ORIGINS=http://a,http://b
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # --- Model artifacts (written by `python ml/train_model.py`) ----------
    # Namespaced so the legacy MODEL_DIR/MODEL_FILE variables from the earlier
    # .pkl setup cannot silently point the service at stale artifacts.
    ml_model_dir: str = "../ml"
    ml_model_file: str = "model.joblib"
    ml_vectorizer_file: str = "vectorizer.joblib"
    ml_metadata_file: str = "metadata.json"

    # --- Database (used from Phase 5 onwards) -----------------------------
    database_url: str = "sqlite:///./dev.db"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def model_path(self) -> Path:
        return self._resolve(self.ml_model_dir) / self.ml_model_file

    @property
    def vectorizer_path(self) -> Path:
        return self._resolve(self.ml_model_dir) / self.ml_vectorizer_file

    @property
    def metadata_path(self) -> Path:
        return self._resolve(self.ml_model_dir) / self.ml_metadata_file

    # The legacy `backend/training/` scripts still write .pkl artifacts under
    # backend/models/. These read-only names keep that path working; the new
    # serving path uses the ml_* fields above.
    @property
    def model_file(self) -> str:
        return "naive_bayes.pkl"

    @property
    def vectorizer_file(self) -> str:
        return "tfidf_vectorizer.pkl"

    @staticmethod
    def _resolve(value: str) -> Path:
        """Resolve a configured path against the backend root, not the current cwd."""
        path = Path(value)
        return (path if path.is_absolute() else BASE_DIR / path).resolve()

    # --- Validators -------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def _split_cors_origins(cls, data: object) -> object:
        """Accept `a,b` as well as a JSON list for CORS_ORIGINS."""
        if isinstance(data, dict):
            value = data.get("cors_origins")
            if isinstance(value, str):
                data = {**data, "cors_origins": parse_origins(value)}
        return data

    @model_validator(mode="after")
    def _guard_production(self) -> "Settings":
        """Fail fast instead of silently starting an insecure production service."""
        if self.is_production:
            if not self.jwt_secret or self.jwt_secret == DEV_JWT_SECRET:
                raise ValueError(
                    "JWT_SECRET must be set to a strong, unique value when ENVIRONMENT=production"
                )
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS must not contain '*' when ENVIRONMENT=production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
