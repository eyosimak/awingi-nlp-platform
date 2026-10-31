"""
Awingi NLP Platform — Shared Application Settings
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory (awingi-nlp-platform/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# On Vercel, data dirs should go to /tmp
_is_vercel = bool(os.getenv("VERCEL"))
_data_base = Path("/tmp") if _is_vercel else BASE_DIR

# Only reference .env if it actually exists
_env_file = str(BASE_DIR / ".env")
if not Path(_env_file).exists():
    _env_file = None


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Awingi NLP Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"

    # Storage Paths
    DATA_DIR: Path = _data_base / "data"
    RAW_DATA_DIR: Path = _data_base / "data" / "raw"
    PROCESSED_DATA_DIR: Path = _data_base / "data" / "processed"

    # Linguistic Standards
    DEFAULT_LANGUAGE: str = "awn"
    DEFAULT_ORTHOGRAPHY: str = "latin_official"

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
