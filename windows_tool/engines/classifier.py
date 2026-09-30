"""
ZeroTrace Automatic File Classification Engine — Autopsy Inspired
Classifies recovered/carved files into forensic artifact categories,
extracts structural metadata, and evaluates evidential significance.
"""

from typing import Dict, Any, Optional
import struct


class FileClassifier:
    """
    Automated classification and metadata extractor inspired by Autopsy forensic modules.
    """

    CATEGORIES = {
        "IMAGE": ["JPEG", "JPG", "PNG", "GIF", "BMP", "TIFF", "WEBP", "ICO"],
        "DOCUMENT": ["PDF", "DOC", "DOCX", "XLS", "XLSX", "PPT", "PPTX", "RTF", "TXT", "HTML"],
        "MEDIA": ["MP4", "AVI", "MKV", "MOV", "MP3", "WAV", "FLAC", "OGG"],
        "ARCHIVE": ["ZIP", "7Z", "RAR", "TAR", "GZ", "BZ2"],
        "DATABASE": ["SQLITE", "MDB", "ACCDB", "EDB"],
        "FORENSIC_ARTIFACT": ["EVTX", "REGISTRY", "PREFETCH", "PCAP", "MEMORY_DUMP"],
    }

    @classmethod
    def classify(cls, file_type: str, data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Classify file and extract metadata.
        """
        u_type = file_type.upper()
        detected_category = "UNKNOWN"

        for cat, types in cls.CATEGORIES.items():
            if any(t in u_type for t in types):
                detected_category = cat
                break

        metadata: Dict[str, Any] = {"category": detected_category}

        if data:
            metadata["size_bytes"] = len(data)
            # Metadata extraction for images
            if detected_category == "IMAGE":
                dims = cls._extract_image_dimensions(data, u_type)
                if dims:
                    metadata["dimensions"] = f"{dims[0]}x{dims[1]}"

            # Metadata extraction for PDF
            elif "PDF" in u_type:
                ver = cls._extract_pdf_version(data)
                if ver:
                    metadata["pdf_version"] = ver

            # Metadata extraction for ZIP/DOCX
            elif detected_category == "ARCHIVE" or "ZIP" in u_type:
                is_office = any(b in data[:2048] for b in [b"word/", b"xl/", b"ppt/", b"[Content_Types].xml"])
                if is_office:
                    metadata["document_type"] = "Microsoft Office OpenXML Document"

        return metadata

    @staticmethod
    def _extract_image_dimensions(data: bytes, file_type: str) -> Optional[tuple[int, int]]:
        try:
            # PNG: IHDR width/height at bytes 16-24
            if "PNG" in file_type and len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
                w, h = struct.unpack(">II", data[16:24])
                return w, h

            # JPEG: Parse SOF marker
            if "JPEG" in file_type and len(data) >= 4:
                idx = 2
                while idx < len(data) - 9:
                    if data[idx] != 0xFF:
                        idx += 1
                        continue
                    marker = data[idx + 1]
                    if marker in (0xC0, 0xC1, 0xC2):  # Baseline / Progressive SOF
                        h, w = struct.unpack(">HH", data[idx + 5 : idx + 9])
                        return w, h
                    length = struct.unpack(">H", data[idx + 2 : idx + 4])[0]
                    idx += 2 + length
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_pdf_version(data: bytes) -> Optional[str]:
        try:
            header_line = data[:32].split(b"\n")[0]
            if b"%PDF-" in header_line:
                return header_line.decode("latin1").strip()
        except Exception:
            pass
        return None
