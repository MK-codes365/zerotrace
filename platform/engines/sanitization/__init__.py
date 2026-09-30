"""
ZEROTrace — Sanitization Engine
Pluggable sanitization strategies with safe demo mode.

CRITICAL: SAFE_DEMO_MODE=true by default.
No actual destructive drive operations occur in demo mode.
"""

import os
import hashlib
import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging_config import get_logger, forensic_log

logger = get_logger("sanitization")


# ═══════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════

class MediaType(str, Enum):
    HDD = "HDD"
    SSD = "SSD"
    USB = "USB"
    SD = "SD"
    EXTERNAL_HDD = "EXTERNAL_HDD"
    EXTERNAL_SSD = "EXTERNAL_SSD"
    UNKNOWN = "UNKNOWN"


class SanitizeMethod(str, Enum):
    ZERO_FILL = "ZERO_FILL"
    RANDOM_DATA = "RANDOM_DATA"
    DOD_522220M = "DOD_522220M"
    GUTMANN = "GUTMANN"
    NIST_800_88_CLEAR = "NIST_800_88_CLEAR"
    NIST_800_88_PURGE = "NIST_800_88_PURGE"
    SECURE_ERASE_ATA = "SECURE_ERASE_ATA"
    CRYPTO_ERASE = "CRYPTO_ERASE"
    SIMULATED = "SIMULATED"


@dataclass
class DeviceInfo:
    """Detected storage device information."""
    path: str
    name: str
    media_type: MediaType
    capacity_bytes: int
    filesystem: str = "UNKNOWN"
    serial_number: str = ""
    sector_size: int = 512
    is_removable: bool = False
    is_system_drive: bool = False
    is_read_only: bool = False
    model: str = ""


@dataclass
class SanitizationResult:
    """Result of a sanitization operation."""
    success: bool
    method: SanitizeMethod
    target: str
    bytes_processed: int = 0
    bytes_total: int = 0
    passes_completed: int = 0
    passes_total: int = 0
    duration_seconds: float = 0.0
    is_simulated: bool = True
    verification_result: Optional[dict] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = ""


# ═══════════════════════════════════════════════════════════
# Strategy Interface
# ═══════════════════════════════════════════════════════════

class SanitizationStrategy(ABC):
    """
    Interface for sanitization strategies.
    Each strategy must implement these methods.
    """

    @abstractmethod
    def get_method(self) -> SanitizeMethod:
        """Return the sanitization method identifier."""
        ...

    @abstractmethod
    def get_passes(self) -> int:
        """Return the number of overwrite passes."""
        ...

    @abstractmethod
    def detect_capabilities(self, device: DeviceInfo) -> dict:
        """Check if this strategy can be applied to the device."""
        ...

    @abstractmethod
    def execute(
        self,
        device: DeviceInfo,
        progress_callback=None,
    ) -> SanitizationResult:
        """Execute the sanitization. MUST respect SAFE_DEMO_MODE."""
        ...

    @abstractmethod
    def verify(self, device: DeviceInfo) -> dict:
        """Independent verification after sanitization."""
        ...


# ═══════════════════════════════════════════════════════════
# Concrete Strategies
# ═══════════════════════════════════════════════════════════

class ZeroFillStrategy(SanitizationStrategy):
    """Single pass zero-fill overwrite."""

    def get_method(self) -> SanitizeMethod:
        return SanitizeMethod.ZERO_FILL

    def get_passes(self) -> int:
        return 1

    def detect_capabilities(self, device: DeviceInfo) -> dict:
        supported = device.media_type in (
            MediaType.HDD, MediaType.USB, MediaType.EXTERNAL_HDD
        )
        return {
            "supported": supported,
            "method": self.get_method().value,
            "passes": self.get_passes(),
            "note": "Single-pass zero fill" if supported else "Not recommended for SSD",
        }

    def execute(self, device: DeviceInfo, progress_callback=None) -> SanitizationResult:
        return _simulate_sanitization(
            device, self.get_method(), self.get_passes(), progress_callback
        )

    def verify(self, device: DeviceInfo) -> dict:
        return _simulate_verification(device, "zero_check")


