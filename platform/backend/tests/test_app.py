"""
ZEROTrace Advisor — Minimal Test App
Creates a FastAPI app with ONLY the advisor router (no DB, no auth)
to enable isolated acceptance-criteria testing.
"""

import sys
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_backend = Path(__file__).resolve().parent.parent
for p in [str(_backend), str(_backend / "app")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import only what we need — no DB, no auth, no Redis
from app.api.v1.endpoints.advisor import router as advisor_router

test_app = FastAPI(
    title="ZEROTrace Advisor (Test)",
    description="Isolated advisor test app for acceptance-criteria validation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

test_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

test_app.include_router(advisor_router, prefix="/api/v1")
