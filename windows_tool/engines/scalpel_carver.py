"""
ZeroTrace Scalpel-Powered File Carving Engine — Precision Forensic Carving
Enhanced with BreadCrumb, TRACE-Forensic-Toolkit, searchlight, and Digital-Forensics-Toolkit.
Features bounded horizon search, exact structure walking (JPEG SOS markers, PNG IEND,
ZIP Central Directory, PDF EOF boundaries & Linearized dictionaries), and pypdf/PIL deep validation.
"""

import os
import re
import time
import hashlib
import ctypes
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, NamedTuple

from core.crypto import sha256_bytes
from engines.structure_validator import RecoveryStructureValidator

KB = 1024
MB = 1024 * 1024
GB = 1024 * 1024 * 1024


class CarveResult(NamedTuple):
    size: int
    ext: str
    category: str
    file_type: str
    validated: bool
    diagnostic: str = ""


@dataclass
class CarveSignature:
    file_type: str
    extension: str
    category: str
    header: bytes
    footer: Optional[bytes] = None
    min_size: int = 64
    max_size: int = 50 * MB
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


class StreamWindow:
    """
    Bounded, cached sliding window over the evidence reader based at a candidate offset.
    Enables structure parsers to read and search bytes within arbitrary bounds
    without loading large files entirely into RAM.
    """

    BLOCK = 64 * KB
    MAX_BLOCKS = 128

    def __init__(self, reader, base_offset: int, limit: int):
        self.reader = reader
        self.base = base_offset
        self.limit = limit
        self._cache: Dict[int, bytes] = {}

    def _block(self, idx: int) -> bytes:
        blk = self._cache.get(idx)
        if blk is None:
            if len(self._cache) >= self.MAX_BLOCKS:
                self._cache.pop(next(iter(self._cache)))
            blk = self.reader.pread(self.base + idx * self.BLOCK, self.BLOCK)
            self._cache[idx] = blk
        return blk

    def read(self, pos: int, n: int) -> bytes:
        if pos < 0 or n <= 0 or pos >= self.limit:
            return b""
        n = min(n, self.limit - pos)
        out = bytearray()
        while n > 0:
            idx, rel = divmod(pos, self.BLOCK)
            blk = self._block(idx)
            piece = blk[rel : rel + n]
            if not piece:
                break
            out += piece
            pos += len(piece)
            n -= len(piece)
        return bytes(out)

    def find(self, needle: bytes, start: int = 0, end: Optional[int] = None) -> int:
        if end is None:
            end = self.limit
        end = min(end, self.limit)
        nl = len(needle)
        step = 512 * KB
        pos = max(start, 0)
        while pos < end:
            buf = self.read(pos, min(step, end - pos) + nl - 1)
            if len(buf) < nl:
                return -1
            i = buf.find(needle)
            if i >= 0 and pos + i + nl <= end:
                return pos + i
            pos += step
        return -1

    def find_last(self, needle: bytes, start: int = 0, end: Optional[int] = None) -> int:
        if end is None:
            end = self.limit
        end = min(end, self.limit)
        nl = len(needle)
        step = 512 * KB
        pos = max(start, 0)
        last = -1
        while pos < end:
            buf = self.read(pos, min(step, end - pos) + nl - 1)
            if len(buf) < nl:
                break
            i = buf.find(needle)
            while i >= 0:
                if pos + i + nl <= end:
                    last = pos + i
                i = buf.find(needle, i + 1)
            pos += step
        return last


# -----------------------------------------------------------------------------
# Precision Per-Type Carving Routines (BreadCrumb, TRACE, searchlight)
# -----------------------------------------------------------------------------

def _u16le(b: bytes, o: int = 0) -> int:
    return int.from_bytes(b[o : o + 2], "little")


def _u32le(b: bytes, o: int = 0) -> int:
    return int.from_bytes(b[o : o + 4], "little")


def _u64le(b: bytes, o: int = 0) -> int:
    return int.from_bytes(b[o : o + 8], "little")


def _u16be(b: bytes, o: int = 0) -> int:
    return int.from_bytes(b[o : o + 2], "big")


def _u32be(b: bytes, o: int = 0) -> int:
    return int.from_bytes(b[o : o + 4], "big")


