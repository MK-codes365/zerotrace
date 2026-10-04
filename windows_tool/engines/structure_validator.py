"""
ZeroTrace Structure-Based Recovery Validator & Confidence Scorer
Inspired by TestDisk, PhotoRec, TRACE-Forensic-Toolkit, and searchlight.
Analyzes internal structure of carved candidate files without filesystem
metadata, calculates structural integrity, and produces forensic confidence scores.
"""

import io
import struct
import zipfile
from typing import Dict, Any, Tuple
from core.crypto import calculate_entropy


class RecoveryStructureValidator:
    """
    Performs deep format structure checks and calculates confidence scores (0.0 to 1.0).
    Uses pypdf, PIL, zipfile, and format-specific binary parsers.
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
        u_type = file_type.upper()

        # Reject Alternate Data Streams (ADS) ZoneTransfer text
        if b"[ZoneTransfer]" in data or b"ZoneId=" in data:
            return {
                "confidence": 0.05,
                "confidence_percent": 5,
                "entropy": entropy,
                "header_matched": False,
                "footer_matched": False,
                "structural_check": False,
                "diagnostics": ["Rejected: Windows Zone.Identifier Alternate Data Stream (not document payload)"],
            }

        if "JPEG" in u_type or "JPG" in u_type:
            valid, reason = cls._validate_jpeg(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.10
            entropy_score = 0.10 if 6.8 <= entropy <= 8.0 else 0.05

        elif "PNG" in u_type:
            valid, reason = cls._validate_png(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.08
            entropy_score = 0.10 if 6.5 <= entropy <= 8.0 else 0.05

        elif "PDF" in u_type:
            valid, reason = cls._validate_pdf(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.05
            entropy_score = 0.10 if 4.0 <= entropy <= 7.8 else 0.05

        elif any(k in u_type for k in ("ZIP", "OFFICE", "DOCX", "XLSX", "PPTX")):
            valid, reason = cls._validate_zip_family(data, u_type)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.10
            entropy_score = 0.10 if 7.0 <= entropy <= 8.0 else 0.05

        elif "SQLITE" in u_type:
            valid, reason = cls._validate_sqlite(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.05
            entropy_score = 0.10 if 2.0 <= entropy <= 7.0 else 0.05

        elif "BMP" in u_type:
            valid, reason = cls._validate_bmp(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.05
            entropy_score = 0.10 if 2.0 <= entropy <= 7.5 else 0.05

        elif "RIFF" in u_type or "WAV" in u_type:
            valid, reason = cls._validate_riff(data)
            diag.append(reason)
            structure_score = 0.25 if valid else 0.05
            entropy_score = 0.10 if 4.0 <= entropy <= 7.8 else 0.05

        else:
            structure_score = 0.15
            entropy_score = 0.08
            diag.append("Generic signature match; standard format rules applied")

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

    # Format-specific deep structural validators

    @staticmethod
    def _validate_jpeg(data: bytes) -> Tuple[bool, str]:
        if len(data) < 4 or not data.startswith(b"\xFF\xD8"):
            return False, "Invalid JPEG SOI marker"

        # Attempt deep PIL validation if available
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            img.verify()
            return True, f"Valid JPEG image: {img.format} {getattr(img, 'size', '')} verified cleanly by PIL"
        except Exception:
            pass

        # Fallback to marker stream walk
        pos = 2
        has_sof = False
        while pos < len(data) - 4:
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xC0, 0xC2):
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

        # Attempt PIL validation
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            img.verify()
            return True, f"Valid PNG image: {img.size[0]}x{img.size[1]} verified cleanly by PIL"
        except Exception:
            pass

        # Fallback to IHDR and IEND check
        if b"IHDR" in data[:32]:
            if b"IEND" in data[-16:]:
                return True, "Valid PNG: Verified IHDR and IEND chunks"
            return True, "Partial PNG: Valid IHDR present"
        return False, "PNG missing IHDR chunk"

    @staticmethod
    def _validate_pdf(data: bytes) -> Tuple[bool, str]:
        if not data.startswith(b"%PDF-"):
            return False, "Invalid PDF header: Missing %PDF- signature"

        # Deep PDF validation via pypdf
        try:
            # pyrefly: ignore [missing-import]
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(data), strict=False)
            num_pages = len(reader.pages)
            is_encrypted = reader.is_encrypted
            enc_str = " (encrypted)" if is_encrypted else ""
            return True, f"Valid PDF: {num_pages} page(s){enc_str} parsed cleanly by pypdf engine"
        except Exception as e:
            err_msg = str(e)

        # Fallback to trailer and %%EOF byte checks
        has_eof = b"%%EOF" in data[-1024:]
        has_trailer = b"trailer" in data or b"/Root" in data or b"/Pages" in data
        if has_eof and has_trailer:
            return True, "Valid PDF: %%EOF trailer and document catalog present"
        if has_eof:
            return True, "Partial PDF: %%EOF marker present, catalog unindexed"
        return False, f"Incomplete PDF: %%EOF trailer not located ({err_msg[:40]})"

    @staticmethod
    def _validate_zip_family(data: bytes, file_type: str) -> Tuple[bool, str]:
        if not data.startswith(b"PK\x03\x04"):
            return False, "Invalid ZIP local file header"

        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                bad_file = zf.testzip()
                if bad_file is None:
                    namelist = zf.namelist()
                    num_files = len(namelist)
                    # Classify Office documents
                    if any("word/" in n for n in namelist):
                        return True, f"Valid DOCX document: {num_files} archive items verified intact"
                    if any("xl/" in n for n in namelist):
                        return True, f"Valid XLSX workbook: {num_files} archive items verified intact"
                    if any("ppt/" in n for n in namelist):
                        return True, f"Valid PPTX presentation: {num_files} archive items verified intact"
                    return True, f"Valid ZIP archive: {num_files} archive items CRC-verified"
                else:
                    return False, f"Corrupted ZIP: Member {bad_file} failed CRC check"
        except Exception:
            pass

        has_eocd = b"PK\x05\x06" in data[-512:]
        if has_eocd:
            return True, "Valid ZIP: End of Central Directory (EOCD) verified"
        if b"PK\x01\x02" in data:
            return True, "Partial ZIP: Central directory headers present"
        return False, "Incomplete ZIP: Central directory missing or truncated"

    @staticmethod
    def _validate_bmp(data: bytes) -> Tuple[bool, str]:
        if len(data) < 26 or not data.startswith(b"BM"):
            return False, "Invalid BMP signature"
        if data[6:10] != b"\x00\x00\x00\x00":
            return False, "Invalid BMP: Reserved header fields non-zero"
        declared_size = struct.unpack("<I", data[2:6])[0]
        dib_header_size = struct.unpack("<I", data[14:18])[0]
        if dib_header_size not in (12, 40, 52, 56, 64, 108, 124):
            return False, "Invalid BMP DIB header structure"
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            img.verify()
            return True, f"Valid BMP: {img.format} {img.size} verified cleanly by PIL"
        except Exception:
            return False, "Corrupted or unopenable BMP: Image failed PIL verification"

    @staticmethod
    def _validate_riff(data: bytes) -> Tuple[bool, str]:
        if len(data) < 12 or not data.startswith(b"RIFF"):
            return False, "Invalid RIFF signature"
        riff_form = data[8:12].decode("latin1", errors="ignore")
        declared_size = struct.unpack("<I", data[4:8])[0] + 8
        return True, f"Valid RIFF container ({riff_form}): Declared size {declared_size} bytes"

    @staticmethod
    def _validate_sqlite(data: bytes) -> Tuple[bool, str]:
        if len(data) < 100 or not data.startswith(b"SQLite format 3\x00"):
            return False, "Invalid SQLite header"

        page_size = struct.unpack(">H", data[16:18])[0]
        if page_size in (512, 1024, 2048, 4096, 8192, 16384, 32768, 65536) or page_size == 1:
            real_page_size = 65536 if page_size == 1 else page_size
            page_count = struct.unpack(">I", data[28:32])[0]
            return True, f"Valid SQLite database: Page size {real_page_size}B, {page_count} pages"
        return False, "Invalid SQLite page size descriptor"
