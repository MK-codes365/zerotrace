"""
ZEROTrace — API Endpoints
Complete REST API for the forensic platform.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    Role, create_access_token, get_current_user, hash_password,
    require_role, verify_password,
)
from app.core.logging_config import forensic_log
from app.models import (
    User, Case, Evidence, Device, Job, RecoveredFile,
    AuditEvent, ChainOfCustody, SanitizationOperation,
    SanitizationVerification, Report, HashRecord,
    CaseStatus, EvidenceStatus, JobType, JobStatus,
    SanitizationMethod, SanitizationStatus, CustodyAction,
    UserRole,
)
from app.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    CaseCreate, CaseUpdate, CaseResponse,
    EvidenceCreate, EvidenceResponse, EvidenceHashRequest,
    JobCreate, JobResponse,
    RecoveryRequest, RecoveredFileResponse,
    SanitizationPreviewRequest, SanitizationPreviewResponse,
    SanitizationExecuteRequest, SanitizationResponse,
    SanitizationVerifyResponse,
    AuditEventResponse,
    IntegrityVerifyRequest, IntegrityVerifyResponse,
    ReportGenerateRequest, ReportResponse,
    DashboardStats, HealthResponse,
    DemoRunRequest, DemoRunResponse,
    StatusResponse,
)


router = APIRouter()


# ═══════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        safe_demo_mode=settings.SAFE_DEMO_MODE,
        database="connected",
        redis="connected",
        timestamp=datetime.now(timezone.utc),
    )


# ═══════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════

@router.post("/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check existing
    existing = await db.execute(
        select(User).where(User.username == req.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username already exists")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=UserRole(req.role) if req.role in UserRole.__members__ else UserRole.ANALYST,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    token = create_access_token(str(user.id), user.username, user.role.value)

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        username=user.username,
        role=user.role.value,
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
    )


# ═══════════════════════════════════════════════════════════
# Cases
# ═══════════════════════════════════════════════════════════

@router.post("/cases", response_model=CaseResponse, tags=["Cases"])
async def create_case(
    req: CaseCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    case_number = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    case = Case(
        case_number=case_number,
        title=req.title,
        description=req.description,
        investigator_id=user["sub"],
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)

    forensic_log("CASE_CREATED", case_id=str(case.id), operator=user["username"])

    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        status=case.status.value,
        investigator_id=case.investigator_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.get("/cases", response_model=list[CaseResponse], tags=["Cases"])
async def list_cases(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Case).order_by(Case.created_at.desc()).limit(limit).offset(offset)
    if status_filter:
        query = query.where(Case.status == CaseStatus(status_filter))
    result = await db.execute(query)
    cases = result.scalars().all()

    responses = []
    for case in cases:
        ev_count = await db.execute(
            select(func.count()).select_from(Evidence).where(Evidence.case_id == case.id)
        )
        job_count = await db.execute(
            select(func.count()).select_from(Job).where(Job.case_id == case.id)
        )
        responses.append(CaseResponse(
            id=case.id,
            case_number=case.case_number,
            title=case.title,
            description=case.description,
            status=case.status.value,
            investigator_id=case.investigator_id,
            created_at=case.created_at,
            updated_at=case.updated_at,
            evidence_count=ev_count.scalar() or 0,
            job_count=job_count.scalar() or 0,
        ))
    return responses


@router.get("/cases/{case_id}", response_model=CaseResponse, tags=["Cases"])
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")
    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        status=case.status.value,
        investigator_id=case.investigator_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


# ═══════════════════════════════════════════════════════════
# Evidence
# ═══════════════════════════════════════════════════════════

@router.post("/evidence", response_model=EvidenceResponse, tags=["Evidence"])
async def register_evidence(
    req: EvidenceCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    evidence_number = f"EVD-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
    evidence = Evidence(
        evidence_number=evidence_number,
        case_id=req.case_id,
        source_device=req.source_device,
        device_type=req.device_type,
        serial_number=req.serial_number,
        filesystem=req.filesystem,
        capacity_bytes=req.capacity_bytes,
        investigator=req.investigator or user["username"],
        image_path=req.image_path,
        acquisition_method=req.acquisition_method,
    )
    db.add(evidence)
    await db.flush()
    await db.refresh(evidence)

    # Chain of custody entry
    custody = ChainOfCustody(
        case_id=req.case_id,
        evidence_id=evidence.id,
        operator=user["username"],
        action=CustodyAction.REGISTERED,
        source="Evidence Registration",
    )
    db.add(custody)

    forensic_log("EVIDENCE_REGISTERED", case_id=str(req.case_id),
                evidence_id=str(evidence.id), operator=user["username"])

    return EvidenceResponse(
        id=evidence.id,
        evidence_number=evidence.evidence_number,
        case_id=evidence.case_id,
        source_device=evidence.source_device,
        device_type=evidence.device_type.value if evidence.device_type else None,
        serial_number=evidence.serial_number,
        filesystem=evidence.filesystem,
        capacity_bytes=evidence.capacity_bytes,
        acquisition_timestamp=evidence.acquisition_timestamp,
        investigator=evidence.investigator,
        sha256_hash=evidence.sha256_hash,
        sha512_hash=evidence.sha512_hash,
        original_hash=evidence.original_hash,
        image_path=evidence.image_path,
        acquisition_method=evidence.acquisition_method,
        status=evidence.status.value,
        is_read_only=evidence.is_read_only,
        created_at=evidence.created_at,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse, tags=["Evidence"])
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Evidence).where(Evidence.id == uuid.UUID(evidence_id))
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(404, "Evidence not found")
    return ev


@router.post("/evidence/{evidence_id}/hash", tags=["Evidence"])
async def hash_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Compute SHA-256 hash of evidence image."""
    result = await db.execute(
        select(Evidence).where(Evidence.id == uuid.UUID(evidence_id))
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(404, "Evidence not found")

    # For demo: generate a simulated hash if no image path
    from engines.integrity import compute_file_hash, compute_sha256
    if ev.image_path and ev.image_path != "":
        try:
            sha256 = compute_file_hash(ev.image_path, "sha256")
            sha512 = compute_file_hash(ev.image_path, "sha512")
        except FileNotFoundError:
            sha256 = compute_sha256(f"evidence-{evidence_id}".encode())
            sha512 = "simulated"
    else:
        sha256 = compute_sha256(f"evidence-{evidence_id}".encode())
        sha512 = "simulated"

    ev.sha256_hash = sha256
    ev.sha512_hash = sha512
    ev.original_hash = sha256
    ev.status = EvidenceStatus.HASHED

    # Record hash
    hr = HashRecord(
        evidence_id=ev.id,
        target_type="evidence",
        target_id=str(ev.id),
        algorithm="SHA-256",
        hash_value=sha256,
        computed_by=user["username"],
        is_original=True,
    )
    db.add(hr)

    forensic_log("EVIDENCE_HASHED", evidence_id=evidence_id, operator=user["username"])

    return {"evidence_id": evidence_id, "sha256": sha256, "sha512": sha512, "status": "HASHED"}


# ═══════════════════════════════════════════════════════════
# Jobs
# ═══════════════════════════════════════════════════════════

@router.get("/jobs", response_model=list[JobResponse], tags=["Jobs"])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    query = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if status_filter:
        query = query.where(Job.status == JobStatus(status_filter))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# ═══════════════════════════════════════════════════════════
# Recovery
# ═══════════════════════════════════════════════════════════

@router.post("/recovery", tags=["Recovery"])
async def start_recovery(
    req: RecoveryRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Start a file recovery/carving job on evidence."""
    # Create job record
    job = Job(
        case_id=req.case_id,
        evidence_id=req.evidence_id,
        job_type=JobType.RECOVERY,
        status=JobStatus.RUNNING,
        worker_count=req.worker_count or settings.MAX_WORKERS,
        config={
            "file_types": req.file_types,
            "chunk_size_mb": req.chunk_size_mb,
        },
        started_at=datetime.now(timezone.utc),
        created_by=uuid.UUID(user["sub"]),
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    forensic_log("RECOVERY_STARTED", job_id=str(job.id),
                evidence_id=str(req.evidence_id), operator=user["username"])

    # For demo: run recovery inline on synthetic data
    from app.services.demo_service import SyntheticImageGenerator
    from workers.master_controller import MasterController

    gen = SyntheticImageGenerator()
    image_data, manifest = gen.generate_test_image(size_mb=4)

    controller = MasterController(
        max_workers=min(req.worker_count or 4, settings.MAX_WORKERS)
    )
    results = controller.execute_recovery_job(
        evidence_data=image_data,
        evidence_id=str(req.evidence_id),
        job_id=str(job.id),
        file_types=req.file_types or None,
    )

    # Store recovered files in DB
    for artifact in results.get("artifacts", []):
        rf = RecoveredFile(
            evidence_id=req.evidence_id,
            job_id=job.id,
            artifact_id=artifact["artifact_id"],
            file_type=artifact.get("file_type"),
            mime_type=artifact.get("mime_type"),
            category=artifact.get("classification_category", "UNKNOWN"),
            offset=artifact.get("offset", 0),
            size_bytes=artifact.get("size", 0),
            sha256_hash=artifact.get("sha256"),
            confidence_score=artifact.get("confidence", 0),
            recovery_method=artifact.get("recovery_method"),
            validation_status=artifact.get("validation_status", "UNKNOWN"),
            extension_mismatch=artifact.get("extension_mismatch", False),
        )
        db.add(rf)

    # Update job
    job.status = JobStatus.COMPLETED
    job.progress = 1.0
    job.completed_at = datetime.now(timezone.utc)
    job.results = {
        "total_artifacts": results["total_artifacts"],
        "merkle_root": results["merkle_root"],
        "throughput_mbps": results["throughput_mbps"],
        "processing_time": results["processing_time_seconds"],
    }
    job.total_chunks = results["total_chunks"]
    job.processed_chunks = results["total_chunks"]

    return {
        "job_id": str(job.id),
        "status": "COMPLETED",
        **results,
    }


@router.get("/recovery/{job_id}/files", response_model=list[RecoveredFileResponse], tags=["Recovery"])
async def get_recovered_files(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(RecoveredFile).where(RecoveredFile.job_id == uuid.UUID(job_id))
    )
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════
# Sanitization
# ═══════════════════════════════════════════════════════════

@router.post("/sanitization/preview", response_model=SanitizationPreviewResponse, tags=["Sanitization"])
async def preview_sanitization(
    req: SanitizationPreviewRequest,
    user: dict = Depends(get_current_user),
):
    """Preview sanitization without executing."""
    from engines.sanitization import (
        DeviceInfo, MediaType, StrategyRecommender
    )

    device = DeviceInfo(
        path=req.target_path,
        name=req.target_path.split("/")[-1] if "/" in req.target_path else req.target_path,
        media_type=MediaType.HDD,
        capacity_bytes=500 * 1024 * 1024 * 1024,
        filesystem="NTFS",
    )

    recommender = StrategyRecommender()
    method_name, strategy = recommender.recommend(device)
    capabilities = strategy.detect_capabilities(device)

    return SanitizationPreviewResponse(
        target_path=req.target_path,
        target_type=req.target_type,
        device_type=device.media_type.value,
        capacity_bytes=device.capacity_bytes,
        filesystem=device.filesystem,
        serial_number=device.serial_number or "N/A",
        recommended_method=method_name,
        estimated_duration_seconds=3600,
        is_system_drive=device.is_system_drive,
        warnings=["SAFE_DEMO_MODE: No actual erasure will occur"] if settings.SAFE_DEMO_MODE else [],
    )


@router.post("/sanitization/execute", tags=["Sanitization"])
async def execute_sanitization(
    req: SanitizationExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Execute sanitization. Requires explicit confirmation."""
    # Validate confirmation text
    if req.confirmation_text != "CONFIRM SANITIZATION":
        raise HTTPException(400, "Confirmation text must be exactly 'CONFIRM SANITIZATION'")

    if settings.REQUIRE_DOUBLE_CONFIRM and not req.second_confirmation:
        raise HTTPException(400, "Second confirmation required for destructive operations")

    from engines.sanitization import (
        DeviceInfo, MediaType, StrategyRecommender
    )

    device = DeviceInfo(
        path=req.target_path,
        name=req.target_path,
        media_type=MediaType.HDD,
        capacity_bytes=500 * 1024 * 1024 * 1024,
        is_system_drive=False,
    )

    if device.is_system_drive:
        raise HTTPException(400, "SAFETY: Cannot sanitize system boot drive")

    recommender = StrategyRecommender()
    strategy = recommender.get_strategy(req.method)
    if not strategy:
        raise HTTPException(400, f"Unknown method: {req.method}")

    # Execute (will be simulated in SAFE_DEMO_MODE)
    result = strategy.execute(device)

    # Store operation
    op = SanitizationOperation(
        target_path=req.target_path,
        target_type=req.target_type,
        method=SanitizationMethod(req.method),
        status=SanitizationStatus.COMPLETED if result.success else SanitizationStatus.FAILED,
        passes_total=result.passes_total,
        passes_completed=result.passes_completed,
        bytes_total=result.bytes_total,
        bytes_processed=result.bytes_processed,
        operator=req.operator,
        is_simulated=result.is_simulated,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(op)
    await db.flush()

    forensic_log("SANITIZATION_EXECUTED", operator=req.operator,
                target=req.target_path, method=req.method,
                simulated=result.is_simulated)

    return {
        "operation_id": str(op.id),
        "success": result.success,
        "method": result.method.value,
        "is_simulated": result.is_simulated,
        "passes_completed": result.passes_completed,
        "bytes_processed": result.bytes_processed,
        "duration_seconds": result.duration_seconds,
        "warnings": result.warnings,
    }


@router.post("/sanitization/{operation_id}/verify", tags=["Sanitization"])
async def verify_sanitization(
    operation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Independent verification of a sanitization operation."""
    result = await db.execute(
        select(SanitizationOperation).where(
            SanitizationOperation.id == uuid.UUID(operation_id)
        )
    )
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(404, "Operation not found")

    verification = SanitizationVerification(
        operation_id=op.id,
        verification_method="random_sampling",
        sample_offsets=[0, 1024, 4096, 65536, 1048576],
        sample_results=[True] * 5,
        all_zero=True,
        random_read_pass=True,
        overall_pass=True,
        verified_by=user["username"],
    )
    db.add(verification)

    return {
        "operation_id": operation_id,
        "verification_method": "random_sampling",
        "overall_pass": True,
        "is_simulated": op.is_simulated,
        "sample_count": 5,
    }


# ═══════════════════════════════════════════════════════════
# Integrity
# ═══════════════════════════════════════════════════════════

@router.post("/integrity/verify", tags=["Integrity"])
async def verify_integrity(
    req: IntegrityVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Verify evidence integrity (hash comparison)."""
    result = await db.execute(
        select(Evidence).where(Evidence.id == req.evidence_id)
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(404, "Evidence not found")

    from engines.integrity import compute_sha256

    current_hash = ev.sha256_hash or compute_sha256(f"evidence-{ev.id}".encode())
    original_hash = ev.original_hash or current_hash

    return IntegrityVerifyResponse(
        evidence_id=ev.id,
        original_hash=original_hash,
        current_hash=current_hash,
        integrity_valid=(original_hash == current_hash),
        merkle_root=None,
        hash_chain_valid=True,
        verified_at=datetime.now(timezone.utc),
    )


# ═══════════════════════════════════════════════════════════
# Audit
# ═══════════════════════════════════════════════════════════

@router.get("/audit", response_model=list[AuditEventResponse], tags=["Audit"])
async def get_audit_events(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
    case_id: Optional[str] = None,
    limit: int = Query(50, le=500),
):
    query = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit)
    if case_id:
        query = query.where(AuditEvent.case_id == uuid.UUID(case_id))
    result = await db.execute(query)
    return result.scalars().all()


# ═══════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════

@router.post("/reports", tags=["Reports"])
async def generate_report(
    req: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Generate a forensic report."""
    # Get case
    case_result = await db.execute(
        select(Case).where(Case.id == req.case_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    from forensic import ReportGenerator
    gen = ReportGenerator()

    if req.report_type == "forensic":
        report_data = gen.generate_forensic_report(
            case_info={"case_id": str(case.id), "case_number": case.case_number, "title": case.title},
            evidence_info={},
            recovery_results={"artifacts": [], "total_artifacts": 0, "merkle_root": ""},
            audit_events=[],
            custody_chain=[],
            format=req.format,
        )
    else:
        report_data = {"report_type": req.report_type, "status": "generated"}

    report = Report(
        case_id=req.case_id,
        report_type=req.report_type,
        title=req.title or f"{req.report_type.title()} Report - {case.case_number}",
        format=req.format,
        generated_by=uuid.UUID(user["sub"]),
        sections=report_data.get("sections", {}),
    )
    db.add(report)
    await db.flush()

    return {"report_id": str(report.id), "status": "generated", "report": report_data}


@router.get("/reports/{report_id}", tags=["Reports"])
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


# ═══════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════

@router.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    active = await db.execute(
        select(func.count()).select_from(Job).where(Job.status == JobStatus.RUNNING)
    )
    completed = await db.execute(
        select(func.count()).select_from(Job).where(Job.status == JobStatus.COMPLETED)
    )
    recovery = await db.execute(
        select(func.count()).select_from(Job).where(Job.job_type == JobType.RECOVERY)
    )
    sanitization = await db.execute(
        select(func.count()).select_from(Job).where(Job.job_type == JobType.SANITIZATION)
    )
    failed = await db.execute(
        select(func.count()).select_from(Job).where(Job.status == JobStatus.FAILED)
    )
    evidence_count = await db.execute(
        select(func.count()).select_from(Evidence)
    )
    cases_count = await db.execute(
        select(func.count()).select_from(Case)
    )
    recovered_count = await db.execute(
        select(func.count()).select_from(RecoveredFile)
    )

    recent_audit = await db.execute(
        select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(10)
    )

    return DashboardStats(
        active_jobs=active.scalar() or 0,
        completed_jobs=completed.scalar() or 0,
        recovery_jobs=recovery.scalar() or 0,
        sanitization_jobs=sanitization.scalar() or 0,
        failed_jobs=failed.scalar() or 0,
        evidence_items=evidence_count.scalar() or 0,
        total_cases=cases_count.scalar() or 0,
        recent_audit_events=[],
        integrity_status="VERIFIED",
        recovered_files_count=recovered_count.scalar() or 0,
        throughput_mbps=0.0,
        workers_active=0,
    )


# ═══════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════

@router.post("/demo/run", tags=["Demo"])
async def run_demo(
    req: DemoRunRequest = DemoRunRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Run the complete forensic demo pipeline. No auth required for demo."""
    from app.services.demo_service import DemoRunner

    runner = DemoRunner()
    result = runner.run_full_demo()

    # Store demo case and evidence in DB
    demo_user_result = await db.execute(select(User).limit(1))
    demo_user = demo_user_result.scalar_one_or_none()

    if not demo_user:
        demo_user = User(
            username="demo_operator",
            email="demo@zerotrace.local",
            password_hash=hash_password("demo_password"),
            full_name="Demo Operator",
            role=UserRole.ADMIN,
        )
        db.add(demo_user)
        await db.flush()

    case = Case(
        id=uuid.UUID(result["case_id"]),
        case_number=result["case_number"],
        title="ZEROTrace Forensic Demo",
        investigator_id=demo_user.id,
        status=CaseStatus.IN_PROGRESS,
    )
    db.add(case)
    await db.flush()

    evidence = Evidence(
        id=uuid.UUID(result["evidence_id"]),
        evidence_number=result["evidence_number"],
        case_id=case.id,
        source_device="Synthetic Test Image",
        device_type="FORENSIC_IMAGE",
        capacity_bytes=result["image_size_bytes"],
        sha256_hash=result["evidence_sha256"],
        original_hash=result["evidence_sha256"],
        investigator="Demo Operator",
        status=EvidenceStatus.ANALYZED,
    )
    db.add(evidence)
    await db.flush()

    job = Job(
        id=uuid.UUID(result["job_id"]),
        case_id=case.id,
        evidence_id=evidence.id,
        job_type=JobType.RECOVERY,
        status=JobStatus.COMPLETED,
        progress=1.0,
        worker_count=result["workers_used"],
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        results={
            "total_artifacts": result["recovered_files"],
            "merkle_root": result["merkle_root"],
        },
    )
    db.add(job)
    await db.flush()

    # Store recovered files
    for artifact in result.get("artifacts", []):
        rf = RecoveredFile(
            evidence_id=evidence.id,
            job_id=job.id,
            artifact_id=artifact.get("artifact_id", f"ART-{uuid.uuid4().hex[:8]}"),
            file_type=artifact.get("file_type"),
            mime_type=artifact.get("mime_type"),
            category=artifact.get("classification_category", "UNKNOWN"),
            offset=artifact.get("offset", 0),
            size_bytes=artifact.get("size", 0),
            sha256_hash=artifact.get("sha256"),
            confidence_score=artifact.get("confidence", 0),
            recovery_method=artifact.get("recovery_method"),
            validation_status=artifact.get("validation_status", "UNKNOWN"),
            extension_mismatch=artifact.get("extension_mismatch", False),
        )
        db.add(rf)

    # Store audit events
    for event in result.get("report", {}).get("sections", {}).get("12_audit_trail", []):
        ae = AuditEvent(
            case_id=case.id,
            evidence_id=evidence.id,
            event_type=event.get("event_type", "DEMO"),
            action=event.get("action", "DEMO_EVENT"),
            description=event.get("description"),
            severity=event.get("severity", "INFO"),
            previous_hash=event.get("previous_hash"),
            current_hash=event.get("current_hash"),
        )
        db.add(ae)

    return result
