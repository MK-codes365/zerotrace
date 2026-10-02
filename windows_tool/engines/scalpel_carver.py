"""
ZeroTrace Scalpel-Powered File Carving Engine — Module 3
High-performance signature-based file carver utilizing the signature
dictionary and algorithms from Scalpel (scalpel.conf).
Scans raw unallocated disk space, raw drives, or disk images (.dd/.raw/.img)
with sliding-window chunk extraction and reverse footer parsing.
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from core.crypto import sha256_bytes


@dataclass
class CarveSignature:
    file_type: str
    extension: str
    category: str
    header: bytes
    footer: Optional[bytes] = None
    min_size: int = 64
    max_size: int = 50 * 1024 * 1024  # 50 MB default
    reverse_search: bool = False
    description: str = ""


@dataclass
class CarvedFile:
    file_id: str
    file_type: str
    extension: str
    category: str
    offset: int
    size: int
    sha256: str
    confidence: float
    data: Optional[bytes] = None
    preview_snippet: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_target: str = ""


class ScalpelCarver:
    """
    Signature-based carver inspired by Scalpel.
    Carves files from raw disk streams or image files without filesystem metadata.
    """

    def __init__(self, chunk_size: int = 2 * 1024 * 1024, overlap_size: int = 64 * 1024):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.signatures: List[CarveSignature] = []
        self.is_running = False
        self.is_cancelled = False
        self._load_signatures()

    def _load_signatures(self):
        """Load comprehensive forensic signatures matching Scalpel configuration."""
        # Images
        self.signatures.append(CarveSignature(
            file_type="JPEG", extension=".jpg", category="IMAGE",
            header=b"\xFF\xD8\xFF", footer=b"\xFF\xD9",
            min_size=100, max_size=30 * 1024 * 1024,
            description="JPEG Image with EXIF/JFIF marker"
        ))
        self.signatures.append(CarveSignature(
            file_type="PNG", extension=".png", category="IMAGE",
            header=b"\x89PNG\r\n\x1a\n", footer=b"IEND\xaeB`\x82",
            min_size=64, max_size=30 * 1024 * 1024,
            description="Portable Network Graphics"
        ))
        self.signatures.append(CarveSignature(
            file_type="GIF", extension=".gif", category="IMAGE",
            header=b"GIF89a", footer=b"\x00\x3B",
            min_size=64, max_size=20 * 1024 * 1024,
            description="Graphics Interchange Format (GIF89a)"
        ))
        self.signatures.append(CarveSignature(
            file_type="GIF", extension=".gif", category="IMAGE",
            header=b"GIF87a", footer=b"\x00\x3B",
            min_size=64, max_size=20 * 1024 * 1024,
            description="Graphics Interchange Format (GIF87a)"
        ))
        self.signatures.append(CarveSignature(
            file_type="BMP", extension=".bmp", category="IMAGE",
            header=b"BM", footer=None,
            min_size=128, max_size=25 * 1024 * 1024,
            description="Windows Bitmap Image"
        ))

        # Documents
        self.signatures.append(CarveSignature(
            file_type="PDF", extension=".pdf", category="DOCUMENT",
            header=b"%PDF-", footer=b"%%EOF",
            min_size=256, max_size=60 * 1024 * 1024,
            reverse_search=True,
            description="Adobe Portable Document Format"
        ))
        self.signatures.append(CarveSignature(
            file_type="ZIP/OFFICE", extension=".zip", category="ARCHIVE",
            header=b"PK\x03\x04", footer=b"PK\x05\x06",
            min_size=128, max_size=100 * 1024 * 1024,
            reverse_search=True,
            description="ZIP Archive or Office OpenXML (DOCX, XLSX, PPTX)"
        ))
        self.signatures.append(CarveSignature(
            file_type="RAR", extension=".rar", category="ARCHIVE",
            header=b"Rar!\x1a\x07", footer=None,
            min_size=128, max_size=100 * 1024 * 1024,
            description="WinRAR Compressed Archive"
        ))
        self.signatures.append(CarveSignature(
            file_type="7Z", extension=".7z", category="ARCHIVE",
            header=b"7z\xbc\xaf\x27\x1c", footer=None,
            min_size=128, max_size=100 * 1024 * 1024,
            description="7-Zip Compressed Archive"
        ))

        # Media
        self.signatures.append(CarveSignature(
            file_type="MP4", extension=".mp4", category="MEDIA",
            header=b"\x00\x00\x00\x18ftypmp42", footer=None,
            min_size=1024, max_size=100 * 1024 * 1024,
            description="MPEG-4 Video File"
        ))
        self.signatures.append(CarveSignature(
            file_type="MP4", extension=".mp4", category="MEDIA",
            header=b"\x00\x00\x00\x20ftypisom", footer=None,
            min_size=1024, max_size=100 * 1024 * 1024,
            description="ISO Base Media File / MP4"
        ))
        self.signatures.append(CarveSignature(
            file_type="MP3", extension=".mp3", category="MEDIA",
            header=b"ID3", footer=None,
            min_size=512, max_size=50 * 1024 * 1024,
            description="MPEG Audio Layer III (ID3 Tagged)"
        ))
        self.signatures.append(CarveSignature(
            file_type="WAV", extension=".wav", category="MEDIA",
            header=b"RIFF", footer=None,
            min_size=1024, max_size=100 * 1024 * 1024,
            description="Waveform Audio File Format"
        ))

        # Forensic Artifacts
        self.signatures.append(CarveSignature(
            file_type="SQLITE", extension=".sqlite", category="DATABASE",
            header=b"SQLite format 3\x00", footer=None,
            min_size=512, max_size=100 * 1024 * 1024,
            description="SQLite 3 Database File"
        ))
        self.signatures.append(CarveSignature(
            file_type="EVTX", extension=".evtx", category="FORENSIC",
            header=b"ElfFile\x00", footer=None,
            min_size=4096, max_size=60 * 1024 * 1024,
            description="Windows Event Log (EVTX)"
        ))
        self.signatures.append(CarveSignature(
            file_type="REGISTRY", extension=".dat", category="FORENSIC",
            header=b"regf", footer=None,
            min_size=4096, max_size=50 * 1024 * 1024,
            description="Windows Registry Hive (regf)"
        ))

        # Dynamically load from scalpel.conf if present
        conf_candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scalpel.conf"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reference_repos", "scalpel", "scalpel.conf"),
        ]
        for conf_path in conf_candidates:
            if os.path.isfile(conf_path):
                self._load_from_conf_file(conf_path)
                break

    def _load_from_conf_file(self, conf_path: str):
        """Parse active rules from a Scalpel configuration file."""
        try:
            with open(conf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        ext = parts[0].lower()
                        if not ext.startswith("."):
                            ext = f".{ext}"
                        case_sens = parts[1].lower() == "y"
                        size_spec = parts[2]
                        header_raw = parts[3]
                        footer_raw = parts[4] if len(parts) >= 5 and parts[4] != "REVERSE" else None
                        reverse = "REVERSE" in parts

                        min_sz, max_sz = 64, 50 * 1024 * 1024
                        if ":" in size_spec:
                            s_parts = size_spec.split(":")
                            try:
                                min_sz = int(s_parts[0])
                                max_sz = int(s_parts[1])
                            except Exception:
                                pass
                        else:
                            try:
                                max_sz = int(size_spec)
                            except Exception:
                                pass

                        header_bytes = self._parse_escape_seq(header_raw)
                        footer_bytes = self._parse_escape_seq(footer_raw) if footer_raw else None

                        if header_bytes and not any(s.extension == ext for s in self.signatures):
                            self.signatures.append(CarveSignature(
                                file_type=ext.replace(".", "").upper(),
                                extension=ext,
                                category="IMAGE" if ext in (".jpg", ".png", ".gif", ".bmp") else "DOCUMENT",
                                header=header_bytes,
                                footer=footer_bytes,
                                min_size=min_sz,
                                max_size=max_sz,
                                reverse_search=reverse,
                                description=f"Scalpel rule: {ext}"
                            ))
        except Exception:
            pass

    def _parse_escape_seq(self, s: str) -> Optional[bytes]:
        """Convert Scalpel slash-hex escaped string into bytes."""
        if not s:
            return None
        try:
            res = bytearray()
            i = 0
            while i < len(s):
                if s[i:i+2] == "\\x" and i + 4 <= len(s):
                    res.append(int(s[i+2:i+4], 16))
                    i += 4
                elif s[i:i+2] == "\\s":
                    res.append(0x20)
                    i += 2
                elif s[i] == "\\" and i + 1 < len(s):
                    res.append(ord(s[i+1]))
                    i += 2
                else:
                    res.append(ord(s[i]))
                    i += 1
            return bytes(res)
        except Exception:
            return None

    def cancel(self):
        self.is_cancelled = True

    def carve_stream(
        self,
        source_path: str,
        total_bytes_to_scan: int = 0,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        file_found_callback: Optional[Callable[[CarvedFile], None]] = None,
        max_files: int = 500,
    ) -> List[CarvedFile]:
        """
        Carve files from a disk image, volume, or raw drive stream.
        """
        self.is_running = True
        self.is_cancelled = False
        carved_results: List[CarvedFile] = []
        start_time = time.time()

        if total_bytes_to_scan <= 0:
            if os.path.isfile(source_path):
                total_bytes_to_scan = os.path.getsize(source_path)
            else:
                total_bytes_to_scan = 100 * 1024 * 1024  # Default 100MB scan window for raw volume

        bytes_scanned = 0
        overlap_buffer = b""
        stream_offset = 0

        # Try opening target
        f = None
        is_simulated = False
        try:
            if os.path.isfile(source_path):
                f = open(source_path, "rb")
            else:
                # Raw handle or device
                import ctypes
                ctypes.windll.kernel32.CreateFileW.restype = ctypes.c_void_p
                target_dev = source_path
                handle = ctypes.windll.kernel32.CreateFileW(
                    target_dev, 0x80000000, 3, None, 3, 0, None
                )
                if not handle or handle == ctypes.c_void_p(-1).value:
                    # Attempt fallback from PhysicalDrive to volume letter (e.g. \\.\F:)
                    vol_letter = None
                    m = re.search(r"([A-Za-z]):", source_path)
                    if m:
                        vol_letter = m.group(1).upper()
                    elif "PHYSICALDRIVE" in source_path.upper():
                        try:
                            from engines.tsk_filesystem import _resolve_target_to_volume
                            vol_letter = _resolve_target_to_volume(source_path)
                        except Exception:
                            pass
                    if vol_letter:
                        target_dev = f"\\\\.\\{vol_letter}:"
                        handle = ctypes.windll.kernel32.CreateFileW(
                            target_dev, 0x80000000, 3, None, 3, 0, None
                        )

                if handle and handle != ctypes.c_void_p(-1).value:
                    # Wrapped raw reader
                    f = RawHandleStream(handle)
                else:
                    if "DEMO" in source_path.upper() or "SIMULAT" in source_path.upper():
                        is_simulated = True
                    else:
                        raise PermissionError(f"Cannot open raw evidence device '{source_path}'. Run ZeroTrace as Administrator or select the logical drive directly.")
        except PermissionError:
            raise
        except Exception:
            if "DEMO" in source_path.upper() or "SIMULAT" in source_path.upper():
                is_simulated = True
            else:
                raise

        try:
            while bytes_scanned < total_bytes_to_scan and len(carved_results) < max_files:
                if self.is_cancelled:
                    break

                read_size = min(self.chunk_size, total_bytes_to_scan - bytes_scanned)
                if not is_simulated and f:
                    chunk = f.read(read_size)
                    if not chunk:
                        break
                else:
                    # Generates simulated raw forensic disk chunk with embedded artifacts
                    chunk = self._generate_simulated_chunk(read_size, stream_offset)
                    time.sleep(0.04)

                combined_chunk = overlap_buffer + chunk
                chunk_base_offset = stream_offset - len(overlap_buffer)

                # Search signatures in current window
                for sig in self.signatures:
                    if self.is_cancelled or len(carved_results) >= max_files:
                        break

                    sig_len = len(sig.header)
                    start_pos = 0

                    while True:
                        hdr_idx = combined_chunk.find(sig.header, start_pos)
                        if hdr_idx == -1:
                            break

                        abs_offset = chunk_base_offset + hdr_idx

                        # Search for footer or calculate size
                        candidate_data = None
                        carve_size = 0
                        footer_found = False

                        if sig.footer:
                            # Forward or reverse search
                            max_search_len = min(sig.max_size, len(combined_chunk) - hdr_idx)
                            payload_window = combined_chunk[hdr_idx : hdr_idx + max_search_len]

                            if sig.reverse_search:
                                ftr_idx = payload_window.rfind(sig.footer)
                            else:
                                ftr_idx = payload_window.find(sig.footer)

                            if ftr_idx != -1:
                                carve_size = ftr_idx + len(sig.footer)
                                candidate_data = payload_window[:carve_size]
                                footer_found = True
                            elif len(payload_window) >= sig.min_size:
                                # Truncated candidate
                                carve_size = len(payload_window)
                                candidate_data = payload_window
                        else:
                            # Signature has no footer; estimate plausible size
                            carve_size = min(sig.max_size, max(sig.min_size, 64 * 1024))
                            candidate_data = combined_chunk[hdr_idx : hdr_idx + carve_size]

                        if candidate_data and len(candidate_data) >= sig.min_size:
                            # Validate file isn't duplicate offset
                            if not any(c.offset == abs_offset for c in carved_results):
                                c_file = self._build_carved_file(
                                    sig=sig,
                                    offset=abs_offset,
                                    data=candidate_data,
                                    footer_found=footer_found,
                                    source_target=source_path,
                                    carve_id=len(carved_results) + 1,
                                )
                                carved_results.append(c_file)
                                if file_found_callback:
                                    file_found_callback(c_file)

                        start_pos = hdr_idx + sig_len

                bytes_scanned += len(chunk)
                stream_offset += len(chunk)
                overlap_buffer = chunk[-self.overlap_size:] if len(chunk) >= self.overlap_size else chunk

                # Telemetry
                now = time.time()
                elapsed = max(0.001, now - start_time)
                speed_mb_s = (bytes_scanned / (1024 * 1024)) / elapsed

                if progress_callback:
                    progress_callback({
                        "bytes_scanned": bytes_scanned,
                        "total_bytes": total_bytes_to_scan,
                        "percent": (bytes_scanned / max(1, total_bytes_to_scan)) * 100,
                        "files_found": len(carved_results),
                        "speed_mb_s": round(speed_mb_s, 2),
                        "elapsed_seconds": int(elapsed),
                        "status": "CARVING",
                    })

        finally:
            if f:
                try:
                    f.close()
                except Exception:
                    pass

        return carved_results

    def _build_carved_file(
        self,
        sig: CarveSignature,
        offset: int,
        data: bytes,
        footer_found: bool,
        source_target: str,
        carve_id: int,
    ) -> CarvedFile:
        """Create structured CarvedFile object with hash, confidence, and preview."""
        c_hash = sha256_bytes(data)
        preview = data[:32].hex(" ")

        # Initial confidence heuristic (further refined by structure validator)
        confidence = 0.50
        if footer_found:
            confidence += 0.35
        if len(data) > sig.min_size * 2:
            confidence += 0.10

        return CarvedFile(
            file_id=f"CARVE-{carve_id:04d}",
            file_type=sig.file_type,
            extension=sig.extension,
            category=sig.category,
            offset=offset,
            size=len(data),
            sha256=c_hash,
            confidence=min(1.0, round(confidence, 2)),
            data=data,
            preview_snippet=preview,
            source_target=source_target,
            metadata={"footer_matched": footer_found, "description": sig.description},
        )

    def _generate_simulated_chunk(self, size: int, current_offset: int) -> bytes:
        """
        Creates authentic forensic raw byte blocks containing deleted artifacts
        for safe live demonstrations on any system without requiring raw unallocated disk images.
        """
        buf = bytearray(b"\x00" * size)

        # Inject sample JPEG
        if current_offset == 0:
            try:
                from core.payload_generator import generate_valid_jpeg
                jpeg_sample = generate_valid_jpeg(
                    file_id="CARVE-0001",
                    details="Restored from physical sector 0x400 (NTFS unallocated cluster run)"
                )
            except Exception:
                jpeg_sample = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + (b"\x12\x34\x56" * 500) + b"\xFF\xD9"
            if len(jpeg_sample) < size - 2048:
                buf[1024 : 1024 + len(jpeg_sample)] = jpeg_sample

        # Inject sample PDF
        if current_offset < 2 * 1024 * 1024:
            try:
                from core.payload_generator import generate_valid_pdf
                pdf_sample = generate_valid_pdf(
                    file_id="CARVE-0002",
                    details="Executive Briefing & Forensic Telemetry Document"
                )
            except Exception:
                pdf_sample = b"%PDF-1.4\n1 0 obj\n<< /Title (ZeroTrace Forensic Audit Report) >>\nendobj\nxref\n0 2\ntrailer\n<< /Size 2 >>\nstartxref\n120\n%%EOF"
            if len(pdf_sample) < size - 65536:
                buf[65536 : 65536 + len(pdf_sample)] = pdf_sample

        # Inject sample ZIP / DOCX
        if current_offset >= 2 * 1024 * 1024:
            try:
                from core.payload_generator import generate_valid_docx
                zip_sample = generate_valid_docx(
                    file_id="CARVE-0003",
                    details="Recovered Operational Debrief & System Architecture"
                )
            except Exception:
                zip_sample = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"[Content_Types].xml" + (b"\xAA\xBB\xCC" * 100) + b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            if len(zip_sample) < size - 32768:
                buf[32768 : 32768 + len(zip_sample)] = zip_sample

        return bytes(buf)


class RawHandleStream:
    """Helper wrapper for Win32 device handle reading with sector alignment."""

    def __init__(self, handle, sector_size: int = 512):
        self.handle = handle
        self.sector_size = sector_size

    def read(self, size: int) -> bytes:
        import ctypes
        if size <= 0:
            return b""
        aligned_size = ((size + self.sector_size - 1) // self.sector_size) * self.sector_size
        buf = ctypes.create_string_buffer(aligned_size)
        bytes_read = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.ReadFile(
            ctypes.c_void_p(self.handle), buf, aligned_size, ctypes.byref(bytes_read), None
        )
        if not ok or bytes_read.value == 0:
            return b""
        return buf.raw[:min(size, bytes_read.value)]

    def close(self):
        import ctypes
        try:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(self.handle))
        except Exception:
            pass
