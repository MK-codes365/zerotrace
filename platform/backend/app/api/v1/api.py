"""
ZEROTrace — v1 API Router
Aggregates all v1 endpoint routers under the /v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.advisor import router as advisor_router

api_router = APIRouter(prefix="/v1")

# Register sub-routers
api_router.include_router(advisor_router)
