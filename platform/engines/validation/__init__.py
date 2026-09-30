"""
ZEROTrace — Structure-Based Validation Engine
Header, footer, structure, MIME, parser, and integrity validation.
"""

import hashlib
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger("validation")


class ValidationStatus(str, Enum):
    VALID = "VALID"
    PARTIALLY_VALID = "PARTIALLY_VALID"
    CORRUPTED = "CORRUPTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ValidationReport:
    """Complete validation report for a recovered artifact."""
    file_type: str
    header_valid: bool = False
    footer_valid: bool = False
    structure_valid: bool = False
    size_valid: bool = False
    mime_consistent: bool = False
    parser_valid: bool = False
    metadata_consistent: bool = False
    sha256: str = ""
    overall_status: ValidationStatus = ValidationStatus.UNKNOWN
    confidence_boost: float = 0.0
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def compute_status(self) -> ValidationStatus:
        checks = [
            self.header_valid,
            self.footer_valid,
            self.structure_valid,
            self.size_valid,
            self.parser_valid,
        ]
        passed = sum(1 for c in checks if c)
        total = len(checks)

        if passed == total:
            self.overall_status = ValidationStatus.VALID
            self.confidence_boost = 0.2
        elif passed >= 3:
            self.overall_status = ValidationStatus.PARTIALLY_VALID
            self.confidence_boost = 0.1
        elif passed >= 1:
            self.overall_status = ValidationStatus.CORRUPTED
            self.confidence_boost = -0.1
        else:
            self.overall_status = ValidationStatus.UNKNOWN
            self.confidence_boost = -0.2

        return self.overall_status


