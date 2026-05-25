"""
Global configuration settings using Pydantic BaseSettings.
Loads from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Smart Recruitment Platform – AI-Powered"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-super-secret-key-32chars"

    # ─── LLM ──────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "ollama"        # "openai" | "groq" | "ollama"
    LLM_MODEL: str = "llama3"           # specific ollama model
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ─── HuggingFace ──────────────────────────────────────────────────────────
    HF_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    HF_DEVICE: str = "cpu"

    # ─── MongoDB ──────────────────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "hr_platform"

    # ─── MySQL ────────────────────────────────────────────────────────────────
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "hr_user"
    MYSQL_PASSWORD: str = "hr_password"
    MYSQL_DB: str = "hr_structured"
    MYSQL_URL: str = "mysql+aiomysql://hr_user:hr_password@localhost:3306/hr_structured"

    # ─── SQLite fallback (useful for local dev without MySQL) ─────────────────
    USE_SQLITE: bool = True
    SQLITE_PATH: str = "./hr_local.db"

    # ─── Redis / Celery ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ─── CV Processing ────────────────────────────────────────────────────────
    CV_UPLOAD_DIR: str = "./uploaded_cvs"
    MAX_CV_SIZE_MB: int = 10
    OCR_ENABLED: bool = True
    SPACY_MODEL: str = "en_core_web_sm"

    # ─── GitHub ───────────────────────────────────────────────────────────────
    GITHUB_TOKEN: Optional[str] = None

    # ─── Langfuse (Observabilité & Tracing IA) ────────────────────────────────
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # ─── Privacy / RGPD ───────────────────────────────────────────────────────
    DATA_RETENTION_HOURS: int = 72      # Durée avant suppression automatique des PII
    ANONYMIZE_BEFORE_LLM: bool = True   # Anonymiser les données avant envoi au LLM

    # ─── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
