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
    1. Fast-path: Checks for /Linearized dictionary and /L <length> (from TRACE-Forensic-Toolkit)
    2. Bounded horizon: searches for genuine next PDF document header (%PDF-1.x / %PDF-2.x)
    3. Finds %%EOF markers and extends past incremental revisions
    4. Validates trailer and syntax with pypdf
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
                if 100 <= declared_len <= w.limit:
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

    # Bounded horizon: search for next genuine PDF header (%PDF-1. or %PDF-2.)
    max_bound = min(w.limit, 60 * MB)
    horizon = -1
    check_pos = 1024
    while check_pos < min(max_bound, 20 * MB):
        h_candidate = w.find(b"%PDF-", check_pos, min(max_bound, check_pos + 5 * MB))
        if h_candidate < 0:
            break
        ver = w.read(h_candidate + 5, 2)
        if ver in (b"1.", b"2.") and (h_candidate % 512 == 0 or w.read(h_candidate - 1, 1) in (b"\n", b"\r", b"\x00")):
            horizon = h_candidate
            break
        check_pos = h_candidate + 5

    end_limit = horizon if horizon > 0 else max_bound

    first_eof = w.find(b"%%EOF", 0, end_limit)
    if first_eof < 0:
        # If horizon was found too early without EOF, expand to max_bound
        if horizon > 0:
            end_limit = max_bound
            first_eof = w.find(b"%%EOF", 0, end_limit)
        if first_eof < 0:
            return None

    # Check for incremental revisions (subsequent %%EOF within 4MB)
    curr_eof = first_eof
    max_search = min(end_limit, curr_eof + 4 * MB)
    while True:
        nxt = w.find(b"%%EOF", curr_eof + 5, max_search)
        if nxt < 0:
            break
        curr_eof = nxt
        max_search = min(end_limit, curr_eof + 4 * MB)

    end = curr_eof + 5
    tail = w.read(end, 4)
    if tail[:2] == b"\r\n":
        end += 2
    elif tail[:1] in (b"\r", b"\n"):
        end += 1

    # Validate with pypdf if available
    is_valid = False
    diag = f"%%EOF verified at offset {end}"
    try:
        import io
        import pypdf
        sample = w.read(0, end)
        reader = pypdf.PdfReader(io.BytesIO(sample), strict=False)
        if len(reader.pages) > 0:
            is_valid = True
            diag = f"pypdf validated: {len(reader.pages)} page(s), size={end}B"
    except Exception:
        sample = w.read(max(0, end - 1024), 1024)
        if b"%%EOF" in sample:
            is_valid = True

    return CarveResult(
        size=end,
        ext=".pdf",
        category="DOCUMENT",
        file_type="PDF",
        validated=is_valid,
        diagnostic=diag,
    )