class RandomDataStrategy(SanitizationStrategy):
    """Single pass random data overwrite."""

    def get_method(self) -> SanitizeMethod:
        return SanitizeMethod.RANDOM_DATA

    def get_passes(self) -> int:
        return 1

    def detect_capabilities(self, device: DeviceInfo) -> dict:
        supported = device.media_type in (
            MediaType.HDD, MediaType.USB, MediaType.EXTERNAL_HDD
        )
        return {
            "supported": supported,
            "method": self.get_method().value,
            "passes": 1,
            "note": "Single-pass random data",
        }

    def execute(self, device: DeviceInfo, progress_callback=None) -> SanitizationResult:
        return _simulate_sanitization(
            device, self.get_method(), self.get_passes(), progress_callback
        )

    def verify(self, device: DeviceInfo) -> dict:
        return _simulate_verification(device, "entropy_check")


class DoD522220MStrategy(SanitizationStrategy):
    """DoD 5220.22-M 3-pass overwrite."""

    def get_method(self) -> SanitizeMethod:
        return SanitizeMethod.DOD_522220M

    def get_passes(self) -> int:
        return 3

    def detect_capabilities(self, device: DeviceInfo) -> dict:
        supported = device.media_type in (
            MediaType.HDD, MediaType.USB, MediaType.EXTERNAL_HDD
        )
        return {
            "supported": supported,
            "method": self.get_method().value,
            "passes": 3,
            "pattern": "Pass 1: 0x00, Pass 2: 0xFF, Pass 3: Random",
            "note": "DoD 5220.22-M standard" if supported else "Not effective on SSD",
        }

    def execute(self, device: DeviceInfo, progress_callback=None) -> SanitizationResult:
        return _simulate_sanitization(
            device, self.get_method(), self.get_passes(), progress_callback
        )

    def verify(self, device: DeviceInfo) -> dict:
        return _simulate_verification(device, "pattern_check")


class GutmannStrategy(SanitizationStrategy):
    """Gutmann 35-pass overwrite."""

    def get_method(self) -> SanitizeMethod:
        return SanitizeMethod.GUTMANN

    def get_passes(self) -> int:
        return 35

    def detect_capabilities(self, device: DeviceInfo) -> dict:
        supported = device.media_type == MediaType.HDD
        return {
            "supported": supported,
            "method": self.get_method().value,
            "passes": 35,
            "note": "Gutmann 35-pass method. Very slow. Only for HDD.",
            "estimated_time": "Very long — approximately 35x write time",
        }

    def execute(self, device: DeviceInfo, progress_callback=None) -> SanitizationResult:
        return _simulate_sanitization(
            device, self.get_method(), self.get_passes(), progress_callback
        )

    def verify(self, device: DeviceInfo) -> dict:
        return _simulate_verification(device, "full_scan")


class SSDSecureEraseStrategy(SanitizationStrategy):
    """SSD-specific secure erase (ATA Secure Erase / NVMe Sanitize)."""

    def get_method(self) -> SanitizeMethod:
        return SanitizeMethod.SECURE_ERASE_ATA

    def get_passes(self) -> int:
        return 1

    def detect_capabilities(self, device: DeviceInfo) -> dict:
        is_ssd = device.media_type in (MediaType.SSD, MediaType.EXTERNAL_SSD)
        return {
            "supported": is_ssd,
            "method": self.get_method().value,
            "passes": 1,
            "note": (
                "Requires device-level ATA Secure Erase or NVMe Sanitize command. "
                "Cannot be performed from user-space in demo mode."
            ),
            "requires_hardware": True,
        }

    def execute(self, device: DeviceInfo, progress_callback=None) -> SanitizationResult:
        # SSD secure erase requires OS-level / hardware commands
        # In demo mode, simulate
        return _simulate_sanitization(
            device, self.get_method(), 1, progress_callback,
            extra_warnings=[
                "SIMULATED: Real SSD Secure Erase requires ATA/NVMe commands "
                "and root/admin privileges."
            ],
        )

    def verify(self, device: DeviceInfo) -> dict:
        return _simulate_verification(device, "ssd_verify")


