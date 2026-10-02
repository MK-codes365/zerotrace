"""
ZEROTrace — Central Configuration
All settings loaded from environment variables with safe defaults.
"""

import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with safe defaults."""

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "ZEROTrace"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Integrated Secure Data Erasure & Advanced File Recovery Platform"
    )
    DEBUG: bool = False

    # ── Safety ───────────────────────────────────────────
    SAFE_DEMO_MODE: bool = True  # CRITICAL: Default to safe mode
    REQUIRE_DOUBLE_CONFIRM: bool = True

    # ── Database ─────────────────────────────────────────
    _local_db = Path(__file__).resolve().parent.parent.parent / "zerotrace.db"
    DATABASE_URL: str = (
        f"sqlite+aiosqlite:///{_local_db}"
        if not os.path.exists("/.dockerenv") and not os.environ.get("DATABASE_URL")
        else "postgresql+asyncpg://zerotrace:zerotrace_secret@postgres:5432/zerotrace"
    )
    DATABASE_URL_SYNC: str = (
        f"sqlite:///{_local_db}"
        if not os.path.exists("/.dockerenv") and not os.environ.get("DATABASE_URL_SYNC")
        else "postgresql+psycopg2://zerotrace:zerotrace_secret@postgres:5432/zerotrace"
    )

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Auth / JWT ───────────────────────────────────────
    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-openssl-rand-hex-64",
        description="JWT signing key — MUST be overridden in production",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480  # 8 hours

    # ── Workers ──────────────────────────────────────────
    MAX_WORKERS: int = Field(
        default=max(1, (os.cpu_count() or 4) - 1),
        description="Worker pool size, defaults to CPU_COUNT - 1",
    )
    CHUNK_SIZE_MB: int = 256  # MapReduce chunk size in MB
    WORKER_TIMEOUT_SECONDS: int = 3600
    MAX_RETRY_COUNT: int = 3

    # ── Paths ────────────────────────────────────────────
    BASE_DIR: Path = Path("/app")
    EVIDENCE_STORAGE: Path = Path("/app/storage/evidence")
    REPORT_STORAGE: Path = Path("/app/storage/reports")
    TEMP_STORAGE: Path = Path("/app/storage/temp")
    LOG_DIR: Path = Path("/app/logs")

    # ── Carving ──────────────────────────────────────────
    MAX_CARVED_FILE_SIZE_MB: int = 500
    BOUNDARY_OVERLAP_BYTES: int = 65536  # 64 KB overlap between chunks

    # ── Logging ──────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
