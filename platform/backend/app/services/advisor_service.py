"""
ZEROTrace — Advisor Service
Forensic rule-matrix engine that evaluates data-loss scenarios and
returns expert recovery recommendations with appropriate safety warnings.
"""

from app.core.logging_config import get_logger
from app.schemas.advisor import (
    ActionType,
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorRequest,
    AdvisorResponse,
    FileSystem,
    LossScenario,
    RiskLevel,
    StorageMedium,
)

logger = get_logger("advisor")

# ─── Fragmented media extensions that trigger fragment-graph logic ────────────
_FRAGMENTED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "raw", "cr2", "nef", "arw"}

# ─── Chat knowledge-base: keyword → (answer, warnings, action) ───────────────
_CHAT_KB: list[dict] = [
    {
        "keywords": {"trim", "ssd", "garbage"},
        "answer": (
            "TRIM is a command that modern SSDs use to mark deleted blocks as available "
            "for immediate reuse. Once TRIM runs, the OS or SSD firmware zeroes those "
            "sectors before any new write, making forensic recovery extremely unlikely. "
            "You MUST acquire a read-only bitstream image of the SSD immediately—before "
            "the device is powered on again—to preserve any recoverable data."
        ),
        "warnings": [
            "Do NOT power on the SSD again; each boot cycle may trigger background TRIM.",
            "Acquire a read-only bitstream image using ddrescue or FTK Imager in write-blocker mode.",
            "Even with a fresh image, recovery success on TRIM-enabled SSDs is low.",
        ],
        "action": ActionType.IMAGE_DISK,
    },
    {
        "keywords": {"mechanical", "clicking", "head", "hardware", "bad sector"},
        "answer": (
            "Clicking or grinding noises indicate physical read-head or platter damage. "
            "Continuous read attempts will deepen platter scratches and cause irreversible "
            "data loss. Power off immediately. Use specialised hardware imaging equipment "
            "(e.g. PC-3000) with bad-sector skipping. Consider a clean-room HDD specialist "
            "if internal damage is suspected."
        ),
        "warnings": [
            "CRITICAL: Power off the drive immediately to prevent further platter damage.",
            "Do NOT attempt software carving directly on a failing mechanical drive.",
            "Use hardware imaging with bad-sector skipping (ddrescue --force --no-split).",
            "Consult a clean-room data recovery specialist if clicking persists.",
        ],
        "action": ActionType.IMAGE_DISK,
    },
    {
        "keywords": {"format", "quick format", "partition"},
        "answer": (
            "A quick format only erases the partition table and directory metadata; "
            "file data blocks remain intact until overwritten. Use ZeroTrace partition "
            "table search followed by Scalpel signature carving to reconstruct lost files. "
            "Risk is low if no new data has been written to the medium since formatting."
        ),
        "warnings": [
            "Stop using the drive immediately to prevent overwriting recoverable data.",
            "Run a partition table search before signature carving for best results.",
        ],
        "action": ActionType.LAUNCH_CARVE,
    },
    {
        "keywords": {"mft", "ntfs", "master file table"},
        "answer": (
            "NTFS Master File Table (MFT) scanning is the fastest and most accurate "
            "method for recovering recently deleted files on NTFS volumes. The MFT entry "
            "retains file name, timestamps, and cluster chain pointers until the entry is "
            "overwritten. Run ZeroTrace MFT scan for immediate results."
        ),
        "warnings": [
            "MFT entries can be overwritten by new files; act quickly.",
            "If MFT itself is damaged, fall back to signature carving.",
        ],
        "action": ActionType.RUN_MFT_SCAN,
    },
    {
        "keywords": {"fragment", "mp4", "raw", "video", "fragmented"},
        "answer": (
            "Video and RAW photo formats are often written in multiple non-contiguous "
            "fragments, especially on flash storage with wear-levelling. ZeroTrace's "
            "Bi-Directional Fragment Graph combined with Structural Consensus Scoring "
            "identifies and stitches fragments by analysing inter-frame dependencies and "
            "codec-level structural markers."
        ),
        "warnings": [
            "Standard carving tools will produce incomplete or corrupt video files.",
            "Use ZeroTrace Fragment Graph engine for fragmented MP4/RAW recovery.",
            "Ensure source image is a read-only bitstream copy before running analysis.",
        ],
        "action": ActionType.LAUNCH_CARVE,
    },
]


