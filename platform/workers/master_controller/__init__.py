"""
ZEROTrace — Master Controller & Worker Pool
Job management, MapReduce chunk processing, and worker orchestration.
"""

import math
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from app.core.config import settings
from app.core.logging_config import get_logger, forensic_log

logger = get_logger("master_controller")


# ═══════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════

@dataclass
class ChunkDescriptor:
    """Describes a chunk of evidence for MapReduce processing."""
    index: int
    offset: int
    size: int
    overlap_start: int = 0
    overlap_end: int = 0
    data: Optional[bytes] = None


@dataclass
class ChunkResult:
    """Result from processing a single chunk."""
    chunk_index: int
    offset: int
    size: int
    candidates_found: int
    results: list  # list of RecoveryResult dicts
    errors: list[str] = field(default_factory=list)
    processing_time: float = 0.0
    worker_id: str = ""


@dataclass
class JobProgress:
    """Real-time job progress tracking."""
    job_id: str
    total_chunks: int
    processed_chunks: int
    progress: float
    candidates_found: int
    errors: int
    workers_active: int
    throughput_mbps: float
    eta_seconds: float
    started_at: str
    status: str


# ═══════════════════════════════════════════════════════════
# Chunk Generator (MAP phase)
# ═══════════════════════════════════════════════════════════

class ChunkGenerator:
    """
    Split evidence into chunks for parallel processing.
    Handles boundary overlap to catch signatures crossing chunk boundaries.
    """

    def __init__(
        self,
        chunk_size_bytes: int = None,
        overlap_bytes: int = None,
    ):
        self.chunk_size = chunk_size_bytes or (settings.CHUNK_SIZE_MB * 1024 * 1024)
        self.overlap = overlap_bytes or settings.BOUNDARY_OVERLAP_BYTES

    def generate_chunks(
        self, data: bytes, base_offset: int = 0
    ) -> list[ChunkDescriptor]:
        """
        Split data into overlapping chunks.
        Overlap ensures signatures at chunk boundaries are detected.
        """
        total_size = len(data)
        chunks = []
        offset = 0
        index = 0

        while offset < total_size:
            # Calculate chunk boundaries
            chunk_start = max(0, offset - self.overlap) if offset > 0 else 0
            chunk_end = min(offset + self.chunk_size + self.overlap, total_size)
            actual_size = chunk_end - chunk_start

            overlap_start = offset - chunk_start if offset > 0 else 0
            overlap_end = (
                chunk_end - (offset + self.chunk_size)
                if chunk_end > offset + self.chunk_size
                else 0
            )

            chunks.append(ChunkDescriptor(
                index=index,
                offset=base_offset + chunk_start,
                size=actual_size,
                overlap_start=overlap_start,
                overlap_end=overlap_end,
                data=data[chunk_start:chunk_end],
            ))

            offset += self.chunk_size
            index += 1

        logger.info(
            "chunks_generated",
            total_size=total_size,
            chunk_count=len(chunks),
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )
        return chunks


# ═══════════════════════════════════════════════════════════
# Worker Function (runs in separate thread/process)
# ═══════════════════════════════════════════════════════════

def process_chunk_worker(
    chunk_data: bytes,
    chunk_index: int,
    chunk_offset: int,
    file_types: list[str] = None,
    evidence_id: str = "",
) -> dict:
    """
    Worker function for processing a single chunk.
    Designed to run in a ProcessPoolExecutor.
    Returns a serializable dict.
    """
    from engines.recovery import ConsensusRecoveryEngine

    start_time = time.time()
    worker_id = f"worker-{uuid.uuid4().hex[:8]}"
    errors = []

    try:
        engine = ConsensusRecoveryEngine()
        results = engine.recover_from_chunk(
            chunk_data,
            base_offset=chunk_offset,
            file_types=file_types,
            evidence_id=evidence_id,
        )

        # Convert to serializable dicts
        result_dicts = []
        for r in results:
            result_dicts.append({
                "artifact_id": r.artifact_id,
                "file_type": r.file_type,
                "extension": r.extension,
                "mime_type": r.mime_type,
                "category": r.category,
                "offset": r.offset,
                "size": r.size,
                "sha256": r.sha256,
                "confidence": r.consensus_score,
                "is_fragmented": r.is_fragmented,
                "fragment_count": r.fragment_count,
                "recovery_method": r.recovery_method,
                "method_scores": r.method_scores,
                "validation_status": (
                    r.validation.overall_status.value if r.validation else "UNKNOWN"
                ),
                "classification_category": (
                    r.classification.category if r.classification else "UNKNOWN"
                ),
                "extension_mismatch": (
                    r.classification.extension_mismatch if r.classification else False
                ),
            })

    except Exception as e:
        errors.append(f"Chunk {chunk_index} error: {str(e)}")
        result_dicts = []

    return {
        "chunk_index": chunk_index,
        "offset": chunk_offset,
        "size": len(chunk_data),
        "candidates_found": len(result_dicts),
        "results": result_dicts,
        "errors": errors,
        "processing_time": time.time() - start_time,
        "worker_id": worker_id,
    }


# ═══════════════════════════════════════════════════════════
# Master Controller
# ═══════════════════════════════════════════════════════════

