"""
ZEROTrace — Advisor API Endpoints
POST /api/v1/advisor/recommend  — Forensic rule-matrix recommendation
POST /api/v1/advisor/chat       — Free-form forensic Q&A
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.advisor import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorRequest,
    AdvisorResponse,
)
from app.services.advisor_service import advisor_service

router = APIRouter(prefix="/advisor", tags=["Forensic Advisor"])


@router.post(
    "/recommend",
    response_model=AdvisorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get forensic recovery recommendation",
    description=(
        "Evaluates a data-loss scenario based on storage medium, file system, "
        "and loss reason, then returns an expert forensic recovery recommendation "
        "with risk classification and safety warnings."
    ),
    responses={
        200: {"description": "Successful recovery recommendation"},
        422: {"description": "Validation error in request payload"},
    },
)
async def recommend(req: AdvisorRequest) -> AdvisorResponse:
    """
    **Forensic Rule Matrix**

    | Scenario | Risk | Action |
    |---|---|---|
    | Hardware failure | CRITICAL | IMAGE_DISK |
    | SSD + Deletion (TRIM risk) | MEDIUM | IMAGE_DISK |
    | Quick Format | LOW | LAUNCH_CARVE |
    | Fragmented MP4 / RAW | MEDIUM | LAUNCH_CARVE |
    | NTFS + Deletion | LOW | RUN_MFT_SCAN |
    | Generic deletion | LOW | LAUNCH_CARVE |
    | Corruption | MEDIUM–CRITICAL | IMAGE_DISK |
    """
    try:
        return advisor_service.recommend(req)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advisor engine error: {exc}",
        ) from exc


@router.post(
    "/chat",
    response_model=AdvisorChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Forensic advisor chat (Q&A)",
    description=(
        "Free-form conversational endpoint for forensic questions. "
        "Returns an expert answer, relevant safety warnings, and a suggested "
        "ZeroTrace action when applicable."
    ),
    responses={
        200: {"description": "Successful forensic answer"},
        422: {"description": "Validation error in request payload"},
    },
)
async def chat(req: AdvisorChatRequest) -> AdvisorChatResponse:
    """
    Ask any forensic data-recovery question in plain English.

    Example questions:
    - *"Is it safe to run carving directly on an SSD with TRIM enabled?"*
    - *"My HDD is making clicking sounds, what should I do?"*
    - *"How do I recover a quick-formatted FAT32 USB drive?"*
    """
    try:
        return advisor_service.chat(req)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat engine error: {exc}",
        ) from exc
