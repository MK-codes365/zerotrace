"""
ZEROTrace — File Carving Engine
Signature-based file carving with plugin architecture for extensibility.
Supports: JPEG, PNG, PDF, ZIP, DOCX, XLSX, MP4, MP3, GIF, WAV, BMP.
"""

import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger("carving")


# ═══════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════

@dataclass
class FileSignature:
    """Defines header/footer magic bytes for a file type."""
    file_type: str
    extension: str
    mime_type: str
    category: str
    header: bytes
    header_offset: int = 0
    footer: Optional[bytes] = None
    max_size: int = 100 * 1024 * 1024  # 100 MB default max
    min_size: int = 64  # Minimum plausible file size


@dataclass
class CarvedCandidate:
    """A candidate file discovered during carving."""
    file_type: str
    extension: str
    mime_type: str
    category: str
    offset: int
    size: int
    header_bytes: bytes
    footer_offset: Optional[int] = None
    footer_found: bool = False
    confidence: float = 0.0
    data: Optional[bytes] = None
    metadata: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# Signature Registry (Plugin Architecture)
# ═══════════════════════════════════════════════════════════

class SignatureRegistry:
    """
    Plugin registry for file signatures.
    New file types can be added by registering a FileSignature.
    """

    def __init__(self):
        self._signatures: list[FileSignature] = []
        self._register_defaults()

    def register(self, sig: FileSignature):
        """Register a new file type signature."""
        self._signatures.append(sig)
        logger.info("signature_registered", file_type=sig.file_type, ext=sig.extension)

    def get_all(self) -> list[FileSignature]:
        return list(self._signatures)

    def get_by_type(self, file_type: str) -> Optional[FileSignature]:
        for sig in self._signatures:
            if sig.file_type == file_type:
                return sig
        return None

    def get_supported_types(self) -> list[str]:
        return [s.file_type for s in self._signatures]

    def _register_defaults(self):
        """Register all built-in file type signatures."""

        # ── Images ────────────────────────────────────
        self.register(FileSignature(
            file_type="JPEG",
            extension=".jpg",
            mime_type="image/jpeg",
            category="IMAGE",
            header=b"\xFF\xD8\xFF",
            footer=b"\xFF\xD9",
            max_size=50 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="PNG",
            extension=".png",
            mime_type="image/png",
            category="IMAGE",
            header=b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A",
            footer=b"\x49\x45\x4E\x44\xAE\x42\x60\x82",
            max_size=50 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="GIF",
            extension=".gif",
            mime_type="image/gif",
            category="IMAGE",
            header=b"\x47\x49\x46\x38",  # GIF87a or GIF89a
            footer=b"\x00\x3B",
            max_size=20 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="BMP",
            extension=".bmp",
            mime_type="image/bmp",
            category="IMAGE",
            header=b"\x42\x4D",
            max_size=50 * 1024 * 1024,
        ))

        # ── Documents ─────────────────────────────────
        self.register(FileSignature(
            file_type="PDF",
            extension=".pdf",
            mime_type="application/pdf",
            category="DOCUMENT",
            header=b"\x25\x50\x44\x46",  # %PDF
            footer=b"\x25\x25\x45\x4F\x46",  # %%EOF
            max_size=200 * 1024 * 1024,
        ))

        # ── Archives (ZIP-based: DOCX, XLSX, etc.) ───
        self.register(FileSignature(
            file_type="ZIP",
            extension=".zip",
            mime_type="application/zip",
            category="ARCHIVE",
            header=b"\x50\x4B\x03\x04",
            footer=b"\x50\x4B\x05\x06",
            max_size=500 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="DOCX",
            extension=".docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            category="DOCUMENT",
            header=b"\x50\x4B\x03\x04",
            footer=b"\x50\x4B\x05\x06",
            max_size=100 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="XLSX",
            extension=".xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            category="DOCUMENT",
            header=b"\x50\x4B\x03\x04",
            footer=b"\x50\x4B\x05\x06",
            max_size=100 * 1024 * 1024,
        ))

        # ── Audio ─────────────────────────────────────
        self.register(FileSignature(
            file_type="MP3",
            extension=".mp3",
            mime_type="audio/mpeg",
            category="AUDIO",
            header=b"\xFF\xFB",
            max_size=50 * 1024 * 1024,
        ))
        self.register(FileSignature(
            file_type="WAV",
            extension=".wav",
            mime_type="audio/wav",
            category="AUDIO",
            header=b"\x52\x49\x46\x46",  # RIFF
            max_size=200 * 1024 * 1024,
        ))

        # ── Video ─────────────────────────────────────
        self.register(FileSignature(
            file_type="MP4",
            extension=".mp4",
            mime_type="video/mp4",
            category="VIDEO",
            header=b"\x00\x00\x00",  # ftyp box (variable offset)
            max_size=2 * 1024 * 1024 * 1024,
        ))


# ═══════════════════════════════════════════════════════════
# Block Scanner
# ═══════════════════════════════════════════════════════════

