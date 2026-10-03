"""
ZEROTrace — Advisor Schemas
Pydantic models for the forensic recovery advisor endpoint.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════


class StorageMedium(str, Enum):
    """Supported storage medium types."""
    SSD = "SSD"
    HDD = "HDD"
    USB = "USB"
    SD_CARD = "SD_CARD"


class FileSystem(str, Enum):
    """Supported file system types."""
    NTFS = "NTFS"
    FAT32 = "FAT32"
    EXFAT = "EXFAT"
    EXT4 = "EXT4"
    UNKNOWN = "UNKNOWN"


class LossScenario(str, Enum):
    """Data loss scenario categories."""
    DELETED = "DELETED"
    FORMATTED = "FORMATTED"
    CORRUPTED = "CORRUPTED"
    HARDWARE_ISSUE = "HARDWARE_ISSUE"


class RiskLevel(str, Enum):
    """Risk level of the recommended recovery approach."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    """Recommended primary action to perform in ZeroTrace."""
    LAUNCH_CARVE = "LAUNCH_CARVE"
    IMAGE_DISK = "IMAGE_DISK"
    RUN_MFT_SCAN = "RUN_MFT_SCAN"


# ═══════════════════════════════════════════════════════════
# Request / Response
# ═══════════════════════════════════════════════════════════


class AdvisorRequest(BaseModel):
    """
    Describes a user's data-loss scenario so the forensic advisor
    can return a tailored recovery recommendation.
    """
    storage_medium: StorageMedium = Field(
        ...,
        description="Physical storage type where data was lost.",
        example="SSD",
    )
    file_system: FileSystem = Field(
        ...,
        description="File system present on the storage medium.",
        example="NTFS",
    )
    loss_scenario: LossScenario = Field(
        ...,
        description="Category of data-loss event.",
        example="DELETED",
    )
    target_extension: Optional[str] = Field(
        None,
        description="Optional target file extension to recover (e.g. 'mp4', 'raw', 'jpg').",
        example="mp4",
        pattern=r"^[a-zA-Z0-9]{1,10}$",
    )


class AdvisorResponse(BaseModel):
    """
    Expert forensic recovery recommendation returned by the advisor engine.
    """
    recommended_method: str = Field(
        ...,
        description="Human-readable description of the recommended recovery method.",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Risk level associated with the recommended approach.",
    )
    safety_warnings: List[str] = Field(
        default_factory=list,
        description="Ordered list of safety warnings the operator must acknowledge before proceeding.",
    )
    action_type: ActionType = Field(
        ...,
        description="Primary action to launch in ZeroTrace.",
    )


# ═══════════════════════════════════════════════════════════
# Chat
# ═══════════════════════════════════════════════════════════


class AdvisorChatRequest(BaseModel):
    """Free-form forensic question for conversational Q&A."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural-language forensic question.",
        example="Is it safe to run carving directly on an SSD that has TRIM enabled?",
    )
    context: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional additional context (e.g. OS, tool version).",
    )


class AdvisorChatResponse(BaseModel):
    """Conversational answer from the forensic advisor."""
    answer: str = Field(..., description="Expert forensic answer.")
    related_warnings: List[str] = Field(
        default_factory=list,
        description="Any safety warnings relevant to the question.",
    )
    suggested_action: Optional[ActionType] = Field(
        None,
        description="Suggested ZeroTrace action if applicable.",
    )
