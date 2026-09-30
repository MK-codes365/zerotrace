"""
ZEROTrace — FastAPI Application Entry Point
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project and backend roots to path for engine imports
_app_dir = Path(__file__).resolve().parent
_backend_dir = _app_dir.parent
_project_dir = _backend_dir.parent

for _p in [str(_app_dir), str(_backend_dir), str(_project_dir), "/app"]:
    if _p not in sys.path and Path(_p).exists():
        sys.path.insert(0, _p)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging_config import setup_logging
from app.api.endpoints import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "safe_demo_mode": settings.SAFE_DEMO_MODE,
        "docs": "/docs",
        "api": "/api",
    }
