"""
ZEROTrace — Pydantic Schemas
Request/response models for all API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


# ═══════════════════════════════════════════════════════════
# Common
# ═══════════════════════════════════════════════════════════

class StatusResponse(BaseModel):
    status: str
    message: str
    data: Any = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    version: str
    safe_demo_mode: bool
    database: str
    redis: str
    timestamp: datetime


# ═══════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = "ANALYST"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Cases
# ═══════════════════════════════════════════════════════════

class CaseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CaseResponse(BaseModel):
    id: UUID
    case_number: str
    title: str
    description: Optional[str]
    status: str
    investigator_id: UUID
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    job_count: int = 0

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Evidence
# ═══════════════════════════════════════════════════════════

class EvidenceCreate(BaseModel):
    case_id: UUID
    source_device: Optional[str] = None
    device_type: Optional[str] = None
    serial_number: Optional[str] = None
    filesystem: Optional[str] = None
    capacity_bytes: Optional[int] = None
    investigator: Optional[str] = None
    image_path: Optional[str] = None
    acquisition_method: Optional[str] = "manual"


class EvidenceResponse(BaseModel):
    id: UUID
    evidence_number: str
    case_id: UUID
    source_device: Optional[str]
    device_type: Optional[str]
    serial_number: Optional[str]
    filesystem: Optional[str]
    capacity_bytes: Optional[int]
    acquisition_timestamp: datetime
    investigator: Optional[str]
    sha256_hash: Optional[str]
    sha512_hash: Optional[str]
    original_hash: Optional[str]
    image_path: Optional[str]
    acquisition_method: Optional[str]
    status: str
    is_read_only: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceHashRequest(BaseModel):
    algorithm: str = "SHA-256"


# ═══════════════════════════════════════════════════════════
# Jobs
# ═══════════════════════════════════════════════════════════

class JobCreate(BaseModel):
    case_id: Optional[UUID] = None
    evidence_id: Optional[UUID] = None
    job_type: str
    config: dict = {}
    worker_count: Optional[int] = None


class JobResponse(BaseModel):
    id: UUID
    case_id: Optional[UUID]
    evidence_id: Optional[UUID]
    job_type: str
    status: str
    priority: int
    worker_count: int
    progress: float
    total_chunks: int
    processed_chunks: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    config: dict
    results: dict
    errors: list

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Recovery
# ═══════════════════════════════════════════════════════════

class RecoveryRequest(BaseModel):
    evidence_id: UUID
    case_id: Optional[UUID] = None
    file_types: list[str] = []  # empty = all supported types
    chunk_size_mb: int = 256
    worker_count: Optional[int] = None


class RecoveredFileResponse(BaseModel):
    id: UUID
    artifact_id: str
    evidence_id: UUID
    filename: Optional[str]
    file_type: Optional[str]
    mime_type: Optional[str]
    category: str
    offset: int
    size_bytes: Optional[int]
    sha256_hash: Optional[str]
    confidence_score: float
    is_fragmented: bool
    fragment_count: int
    recovery_method: Optional[str]
    validation_status: str
    extension_mismatch: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Sanitization
# ═══════════════════════════════════════════════════════════

class SanitizationPreviewRequest(BaseModel):
    target_path: str
    target_type: str = "drive"  # drive / file / folder


class SanitizationPreviewResponse(BaseModel):
    target_path: str
    target_type: str
    device_type: Optional[str]
    capacity_bytes: Optional[int]
    filesystem: Optional[str]
    serial_number: Optional[str]
    recommended_method: str
    estimated_duration_seconds: Optional[int]
    is_system_drive: bool
    warnings: list[str]


class SanitizationExecuteRequest(BaseModel):
    target_path: str
    target_type: str
    method: str
    confirmation_text: str = Field(
        ..., description="Must be exactly 'CONFIRM SANITIZATION'"
    )
    second_confirmation: bool = False
    operator: str


class SanitizationResponse(BaseModel):
    id: UUID
    target_path: Optional[str]
    target_type: str
    method: str
    status: str
    passes_total: int
    passes_completed: int
    bytes_total: Optional[int]
    bytes_processed: int
    operator: Optional[str]
    is_simulated: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    errors: list

    model_config = {"from_attributes": True}


class SanitizationVerifyResponse(BaseModel):
    operation_id: UUID
    verification_method: str
    overall_pass: bool
    all_zero: Optional[bool]
    random_read_pass: Optional[bool]
    sample_count: int
    verified_at: datetime
    details: dict


# ═══════════════════════════════════════════════════════════
# Audit
# ═══════════════════════════════════════════════════════════

class AuditEventResponse(BaseModel):
    id: UUID
    case_id: Optional[UUID]
    evidence_id: Optional[UUID]
    job_id: Optional[UUID]
    user_id: Optional[UUID]
    event_type: str
    action: str
    description: Optional[str]
    severity: str
    previous_hash: Optional[str]
    current_hash: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Integrity
# ═══════════════════════════════════════════════════════════

class IntegrityVerifyRequest(BaseModel):
    evidence_id: UUID


class IntegrityVerifyResponse(BaseModel):
    evidence_id: UUID
    original_hash: Optional[str]
    current_hash: str
    integrity_valid: bool
    merkle_root: Optional[str]
    hash_chain_valid: bool
    verified_at: datetime


# ═══════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    case_id: UUID
    report_type: str = "forensic"  # forensic / sanitization / audit
    format: str = "JSON"  # PDF / JSON / CSV
    title: Optional[str] = None


class ReportResponse(BaseModel):
    id: UUID
    case_id: UUID
    report_type: str
    title: str
    format: str
    file_path: Optional[str]
    sha256_hash: Optional[str]
    generated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    active_jobs: int
    completed_jobs: int
    recovery_jobs: int
    sanitization_jobs: int
    failed_jobs: int
    evidence_items: int
    total_cases: int
    recent_audit_events: list[AuditEventResponse]
    integrity_status: str
    recovered_files_count: int
    throughput_mbps: float
    workers_active: int


# ═══════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════

class DemoRunRequest(BaseModel):
    scenario: str = "full"  # full / recovery_only / sanitization_only


class DemoRunResponse(BaseModel):
    status: str
    case_id: UUID
    evidence_id: UUID
    job_id: UUID
    steps_completed: list[str]
    recovered_files: int
    merkle_root: str
    report_id: Optional[UUID]
    duration_seconds: float
