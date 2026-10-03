"""
ZeroTrace Structure-Based Recovery Validator & Confidence Scorer
Inspired by TestDisk and PhotoRec structure-validation routines.
Analyzes internal structure of carved candidate files without filesystem
metadata, calculates structural integrity, and produces forensic confidence scores.
"""

import struct
from typing import Dict, Any, Tuple
from core.crypto import calculate_entropy


class RecoveryStructureValidator:
    """
    Performs deep format structure checks and calculates confidence scores (0.0 to 1.0).
    """

    @classmethod
    def validate_and_score(cls, file_type: str, data: bytes, footer_matched: bool = False) -> Dict[str, Any]:
        """
        Evaluate structural validity and return confidence score + diagnostics.
        """
        if not data:
            return {"confidence": 0.0, "valid": False, "reason": "Empty payload"}

        header_score = 0.30  # Signature was matched
        footer_score = 0.25 if footer_matched else 0.05
        structure_score = 0.0
        entropy_score = 0.0
        size_score = 0.10 if len(data) >= 128 else 0.02
        diag = []

        entropy = calculate_entropy(data)

        # format-specific structure validation
        u_type = file_type.upper()

        if "JPEG" in u_type or "JPG" in u_type:
            valid, reason = cls._validate_jpeg(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.10
            # JPEG entropy typically 7.2 - 7.9
            entropy_score = 0.10 if 6.8 <= entropy <= 8.0 else 0.05

        elif "PNG" in u_type:
            valid, reason = cls._validate_png(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.08
            entropy_score = 0.10 if 6.5 <= entropy <= 8.0 else 0.05

        elif "PDF" in u_type:
            valid, reason = cls._validate_pdf(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.12
            # PDF has mixed text and streams, entropy typically 4.5 - 7.5
            entropy_score = 0.10 if 4.0 <= entropy <= 7.8 else 0.05

        elif "ZIP" in u_type or "OFFICE" in u_type or "DOCX" in u_type or "XLSX" in u_type:
            valid, reason = cls._validate_zip(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.10
            entropy_score = 0.10 if 7.0 <= entropy <= 8.0 else 0.05

        elif "SQLITE" in u_type:
            valid, reason = cls._validate_sqlite(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.05
            entropy_score = 0.10 if 2.0 <= entropy <= 7.0 else 0.05

        else:
            # Generic structure validation
            structure_score = 0.15
            entropy_score = 0.08
            diag.append("Generic signature match; no specialized validator")

        total_confidence = round(header_score + footer_score + structure_score + entropy_score + size_score, 2)
        total_confidence = min(1.0, max(0.0, total_confidence))

        return {
            "confidence": total_confidence,
            "confidence_percent": int(total_confidence * 100),
            "entropy": entropy,
            "header_matched": True,
            "footer_matched": footer_matched,
            "structural_check": structure_score >= 0.20,
            "diagnostics": diag,
        }

    # parser helpers for different formats

    @staticmethod
    def _validate_jpeg(data: bytes) -> Tuple[bool, str]:
        if len(data) < 4 or not data.startswith(b"\xFF\xD8"):
            return False, "Invalid JPEG SOI marker"

        # Search for markers (SOF0, SOF2, etc.)
        pos = 2
        has_sof = False
        while pos < len(data) - 4:
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xC0, 0xC2):  # SOF0 / SOF2
                has_sof = True
                break
            pos += 2

        if data.endswith(b"\xFF\xD9"):
            if has_sof:
                return True, "Valid JPEG: SOI, SOF marker, and clean EOI trailer present"
            return True, "Valid JPEG: Clean EOI trailer found"
        return False, "Incomplete JPEG: EOI trailer missing or truncated"

    @staticmethod
    def _validate_png(data: bytes) -> Tuple[bool, str]:
        if len(data) < 8 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return False, "Invalid PNG magic header"

        # Check IHDR
        if b"IHDR" in data[:32]:
            if b"IEND" in data[-16:]:
                return True, "Valid PNG: Verified IHDR and IEND chunks"
            return True, "Partial PNG: Valid IHDR present"
        return False, "PNG missing IHDR chunk"

    @staticmethod
    def _validate_pdf(data: bytes) -> Tuple[bool, str]:
        if not data.startswith(b"%PDF-"):
            return False, "Invalid PDF header version"

        has_eof = b"%%EOF" in data[-1024:]
        has_trailer = b"trailer" in data or b"/Root" in data
        if has_eof and has_trailer:
            return True, "Valid PDF: %%EOF trailer and document catalog present"
        if has_eof:
            return True, "Valid PDF: %%EOF marker present"
        return False, "Truncated PDF: %%EOF trailer not located"

    @staticmethod
    def _validate_zip(data: bytes) -> Tuple[bool, str]:
        if not data.startswith(b"PK\x03\x04"):
            return False, "Invalid ZIP local file header"

        has_eocd = b"PK\x05\x06" in data[-512:]
        if has_eocd:
            return True, "Valid ZIP: End of Central Directory (EOCD) verified"
        if b"PK\x01\x02" in data:
            return True, "Valid ZIP: Central directory headers present"
        return False, "Incomplete ZIP: Central directory missing"

    @staticmethod
    def _validate_sqlite(data: bytes) -> Tuple[bool, str]:
        if len(data) < 100 or not data.startswith(b"SQLite format 3\x00"):
            return False, "Invalid SQLite header"

        page_size = struct.unpack(">H", data[16:18])[0]
        if page_size in (512, 1024, 2048, 4096, 8192, 16384, 32768, 65536) or page_size == 1:
            return True, f"Valid SQLite database: Page size {page_size} bytes"
        return False, "Invalid SQLite page size descriptor"