# ═══════════════════════════════════════════════════════════
# Strategy Recommender
# ═══════════════════════════════════════════════════════════

class StrategyRecommender:
    """Recommend the best sanitization strategy for a given device."""

    STRATEGIES: dict[str, SanitizationStrategy] = {
        "ZERO_FILL": ZeroFillStrategy(),
        "RANDOM_DATA": RandomDataStrategy(),
        "DOD_522220M": DoD522220MStrategy(),
        "GUTMANN": GutmannStrategy(),
        "SECURE_ERASE_ATA": SSDSecureEraseStrategy(),
    }

    def recommend(self, device: DeviceInfo) -> tuple[str, SanitizationStrategy]:
        """
        Recommend a sanitization method based on device type.
        Returns (method_name, strategy).
        """
        if device.media_type in (MediaType.SSD, MediaType.EXTERNAL_SSD):
            return "SECURE_ERASE_ATA", self.STRATEGIES["SECURE_ERASE_ATA"]
        elif device.media_type == MediaType.HDD:
            return "DOD_522220M", self.STRATEGIES["DOD_522220M"]
        elif device.media_type in (MediaType.USB, MediaType.SD):
            return "RANDOM_DATA", self.STRATEGIES["RANDOM_DATA"]
        else:
            return "ZERO_FILL", self.STRATEGIES["ZERO_FILL"]

    def get_strategy(self, method: str) -> Optional[SanitizationStrategy]:
        return self.STRATEGIES.get(method)

    def get_all_capabilities(self, device: DeviceInfo) -> list[dict]:
        """Return capability assessment for all strategies."""
        results = []
        for name, strategy in self.STRATEGIES.items():
            cap = strategy.detect_capabilities(device)
            cap["method_name"] = name
            results.append(cap)
        return results


# ═══════════════════════════════════════════════════════════
# File / Folder Eraser
# ═══════════════════════════════════════════════════════════