class AdvisorService:
    """
    Stateless forensic rule-matrix engine.

    Decision logic:
    1. Hardware failure  → CRITICAL risk, forbid carving, recommend hardware imaging.
    2. SSD + Deletion    → MEDIUM risk, TRIM warning, immediate bitstream image.
    3. Quick Format      → LOW risk, partition search + Scalpel carving.
    4. Fragmented media  → MEDIUM/HIGH risk, ZeroTrace Fragment Graph.
    5. NTFS + Deletion   → MFT scan first, carving as fallback.
    6. Generic deletion  → signature carving.
    7. Corruption        → filesystem-aware carving or imaging.
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def recommend(self, req: AdvisorRequest) -> AdvisorResponse:
        """Evaluate a data-loss scenario and return a typed recommendation."""
        logger.info(
            "advisor.recommend",
            storage=req.storage_medium,
            fs=req.file_system,
            scenario=req.loss_scenario,
            ext=req.target_extension,
        )

        # Normalise extension for rule matching
        ext = (req.target_extension or "").lower().lstrip(".")

        # ── Rule 1: Hardware failure (always CRITICAL, always image first) ─────
        if req.loss_scenario == LossScenario.HARDWARE_ISSUE:
            return self._hardware_failure_response(req.storage_medium)

        # ── Rule 2: SSD + Deletion (TRIM risk) ────────────────────────────────
        if (
            req.storage_medium == StorageMedium.SSD
            and req.loss_scenario == LossScenario.DELETED
        ):
            return self._ssd_deletion_response()

        # ── Rule 3: Quick Format ───────────────────────────────────────────────
        if req.loss_scenario == LossScenario.FORMATTED:
            return self._formatted_response(req.file_system)

        # ── Rule 4: Fragmented media (MP4 / RAW etc.) ─────────────────────────
        if ext in _FRAGMENTED_EXTENSIONS:
            return self._fragmented_media_response(ext)

        # ── Rule 5: NTFS + Deletion → prefer MFT scan ─────────────────────────
        if (
            req.file_system == FileSystem.NTFS
            and req.loss_scenario == LossScenario.DELETED
        ):
            return self._ntfs_deletion_response()

        # ── Rule 6: Generic corruption ─────────────────────────────────────────
        if req.loss_scenario == LossScenario.CORRUPTED:
            return self._corruption_response(req.storage_medium, req.file_system)

        # ── Rule 7: Generic deletion (non-NTFS, non-SSD) ──────────────────────
        return self._generic_deletion_response(req.storage_medium, req.file_system)

    def chat(self, req: AdvisorChatRequest) -> AdvisorChatResponse:
        """Answer a free-form forensic question using the built-in knowledge base."""
        logger.info("advisor.chat", question_len=len(req.question))

        q_lower = req.question.lower()

        for entry in _CHAT_KB:
            if any(kw in q_lower for kw in entry["keywords"]):
                return AdvisorChatResponse(
                    answer=entry["answer"],
                    related_warnings=entry["warnings"],
                    suggested_action=entry["action"],
                )

        # Fallback generic answer
        return AdvisorChatResponse(
            answer=(
                "ZeroTrace recommends always working on a read-only bitstream copy of "
                "the source media before running any recovery operation. Identify your "
                "loss scenario (deletion, format, corruption, or hardware failure) and "
                "use the /advisor/recommend endpoint for a tailored recovery plan."
            ),
            related_warnings=[
                "Never write to the source drive before imaging.",
                "Document chain of custody before beginning any forensic operation.",
            ],
            suggested_action=None,
        )

    # ── Private rule helpers ───────────────────────────────────────────────────

    @staticmethod
    def _hardware_failure_response(medium: StorageMedium) -> AdvisorResponse:
        warnings = [
            "CRITICAL: Power off the drive immediately to prevent further damage.",
            "Do NOT attempt direct software carving on a failing drive.",
            "Use hardware imaging with bad-sector skipping (e.g. ddrescue --force --no-split).",
        ]
        if medium == StorageMedium.HDD:
            warnings.append(
                "Clicking or grinding sounds indicate read-head failure; "
                "consult a clean-room specialist before any further attempts."
            )
        elif medium in (StorageMedium.SSD, StorageMedium.USB, StorageMedium.SD_CARD):
            warnings.append(
                "Flash controller failure may require chip-off forensics "
                "by a specialist laboratory."
            )

        return AdvisorResponse(
            recommended_method=(
                "Hardware imaging with bad-sector skipping. "
                "Acquire a full bitstream image using write-blocked hardware imager "
                "(PC-3000, ddrescue, or FTK Imager) before any software analysis."
            ),
            risk_level=RiskLevel.CRITICAL,
            safety_warnings=warnings,
            action_type=ActionType.IMAGE_DISK,
        )

    @staticmethod
    def _ssd_deletion_response() -> AdvisorResponse:
        return AdvisorResponse(
            recommended_method=(
                "Immediate read-only bitstream acquisition followed by signature carving. "
                "TRIM may have already erased deleted block data; act before the next "
                "power-on cycle triggers background garbage collection."
            ),
            risk_level=RiskLevel.MEDIUM,
            safety_warnings=[
                "WARNING: SSD TRIM can permanently erase deleted data during background "
                "garbage collection—even without new writes.",
                "Do NOT power the SSD on again before imaging.",
                "Acquire a read-only bitstream image immediately using a write-blocker.",
                "TRIM-erased sectors are unrecoverable; set realistic expectations.",
            ],
            action_type=ActionType.IMAGE_DISK,
        )

    @staticmethod
    def _formatted_response(fs: FileSystem) -> AdvisorResponse:
        method_detail = (
            "Run a partition table search to locate lost partitions, then apply "
            "Scalpel signature-based file carving across the entire raw partition space."
        )
        if fs == FileSystem.NTFS:
            method_detail = (
                "Scan for orphaned MFT entries and run partition recovery, "
                "then apply Scalpel signature carving on unallocated clusters."
            )
        elif fs in (FileSystem.FAT32, FileSystem.EXFAT):
            method_detail = (
                "Reconstruct the FAT/exFAT directory entry chain, then apply "
                "Scalpel signature carving on unallocated clusters."
            )

        return AdvisorResponse(
            recommended_method=method_detail,
            risk_level=RiskLevel.LOW,
            safety_warnings=[
                "Stop using the drive immediately; new writes overwrite recoverable data.",
                "Quick format only erases metadata—file content blocks are still intact.",
                "Run partition table search before carving for best recovery rate.",
            ],
            action_type=ActionType.LAUNCH_CARVE,
        )

    @staticmethod
    def _fragmented_media_response(ext: str) -> AdvisorResponse:
        ext_upper = ext.upper()
        return AdvisorResponse(
            recommended_method=(
                f"{ext_upper} files are frequently stored in non-contiguous fragments "
                "on flash media due to wear-levelling. Use ZeroTrace Bi-Directional "
                "Fragment Graph with Structural Consensus Scoring to identify fragment "
                "boundaries and reassemble the file by analysing codec-level structural markers."
            ),
            risk_level=RiskLevel.MEDIUM,
            safety_warnings=[
                f"Standard carvers will produce incomplete or unplayable {ext_upper} files.",
                "Ensure you are working on a verified read-only bitstream copy.",
                "Fragment Graph analysis is CPU-intensive; allocate sufficient resources.",
                "Validate recovered files with a codec integrity checker before use.",
            ],
            action_type=ActionType.LAUNCH_CARVE,
        )

    @staticmethod
    def _ntfs_deletion_response() -> AdvisorResponse:
        return AdvisorResponse(
            recommended_method=(
                "Run ZeroTrace MFT (Master File Table) scan first: NTFS retains "
                "file name, timestamps, and cluster chain in the MFT entry until "
                "overwritten. If MFT entries are already recycled, fall back to "
                "signature carving on unallocated clusters."
            ),
            risk_level=RiskLevel.LOW,
            safety_warnings=[
                "MFT entries are overwritten as new files are created; act quickly.",
                "Mount the volume read-only or work from a bitstream image.",
                "Do NOT write new data to the NTFS volume before scanning.",
            ],
            action_type=ActionType.RUN_MFT_SCAN,
        )

    @staticmethod
    def _corruption_response(medium: StorageMedium, fs: FileSystem) -> AdvisorResponse:
        risk = RiskLevel.MEDIUM
        warnings = [
            "Work from a bitstream copy, never the original corrupted volume.",
            "Run filesystem consistency checks (chkdsk/fsck) on the image, not the source.",
        ]
        method = (
            "Acquire a full bitstream image, then apply filesystem-aware recovery "
            f"tools for {fs.value}. Use ZeroTrace signature carving on unallocated "
            "and slack space to supplement metadata-based recovery."
        )

        if medium == StorageMedium.HDD:
            risk = RiskLevel.CRITICAL
            warnings.insert(0, "CRITICAL: Corruption on HDD may indicate imminent hardware failure.")
            warnings.append("Monitor S.M.A.R.T. data before extended read operations.")

        return AdvisorResponse(
            recommended_method=method,
            risk_level=risk,
            safety_warnings=warnings,
            action_type=ActionType.IMAGE_DISK,
        )

    @staticmethod
    def _generic_deletion_response(medium: StorageMedium, fs: FileSystem) -> AdvisorResponse:
        return AdvisorResponse(
            recommended_method=(
                f"Signature-based file carving on the {medium.value} ({fs.value} volume). "
                "ZeroTrace will scan raw sectors for known file headers and footers "
                "to reconstruct deleted files independent of directory entries."
            ),
            risk_level=RiskLevel.LOW,
            safety_warnings=[
                "Stop using the drive immediately to prevent overwriting recoverable data.",
                "Work from a verified read-only bitstream copy of the source media.",
            ],
            action_type=ActionType.LAUNCH_CARVE,
        )


# Singleton instance for dependency injection
advisor_service = AdvisorService()