class BlockScanner:
    """
    Scans a data buffer for file signatures.
    Handles chunk boundaries via overlap bytes.
    """

    def __init__(self, registry: SignatureRegistry):
        self.registry = registry

    def scan(
        self,
        data: bytes,
        base_offset: int = 0,
        file_types: Optional[list[str]] = None,
    ) -> list[CarvedCandidate]:
        """
        Scan a data buffer for file signatures.
        
        Args:
            data: Raw bytes to scan
            base_offset: Absolute offset of this chunk in the evidence image
            file_types: Optional filter — only scan for these types
        
        Returns:
            List of CarvedCandidate objects
        """
        candidates = []
        signatures = self.registry.get_all()

        if file_types:
            signatures = [s for s in signatures if s.file_type in file_types]

        for sig in signatures:
            offset = 0
            while offset < len(data) - len(sig.header):
                # Search for header
                pos = data.find(sig.header, offset)
                if pos == -1:
                    break

                absolute_offset = base_offset + pos
                candidate = self._extract_candidate(data, pos, sig, absolute_offset)
                if candidate:
                    candidates.append(candidate)

                offset = pos + 1

        # Sort by offset
        candidates.sort(key=lambda c: c.offset)
        logger.info(
            "scan_complete",
            base_offset=base_offset,
            data_size=len(data),
            candidates_found=len(candidates),
        )
        return candidates

    def _extract_candidate(
        self,
        data: bytes,
        pos: int,
        sig: FileSignature,
        absolute_offset: int,
    ) -> Optional[CarvedCandidate]:
        """Extract a candidate file from the data buffer."""

        # Special handling for MP4
        if sig.file_type == "MP4":
            return self._extract_mp4(data, pos, sig, absolute_offset)

        # If footer exists, search for it
        footer_offset = None
        footer_found = False
        file_size = 0

        if sig.footer:
            footer_pos = data.find(sig.footer, pos + len(sig.header))
            if footer_pos != -1:
                file_size = (footer_pos + len(sig.footer)) - pos
                footer_offset = absolute_offset + (footer_pos - pos)
                footer_found = True
            else:
                # Footer not found in this chunk — might be in next chunk
                # Use max_size as upper bound
                file_size = min(sig.max_size, len(data) - pos)
        else:
            # No footer defined — try to determine size from structure
            file_size = self._estimate_size(data, pos, sig)

        # Validate size
        if file_size < sig.min_size or file_size > sig.max_size:
            return None

        # Calculate initial confidence
        confidence = self._calculate_confidence(
            sig, footer_found, file_size
        )

        # Extract header bytes for metadata
        header_sample = data[pos : pos + min(32, len(data) - pos)]

        return CarvedCandidate(
            file_type=sig.file_type,
            extension=sig.extension,
            mime_type=sig.mime_type,
            category=sig.category,
            offset=absolute_offset,
            size=file_size,
            header_bytes=header_sample,
            footer_offset=footer_offset,
            footer_found=footer_found,
            confidence=confidence,
            data=data[pos : pos + file_size] if file_size <= 10 * 1024 * 1024 else None,
        )

    def _extract_mp4(
        self, data: bytes, pos: int, sig: FileSignature, absolute_offset: int
    ) -> Optional[CarvedCandidate]:
        """Special MP4 extraction using box/atom structure."""
        # Check for 'ftyp' marker at offset +4
        if pos + 8 > len(data):
            return None
        if data[pos + 4 : pos + 8] != b"ftyp":
            return None

        # Read box size
        box_size = struct.unpack(">I", data[pos : pos + 4])[0]
        if box_size < 8:
            return None

        # Estimate total size by walking boxes
        total_size = 0
        scan_pos = pos
        while scan_pos < len(data) - 8:
            if scan_pos + 4 > len(data):
                break
            bsize = struct.unpack(">I", data[scan_pos : scan_pos + 4])[0]
            if bsize < 8:
                break
            total_size += bsize
            scan_pos += bsize
            if total_size > sig.max_size:
                break

        if total_size < sig.min_size:
            return None

        return CarvedCandidate(
            file_type="MP4",
            extension=".mp4",
            mime_type="video/mp4",
            category="VIDEO",
            offset=absolute_offset,
            size=min(total_size, len(data) - pos),
            header_bytes=data[pos : pos + 32],
            footer_found=False,
            confidence=0.6,
            data=None,  # MP4s are typically too large to hold in memory
        )

    def _estimate_size(
        self, data: bytes, pos: int, sig: FileSignature
    ) -> int:
        """Estimate file size when no footer is defined."""
        if sig.file_type == "BMP" and pos + 6 <= len(data):
            # BMP has file size at offset 2
            return struct.unpack("<I", data[pos + 2 : pos + 6])[0]
        if sig.file_type == "WAV" and pos + 8 <= len(data):
            # RIFF/WAV has size at offset 4
            return struct.unpack("<I", data[pos + 4 : pos + 8])[0] + 8
        # Default: use max_size or remaining data
        return min(sig.max_size, len(data) - pos)

    def _calculate_confidence(
        self,
        sig: FileSignature,
        footer_found: bool,
        file_size: int,
    ) -> float:
        """Calculate initial confidence score for a candidate."""
        confidence = 0.4  # Base confidence for header match

        if footer_found:
            confidence += 0.3

        # Size plausibility
        if sig.min_size <= file_size <= sig.max_size:
            confidence += 0.1

        # Longer headers are more specific
        if len(sig.header) >= 4:
            confidence += 0.1
        if len(sig.header) >= 8:
            confidence += 0.1

        return min(confidence, 1.0)


# ═══════════════════════════════════════════════════════════
# Singleton Registry
# ═══════════════════════════════════════════════════════════

_default_registry = None


def get_signature_registry() -> SignatureRegistry:
    """Get or create the default signature registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SignatureRegistry()
    return _default_registry