class FileEraser:
    """
    Secure file and folder deletion.
    Overwrites file content before unlinking.
    """

    def preview(self, target_path: str) -> dict:
        """Preview what would be affected by deletion."""
        path = Path(target_path)
        if not path.exists():
            return {"error": f"Path not found: {target_path}"}

        if path.is_file():
            return {
                "target": str(path),
                "type": "file",
                "files_count": 1,
                "total_size": path.stat().st_size,
                "filesystem": "detected",
                "operation": "SECURE_DELETE",
            }
        elif path.is_dir():
            files = list(path.rglob("*"))
            file_list = [f for f in files if f.is_file()]
            total_size = sum(f.stat().st_size for f in file_list)
            return {
                "target": str(path),
                "type": "folder",
                "files_count": len(file_list),
                "total_size": total_size,
                "filesystem": "detected",
                "operation": "SECURE_DELETE_RECURSIVE",
            }
        return {"error": "Invalid target"}

    def execute(
        self,
        target_path: str,
        passes: int = 3,
        operator: str = "system",
    ) -> SanitizationResult:
        """
        Securely delete a file or folder.
        In SAFE_DEMO_MODE, simulates the operation.
        """
        path = Path(target_path)
        if not path.exists():
            return SanitizationResult(
                success=False,
                method=SanitizeMethod.RANDOM_DATA,
                target=target_path,
                is_simulated=True,
                errors=[f"Path not found: {target_path}"],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        if settings.SAFE_DEMO_MODE:
            return self._simulate_file_erasure(path, passes, operator)
        else:
            return self._real_file_erasure(path, passes, operator)

    def _simulate_file_erasure(
        self, path: Path, passes: int, operator: str
    ) -> SanitizationResult:
        """Simulate file erasure without actually deleting anything."""
        size = path.stat().st_size if path.is_file() else 0
        if path.is_dir():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        forensic_log(
            "FILE_ERASURE_SIMULATED",
            operator=operator,
            target=str(path),
            size=size,
        )

        return SanitizationResult(
            success=True,
            method=SanitizeMethod.SIMULATED,
            target=str(path),
            bytes_processed=size,
            bytes_total=size,
            passes_completed=passes,
            passes_total=passes,
            duration_seconds=0.5,
            is_simulated=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            warnings=["SAFE_DEMO_MODE: No actual deletion performed"],
        )

    def _real_file_erasure(
        self, path: Path, passes: int, operator: str
    ) -> SanitizationResult:
        """Actually overwrite and delete files. Only runs when SAFE_DEMO_MODE=false."""
        start = time.time()
        errors = []
        total_bytes = 0

        try:
            if path.is_file():
                total_bytes = self._overwrite_file(path, passes)
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        try:
                            total_bytes += self._overwrite_file(f, passes)
                        except Exception as e:
                            errors.append(f"Failed to erase {f}: {e}")
                # Remove directory tree after files are overwritten
                import shutil
                shutil.rmtree(path, ignore_errors=True)
        except Exception as e:
            errors.append(str(e))

        duration = time.time() - start

        forensic_log(
            "FILE_ERASURE_COMPLETED",
            operator=operator,
            target=str(path),
            bytes=total_bytes,
            passes=passes,
            errors=len(errors),
        )

        return SanitizationResult(
            success=len(errors) == 0,
            method=SanitizeMethod.RANDOM_DATA,
            target=str(path),
            bytes_processed=total_bytes,
            bytes_total=total_bytes,
            passes_completed=passes,
            passes_total=passes,
            duration_seconds=duration,
            is_simulated=False,
            errors=errors,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _overwrite_file(self, file_path: Path, passes: int) -> int:
        """Overwrite a single file with random data, then delete."""
        size = file_path.stat().st_size
        for _ in range(passes):
            with open(file_path, "wb") as f:
                remaining = size
                while remaining > 0:
                    chunk = min(remaining, 65536)
                    f.write(secrets.token_bytes(chunk))
                    remaining -= chunk
                f.flush()
                os.fsync(f.fileno())
        file_path.unlink()
        return size


# ═══════════════════════════════════════════════════════════
# Simulation Helper
# ═══════════════════════════════════════════════════════════

def _simulate_sanitization(
    device: DeviceInfo,
    method: SanitizeMethod,
    passes: int,
    progress_callback=None,
    extra_warnings: list[str] = None,
) -> SanitizationResult:
    """Simulate a sanitization operation (SAFE_DEMO_MODE)."""
    start = time.time()
    total = device.capacity_bytes or (500 * 1024 * 1024 * 1024)

    # Simulate progress
    steps = 20
    for step in range(steps):
        progress = (step + 1) / steps
        if progress_callback:
            progress_callback(progress, step + 1, passes)
        time.sleep(0.05)

    duration = time.time() - start
    warnings = extra_warnings or []
    warnings.append("SAFE_DEMO_MODE: No actual data was written to the device")

    forensic_log(
        "SANITIZATION_SIMULATED",
        method=method.value,
        target=device.path,
        passes=passes,
    )

    return SanitizationResult(
        success=True,
        method=method,
        target=device.path,
        bytes_processed=total,
        bytes_total=total,
        passes_completed=passes,
        passes_total=passes,
        duration_seconds=duration,
        is_simulated=True,
        warnings=warnings,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _simulate_verification(device: DeviceInfo, method: str) -> dict:
    """Simulate verification after sanitization."""
    return {
        "device": device.path,
        "verification_method": method,
        "is_simulated": True,
        "overall_pass": True,
        "sample_count": 10,
        "all_zero": method == "zero_check",
        "random_read_pass": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "SAFE_DEMO_MODE: Verification result is simulated",
    }
