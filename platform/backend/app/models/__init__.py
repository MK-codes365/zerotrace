"""
ZEROTrace — Database Models
Complete database schema for forensic platform.
Tables: users, cases, evidence, devices, jobs, job_tasks, workers,
recovered_files, file_fragments, reconstruction_candidates,
validation_results, hash_records, audit_events, chain_of_custody,
sanitization_operations, sanitization_verification, reports.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    BigInteger,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# ═══════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════

class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"


class CaseStatus(str, PyEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class EvidenceStatus(str, PyEnum):
    REGISTERED = "REGISTERED"
    ACQUIRED = "ACQUIRED"
    HASHED = "HASHED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    COMPLETED = "COMPLETED"


class DeviceType(str, PyEnum):
    HDD = "HDD"
    SSD = "SSD"
    USB = "USB"
    SD = "SD"
    EXTERNAL_HDD = "EXTERNAL_HDD"
    EXTERNAL_SSD = "EXTERNAL_SSD"
    FORENSIC_IMAGE = "FORENSIC_IMAGE"


class JobType(str, PyEnum):
    SANITIZATION = "SANITIZATION"
    FILE_ERASURE = "FILE_ERASURE"
    RECOVERY = "RECOVERY"
    CARVING = "CARVING"
    VALIDATION = "VALIDATION"
    HASHING = "HASHING"
    REPORT = "REPORT"


class JobStatus(str, PyEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FileCategory(str, PyEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    ARCHIVE = "ARCHIVE"
    DATABASE = "DATABASE"
    EXECUTABLE = "EXECUTABLE"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"


class ValidationStatus(str, PyEnum):
    VALID = "VALID"
    PARTIALLY_VALID = "PARTIALLY_VALID"
    CORRUPTED = "CORRUPTED"
    UNKNOWN = "UNKNOWN"


class CustodyAction(str, PyEnum):
    REGISTERED = "REGISTERED"
    ACQUIRED = "ACQUIRED"
    IMAGED = "IMAGED"
    HASHED = "HASHED"
    ANALYZED = "ANALYZED"
    RECOVERED = "RECOVERED"
    VALIDATED = "VALIDATED"
    EXPORTED = "EXPORTED"
    REPORTED = "REPORTED"
    SANITIZED = "SANITIZED"


class SanitizationMethod(str, PyEnum):
    ZERO_FILL = "ZERO_FILL"
    RANDOM_DATA = "RANDOM_DATA"
    DOD_522220M = "DOD_522220M"
    GUTMANN = "GUTMANN"
    NIST_800_88_CLEAR = "NIST_800_88_CLEAR"
    NIST_800_88_PURGE = "NIST_800_88_PURGE"
    SECURE_ERASE_ATA = "SECURE_ERASE_ATA"
    CRYPTO_ERASE = "CRYPTO_ERASE"
    SIMULATED = "SIMULATED"


class SanitizationStatus(str, PyEnum):
    PENDING = "PENDING"
    PREFLIGHT = "PREFLIGHT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


# ═══════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════

def _uuid():
    return uuid.uuid4()

def _utcnow():
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ANALYST)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)

    cases = relationship("Case", back_populates="investigator_user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN)
    investigator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)

    investigator_user = relationship("User", back_populates="cases")
    evidence_items = relationship("Evidence", back_populates="case")
    jobs = relationship("Job", back_populates="case")
    reports = relationship("Report", back_populates="case")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    evidence_number = Column(String(50), unique=True, nullable=False, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    source_device = Column(String(255), nullable=True)
    device_type = Column(Enum(DeviceType), nullable=True)
    serial_number = Column(String(255), nullable=True)
    filesystem = Column(String(50), nullable=True)
    capacity_bytes = Column(BigInteger, nullable=True)
    acquisition_timestamp = Column(DateTime(timezone=True), default=_utcnow)
    investigator = Column(String(255), nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    sha512_hash = Column(String(128), nullable=True)
    original_hash = Column(String(64), nullable=True)
    processing_hash = Column(String(64), nullable=True)
    final_hash = Column(String(64), nullable=True)
    image_path = Column(String(1024), nullable=True)
    acquisition_method = Column(String(100), nullable=True)
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.REGISTERED)
    is_read_only = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    case = relationship("Case", back_populates="evidence_items")
    recovered_files = relationship("RecoveredFile", back_populates="evidence")
    custody_events = relationship("ChainOfCustody", back_populates="evidence")
    hash_records = relationship("HashRecord", back_populates="evidence")
    jobs = relationship("Job", back_populates="evidence")


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=True)
    device_type = Column(Enum(DeviceType), nullable=False)
    capacity_bytes = Column(BigInteger, nullable=True)
    filesystem = Column(String(50), nullable=True)
    serial_number = Column(String(255), nullable=True)
    sector_size = Column(Integer, default=512)
    is_removable = Column(Boolean, default=False)
    is_read_only = Column(Boolean, default=False)
    is_system_drive = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone=True), default=_utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    sanitization_ops = relationship("SanitizationOperation", back_populates="device")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    priority = Column(Integer, default=5)
    worker_count = Column(Integer, default=1)
    progress = Column(Float, default=0.0)
    total_chunks = Column(Integer, default=0)
    processed_chunks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    config = Column(JSON, default=dict)
    results = Column(JSON, default=dict)
    errors = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    case = relationship("Case", back_populates="jobs")
    evidence = relationship("Evidence", back_populates="jobs")
    tasks = relationship("JobTask", back_populates="job")

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_type", "job_type"),
    )


class JobTask(Base):
    __tablename__ = "job_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    worker_id = Column(String(100), nullable=True)
    chunk_index = Column(Integer, nullable=True)
    chunk_offset = Column(BigInteger, nullable=True)
    chunk_size = Column(BigInteger, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    results = Column(JSON, default=dict)
    errors = Column(JSON, default=list)

    job = relationship("Job", back_populates="tasks")


class RecoveredFile(Base):
    __tablename__ = "recovered_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    artifact_id = Column(String(50), unique=True, nullable=False)
    filename = Column(String(500), nullable=True)
    file_type = Column(String(100), nullable=True)
    mime_type = Column(String(255), nullable=True)
    category = Column(Enum(FileCategory), default=FileCategory.UNKNOWN)
    offset = Column(BigInteger, nullable=False)
    size_bytes = Column(BigInteger, nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    confidence_score = Column(Float, default=0.0)
    is_fragmented = Column(Boolean, default=False)
    fragment_count = Column(Integer, default=1)
    recovery_method = Column(String(100), nullable=True)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.UNKNOWN)
    extension_mismatch = Column(Boolean, default=False)
    stored_path = Column(String(1024), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    evidence = relationship("Evidence", back_populates="recovered_files")
    fragments = relationship("FileFragment", back_populates="recovered_file")
    validation = relationship("ValidationResult", back_populates="recovered_file", uselist=False)


class FileFragment(Base):
    __tablename__ = "file_fragments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    recovered_file_id = Column(UUID(as_uuid=True), ForeignKey("recovered_files.id"), nullable=False)
    fragment_index = Column(Integer, nullable=False)
    offset = Column(BigInteger, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    entropy = Column(Float, nullable=True)
    is_contiguous = Column(Boolean, default=True)

    recovered_file = relationship("RecoveredFile", back_populates="fragments")


class ReconstructionCandidate(Base):
    __tablename__ = "reconstruction_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    fragment_ids = Column(JSON, default=list)
    reconstruction_path = Column(JSON, default=list)
    confidence_score = Column(Float, default=0.0)
    file_type = Column(String(100), nullable=True)
    total_size = Column(BigInteger, nullable=True)
    is_selected = Column(Boolean, default=False)
    method_scores = Column(JSON, default=dict)
    agreement_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    recovered_file_id = Column(UUID(as_uuid=True), ForeignKey("recovered_files.id"), nullable=False)
    signature_valid = Column(Boolean, nullable=True)
    structure_valid = Column(Boolean, nullable=True)
    footer_valid = Column(Boolean, nullable=True)
    parser_valid = Column(Boolean, nullable=True)
    size_valid = Column(Boolean, nullable=True)
    mime_consistent = Column(Boolean, nullable=True)
    metadata_consistent = Column(Boolean, nullable=True)
    overall_status = Column(Enum(ValidationStatus), default=ValidationStatus.UNKNOWN)
    details = Column(JSON, default=dict)
    validated_at = Column(DateTime(timezone=True), default=_utcnow)

    recovered_file = relationship("RecoveredFile", back_populates="validation")


class HashRecord(Base):
    __tablename__ = "hash_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(255), nullable=False)
    algorithm = Column(String(20), nullable=False, default="SHA-256")
    hash_value = Column(String(256), nullable=False)
    computed_at = Column(DateTime(timezone=True), default=_utcnow)
    computed_by = Column(String(255), nullable=True)
    is_original = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, default=dict)

    evidence = relationship("Evidence", back_populates="hash_records")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="INFO")
    source_ip = Column(String(45), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)


class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    operator = Column(String(255), nullable=False)
    action = Column(Enum(CustodyAction), nullable=False)
    source = Column(String(500), nullable=True)
    destination = Column(String(500), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)

    evidence = relationship("Evidence", back_populates="custody_events")


class SanitizationOperation(Base):
    __tablename__ = "sanitization_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    target_path = Column(String(1024), nullable=True)
    target_type = Column(String(50), nullable=False)  # drive / file / folder
    method = Column(Enum(SanitizationMethod), nullable=False)
    status = Column(Enum(SanitizationStatus), default=SanitizationStatus.PENDING)
    passes_total = Column(Integer, default=1)
    passes_completed = Column(Integer, default=0)
    bytes_total = Column(BigInteger, nullable=True)
    bytes_processed = Column(BigInteger, default=0)
    operator = Column(String(255), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_simulated = Column(Boolean, default=True)
    errors = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    device = relationship("Device", back_populates="sanitization_ops")
    verification = relationship("SanitizationVerification", back_populates="operation", uselist=False)


class SanitizationVerification(Base):
    __tablename__ = "sanitization_verification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    operation_id = Column(UUID(as_uuid=True), ForeignKey("sanitization_operations.id"), nullable=False)
    verification_method = Column(String(100), nullable=False)
    sample_offsets = Column(JSON, default=list)
    sample_results = Column(JSON, default=list)
    all_zero = Column(Boolean, nullable=True)
    random_read_pass = Column(Boolean, nullable=True)
    overall_pass = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), default=_utcnow)
    verified_by = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)

    operation = relationship("SanitizationOperation", back_populates="verification")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # forensic / sanitization / audit
    title = Column(String(500), nullable=False)
    format = Column(String(10), default="PDF")  # PDF / JSON / CSV
    file_path = Column(String(1024), nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sections = Column(JSON, default=dict)
    metadata_ = Column("metadata", JSON, default=dict)
    generated_at = Column(DateTime(timezone=True), default=_utcnow)

    case = relationship("Case", back_populates="reports")