class FileValidator:
    """
    Validates recovered files through multiple checks:
    1. Header validation
    2. Footer validation
    3. File-size validation
    4. Internal structure validation
    5. MIME detection
    6. Parser validation
    7. Hash calculation
    8. Recoverability score
    """

    def validate(self, data: bytes, file_type: str, **kwargs) -> ValidationReport:
        """Run all validations on the provided data."""
        report = ValidationReport(file_type=file_type)

        # SHA-256
        report.sha256 = hashlib.sha256(data).hexdigest()

        # Dispatch to type-specific validator
        validator_map = {
            "JPEG": self._validate_jpeg,
            "PNG": self._validate_png,
            "PDF": self._validate_pdf,
            "ZIP": self._validate_zip,
            "DOCX": self._validate_zip,  # DOCX is ZIP-based
            "XLSX": self._validate_zip,
            "GIF": self._validate_gif,
            "BMP": self._validate_bmp,
            "WAV": self._validate_wav,
            "MP3": self._validate_mp3,
            "MP4": self._validate_mp4,
        }

        validator_fn = validator_map.get(file_type, self._validate_generic)
        validator_fn(data, report)
        report.compute_status()

        logger.info(
            "validation_complete",
            file_type=file_type,
            status=report.overall_status.value,
            sha256=report.sha256[:16] + "...",
        )
        return report

    # ── JPEG ───────────────────────────────────────────

    def _validate_jpeg(self, data: bytes, report: ValidationReport):
        # Header: FF D8 FF
        report.header_valid = len(data) >= 3 and data[:3] == b"\xFF\xD8\xFF"

        # Footer: FF D9
        report.footer_valid = len(data) >= 2 and data[-2:] == b"\xFF\xD9"

        # Structure: Check for JFIF or Exif markers
        has_jfif = b"JFIF" in data[:20]
        has_exif = b"Exif" in data[:20]
        report.structure_valid = has_jfif or has_exif or (
            len(data) >= 4 and data[3] in (0xE0, 0xE1, 0xE2, 0xDB, 0xC0, 0xC4)
        )

        # Size: JPEG should be at least a few hundred bytes
        report.size_valid = 100 < len(data) < 50 * 1024 * 1024

        # MIME
        report.mime_consistent = report.header_valid

        # Parser: Check for SOS (Start of Scan) marker
        report.parser_valid = b"\xFF\xDA" in data

        report.details = {
            "has_jfif": has_jfif,
            "has_exif": has_exif,
            "has_sos": report.parser_valid,
            "size": len(data),
        }

    # ── PNG ────────────────────────────────────────────

    def _validate_png(self, data: bytes, report: ValidationReport):
        png_header = b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
        png_footer = b"\x49\x45\x4E\x44\xAE\x42\x60\x82"

        report.header_valid = len(data) >= 8 and data[:8] == png_header
        report.footer_valid = len(data) >= 12 and data[-12:].find(png_footer) != -1

        # Check for IHDR chunk
        has_ihdr = len(data) >= 16 and data[12:16] == b"IHDR"
        report.structure_valid = has_ihdr

        if has_ihdr and len(data) >= 24:
            width = struct.unpack(">I", data[16:20])[0]
            height = struct.unpack(">I", data[20:24])[0]
            report.details = {"width": width, "height": height}
            report.size_valid = 0 < width < 65536 and 0 < height < 65536
        else:
            report.size_valid = 100 < len(data) < 50 * 1024 * 1024

        report.mime_consistent = report.header_valid
        report.parser_valid = has_ihdr and b"IDAT" in data

    # ── PDF ────────────────────────────────────────────

    def _validate_pdf(self, data: bytes, report: ValidationReport):
        report.header_valid = data[:5] == b"%PDF-"
        report.footer_valid = b"%%EOF" in data[-1024:]

        # Check for PDF objects
        has_obj = b" obj" in data or b" 0 obj" in data
        report.structure_valid = has_obj

        report.size_valid = 100 < len(data) < 500 * 1024 * 1024
        report.mime_consistent = report.header_valid

        # Check for stream data (actual content)
        report.parser_valid = b"stream" in data and b"endstream" in data

        # Extract PDF version
        if report.header_valid and len(data) >= 8:
            version = data[:8].decode("ascii", errors="ignore")
            report.details = {"pdf_version": version.strip()}

    # ── ZIP ────────────────────────────────────────────

    def _validate_zip(self, data: bytes, report: ValidationReport):
        report.header_valid = len(data) >= 4 and data[:4] == b"\x50\x4B\x03\x04"

        # End of Central Directory
        eocd = b"\x50\x4B\x05\x06"
        report.footer_valid = eocd in data[-65536:]

        # Local file header structure
        if len(data) >= 30:
            version = struct.unpack("<H", data[4:6])[0]
            compressed_size = struct.unpack("<I", data[18:22])[0]
            filename_len = struct.unpack("<H", data[26:28])[0]
            report.structure_valid = version < 100 and filename_len < 1024
            report.details = {
                "version": version,
                "filename_length": filename_len,
            }
        else:
            report.structure_valid = False

        report.size_valid = 22 < len(data) < 2 * 1024 * 1024 * 1024
        report.mime_consistent = report.header_valid
        report.parser_valid = report.header_valid and report.footer_valid

    # ── GIF ────────────────────────────────────────────

    def _validate_gif(self, data: bytes, report: ValidationReport):
        report.header_valid = data[:4] == b"GIF8" and (
            data[4:6] in (b"7a", b"9a")
        )
        report.footer_valid = len(data) >= 2 and data[-1:] == b"\x3B"

        if len(data) >= 10:
            width = struct.unpack("<H", data[6:8])[0]
            height = struct.unpack("<H", data[8:10])[0]
            report.structure_valid = 0 < width < 65536 and 0 < height < 65536
            report.details = {"width": width, "height": height}
        else:
            report.structure_valid = False

        report.size_valid = 10 < len(data) < 50 * 1024 * 1024
        report.mime_consistent = report.header_valid
        report.parser_valid = report.header_valid

    # ── BMP ────────────────────────────────────────────

    def _validate_bmp(self, data: bytes, report: ValidationReport):
        report.header_valid = len(data) >= 2 and data[:2] == b"BM"

        if len(data) >= 26:
            file_size = struct.unpack("<I", data[2:6])[0]
            width = struct.unpack("<i", data[18:22])[0]
            height = struct.unpack("<i", data[22:26])[0]
            report.structure_valid = abs(width) < 65536 and abs(height) < 65536
            report.size_valid = file_size > 0 and abs(file_size - len(data)) < 1024
            report.details = {
                "declared_size": file_size,
                "actual_size": len(data),
                "width": width,
                "height": abs(height),
            }
        else:
            report.structure_valid = False
            report.size_valid = False

        report.footer_valid = True  # BMP has no footer
        report.mime_consistent = report.header_valid
        report.parser_valid = report.structure_valid

    # ── WAV ────────────────────────────────────────────

    def _validate_wav(self, data: bytes, report: ValidationReport):
        report.header_valid = (
            len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"
        )

        if len(data) >= 8:
            chunk_size = struct.unpack("<I", data[4:8])[0]
            report.size_valid = abs((chunk_size + 8) - len(data)) < 1024
        else:
            report.size_valid = False

        report.footer_valid = True  # WAV has no distinct footer
        report.structure_valid = report.header_valid and b"fmt " in data[:100]
        report.mime_consistent = report.header_valid
        report.parser_valid = b"data" in data

    # ── MP3 ────────────────────────────────────────────

    def _validate_mp3(self, data: bytes, report: ValidationReport):
        # MP3 frame sync: 0xFF 0xFB or ID3 tag
        has_sync = len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0
        has_id3 = data[:3] == b"ID3"
        report.header_valid = has_sync or has_id3
        report.footer_valid = True  # No standard footer
        report.structure_valid = report.header_valid
        report.size_valid = 100 < len(data) < 100 * 1024 * 1024
        report.mime_consistent = report.header_valid
        report.parser_valid = has_sync or has_id3
        report.details = {"has_id3": has_id3, "has_sync": has_sync}

    # ── MP4 ────────────────────────────────────────────

    def _validate_mp4(self, data: bytes, report: ValidationReport):
        if len(data) < 8:
            return
        report.header_valid = data[4:8] == b"ftyp"
        report.footer_valid = True  # Validated via box structure
        report.structure_valid = report.header_valid

        # Walk boxes
        pos = 0
        box_count = 0
        while pos + 8 <= len(data):
            box_size = struct.unpack(">I", data[pos:pos + 4])[0]
            if box_size < 8:
                break
            box_count += 1
            pos += box_size

        report.size_valid = box_count > 1
        report.mime_consistent = report.header_valid
        report.parser_valid = box_count >= 2
        report.details = {"box_count": box_count}

    # ── Generic ────────────────────────────────────────

    def _validate_generic(self, data: bytes, report: ValidationReport):
        report.header_valid = len(data) > 0
        report.footer_valid = True
        report.structure_valid = len(data) >= 64
        report.size_valid = 0 < len(data) < 500 * 1024 * 1024
        report.mime_consistent = True
        report.parser_valid = True
