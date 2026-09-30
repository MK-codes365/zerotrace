"""
ZEROTrace — Classification Engine
Automatic classification of recovered files with mismatch detection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger("classification")


MIME_TO_CATEGORY = {
    "image/jpeg": "IMAGE",
    "image/png": "IMAGE",
    "image/gif": "IMAGE",
    "image/bmp": "IMAGE",
    "image/webp": "IMAGE",
    "image/tiff": "IMAGE",
    "video/mp4": "VIDEO",
    "video/avi": "VIDEO",
    "video/mkv": "VIDEO",
    "audio/mpeg": "AUDIO",
    "audio/wav": "AUDIO",
    "audio/ogg": "AUDIO",
    "application/pdf": "DOCUMENT",
    "application/msword": "DOCUMENT",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCUMENT",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "DOCUMENT",
    "application/zip": "ARCHIVE",
    "application/x-rar-compressed": "ARCHIVE",
    "application/x-7z-compressed": "ARCHIVE",
    "application/gzip": "ARCHIVE",
    "application/x-sqlite3": "DATABASE",
    "application/x-executable": "EXECUTABLE",
    "application/x-msdos-program": "EXECUTABLE",
    "text/plain": "TEXT",
    "text/html": "TEXT",
    "text/csv": "TEXT",
    "application/json": "TEXT",
    "application/xml": "TEXT",
}

EXTENSION_TO_TYPE = {
    ".jpg": "JPEG", ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".pdf": "PDF",
    ".zip": "ZIP",
    ".docx": "DOCX",
    ".xlsx": "XLSX",
    ".mp3": "MP3",
    ".wav": "WAV",
    ".mp4": "MP4",
    ".avi": "AVI",
    ".txt": "TEXT",
    ".exe": "EXE",
    ".dll": "DLL",
}

SIGNATURE_TO_TYPE = {
    b"\xFF\xD8\xFF": "JPEG",
    b"\x89\x50\x4E\x47": "PNG",
    b"\x47\x49\x46\x38": "GIF",
    b"\x42\x4D": "BMP",
    b"\x25\x50\x44\x46": "PDF",
    b"\x50\x4B\x03\x04": "ZIP",
    b"\x52\x49\x46\x46": "WAV",
    b"\x00\x00\x00": "MP4",  # requires ftyp check
}


@dataclass
class ClassificationResult:
    """Classification output for a recovered artifact."""
    detected_type: str
    detected_extension: str
    detected_mime: str
    category: str
    magic_bytes: str
    size: int
    extension_mismatch: bool = False
    mismatch_details: str = ""
    metadata_extracted: dict = field(default_factory=dict)
    confidence: float = 0.0


class ClassificationEngine:
    """
    Classifies recovered files using:
    - Magic bytes / file signatures
    - MIME type detection
    - Extension analysis
    - Mismatch detection
    """

    def classify(
        self,
        data: bytes,
        original_filename: Optional[str] = None,
        declared_type: Optional[str] = None,
    ) -> ClassificationResult:
        """Classify a file based on its content and metadata."""

        # Detect type from magic bytes
        detected_type = self._detect_from_magic(data)
        detected_mime = self._get_mime(detected_type)
        category = MIME_TO_CATEGORY.get(detected_mime, "UNKNOWN")
        detected_ext = self._get_extension(detected_type)

        # Check for extension mismatch
        mismatch = False
        mismatch_detail = ""
        if original_filename:
            ext = self._get_file_extension(original_filename)
            expected_type = EXTENSION_TO_TYPE.get(ext.lower(), "UNKNOWN")
            if expected_type != "UNKNOWN" and expected_type != detected_type:
                mismatch = True
                mismatch_detail = (
                    f"Extension '{ext}' suggests {expected_type}, "
                    f"but signature indicates {detected_type}"
                )

        if declared_type and declared_type != detected_type:
            mismatch = True
            mismatch_detail += (
                f"; Declared type '{declared_type}' != detected '{detected_type}'"
            )

        # Extract basic metadata
        metadata = self._extract_metadata(data, detected_type)

        # Magic bytes hex representation
        magic_hex = data[:8].hex() if len(data) >= 8 else data.hex()

        confidence = self._compute_confidence(
            detected_type, mismatch, len(data)
        )

        result = ClassificationResult(
            detected_type=detected_type,
            detected_extension=detected_ext,
            detected_mime=detected_mime,
            category=category,
            magic_bytes=magic_hex,
            size=len(data),
            extension_mismatch=mismatch,
            mismatch_details=mismatch_detail.strip("; "),
            metadata_extracted=metadata,
            confidence=confidence,
        )

        logger.info(
            "classification_complete",
            detected_type=detected_type,
            category=category,
            mismatch=mismatch,
            size=len(data),
        )
        return result

    def _detect_from_magic(self, data: bytes) -> str:
        """Detect file type from magic bytes."""
        if len(data) < 2:
            return "UNKNOWN"

        # Check specific signatures (longest first)
        if data[:8] == b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A":
            return "PNG"
        if data[:4] == b"\x25\x50\x44\x46":
            return "PDF"
        if data[:4] == b"\x50\x4B\x03\x04":
            # Could be ZIP, DOCX, XLSX — check for Office markers
            if b"word/" in data[:2000]:
                return "DOCX"
            if b"xl/" in data[:2000]:
                return "XLSX"
            return "ZIP"
        if data[:4] == b"\x47\x49\x46\x38":
            return "GIF"
        if data[:3] == b"\xFF\xD8\xFF":
            return "JPEG"
        if data[:2] == b"\x42\x4D":
            return "BMP"
        if data[:4] == b"\x52\x49\x46\x46" and len(data) >= 12:
            if data[8:12] == b"WAVE":
                return "WAV"
            if data[8:12] == b"AVI ":
                return "AVI"
        if len(data) >= 8 and data[4:8] == b"ftyp":
            return "MP4"
        if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
            return "MP3"
        if data[:3] == b"ID3":
            return "MP3"

        # Try text detection
        try:
            data[:512].decode("utf-8")
            return "TEXT"
        except (UnicodeDecodeError, ValueError):
            pass

        return "UNKNOWN"

    def _get_mime(self, file_type: str) -> str:
        type_to_mime = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "BMP": "image/bmp",
            "PDF": "application/pdf",
            "ZIP": "application/zip",
            "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "MP3": "audio/mpeg",
            "WAV": "audio/wav",
            "MP4": "video/mp4",
            "AVI": "video/avi",
            "TEXT": "text/plain",
        }
        return type_to_mime.get(file_type, "application/octet-stream")

    def _get_extension(self, file_type: str) -> str:
        type_to_ext = {
            "JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "BMP": ".bmp",
            "PDF": ".pdf", "ZIP": ".zip", "DOCX": ".docx", "XLSX": ".xlsx",
            "MP3": ".mp3", "WAV": ".wav", "MP4": ".mp4", "TEXT": ".txt",
        }
        return type_to_ext.get(file_type, ".bin")

    def _get_file_extension(self, filename: str) -> str:
        if "." in filename:
            return "." + filename.rsplit(".", 1)[-1]
        return ""

    def _extract_metadata(self, data: bytes, file_type: str) -> dict:
        """Extract basic metadata from the file data."""
        meta = {"size_bytes": len(data)}

        if file_type == "PNG" and len(data) >= 24:
            import struct
            meta["width"] = struct.unpack(">I", data[16:20])[0]
            meta["height"] = struct.unpack(">I", data[20:24])[0]
        elif file_type == "GIF" and len(data) >= 10:
            import struct
            meta["width"] = struct.unpack("<H", data[6:8])[0]
            meta["height"] = struct.unpack("<H", data[8:10])[0]
        elif file_type == "BMP" and len(data) >= 26:
            import struct
            meta["width"] = struct.unpack("<i", data[18:22])[0]
            meta["height"] = abs(struct.unpack("<i", data[22:26])[0])
        elif file_type == "PDF":
            if b"/Pages" in data:
                meta["has_pages"] = True
            version = data[:8].decode("ascii", errors="ignore").strip()
            meta["version"] = version

        return meta

    def _compute_confidence(
        self, file_type: str, has_mismatch: bool, size: int
    ) -> float:
        """Compute classification confidence."""
        if file_type == "UNKNOWN":
            return 0.1

        confidence = 0.7
        if has_mismatch:
            confidence -= 0.3
        if size > 1024:
            confidence += 0.1
        if size > 10240:
            confidence += 0.1
        if file_type in ("JPEG", "PNG", "PDF", "ZIP"):
            confidence += 0.1  # Well-known signatures

        return min(max(confidence, 0.0), 1.0)