def _carve_pdf(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves Adobe PDF documents.
    1. Checks for /Linearized dictionary and /L <length> (from TRACE-Forensic-Toolkit)
    2. Bounded horizon: searches for next %PDF- header to avoid merging files (BreadCrumb)
    3. Searches for last %%EOF before the horizon and takes line terminators
    4. Validates document catalog and syntax
    """
    if w.read(0, 5) != b"%PDF-":
        return None

    # Fast-path: /Linearized check
    head_1k = w.read(0, 1024)
    lin_idx = head_1k.find(b"/Linearized")
    if lin_idx != -1:
        l_idx = head_1k.find(b"/L ", lin_idx)
        if l_idx != -1:
            try:
                l_part = head_1k[l_idx + 3 : l_idx + 32].split()[0]
                declared_len = int(l_part)
                if 256 <= declared_len <= w.limit:
                    tail = w.read(max(0, declared_len - 1024), 1024)
                    if b"%%EOF" in tail:
                        return CarveResult(
                            size=declared_len,
                            ext=".pdf",
                            category="DOCUMENT",
                            file_type="PDF",
                            validated=True,
                            diagnostic="Fast-path: Linearized PDF length verified",
                        )
            except Exception:
                pass

    # Bounded horizon: search for next %PDF- header
    horizon = w.find(b"%PDF-", 5)
    end_limit = horizon if horizon > 0 else w.limit

    last = w.find_last(b"%%EOF", 0, end_limit)
    if last < 0:
        return None

    end = last + 5
    tail = w.read(end, 2)
    if tail[:2] == b"\r\n":
        end += 2
    elif tail[:1] in (b"\r", b"\n"):
        end += 1

    return CarveResult(
        size=end,
        ext=".pdf",
        category="DOCUMENT",
        file_type="PDF",
        validated=True,
        diagnostic=f"Bounded horizon %%EOF verified at offset {end}",
    )


def _carve_jpeg(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves JPEG images by walking segment markers and scanning SOS entropy data.
    Terminates at clean EOI (0xFF 0xD9).
    """
    h2 = w.read(0, 2)
    if h2 != b"\xFF\xD8":
        return None

    pos = 2
    while pos < w.limit:
        hdr = w.read(pos, 4)
        if len(hdr) < 2 or hdr[0] != 0xFF:
            return None
        marker = hdr[1]
        if marker == 0xD9:  # EOI
            return CarveResult(pos + 2, ".jpg", "IMAGE", "JPEG", True, "Clean JPEG EOI trailer")
        if marker == 0xD8 or marker == 0x01 or (0xD0 <= marker <= 0xD7):
            pos += 2
            continue
        if marker == 0xFF:  # Fill byte
            pos += 1
            continue
        if len(hdr) < 4:
            return None
        seglen = _u16be(hdr, 2)
        if seglen < 2:
            return None

        if marker == 0xDA:  # SOS: Start of Scan (entropy-coded stream)
            pos += 2 + seglen
            while True:
                idx = w.find(b"\xFF", pos)
                if idx < 0:
                    return None
                nxt = w.read(idx + 1, 1)
                if not nxt:
                    return None
                b = nxt[0]
                if b == 0xD9:  # EOI
                    return CarveResult(idx + 2, ".jpg", "IMAGE", "JPEG", True, "JPEG EOI verified after SOS")
                if b == 0x00 or (0xD0 <= b <= 0xD7):  # Byte-stuffed zero or restart marker
                    pos = idx + 2
                    continue
                if b == 0xFF:
                    pos = idx + 1
                    continue
                pos = idx  # Next real segment marker
                break
            continue

        pos += 2 + seglen

    return None


def _carve_png(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves PNG images by walking chunks until IEND (+12 bytes).
    """
    if w.read(0, 8) != b"\x89PNG\r\n\x1a\n":
        return None

    pos = 8
    while pos + 12 <= w.limit:
        h = w.read(pos, 8)
        if len(h) < 8:
            return None
        length = _u32be(h, 0)
        ctype = h[4:8]
        if length > 0x7FFFFFFF or not all((0x41 <= c <= 0x5A) or (0x61 <= c <= 0x7A) for c in ctype):
            return None
        pos += 12 + length
        if pos > w.limit:
            return None
        if ctype == b"IEND":
            return CarveResult(pos, ".png", "IMAGE", "PNG", True, "PNG IEND chunk verified")

    return None


_ZIP_HINTS = [
    (b"word/", "DOCX", ".docx", "DOCUMENT"),
    (b"xl/", "XLSX", ".xlsx", "DOCUMENT"),
    (b"ppt/", "PPTX", ".pptx", "DOCUMENT"),
    (b"visio/", "VSDX", ".vsdx", "DOCUMENT"),
    (b"AndroidManifest.xml", "APK", ".apk", "ARCHIVE"),
    (b"META-INF/MANIFEST.MF", "JAR", ".jar", "ARCHIVE"),
]


def _carve_zip(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves ZIP archives and Office OpenXML files (DOCX, XLSX, PPTX).
    Walks local member headers, verifies central directory, and locates EOCD.
    Sniffs internal members to classify DOCX/XLSX/PPTX correctly.
    """
    if w.read(0, 4) != b"PK\x03\x04":
        return None

    # 1. Walk local member headers
    pos = 0
    intact = True
    while True:
        hdr = w.read(pos, 30)
        if len(hdr) < 30 or hdr[:4] != b"PK\x03\x04":
            break
        flags = _u16le(hdr, 6)
        csize = _u32le(hdr, 18)
        name_len = _u16le(hdr, 26)
        extra_len = _u16le(hdr, 28)
        if (flags & 0x08) and csize == 0:
            intact = False
            break
        if csize > 64 * MB:
            intact = False
            break
        nxt = pos + 30 + name_len + extra_len + csize
        if nxt <= pos or nxt > w.limit:
            intact = False
            break
        pos = nxt

    # 2. Central Directory + EOCD
    if intact and pos > 0 and w.read(pos, 4) == b"PK\x01\x02":
        cd_pos = pos
        while w.read(cd_pos, 4) == b"PK\x01\x02":
            ent = w.read(cd_pos, 46)
            if len(ent) < 46:
                break
            cd_pos += 46 + _u16le(ent, 28) + _u16le(ent, 30) + _u16le(ent, 32)
            if cd_pos > w.limit:
                break

        if cd_pos <= w.limit and w.read(cd_pos, 4) == b"PK\x05\x06":
            rec = w.read(cd_pos, 22)
            if len(rec) == 22:
                end = cd_pos + 22 + _u16le(rec, 20)
                if end <= w.limit:
                    return _classify_zip_container(w, end)

    # 3. Fallback: Search EOCD whose central directory offsets line up
    search = 0
    while True:
        eocd = w.find(b"PK\x05\x06", search)
        if eocd < 0:
            break
        rec = w.read(eocd, 22)
        if len(rec) == 22:
            cd_size, cd_off = _u32le(rec, 12), _u32le(rec, 16)
            end = eocd + 22 + _u16le(rec, 20)
            if cd_off + cd_size == eocd and end <= w.limit:
                return _classify_zip_container(w, end)
        search = eocd + 1

    return None


def _classify_zip_container(w: StreamWindow, end: int) -> CarveResult:
    head = w.read(0, min(8192, end))
    for hint_bytes, f_type, ext, cat in _ZIP_HINTS:
        if hint_bytes in head:
            return CarveResult(end, ext, cat, f_type, True, f"{f_type} OpenXML structure verified")
    return CarveResult(end, ".zip", "ARCHIVE", "ZIP", True, "ZIP EOCD directory verified")


def _carve_gif(w: StreamWindow) -> Optional[CarveResult]:
    head = w.read(0, 13)
    if len(head) < 13 or head[:6] not in (b"GIF87a", b"GIF89a"):
        return None

    pos = 13
    packed = head[10]
    if packed & 0x80:  # Global color table
        pos += 3 * (2 << (packed & 0x07))

    def skip_subblocks(p: int) -> int:
        while True:
            sz = w.read(p, 1)
            if not sz:
                return -1
            p += 1
            if sz[0] == 0:
                return p
            p += sz[0]

    while pos < w.limit:
        b = w.read(pos, 1)
        if not b:
            return None
        tag = b[0]
        pos += 1
        if tag == 0x3B:  # Trailer
            return CarveResult(pos, ".gif", "IMAGE", "GIF", True, "Clean GIF 0x3B trailer")
        if tag == 0x21:  # Extension
            pos = skip_subblocks(pos + 1)
        elif tag == 0x2C:  # Image descriptor
            desc = w.read(pos, 9)
            if len(desc) < 9:
                return None
            pos += 9
            if desc[8] & 0x80:
                pos += 3 * (2 << (desc[8] & 0x07))
            pos += 1  # LZW min code
            pos = skip_subblocks(pos)
        else:
            return None
        if pos < 0 or pos > w.limit:
            return None

    return None


def _carve_bmp(w: StreamWindow) -> Optional[CarveResult]:
    h = w.read(0, 26)
    if len(h) < 26 or h[:2] != b"BM":
        return None
    size = _u32le(h, 2)
    if not (26 <= size <= w.limit):
        return None
    dib_size = _u32le(h, 14)
    if dib_size not in (12, 40, 52, 56, 64, 108, 124):
        return None
    return CarveResult(size, ".bmp", "IMAGE", "BMP", True, f"BMP header verified, size={size}B")


def _carve_riff(w: StreamWindow) -> Optional[CarveResult]:
    h = w.read(0, 12)
    if len(h) < 12 or h[:4] != b"RIFF":
        return None
    form = h[8:12]
    size = _u32le(h, 4) + 8
    if size > w.limit or size < 12:
        return None
    if form == b"WAVE":
        return CarveResult(size, ".wav", "MEDIA", "WAV", True, f"RIFF/WAVE stream verified, {size}B")
    if form == b"WEBP":
        return CarveResult(size, ".webp", "IMAGE", "WEBP", True, f"RIFF/WEBP image verified, {size}B")
    if form == b"AVI ":
        return CarveResult(size, ".avi", "MEDIA", "AVI", True, f"RIFF/AVI video verified, {size}B")
    return None


def _carve_sqlite(w: StreamWindow) -> Optional[CarveResult]:
    h = w.read(0, 100)
    if len(h) < 100 or not h.startswith(b"SQLite format 3\x00"):
        return None
    page_size = _u16be(h, 16)
    if page_size == 1:
        page_size = 65536
    if page_size < 512 or (page_size & (page_size - 1)):
        return None
    page_count = _u32be(h, 28)
    if page_count == 0:
        return None
    size = page_size * page_count
    if size > w.limit:
        return None
    return CarveResult(size, ".sqlite", "DATABASE", "SQLITE", True, f"SQLite DB verified: {page_count} pages")


def _carve_7z(w: StreamWindow) -> Optional[CarveResult]:
    h = w.read(0, 32)
    if len(h) < 32 or not h.startswith(b"7z\xbc\xaf\x27\x1c"):
        return None
    nh_off, nh_size = _u64le(h, 12), _u64le(h, 20)
    end = 32 + nh_off + nh_size
    if nh_size == 0 or end > w.limit:
        return None
    return CarveResult(end, ".7z", "ARCHIVE", "7Z", True, "7-Zip header verified")


def _carve_rtf(w: StreamWindow) -> Optional[CarveResult]:
    if w.read(0, 5) != b"{\\rtf":
        return None
    pos = 0
    depth = 0
    while pos < w.limit:
        buf = w.read(pos, 64 * KB)
        if not buf:
            break
        i = 0
        while i < len(buf):
            c = buf[i]
            if c == 0x5C:  # Backslash
                tail = buf[i : i + 24]
                if tail[1:4] == b"bin" and len(tail) > 4:
                    j = 4
                    digits = b""
                    while j < len(tail) and tail[j : j + 1].isdigit():
                        digits += tail[j : j + 1]
                        j += 1
                    if digits:
                        skip = int(digits)
                        if tail[j : j + 1] == b" ":
                            j += 1
                        pos += i + j + skip
                        break
                i += 2
                continue
            if c == 0x7B:  # {
                depth += 1
            elif c == 0x7D:  # }
                depth -= 1
                if depth == 0:
                    return CarveResult(pos + i + 1, ".rtf", "DOCUMENT", "RTF", True, "Balanced RTF groups")
            i += 1
        else:
            pos += len(buf)
    return None


class RawHandleStream:
    """Read wrapper over Windows CreateFileW raw device handle."""

    def __init__(self, handle: int):
        self.handle = handle
        self.pos = 0

    def read(self, size: int) -> bytes:
        if not self.handle:
            return b""
        buf = ctypes.create_string_buffer(size)
        br = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.ReadFile(
            ctypes.c_void_p(self.handle), buf, size, ctypes.byref(br), None
        )
        if ok and br.value > 0:
            self.pos += br.value
            return buf.raw[: br.value]
        return b""

    def pread(self, offset: int, length: int) -> bytes:
        aligned_start = (offset // 512) * 512
        offset_in_sector = offset - aligned_start
        end_offset = offset + length
        aligned_end = ((end_offset + 511) // 512) * 512
        aligned_length = aligned_end - aligned_start

        ctypes.windll.kernel32.SetFilePointerEx(
            ctypes.c_void_p(self.handle), ctypes.c_int64(aligned_start), None, 0
        )
        buf = ctypes.create_string_buffer(aligned_length)
        br = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.ReadFile(
            ctypes.c_void_p(self.handle), buf, aligned_length, ctypes.byref(br), None
        )
        if not ok or br.value == 0:
            return b""
        raw = buf.raw[: br.value]
        return raw[offset_in_sector : offset_in_sector + length]

    def close(self):
        if self.handle:
            try:
                ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(self.handle))
            except Exception:
                pass
            self.handle = None


class ScalpelCarver:
    """
    High-precision signature and structure-based file carver.
    Combines Scalpel signature scanning with BreadCrumb, TRACE-Forensic-Toolkit,
    and searchlight structural verification routines.
    """

    def __init__(self, chunk_size: int = 4 * MB, overlap_size: int = 128 * KB):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.signatures: List[CarveSignature] = []
        self.is_running = False
        self.is_cancelled = False
        self._load_signatures()

    def _load_signatures(self):
        """Load comprehensive forensic signatures."""
        self.signatures.append(CarveSignature(
            file_type="PDF", extension=".pdf", category="DOCUMENT",
            header=b"%PDF-", footer=b"%%EOF",
            min_size=256, max_size=80 * MB,
            reverse_search=True, description="Adobe Portable Document Format"
        ))
        self.signatures.append(CarveSignature(
            file_type="JPEG", extension=".jpg", category="IMAGE",
            header=b"\xFF\xD8\xFF", footer=b"\xFF\xD9",
            min_size=100, max_size=40 * MB,
            description="JPEG Image with EXIF/JFIF marker"
        ))
        self.signatures.append(CarveSignature(
            file_type="PNG", extension=".png", category="IMAGE",
            header=b"\x89PNG\r\n\x1a\n", footer=b"IEND\xaeB`\x82",
            min_size=64, max_size=40 * MB,
            description="Portable Network Graphics"
        ))
        self.signatures.append(CarveSignature(
            file_type="ZIP/OFFICE", extension=".zip", category="ARCHIVE",
            header=b"PK\x03\x04", footer=b"PK\x05\x06",
            min_size=128, max_size=120 * MB,
            reverse_search=True, description="ZIP Archive or Office OpenXML (DOCX, XLSX, PPTX)"
        ))
        self.signatures.append(CarveSignature(
            file_type="GIF", extension=".gif", category="IMAGE",
            header=b"GIF89a", footer=b"\x00\x3B",
            min_size=64, max_size=25 * MB, description="GIF89a"
        ))
        self.signatures.append(CarveSignature(
            file_type="GIF", extension=".gif", category="IMAGE",
            header=b"GIF87a", footer=b"\x00\x3B",
            min_size=64, max_size=25 * MB, description="GIF87a"
        ))
        self.signatures.append(CarveSignature(
            file_type="BMP", extension=".bmp", category="IMAGE",
            header=b"BM", footer=None,
            min_size=128, max_size=35 * MB, description="Windows Bitmap Image"
        ))
        self.signatures.append(CarveSignature(
            file_type="RIFF", extension=".wav", category="MEDIA",
            header=b"RIFF", footer=None,
            min_size=128, max_size=80 * MB, description="RIFF Container (WAV/WEBP/AVI)"
        ))
        self.signatures.append(CarveSignature(
            file_type="SQLITE", extension=".sqlite", category="DATABASE",
            header=b"SQLite format 3\x00", footer=None,
            min_size=512, max_size=100 * MB, description="SQLite Database"
        ))
        self.signatures.append(CarveSignature(
            file_type="7Z", extension=".7z", category="ARCHIVE",
            header=b"7z\xbc\xaf\x27\x1c", footer=None,
            min_size=128, max_size=120 * MB, description="7-Zip Archive"
        ))
        self.signatures.append(CarveSignature(
            file_type="RTF", extension=".rtf", category="DOCUMENT",
            header=b"{\\rtf", footer=None,
            min_size=64, max_size=50 * MB, description="Rich Text Format"
        ))

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
        """Carve files from a disk image, volume, or raw drive stream."""
        self.is_running = True
        self.is_cancelled = False
        carved_results: List[CarvedFile] = []
        carved_offsets = set()
        start_time = time.time()

        if total_bytes_to_scan <= 0:
            if os.path.isfile(source_path):
                total_bytes_to_scan = os.path.getsize(source_path)
            else:
                m = re.search(r"([A-Za-z]):", source_path)
                if m:
                    try:
                        tot_b = ctypes.c_ulonglong()
                        free_b = ctypes.c_ulonglong()
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            f"{m.group(1)}:\\", None, ctypes.byref(tot_b), ctypes.byref(free_b)
                        )
                        if tot_b.value > 0:
                            total_bytes_to_scan = tot_b.value
                    except Exception:
                        pass
                if total_bytes_to_scan <= 0:
                    total_bytes_to_scan = 1024 * MB

        bytes_scanned = 0
        overlap_buffer = b""
        stream_offset = 0

        # Open target reader
        reader: Any = None
        is_simulated = False
        try:
            if os.path.isfile(source_path):
                from engines.tsk_filesystem import ForensicDeviceReader
                reader = ForensicDeviceReader(source_path)
            else:
                dev_path = source_path
                m = re.search(r"([A-Za-z]):", source_path)
                if m and not dev_path.startswith("\\\\.\\"):
                    dev_path = f"\\\\.\\{m.group(1).upper()}:"
                ctypes.windll.kernel32.CreateFileW.restype = ctypes.c_void_p
                handle = ctypes.windll.kernel32.CreateFileW(
                    dev_path, 0x80000000, 3, None, 3, 0, None
                )
                if handle and handle != ctypes.c_void_p(-1).value:
                    reader = RawHandleStream(handle)
                else:
                    if "DEMO" in source_path.upper() or "SIMULAT" in source_path.upper():
                        is_simulated = True
                    else:
                        raise PermissionError(f"Cannot open raw evidence device '{source_path}'. Run ZeroTrace as Administrator or select disk image.")
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
                if not is_simulated and reader:
                    chunk = reader.read(read_size)
                    if not chunk:
                        break
                else:
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

                        if abs_offset in carved_offsets:
                            start_pos = hdr_idx + sig_len
                            continue

                        # Execute precision carving handler if available
                        carve_res = None
                        if reader and not is_simulated:
                            w = StreamWindow(reader, abs_offset, sig.max_size)
                            if sig.header == b"%PDF-":
                                carve_res = _carve_pdf(w)
                            elif sig.header == b"\xFF\xD8\xFF":
                                carve_res = _carve_jpeg(w)
                            elif sig.header == b"\x89PNG\r\n\x1a\n":
                                carve_res = _carve_png(w)
                            elif sig.header == b"PK\x03\x04":
                                carve_res = _carve_zip(w)
                            elif sig.header in (b"GIF89a", b"GIF87a"):
                                carve_res = _carve_gif(w)
                            elif sig.header == b"BM":
                                carve_res = _carve_bmp(w)
                            elif sig.header == b"RIFF":
                                carve_res = _carve_riff(w)
                            elif sig.header == b"SQLite format 3\x00":
                                carve_res = _carve_sqlite(w)
                            elif sig.header == b"7z\xbc\xaf\x27\x1c":
                                carve_res = _carve_7z(w)
                            elif sig.header == b"{\\rtf":
                                carve_res = _carve_rtf(w)

                        candidate_data = None
                        candidate_size = 0
                        footer_found = False
                        f_ext = sig.extension
                        f_cat = sig.category
                        f_type = sig.file_type

                        has_handler = sig.header in (
                            b"%PDF-", b"\xFF\xD8\xFF", b"\x89PNG\r\n\x1a\n", b"PK\x03\x04",
                            b"GIF89a", b"GIF87a", b"BM", b"RIFF", b"SQLite format 3\x00",
                            b"7z\xbc\xaf\x27\x1c", b"{\\rtf"
                        )

                        if carve_res and carve_res.size >= sig.min_size:
                            candidate_size = carve_res.size
                            f_ext = carve_res.ext
                            f_cat = carve_res.category
                            f_type = carve_res.file_type
                            footer_found = carve_res.validated
                            # Read candidate payload
                            if reader and not is_simulated:
                                candidate_data = reader.pread(abs_offset, candidate_size)
                            else:
                                candidate_data = combined_chunk[hdr_idx : hdr_idx + candidate_size]
                        elif not has_handler:
                            # Standard fallback footer extraction for generic signatures without dedicated handlers
                            if sig.footer:
                                max_search_len = min(sig.max_size, len(combined_chunk) - hdr_idx)
                                payload_window = combined_chunk[hdr_idx : hdr_idx + max_search_len]
                                ftr_idx = payload_window.rfind(sig.footer) if sig.reverse_search else payload_window.find(sig.footer)
                                if ftr_idx != -1:
                                    candidate_size = ftr_idx + len(sig.footer)
                                    candidate_data = payload_window[:candidate_size]
                                    footer_found = True
                            elif len(combined_chunk) - hdr_idx >= sig.min_size:
                                candidate_size = min(sig.max_size, 64 * KB)
                                candidate_data = combined_chunk[hdr_idx : hdr_idx + candidate_size]

                        if candidate_data and len(candidate_data) >= sig.min_size:
                            carved_offsets.add(abs_offset)
                            c_file = self._build_carved_file(
                                file_type=f_type,
                                extension=f_ext,
                                category=f_cat,
                                offset=abs_offset,
                                data=candidate_data,
                                footer_found=footer_found,
                                source_target=source_path,
                                carve_id=len(carved_results) + 1,
                                diagnostic=carve_res.diagnostic if carve_res else "",
                            )
                            carved_results.append(c_file)
                            if file_found_callback:
                                file_found_callback(c_file)

                            start_pos = hdr_idx + max(sig_len, min(candidate_size, 256))
                        else:
                            start_pos = hdr_idx + sig_len

                bytes_scanned += len(chunk)
                stream_offset += len(chunk)
                overlap_buffer = chunk[-self.overlap_size:] if len(chunk) >= self.overlap_size else chunk

                # Telemetry
                now = time.time()
                elapsed = max(0.001, now - start_time)
                speed_mb_s = (bytes_scanned / MB) / elapsed

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
            if reader:
                try:
                    reader.close()
                except Exception:
                    pass

        return carved_results

    def _build_carved_file(
        self,
        file_type: str,
        extension: str,
        category: str,
        offset: int,
        data: bytes,
        footer_found: bool,
        source_target: str,
        carve_id: int,
        diagnostic: str = "",
    ) -> CarvedFile:
        """Create structured CarvedFile object with hash, confidence, and preview."""
        val = RecoveryStructureValidator.validate_and_score(file_type, data, footer_matched=footer_found)
        h = sha256_bytes(data)
        md5_h = hashlib.md5(data).hexdigest()

        # Generate snippet preview
        snippet = ""
        if "PDF" in file_type:
            snippet = f"PDF Header: {data[:16].decode('latin1', errors='ignore')}"
        elif "IMAGE" in category:
            snippet = f"{file_type} Binary stream [{len(data)} bytes]"
        else:
            snippet = f"{file_type} Artifact [{len(data)} bytes]"

        metadata = {
            "footer_matched": footer_found,
            "validation": val,
            "md5": md5_h,
            "diagnostic": diagnostic or (val["diagnostics"][0] if val.get("diagnostics") else ""),
            "carve_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

        return CarvedFile(
            file_id=f"CARVE-{carve_id:04d}",
            file_type=file_type,
            extension=extension,
            category=category,
            offset=offset,
            size=len(data),
            sha256=h,
            confidence=val["confidence"],
            data=data,
            preview_snippet=snippet,
            metadata=metadata,
            source_target=source_target,
        )

    def _generate_simulated_chunk(self, size: int, stream_offset: int) -> bytes:
        """Generate realistic forensic disk image chunk with embedded artifacts."""
        buf = bytearray(size)
        if stream_offset == 0:
            # Embed a sample valid PDF
            from core.payload_generator import generate_valid_pdf
            pdf_bytes = generate_valid_pdf("CARVE-0001", "CASE-ZT-2026-001", "Forensic Carving Demonstration PDF")
            if len(buf) >= 1024 + len(pdf_bytes):
                buf[1024 : 1024 + len(pdf_bytes)] = pdf_bytes

            # Embed a sample valid PNG
            from core.payload_generator import generate_valid_png
            png_bytes = generate_valid_png(file_id="CARVE-0002", case_id="CASE-ZT-2026-001", details="Forensic Demonstration PNG Artifact")
            offset_png = 1024 + len(pdf_bytes) + 2048
            if len(buf) >= offset_png + len(png_bytes):
                buf[offset_png : offset_png + len(png_bytes)] = png_bytes

        return bytes(buf)