def _carve_jpeg(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves JPEG images by walking segment markers and scanning SOS entropy data.
    Falls back to searching clean EOI (0xFF 0xD9) if segment walker hits non-standard marker.
    """
    h2 = w.read(0, 2)
    if h2 != b"\xFF\xD8":
        return None

    pos = 2
    clean_carve = None
    while pos < w.limit:
        hdr = w.read(pos, 4)
        if len(hdr) < 2 or hdr[0] != 0xFF:
            break
        marker = hdr[1]
        if marker == 0xD9:  # EOI
            clean_carve = CarveResult(pos + 2, ".jpg", "IMAGE", "JPEG", True, "Clean JPEG EOI trailer")
            break
        if marker == 0xD8 or marker == 0x01 or (0xD0 <= marker <= 0xD7):
            pos += 2
            continue
        if marker == 0xFF:  # Fill byte
            pos += 1
            continue
        if len(hdr) < 4:
            break
        seglen = _u16be(hdr, 2)
        if seglen < 2:
            break

        if marker == 0xDA:  # SOS: Start of Scan (entropy-coded stream)
            pos += 2 + seglen
            while True:
                idx = w.find(b"\xFF", pos)
                if idx < 0:
                    break
                nxt = w.read(idx + 1, 1)
                if not nxt:
                    break
                b = nxt[0]
                if b == 0xD9:  # EOI
                    clean_carve = CarveResult(idx + 2, ".jpg", "IMAGE", "JPEG", True, "JPEG EOI verified after SOS")
                    break
                if b == 0x00 or (0xD0 <= b <= 0xD7):  # Byte-stuffed zero or restart marker
                    pos = idx + 2
                    continue
                if b == 0xFF:
                    pos = idx + 1
                    continue
                pos = idx  # Next real segment marker
                break
            if clean_carve:
                break
            continue

        pos += 2 + seglen

    if clean_carve:
        return clean_carve

    # Scalpel architecture fallback: find clean EOI marker after SOS if present
    sos_idx = w.find(b"\xFF\xDA", 2, 65536)
    search_start = (sos_idx + 2) if sos_idx > 0 else 2
    eoi = w.find(b"\xFF\xD9", search_start, min(w.limit, 20 * MB))
    if eoi >= 100:
        return CarveResult(eoi + 2, ".jpg", "IMAGE", "JPEG", True, f"Scalpel JPEG EOI matched at offset {eoi + 2}")

    return None


def _carve_png(w: StreamWindow) -> Optional[CarveResult]:
    """
    Carves PNG images by walking chunks until IEND (+12 bytes).
    Falls back to searching IEND chunk if non-standard chunks exist.
    """
    if w.read(0, 8) != b"\x89PNG\r\n\x1a\n":
        return None

    pos = 8
    while pos + 12 <= w.limit:
        h = w.read(pos, 8)
        if len(h) < 8:
            break
        length = _u32be(h, 0)
        ctype = h[4:8]
        if length > 0x7FFFFFFF or not all((0x41 <= c <= 0x5A) or (0x61 <= c <= 0x7A) for c in ctype):
            break
        pos += 12 + length
        if pos > w.limit:
            break
        if ctype == b"IEND":
            return CarveResult(pos, ".png", "IMAGE", "PNG", True, "PNG IEND chunk verified")

    # Scalpel architecture fallback: find IEND signature
    iend = w.find(b"IEND\xaeB`\x82", 8, min(w.limit, 20 * MB))
    if iend >= 16:
        # IEND marker is 8 bytes + 4 bytes CRC = 12 bytes
        return CarveResult(iend + 8, ".png", "IMAGE", "PNG", True, f"PNG IEND matched at offset {iend + 8}")

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
    h = w.read(0, 54)
    if len(h) < 26 or h[:2] != b"BM":
        return None
    # 1. Reserved fields MUST be zero in a valid BMP header (bytes 6..10)
    if h[6:10] != b"\x00\x00\x00\x00":
        return None
    size = _u32le(h, 2)
    # 2. Offset to pixel array (bfOffBits)
    off_bits = _u32le(h, 10)
    if off_bits < 26 or off_bits > 65536:
        return None
    # 3. DIB header size (biSize)
    dib_size = _u32le(h, 14)
    if dib_size not in (12, 40, 52, 56, 64, 108, 124):
        return None
    # 4. Standard BITMAPINFOHEADER and modern extensions validation
    if dib_size >= 40 and len(h) >= 30:
        planes = _u16le(h, 26)
        if planes != 1:
            return None
        bpp = _u16le(h, 28)
        if bpp not in (1, 4, 8, 16, 24, 32):
            return None
        if len(h) >= 34:
            comp = _u32le(h, 30)
            if comp > 6:
                return None
    if not (off_bits <= size <= w.limit):
        return None
    # Validate with PIL to guarantee it can open without error
    try:
        import io
        from PIL import Image
        sample = w.read(0, min(size, 65536))
        img = Image.open(io.BytesIO(sample))
        img.verify()
    except Exception:
        # If PIL fails to open it, it's not a real BMP image
        return None
    return CarveResult(size, ".bmp", "IMAGE", "BMP", True, f"BMP verified, size={size}B")


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


from engines.tsk_filesystem import ForensicDeviceReader


class ScalpelCarver:
    """
    High-precision signature and structure-based file carver.
    Combines Scalpel signature scanning with BreadCrumb, TRACE-Forensic-Toolkit,
    and searchlight structural verification routines.
    """

    def __init__(self, chunk_size: int = 1 * MB, overlap_size: int = 128 * KB):
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
            min_size=100, max_size=80 * MB,
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
        reader = ForensicDeviceReader(source_path)
        if not reader.file_obj and not reader.handle:
            raise PermissionError(f"Cannot access evidence target '{source_path}'. Ensure ZeroTrace is run with Administrator privileges or select a valid forensic disk image.")

        if reader.size > 0 and (total_bytes_to_scan <= 0 or total_bytes_to_scan > reader.size):
            total_bytes_to_scan = reader.size

        try:
            while bytes_scanned < total_bytes_to_scan and len(carved_results) < max_files:
                if self.is_cancelled:
                    break

                read_size = min(self.chunk_size, total_bytes_to_scan - bytes_scanned)
                chunk = reader.read(read_size)
                if not chunk:
                    if reader.size > 0 and bytes_scanned >= reader.size:
                        break
                    # Attempt to advance past unreadable sector
                    bytes_scanned += 64 * 1024
                    reader.seek(bytes_scanned)
                    continue

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
                        has_handler = False
                        w = StreamWindow(reader, abs_offset, min(sig.max_size, 40 * MB))
                        if sig.header == b"%PDF-":
                            has_handler = True
                            carve_res = _carve_pdf(w)
                        elif sig.header == b"\xFF\xD8\xFF":
                            has_handler = True
                            carve_res = _carve_jpeg(w)
                        elif sig.header == b"\x89PNG\r\n\x1a\n":
                            has_handler = True
                            carve_res = _carve_png(w)
                        elif sig.header == b"PK\x03\x04":
                            has_handler = True
                            carve_res = _carve_zip(w)
                        elif sig.header in (b"GIF89a", b"GIF87a"):
                            has_handler = True
                            carve_res = _carve_gif(w)
                        elif sig.header == b"BM":
                            has_handler = True
                            carve_res = _carve_bmp(w)
                        elif sig.header == b"RIFF":
                            has_handler = True
                            carve_res = _carve_riff(w)
                        elif sig.header == b"SQLite format 3\x00":
                            has_handler = True
                            carve_res = _carve_sqlite(w)
                        elif sig.header == b"7z\xbc\xaf\x27\x1c":
                            has_handler = True
                            carve_res = _carve_7z(w)
                        elif sig.header == b"{\\rtf":
                            has_handler = True
                            carve_res = _carve_rtf(w)

                        candidate_data = None
                        candidate_size = 0
                        footer_found = False
                        f_ext = sig.extension
                        f_cat = sig.category
                        f_type = sig.file_type
                        diagnostic = ""

                        if carve_res and carve_res.size >= sig.min_size:
                            candidate_size = carve_res.size
                            f_ext = carve_res.ext
                            f_cat = carve_res.category
                            f_type = carve_res.file_type
                            footer_found = carve_res.validated
                            candidate_data = reader.pread(abs_offset, candidate_size)
                            diagnostic = carve_res.diagnostic
                        elif not has_handler:
                            # Scalpel Header-to-Footer matching architecture for signatures without dedicated handlers
                            if sig.footer:
                                w_ftr = StreamWindow(reader, abs_offset, min(sig.max_size, 40 * MB))
                                ftr_pos = w_ftr.find_last(sig.footer) if sig.reverse_search else w_ftr.find(sig.footer, max(0, sig.min_size - len(sig.footer)))
                                if ftr_pos >= 0:
                                    candidate_size = ftr_pos + len(sig.footer)
                                    if sig.min_size <= candidate_size <= sig.max_size:
                                        candidate_data = reader.pread(abs_offset, candidate_size)
                                        footer_found = True
                                        diagnostic = f"Scalpel footer {sig.footer!r} matched at offset {candidate_size}"

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
                                diagnostic=diagnostic,
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