class MasterController:
    """
    Master Controller for job orchestration.
    
    Responsibilities:
    - Accept job
    - Validate job
    - Split job into chunks (MAP)
    - Schedule tasks to worker pool
    - Track progress
    - Retry failed tasks
    - Collect and merge results (REDUCE)
    - Validate results
    - Generate final output
    """

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or settings.MAX_WORKERS
        self.chunk_generator = ChunkGenerator()
        self._active_jobs: dict[str, JobProgress] = {}

    def execute_recovery_job(
        self,
        evidence_data: bytes,
        evidence_id: str,
        job_id: str = None,
        file_types: list[str] = None,
        progress_callback: Callable = None,
    ) -> dict:
        """
        Execute a complete recovery job using MapReduce.
        
        MAP: Split evidence → process chunks in parallel
        REDUCE: Merge results → deduplicate → validate
        """
        job_id = job_id or str(uuid.uuid4())
        start_time = time.time()

        forensic_log(
            "RECOVERY_JOB_STARTED",
            job_id=job_id,
            evidence_id=evidence_id,
            data_size=len(evidence_data),
            workers=self.max_workers,
        )

        # ── MAP Phase: Generate chunks ────────────────
        chunks = self.chunk_generator.generate_chunks(evidence_data)

        # Initialize progress
        progress = JobProgress(
            job_id=job_id,
            total_chunks=len(chunks),
            processed_chunks=0,
            progress=0.0,
            candidates_found=0,
            errors=0,
            workers_active=0,
            throughput_mbps=0.0,
            eta_seconds=0.0,
            started_at=datetime.now(timezone.utc).isoformat(),
            status="RUNNING",
        )
        self._active_jobs[job_id] = progress

        # ── Process chunks with worker pool ───────────
        all_results = []
        all_errors = []

        # Use ThreadPoolExecutor for in-process work
        # (ProcessPoolExecutor would require pickling issues resolution)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for chunk in chunks:
                future = executor.submit(
                    process_chunk_worker,
                    chunk.data,
                    chunk.index,
                    chunk.offset,
                    file_types or [],
                    evidence_id,
                )
                futures[future] = chunk.index

            for future in as_completed(futures):
                chunk_idx = futures[future]
                try:
                    result = future.result(timeout=settings.WORKER_TIMEOUT_SECONDS)
                    all_results.append(result)
                    if result["errors"]:
                        all_errors.extend(result["errors"])

                    # Update progress
                    progress.processed_chunks += 1
                    progress.candidates_found += result["candidates_found"]
                    progress.progress = progress.processed_chunks / progress.total_chunks
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        bytes_done = sum(r["size"] for r in all_results)
                        progress.throughput_mbps = (bytes_done / (1024 * 1024)) / elapsed

                    if progress_callback:
                        progress_callback(progress)

                except Exception as e:
                    all_errors.append(f"Worker failed on chunk {chunk_idx}: {e}")
                    progress.errors += 1

                    # Retry logic
                    if len(all_errors) <= settings.MAX_RETRY_COUNT:
                        logger.warning("worker_retry", chunk=chunk_idx, error=str(e))

        # ── REDUCE Phase: Merge results ───────────────
        merged = self._reduce_results(all_results)
        total_time = time.time() - start_time

        progress.status = "COMPLETED"
        progress.progress = 1.0

        # Build Merkle tree from artifact hashes
        artifact_hashes = [
            r["sha256"] for r in merged if r.get("sha256")
        ]
        merkle_root = ""
        if artifact_hashes:
            from engines.integrity import MerkleTree
            tree = MerkleTree(artifact_hashes)
            merkle_root = tree.get_root()

        forensic_log(
            "RECOVERY_JOB_COMPLETED",
            job_id=job_id,
            evidence_id=evidence_id,
            total_artifacts=len(merged),
            duration=total_time,
            merkle_root=merkle_root,
        )

        return {
            "job_id": job_id,
            "evidence_id": evidence_id,
            "status": "COMPLETED",
            "total_chunks": len(chunks),
            "total_artifacts": len(merged),
            "artifacts": merged,
            "merkle_root": merkle_root,
            "processing_time_seconds": total_time,
            "throughput_mbps": (
                (len(evidence_data) / (1024 * 1024)) / total_time
                if total_time > 0 else 0
            ),
            "errors": all_errors,
            "workers_used": self.max_workers,
        }

    def _reduce_results(self, chunk_results: list[dict]) -> list[dict]:
        """
        REDUCE phase: merge results from all chunks.
        - Deduplicate candidates found in overlapping regions
        - Sort by offset
        """
        all_candidates = []
        seen_offsets = set()

        # Sort chunk results by offset
        chunk_results.sort(key=lambda r: r["offset"])

        for chunk_result in chunk_results:
            for candidate in chunk_result["results"]:
                offset = candidate["offset"]
                # Deduplicate: skip if we've seen a candidate at a nearby offset
                is_duplicate = any(
                    abs(offset - seen) < 16 for seen in seen_offsets
                )
                if not is_duplicate:
                    all_candidates.append(candidate)
                    seen_offsets.add(offset)

        # Sort final results by offset
        all_candidates.sort(key=lambda c: c["offset"])

        logger.info(
            "reduce_complete",
            total_candidates=len(all_candidates),
            chunks_processed=len(chunk_results),
        )
        return all_candidates

    def get_job_progress(self, job_id: str) -> Optional[JobProgress]:
        return self._active_jobs.get(job_id)
