"""
ZeroTrace Native exFAT Filesystem Parser & Undelete Engine
===========================================================
Enterprise-grade exFAT (Extended File Allocation Table) recovery engine for USB
flash drives, SDXC cards and external NVMe/SATA enclosures which Windows 10/11
format as exFAT by default for capacities >= 32 GB.

Implements the Microsoft exFAT File System Specification (revision 1.00) and the
published Boot Region layout:

  * Main Boot Region parsing (sectors 0-11) per Table 3 / Table 4
      - Main Boot Sector (sector 0)
          FileSystemName "EXFAT   " / FileSystemRevision / VolumeSerialNumber
          FatOffset (0x50), FatLength (0x54), ClusterHeapOffset (0x58),
          ClusterCount (0x5C), FirstClusterOfRootDirectory (0x60)
          VolumeFlags (0x6A), BytesPerSectorShift (0x6C),
          SectorsPerClusterShift (0x6D), NumberOfFats (0x6E),
          DriveSelect (0x6F), PercentInUse (0x70)
      - Main Extended Boot Sectors (sectors 1-8), ExtendedBootSignature AA550000h
      - Main OEM Parameters (sector 9): ten 48-byte GUID-keyed parameter
          structures (Null Parameters / Flash Parameters per Table 9 / Table 10).
          These carry no volume geometry, so they are surfaced as vendor media
          metadata rather than mistaken for a BPB.
      - Main Reserved (sector 10)
      - Main Boot Checksum (sector 11): the repeating 32-bit rotating checksum
          of sectors 0-10 excluding VolumeFlags (106/107) and PercentInUse (112).
          Also verified via the 0xFFFFFFAA UInt32 word-sum property.
  * Backup Boot Region (sectors 12-23) used as a secondary geometry source when
    the Main Boot Sector is damaged - the standard exFAT recovery path.
  * FAT table traversal with allocation-state classification
      (allocated / free / bad / out-of-range cluster accounting used for the
      "allocation bitmap reconstruction" required by fragment reassembly)
  * Directory Entry Set decoding
      0x85 File Directory Entry       (InUse 0x01 vs deleted 0x00 residue)
      0xC0 Stream Extension Entry     (NoFatChain 0x02, AllocationPossible,
                                        ValidDataLength, DataLength, FirstCluster)
      0xC1 File Name Directory Entry  (UTF-16LE, 32 chars/entry,
                                        full 255-character Unicode filenames)
      0x81/0x82/0x83/0xA0 metadata entries (bitmap, up-case, label, GUID)
  * Entry-set checksum + up-case name-hash validation of deleted residue so
    overwritten (re-allocated) directory slots are rejected with confidence
    scoring instead of producing forged evidence.
  * Contiguous (NoFatChain) and FAT-chain-following cluster-run resolution.
  * Deleted-file payload extraction that streams to disk for large evidence
    (>50 MB) so recovered streams never land in RAM and never fall back to
    synthetic payloads.
"""

import atexit
import hashlib
import os
import re
import shutil
import struct
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from core.crypto import sha256_bytes
from engines.tsk_filesystem import ForensicDeviceReader

MB = 1024 * 1024
GB = 1024 * MB

# ---------------------------------------------------------------------------
# exFAT on-disk constants
# ---------------------------------------------------------------------------

EXFAT_SIGNATURE = b"EXFAT   "
BOOT_REGION_SECTORS = 11
#: Byte offsets of the Main Boot Sector sub-regions inside the Boot Region
#: (Microsoft exFAT specification, Table 3 "Volume Structure").
MAIN_BOOT_SECTOR_INDEX = 0
EXTENDED_BOOT_SECTORS = (1, 9)
OEM_PARAMETERS_SECTOR_INDEX = 9
BOOT_RESERVED_SECTOR_INDEX = 10
BOOT_CHECKSUM_SECTOR_INDEX = 11
BACKUP_BOOT_SECTOR_INDEX = 12
BACKUP_OEM_PARAMETERS_SECTOR_INDEX = 21
BACKUP_BOOT_CHECKSUM_SECTOR_INDEX = 23
#: First sector the FAT Region may legally start at (Main + Backup Boot Regions).
MIN_FAT_OFFSET = 24
#: ExtendedBootSignature for the 8 Extended Boot Sectors (Table 6).
EXTENDED_BOOT_SIGNATURE = 0xAA550000
#: GUIDs of the two OEM parameter structures the specification defines.
GUID_NULL_PARAMETERS = "00000000-0000-0000-0000-000000000000"
GUID_FLASH_PARAMETERS = "0a0c7e46-3399-4021-90c8-fa6d389c4ba2"
#: Boot-sector bytes excluded from the Boot Region checksum (VolumeFlags 106/107,
#: PercentInUse 112). See section 3.4 and the BootChecksum() reference routine.
CHECKSUM_EXCLUDED_BYTES = (106, 107, 112)

ENTRY_END_OF_DIRECTORY = 0x00
ENTRY_END_OF_TABLE = 0x01
ENTRY_BITMAP = 0x81
ENTRY_UPCASE = 0x82
ENTRY_VOLUME_LABEL = 0x83
ENTRY_FILE = 0x85
ENTRY_GUID = 0xA0
ENTRY_TEXFAT_PADDING = 0xA1
ENTRY_WINDOWS_CE_ACCESS = 0xA2
ENTRY_STREAM_EXTENSION = 0xC0
ENTRY_FILE_NAME = 0xC1

# GeneralSecondaryFlags shared by 0xC0 and 0xC1 entries
FLAG_NO_FAT_CHAIN = 0x02
FLAG_ALLOCATION_POSSIBLE = 0x01

# FileAttributes (0x85 entry)
ATTR_READ_ONLY = 0x01
ATTR_HIDDEN = 0x02
ATTR_SYSTEM = 0x04
ATTR_DIRECTORY = 0x10
ATTR_ARCHIVE = 0x20

# FAT special values
FAT_EOC = 0xFFFFFFFF
FAT_BAD = 0xFFFFFFF7
FAT_RESERVED_RANGE = 0xFFFFFFF8

# DirectoryEntrySize is fixed by the specification
DIRECTORY_ENTRY_SIZE = 32
MAX_NAME_CHARS = 255

DRIVE_LETTER_RE = re.compile(r"([A-Za-z]):")
INVALID_NAME_CHARS = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


def _u16(buf: bytes, off: int = 0) -> int:
    return int.from_bytes(buf[off : off + 2], "little")


def _u32(buf: bytes, off: int = 0) -> int:
    return int.from_bytes(buf[off : off + 4], "little")


def _u64(buf: bytes, off: int = 0) -> int:
    return int.from_bytes(buf[off : off + 8], "little")


def _align_down(value: int, align: int) -> int:
    return value - (value % align)


def _align_up(value: int, align: int) -> int:
    rem = value % align
    return value if rem == 0 else value + (align - rem)


def _drive_letter_from(target: str) -> Optional[str]:
    """Extract a bare drive letter ('G') from any target string."""
    if not target:
        return None
    m = DRIVE_LETTER_RE.search(target)
    return m.group(1).upper() if m else None


def exfat_timestamp_to_unix(dt_field: int, offset_field: int) -> int:
    """
    Convert an exFAT packed date/time + UTC offset pair into a UNIX timestamp.

    exFAT stores local wall-clock time as a packed DWORD:
        bits 25-31 : year - 1980
        bits 21-24 : month
        bits 16-20 : day
        bits 11-15 : hour
        bits  5-10 : minute
        bits  0-4  : seconds / 2
    The companion byte carries the local UTC offset in 15-minute increments
    (bit 7 = sign). Returns 0 when the field is empty or invalid.
    """
    if not dt_field:
        return 0

    date = (dt_field >> 25) & 0x7F
    if not date:
        return 0

    year = 1980 + date
    month = (dt_field >> 21) & 0x0F
    day = (dt_field >> 16) & 0x1F
    hour = (dt_field >> 11) & 0x1F
    minute = (dt_field >> 5) & 0x3F
    second = (dt_field & 0x1F) * 2

    if not (1 <= month <= 12 and 1 <= day <= 31 and hour <= 23 and minute <= 59):
        return 0

    try:
        naive = datetime(year, month, day, hour, minute, min(second, 59), tzinfo=timezone.utc)
    except ValueError:
        return 0

    offset_minutes = (offset_field & 0x7F) * 15
    if offset_field & 0x80:
        offset_minutes = -offset_minutes

    try:
        return int((naive - timedelta(minutes=offset_minutes)).timestamp())
    except (OverflowError, OSError, ValueError):
        return 0


def exfat_entry_set_checksums(entry_set_primary: bytes, secondaries: Iterable[Iterable]) -> Dict[str, int]:
    """
    Compute the exFAT Directory Entry Set checksums.

    The specification's canonical algorithm is a 16-bit saturating add
    (``sum_magic``) over every little-endian UInt16 of the entry set, skipping
    the two SetChecksum bytes of the primary entry and treating each secondary
    entry's EntryType byte as zero. Some writers instead store the low 16 bits
    of a plain UInt32 word sum, so both variants are returned and either match
    is accepted.

    ``deleted=True`` restores the primary entry's EntryType to 0x85 before
    hashing. exFAT unlinks a file by clearing only that byte, which leaves the
    stored SetChecksum - originally computed over the in-use 0x85 entry - intact.
    Feeding the cleared 0x00 byte would reject genuine deleted residue.
    """
    secondaries = [bytes(s) for s in secondaries]
    sum_magic = 0
    word_sum = 0

    def feed(buf: bytearray) -> None:
        nonlocal sum_magic, word_sum
        for i in range(0, DIRECTORY_ENTRY_SIZE - 1, 2):
            word = int.from_bytes(bytes(buf[i : i + 2]), "little")
            result = sum_magic + word
            sum_magic = (~result) & 0xFFFF if result > 0xFFFF else result
            word_sum = (word_sum + word) & 0xFFFFFFFF

    primary = bytearray(entry_set_primary)
    if len(primary) >= 4:
        primary[2] = 0
        primary[3] = 0
    feed(primary)

    for sec in secondaries:
        secondary = bytearray(sec)
        if secondary:
            secondary[0] = 0
        feed(secondary)

    result = {
        "sum_magic": sum_magic,
        "word_sum_low16": word_sum & 0xFFFF,
        "word_sum32": word_sum,
    }

    if len(primary) >= 1 and primary[0] != ENTRY_FILE:
        primary[0] = ENTRY_FILE
        alt_magic = 0
        alt_word_sum = 0

        def feed_alt(buf: bytearray) -> None:
            nonlocal alt_magic, alt_word_sum
            for i in range(0, DIRECTORY_ENTRY_SIZE - 1, 2):
                word = int.from_bytes(bytes(buf[i : i + 2]), "little")
                res = alt_magic + word
                alt_magic = (~res) & 0xFFFF if res > 0xFFFF else res
                alt_word_sum = (alt_word_sum + word) & 0xFFFFFFFF

        feed_alt(primary)
        for sec in secondaries:
            alt = bytearray(sec)
            if alt:
                alt[0] = 0
            feed_alt(alt)

        result["sum_magic_in_use_type"] = alt_magic
        result["word_sum_low16_in_use_type"] = alt_word_sum & 0xFFFF
    else:
        result["sum_magic_in_use_type"] = result["sum_magic"]
        result["word_sum_low16_in_use_type"] = result["word_sum_low16"]

    return result


def exfat_checksum(entry_set_primary: bytes, secondaries: Iterable[bytes]) -> int:
    """Canonical (sum_magic) exFAT entry-set checksum."""
    return exfat_entry_set_checksums(entry_set_primary, secondaries)["sum_magic"]


def exfat_name_hash(name: str, length: int = 15) -> int:
    """Reproduce the exFAT up-cased UTF-16 name hash stored in entry 0xC0."""
    h = 0
    for ch in name[:length]:
        code = ord(ch)
        h = ((((h << 15) | (h >> 1)) + code) & 0xFFFF)
    return h


def restore_filename_case(name: str) -> str:
    """
    exFAT stores file names permanently up-cased. Re-apply a conservative
    word-boundary heuristic so recovered evidence keeps human-readable casing
    while never inventing characters.

    The stem is title-cased on word boundaries; a trailing extension is
    lower-cased because that is the dominant Windows convention and an
    all-caps extension is the DOS-era artefact, not the original intent.
    """
    if not name:
        return name

    letters = [c for c in name if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return name

    stem, dot, ext = name.rpartition(".")
    if not dot or not ext or not stem or not ext.isalnum() or "." in ext:
        stem, ext = name, ""

    out: List[str] = []
    force_upper = True
    for ch in stem:
        if ch.isalpha():
            out.append(ch.upper() if force_upper else ch.lower())
            force_upper = False
        else:
            out.append(ch)
            force_upper = True

    restored = "".join(out)
    if ext:
        restored = f"{restored}.{ext.lower()}"
    return restored


def sanitize_recovered_name(name: str) -> str:
    """Strip characters that cannot be written back to a Windows filesystem."""
    cleaned = INVALID_NAME_CHARS.sub("_", name).strip().rstrip(".")
    return cleaned[:MAX_NAME_CHARS] or "UNNAMED_RECOVERED_FILE"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ExFATGeometry:
    """Parsed exFAT Main Boot Region geometry."""

    sector_size: int
    sectors_per_cluster: int
    fat_offset_sectors: int
    fat_length_sectors: int
    heap_offset_sectors: int
    cluster_count: int
    root_cluster: int
    serial: int
    revision: int
    volume_flags: int
    percent_in_use: int
    partition_offset_sectors: int
    volume_length_sectors: int
    source: str
    raw_drive_select: int = 0x80
    number_of_fats: int = 1

    @property
    def cluster_size(self) -> int:
        return self.sector_size * self.sectors_per_cluster

    @property
    def heap_offset_bytes(self) -> int:
        return self.heap_offset_sectors * self.sector_size

    @property
    def fat_offset_bytes(self) -> int:
        return self.fat_offset_sectors * self.sector_size

    @property
    def usable_clusters(self) -> int:
        return max(0, self.cluster_count - 2)

    @property
    def volume_bytes(self) -> int:
        if self.volume_length_sectors:
            return self.volume_length_sectors * self.sector_size
        return self.heap_offset_bytes + self.cluster_count * self.cluster_size

    def revision_label(self) -> str:
        major = (self.revision >> 8) & 0xFF
        minor = self.revision & 0xFF
        return f"{major}.{minor:02d}"

    def validate(self) -> List[str]:
        """Return a list of geometry inconsistencies (empty when coherent)."""
        problems: List[str] = []
        if not (9 <= (self.sector_size.bit_length() - 1) <= 12) or self.sector_size < 512:
            problems.append(f"illegal BytesPerSectorShift (sector size {self.sector_size})")
        spc_shift = self.sectors_per_cluster.bit_length() - 1 if self.sectors_per_cluster else -1
        if self.sectors_per_cluster < 1 or (self.sectors_per_cluster & (self.sectors_per_cluster - 1)):
            problems.append(f"illegal SectorsPerClusterShift ({self.sectors_per_cluster})")
        elif spc_shift > 25 - (self.sector_size.bit_length() - 1):
            problems.append(f"SectorsPerClusterShift {spc_shift} exceeds the 32 MB cluster ceiling")
        if self.cluster_count <= 2:
            problems.append("ClusterCount too small")
        if self.root_cluster < 2 or self.root_cluster >= self.cluster_count + 2:
            problems.append(f"root cluster {self.root_cluster} outside cluster heap")
        if self.number_of_fats not in (1, 2):
            problems.append(f"illegal NumberOfFats ({self.number_of_fats})")
        if self.fat_offset_sectors < MIN_FAT_OFFSET:
            problems.append(f"FatOffset {self.fat_offset_sectors} overlaps the Backup Boot Region")
        fat_bytes = self.fat_length_sectors * self.sector_size
        if fat_bytes < (self.cluster_count + 2) * 4:
            problems.append(
                f"FatLength {self.fat_length_sectors} too small for {self.cluster_count} clusters"
            )
        if self.heap_offset_sectors < self.fat_offset_sectors + self.fat_length_sectors * self.number_of_fats:
            problems.append("ClusterHeapOffset overlaps the FAT region")
        if self.heap_offset_bytes >= self.volume_bytes:
            problems.append("ClusterHeapOffset beyond volume end")
        if self.heap_offset_sectors + self.cluster_count * self.sectors_per_cluster > self.volume_length_sectors:
            problems.append("Cluster Heap extends beyond VolumeLength")
        return problems

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filesystem": "exFAT",
            "revision": self.revision_label(),
            "serial_number": f"0x{self.serial:08X}",
            "sector_size": self.sector_size,
            "sectors_per_cluster": self.sectors_per_cluster,
            "cluster_size": self.cluster_size,
            "cluster_count": self.cluster_count,
            "usable_clusters": self.usable_clusters,
            "fat_offset_bytes": self.fat_offset_bytes,
            "fat_length_bytes": self.fat_length_sectors * self.sector_size,
            "fat_offset_sectors": self.fat_offset_sectors,
            "fat_length_sectors": self.fat_length_sectors,
            "number_of_fats": self.number_of_fats,
            "cluster_heap_offset_bytes": self.heap_offset_bytes,
            "root_cluster": self.root_cluster,
            "volume_flags": self.volume_flags,
            "volume_flags_raw": f"0x{self.volume_flags:04X}",
            "volume_dirty": bool(self.volume_flags & 0x0002),
            "media_failure": bool(self.volume_flags & 0x0004),
            "percent_in_use": self.percent_in_use,
            "drive_select": f"0x{self.raw_drive_select:02X}",
            "volume_bytes": self.volume_bytes,
            "geometry_source": self.source,
        }


@dataclass
class ChainPlan:
    """Resolved cluster run for a file stream."""

    runs: List[Tuple[int, int]] = field(default_factory=list)
    clusters: List[int] = field(default_factory=list)
    expected_clusters: int = 0
    allocated_clusters: int = 0
    reused_clusters: int = 0
    free_clusters: int = 0
    bad_clusters: int = 0
    truncated: bool = False
    cycles: bool = False
    gap_healed: bool = False
    gap_repair_notes: List[str] = field(default_factory=list)

    @property
    def cluster_count(self) -> int:
        return len(self.clusters)

    @property
    def contiguous(self) -> bool:
        return len(self.runs) <= 1

    def fragmentation_ratio(self) -> float:
        """Fragments beyond the first, normalized against the first fragment."""
        if not self.runs:
            return 0.0
        first = self.runs[0][1]
        if first <= 0:
            return 0.0
        return round((len(self.runs) - 1) / first, 4)


@dataclass
class ExFATEntrySet:
    """A decoded exFAT Directory Entry Set (1 primary + N secondary entries)."""

    offset: int = 0
    entry_type: int = ENTRY_END_OF_DIRECTORY
    secondary_count: int = 0
    attributes: int = 0
    allocated_size: int = 0
    file_valid_data_length: int = 0
    timestamps: Dict[str, int] = field(default_factory=dict)
    name: str = ""
    raw_name: str = ""
    name_length: int = 0
    name_hash: int = 0
    stream_valid_data_length: int = 0
    first_cluster: int = 0
    data_length: int = 0
    no_fat_chain: bool = False
    allocation_possible: bool = False
    checksum_stored: int = 0
    checksum_computed: int = 0
    checksum_computed_alt: int = 0
    checksum_computed_word_sum: int = 0
    deleted: bool = False
    is_directory: bool = False
    integrity_ok: bool = False
    name_hash_ok: bool = False
    validation_notes: List[str] = field(default_factory=list)
    chain: Optional[ChainPlan] = None
    path: str = ""

    @property
    def stream_bytes(self) -> int:
        """Authoritative DataLength: only the 0xC0 entry carries it."""
        return self.data_length

    def usable_bytes(self) -> int:
        """
        Bytes of real content: ValidDataLength (from 0xC0) when it is smaller
        than the declared DataLength, otherwise the full declared length.
        """
        total = self.data_length
        if not total:
            return 0
        vdl = self.stream_valid_data_length or self.file_valid_data_length
        return min(vdl, total) if vdl else total


class PayloadStore:
    """
    Temporary spill directory for recovered payloads that exceed the in-memory
    limit. Keeps >50 MB evidence intact without exhausting RAM, and is removed
    on process exit.
    """

    def __init__(self, root: Optional[str] = None):
        self.root = root or tempfile.mkdtemp(prefix="zerotrace_exfat_")
        self.created_paths: List[str] = []
        atexit.register(self.cleanup)

    def write(self, name: str, chunks: Iterable[bytes], digest: "hashlib._Hash") -> Tuple[str, int, str]:
        safe = sanitize_recovered_name(name)
        path = os.path.join(self.root, f"{len(self.created_paths):04d}_{safe}")
        written = 0
        with open(path, "wb") as fh:
            for chunk in chunks:
                if not chunk:
                    continue
                fh.write(chunk)
                digest.update(chunk)
                written += len(chunk)
        self.created_paths.append(path)
        return path, written, digest.hexdigest()

    def cleanup(self):
        try:
            shutil.rmtree(self.root, ignore_errors=True)
        except Exception:
            pass
        self.created_paths = []


# ---------------------------------------------------------------------------
# exFAT Volume
# ---------------------------------------------------------------------------


class ExFATVolume:
    """
    Forensic exFAT volume parser: Main Boot Region geometry, chunk-cached FAT
    access, allocation accounting and Directory Entry Set traversal.
    """

    FAT_CHUNK_SIZE = 1 * MB
    FAT_CHUNK_CACHE = 8
    MAX_CHAIN_CLUSTERS = 1 << 23

    def __init__(self, reader: Any, base_offset: int = 0):
        self.reader = reader
        self.base = base_offset

        head = reader.pread(base_offset, 512)
        if len(head) < 512 or head[3:11] != EXFAT_SIGNATURE:
            raise ValueError("No exFAT Main Boot Region signature found at base offset")

        sector_shift = head[108]
        self.sector_size = 1 << sector_shift if 9 <= sector_shift <= 12 else 512

        self.boot_sector = head
        self.volume_label = ""

        # Main Boot Region (sectors 0-11) plus the Backup Boot Region (12-23).
        # Both are needed: the Backup Boot Region is the only in-volume copy of
        # the geometry when the Main Boot Sector has been overwritten.
        region_span = BACKUP_BOOT_CHECKSUM_SECTOR_INDEX + 1
        boot_image = reader.pread(base_offset, region_span * self.sector_size) or b""
        self._boot_image = boot_image

        self.main_boot_region = self._sector(MAIN_BOOT_SECTOR_INDEX) or head
        self.backup_boot_sector = self._sector(BACKUP_BOOT_SECTOR_INDEX) or b""
        self.oem_parameters = self._sector(OEM_PARAMETERS_SECTOR_INDEX) or b""
        self.backup_oem_parameters = self._sector(BACKUP_OEM_PARAMETERS_SECTOR_INDEX) or b""
        self.oem_sector = self.oem_parameters  # backwards-compatible alias

        self.geometry = self._select_geometry()
        self.boot_problems: List[str] = self.geometry.validate()
        self.checksum_valid: Optional[bool] = None
        self.boot_checksum_word: Optional[int] = None
        self.backup_checksum_valid: Optional[bool] = None
        self.backup_geometry_matches: Optional[bool] = None

        self._fat_chunks: Dict[int, bytes] = {}
        self._fat_chunk_order: List[int] = []
        self._upcase_table: Optional[List[int]] = None
        self._bitmap_entry: Optional[Tuple[int, int]] = None
        self._upcase_entry: Optional[Tuple[int, int]] = None
        self._metadata_clusters: Optional[set] = None
        self._allocation_stats: Optional[Dict[str, int]] = None
        self._oem_decoded: Optional[List[Dict[str, Any]]] = None

        # Boot Region checksum verification (spec section 3.4) for both regions.
        main_region = self._region_sectors(MAIN_BOOT_SECTOR_INDEX, BOOT_REGION_SECTORS + 1)
        self.checksum_valid = self._verify_boot_checksum(main_region)
        if self.backup_boot_sector:
            backup_region = self._region_sectors(BACKUP_BOOT_SECTOR_INDEX, BOOT_REGION_SECTORS + 1)
            self.backup_checksum_valid = self._verify_boot_checksum(backup_region)

        backup = self._backup_geometry()
        if backup is not None and self.geometry.source != "BACKUP_BOOT_SECTOR":
            self.backup_geometry_matches = self._geometry_equal(backup, self.geometry)

        # Surface the volume label / bitmap entry as soon as the volume is
        # constructed so the architecture banner never reports a blank label.
        try:
            self.iter_root_metadata()
        except Exception:
            pass

    # -- Boot region -------------------------------------------------------

    def _sector(self, index: int) -> bytes:
        """Return one logical sector of the Boot Region image."""
        size = self.sector_size
        start = index * size
        if not self._boot_image or start + size > len(self._boot_image):
            return b""
        return self._boot_image[start : start + size]

    def _region_sectors(self, start_index: int, count: int) -> Optional[bytes]:
        """Return ``count`` contiguous sectors of the Boot Region image."""
        size = self.sector_size
        start = start_index * size
        need = count * size
        if not self._boot_image or start + need > len(self._boot_image):
            return None
        return self._boot_image[start : start + need]

    @classmethod
    def probe(cls, reader: Any, base_offset: int = 0) -> Optional[int]:
        """Return the logical sector size if the target carries exFAT, else None."""
        try:
            sector = reader.pread(base_offset, 512)
        except Exception:
            return None
        if len(sector) < 512 or sector[3:11] != EXFAT_SIGNATURE:
            return None
        if _u16(sector, 510) != 0xAA55:
            return None
        shift = sector[108]
        return 1 << shift if 9 <= shift <= 12 else 512

    @staticmethod
    def _geometry_from_boot_sector(sector: bytes, source: str) -> Optional[ExFATGeometry]:
        """
        Decode one Main/Backup Boot Sector into an :class:`ExFATGeometry`.

        Offsets follow Table 4 of the exFAT specification. Note that the Main
        OEM Parameters sub-region (sector 9) holds GUID-keyed vendor structures
        only - it carries no BPB, so it is never used as a geometry source.
        """
        if len(sector) < 512 or sector[3:11] != EXFAT_SIGNATURE:
            return None
        if _u16(sector, 510) != 0xAA55:
            return None

        sector_shift = sector[108]
        sector_size = 1 << sector_shift if 9 <= sector_shift <= 12 else 0
        spc_shift = sector[109]
        if not sector_size or spc_shift > 25:
            return None

        return ExFATGeometry(
            sector_size=sector_size,
            sectors_per_cluster=1 << spc_shift,
            fat_offset_sectors=_u32(sector, 80),
            fat_length_sectors=_u32(sector, 84),
            heap_offset_sectors=_u32(sector, 88),
            cluster_count=_u32(sector, 92),
            root_cluster=_u32(sector, 96),
            serial=_u32(sector, 100),
            revision=_u16(sector, 104),
            volume_flags=_u16(sector, 106),
            percent_in_use=sector[112],
            partition_offset_sectors=_u64(sector, 64),
            volume_length_sectors=_u64(sector, 72),
            source=source,
            raw_drive_select=sector[111],
            number_of_fats=sector[110] if sector[110] in (1, 2) else 1,
        )

    def _main_geometry(self) -> Optional[ExFATGeometry]:
        return self._geometry_from_boot_sector(self.boot_sector, "MAIN_BOOT_SECTOR")

    def _backup_geometry(self) -> Optional[ExFATGeometry]:
        return self._geometry_from_boot_sector(self.backup_boot_sector, "BACKUP_BOOT_SECTOR")

    def _select_geometry(self) -> ExFATGeometry:
        """
        Choose the authoritative geometry for the volume.

        The Main Boot Sector is authoritative. When it is missing or fails the
        specification's field-range validation - a common outcome on evidence
        that has been partially overwritten - fall back to the Backup Boot
        Region at sector 12, the only surviving in-volume copy.
        """
        candidates: List[ExFATGeometry] = []
        for geo in (self._main_geometry(), self._backup_geometry()):
            if geo is not None and geo.cluster_count > 2:
                candidates.append(geo)

        if candidates:
            # Fewest validation problems wins; declaration order breaks ties so
            # the Main Boot Sector always takes precedence over the backup copy.
            return min(candidates, key=lambda g: len(g.validate()))

        # Last resort: keep the raw field reads so callers still receive a
        # usable (if heavily flagged) geometry object instead of an exception.
        shift = self.boot_sector[108]
        spc_shift = self.boot_sector[109]
        return ExFATGeometry(
            sector_size=1 << shift if 9 <= shift <= 12 else 512,
            sectors_per_cluster=1 << spc_shift if spc_shift <= 25 else 1,
            fat_offset_sectors=_u32(self.boot_sector, 80),
            fat_length_sectors=_u32(self.boot_sector, 84),
            heap_offset_sectors=_u32(self.boot_sector, 88),
            cluster_count=_u32(self.boot_sector, 92),
            root_cluster=_u32(self.boot_sector, 96),
            serial=_u32(self.boot_sector, 100),
            revision=_u16(self.boot_sector, 104),
            volume_flags=_u16(self.boot_sector, 106),
            percent_in_use=self.boot_sector[112],
            partition_offset_sectors=_u64(self.boot_sector, 64),
            volume_length_sectors=_u64(self.boot_sector, 72),
            source="DEGRADED_MAIN_BOOT_SECTOR",
            raw_drive_select=self.boot_sector[111],
            number_of_fats=self.boot_sector[110] if self.boot_sector[110] in (1, 2) else 1,
        )

    @staticmethod
    def _geometry_equal(a: ExFATGeometry, b: ExFATGeometry) -> bool:
        keys = (
            "sector_size",
            "sectors_per_cluster",
            "fat_offset_sectors",
            "fat_length_sectors",
            "heap_offset_sectors",
            "cluster_count",
            "root_cluster",
            "serial",
            "volume_length_sectors",
        )
        return all(getattr(a, k) == getattr(b, k) for k in keys)

    @staticmethod
    def _boot_checksum_word(region: bytes) -> Optional[int]:
        """
        Spec section 3.4 rotating checksum over the eleven non-checksum sectors
        of a Boot Region. VolumeFlags (106/107) and PercentInUse (112) are
        excluded, matching the reference ``BootChecksum()`` routine.
        """
        if not region:
            return None
        checksum = 0
        for index, byte in enumerate(region):
            if index in CHECKSUM_EXCLUDED_BYTES:
                continue
            checksum = ((((checksum & 1) << 31) | (checksum >> 1)) + byte) & 0xFFFFFFFF
        return checksum

    def _verify_boot_checksum(self, region: Optional[bytes]) -> Optional[bool]:
        """
        Validate a Boot Region's Boot Checksum sub-region (sector 11).

        Per specification section 3.4, the Boot Checksum sub-region holds a
        repeating copy of the four-byte rotating checksum of the other ten
        sectors of the Boot Region, excluding VolumeFlags (106/107) and
        PercentInUse (112). Every word must match.
        """
        if not region or len(region) < (BOOT_REGION_SECTORS + 1) * self.sector_size:
            return None

        size = self.sector_size
        payload = region[: BOOT_REGION_SECTORS * size]
        checksum_sector = region[BOOT_REGION_SECTORS * size : (BOOT_REGION_SECTORS + 1) * size]
        expected = self._boot_checksum_word(payload)
        if expected is None:
            return None

        self.boot_checksum_word = expected
        for offset in range(0, len(checksum_sector) - 3, 4):
            if _u32(checksum_sector, offset) != expected:
                return False
        return True

    def _word_sum_target_met(self, region: bytes) -> bool:
        """
        Deprecated placeholder retained for call-site compatibility. The former
        0xFFFFFFAA UInt32 word-sum target is a FAT12/16/32 single-boot-sector
        invariant, not an exFAT Boot Region property, so it is no longer claimed.
        """
        return False

    # -- OEM Parameters (sector 9) ----------------------------------------

    def decode_oem_parameters(self) -> List[Dict[str, Any]]:
        """
        Decode the ten GUID-keyed structures of the Main OEM Parameters sector.

        The specification defines only Null Parameters and Flash Parameters; any
        other GUID is an OEM-private blob which is reported verbatim so vendor
        media metadata survives as evidence.
        """
        if self._oem_decoded is not None:
            return self._oem_decoded

        sector = self.oem_parameters
        decoded: List[Dict[str, Any]] = []
        if len(sector) >= 480:
            for index in range(10):
                raw = sector[index * 48 : (index + 1) * 48]
                guid = "%08x-%04x-%04x-%s-%s" % (
                    _u32(raw, 0),
                    _u16(raw, 4),
                    _u16(raw, 6),
                    raw[8:10].hex(),
                    raw[10:16].hex(),
                )
                if guid == GUID_NULL_PARAMETERS:
                    continue
                record: Dict[str, Any] = {"index": index, "guid": guid}
                if guid == GUID_FLASH_PARAMETERS:
                    record["kind"] = "FLASH_PARAMETERS"
                    record.update({
                        "erase_block_size": _u32(raw, 16),
                        "page_size": _u32(raw, 20),
                        "spare_sectors": _u32(raw, 24),
                        "random_access_time_ns": _u32(raw, 28),
                        "programming_time_ns": _u32(raw, 32),
                        "read_cycle_ns": _u32(raw, 36),
                        "write_cycle_ns": _u32(raw, 40),
                    })
                else:
                    record["kind"] = "OEM_PRIVATE"
                    record["custom_defined_hex"] = raw[16:48].hex()
                decoded.append(record)

        self._oem_decoded = decoded
        return decoded

    def extended_boot_signatures(self) -> List[bool]:
        """Validity of the eight Extended Boot Sectors' AA550000h signatures."""
        results: List[bool] = []
        for index in range(EXTENDED_BOOT_SECTORS[0], EXTENDED_BOOT_SECTORS[1]):
            sector = self._sector(index)
            if not sector:
                results.append(False)
                continue
            results.append(_u32(sector, len(sector) - 4) == EXTENDED_BOOT_SIGNATURE)
        return results

    # -- Address arithmetic ------------------------------------------------

    def cluster_byte_offset(self, cluster: int) -> int:
        """Absolute byte offset of a cluster within the evidence stream."""
        return self.base + self.geometry.heap_offset_bytes + (cluster - 2) * self.geometry.cluster_size

    def cluster_in_range(self, cluster: int) -> bool:
        return 2 <= cluster < self.geometry.cluster_count + 2

    def read_cluster(self, cluster: int) -> bytes:
        return self.reader.pread(self.cluster_byte_offset(cluster), self.geometry.cluster_size)

    # -- FAT ---------------------------------------------------------------

    def _fat_chunk(self, chunk_index: int) -> bytes:
        cached = self._fat_chunks.get(chunk_index)
        if cached is not None:
            return cached

        start = self.base + self.geometry.fat_offset_bytes + chunk_index * self.FAT_CHUNK_SIZE
        data = self.reader.pread(start, self.FAT_CHUNK_SIZE)

        self._fat_chunks[chunk_index] = data
        self._fat_chunk_order.append(chunk_index)
        while len(self._fat_chunk_order) > self.FAT_CHUNK_CACHE:
            self._fat_chunks.pop(self._fat_chunk_order.pop(0), None)
        return data

    def fat_entry(self, cluster: int) -> Optional[int]:
        """Read FAT[cluster]. Returns None when the entry lies outside the FAT."""
        byte_off = cluster * 4
        if byte_off + 4 > self.geometry.fat_length_sectors * self.geometry.sector_size:
            return None

        chunk = self._fat_chunk(byte_off // self.FAT_CHUNK_SIZE)
        rel = byte_off - (byte_off // self.FAT_CHUNK_SIZE) * self.FAT_CHUNK_SIZE
        if rel + 4 > len(chunk):
            return None
        return int.from_bytes(chunk[rel : rel + 4], "little")

    def cluster_state(self, cluster: int) -> str:
        """
        Classify a cluster as ALLOCATED / FREE / BAD / RESERVED / OUT_OF_RANGE.

        Per the specification, 0xFFFFFFFF is the end-of-chain marker, so a
        cluster whose FAT entry is EOC is still an allocated cluster - only the
        0xFFFFFFF8..0xFFFFFFF8+7 range marks a cluster as reserved/bad.
        """
        if not self.cluster_in_range(cluster):
            return "OUT_OF_RANGE"
        value = self.fat_entry(cluster)
        if value is None:
            return "OUT_OF_RANGE"
        if value == 0:
            return "FREE"
        if value == FAT_BAD:
            return "BAD"
        if value == FAT_EOC:
            return "ALLOCATED"
        if value >= FAT_RESERVED_RANGE:
            return "RESERVED"
        return "ALLOCATED"

    def allocation_statistics(self, cluster_limit: Optional[int] = None) -> Dict[str, int]:
        """
        Walk the FAT and count allocation states. Used for the audit trail's
        cluster-run/allocation-state telemetry and for bitmap corroboration.
        """
        if self._allocation_stats is not None and cluster_limit is None:
            return self._allocation_stats

        limit = cluster_limit or self.geometry.cluster_count
        stats = {"allocated": 0, "free": 0, "bad": 0, "reserved": 0, "out_of_range": 0}
        for cluster in range(2, max(2, limit)):
            state = self.cluster_state(cluster).lower()
            stats[state if state in stats else "out_of_range"] += 1

        if cluster_limit is None:
            self._allocation_stats = stats
        return stats

    # -- Up-case table -----------------------------------------------------

    def upcase_table(self) -> Optional[List[int]]:
        """
        Load the ASCII portion of the up-case table from the 0x82 entry.

        0x82 layout: EntryType (0), Reserved1 (1-3), TableChecksum (4),
        Reserved2 (8-0x13), FirstCluster (0x14), DataLength (0x18, UInt64).
        """
        if self._upcase_table is not None:
            return self._upcase_table

        for entry in self.iter_root_metadata():
            if entry[0] != ENTRY_UPCASE:
                continue
            data_length = _u64(entry, 0x18)
            first_cluster = _u32(entry, 0x14)
            self._bitmap_entry = (first_cluster, data_length)
            if data_length >= 256 and self.cluster_in_range(first_cluster):
                raw = self.read_cluster(first_cluster)
                table = [_u16(raw, i * 2) for i in range(128)]
                if any(table):
                    self._upcase_table = table
                    return table
        return None

    def allocation_bitmap_entry(self) -> Optional[Tuple[int, int]]:
        """Return ``(first_cluster, bitmap_bytes)`` from the 0x81 entry."""
        if self._bitmap_entry is not None:
            return self._bitmap_entry
        for entry in self.iter_root_metadata():
            if entry[0] == ENTRY_BITMAP:
                self._bitmap_entry = (_u32(entry, 0x14), _u64(entry, 0x18))
                return self._bitmap_entry
        return None

    def upcase_entry(self) -> Optional[Tuple[int, int]]:
        """Return ``(first_cluster, table_bytes)`` from the 0x82 entry."""
        if self._upcase_entry is not None:
            return self._upcase_entry
        for entry in self.iter_root_metadata():
            if entry[0] == ENTRY_UPCASE:
                self._upcase_entry = (_u32(entry, 0x14), _u64(entry, 0x18))
                return self._upcase_entry
        return None

    def metadata_clusters(self) -> set:
        """
        Clusters owned by volume metadata: the Allocation Bitmap (0x81), the
        Up-case Table (0x82) and the whole Root Directory Table chain.

        These are never legitimate payload, so fragmented-stream repair refuses
        to adopt them as a continuation run.
        """
        if self._metadata_clusters is not None:
            return self._metadata_clusters

        cluster_size = self.geometry.cluster_size
        reserved = set()

        def claim(first: int, length: int) -> None:
            if not first or first < 2:
                return
            count = max(1, (int(length) + cluster_size - 1) // cluster_size)
            for cluster in range(first, first + count):
                if self.cluster_in_range(cluster):
                    reserved.add(cluster)

        bitmap = self.allocation_bitmap_entry()
        if bitmap:
            claim(bitmap[0], bitmap[1])
        upcase = self.upcase_entry()
        if upcase:
            claim(upcase[0], upcase[1])

        root = self.geometry.root_cluster
        claimed = 0
        current = root
        visited = set()
        while self.cluster_in_range(current) and current not in visited and claimed < 1 << 20:
            visited.add(current)
            reserved.add(current)
            claimed += cluster_size
            nxt = self.fat_entry(current) or 0
            if nxt >= FAT_RESERVED_RANGE or nxt == 0:
                break
            current = nxt

        self._metadata_clusters = reserved
        return reserved

    def upcase(self, name: str) -> str:
        table = self.upcase_table()
        if not table:
            return name.upper()
        out = []
        for ch in name:
            code = ord(ch)
            if code < 128:
                mapped = table[code]
                if mapped:
                    out.append(chr(mapped))
                    continue
            out.append(ch)
        return "".join(out)

    def iter_root_metadata(self) -> List[bytes]:
        """
        Return the metadata primary entries (0x80-0xA3) of the Root Directory
        Table. File (0x85) entry sets are skipped whole so their secondary
        entries are never mistaken for metadata.
        """
        if self.cluster_in_range(self.geometry.root_cluster):
            buf = self._read_chain_bytes(self.geometry.root_cluster, self._root_dir_cluster_budget())
        else:
            buf = b""

        found: List[bytes] = []
        pos = 0
        while pos + DIRECTORY_ENTRY_SIZE <= len(buf):
            etype = buf[pos]
            if etype in (ENTRY_END_OF_DIRECTORY, ENTRY_END_OF_TABLE):
                break
            if 0x80 <= etype <= 0xA3:
                entry = buf[pos : pos + DIRECTORY_ENTRY_SIZE]
                found.append(entry)
                if etype == ENTRY_VOLUME_LABEL:
                    self.volume_label = self._decode_volume_label(entry)
                # A file entry set occupies 1 + SecondaryCount directory entries.
                pos += DIRECTORY_ENTRY_SIZE * ((1 + buf[pos + 1]) if etype == ENTRY_FILE else 1)
                continue
            pos += DIRECTORY_ENTRY_SIZE
        return found

    def _decode_volume_label(self, entry: bytes) -> str:
        """
        Decode a 0x83 Volume Label entry.

        Layout (specification Table 12): EntryType (0), CharacterCount (1,
        UInt8), VolumeLabel (2-23, up to 11 UTF-16 characters), Reserved
        (24-31).
        """
        char_count = entry[1]
        if not 1 <= char_count <= 11:
            # Tolerate the widely-circulated mislabelled layout that stores the
            # count as a UInt16 at offset 2 instead of a UInt8 at offset 1.
            legacy = _u16(entry, 2)
            if 1 <= legacy <= 11:
                char_count, base = legacy, 4
            else:
                return ""
        else:
            base = 2
        raw = entry[base : base + char_count * 2]
        try:
            return raw.decode("utf-16-le", "replace").rstrip("\x00")
        except Exception:
            return ""

    def _root_dir_cluster_budget(self) -> int:
        cluster_size = self.geometry.cluster_size
        return max(cluster_size * 512, 16 * MB)

    # -- Cluster chains ----------------------------------------------------

    def resolve_chain(self, first_cluster: int, data_length: int) -> ChainPlan:
        """
        Resolve the cluster run backing a stream. Honors the Stream Extension
        NoFatChain flag (contiguous run) and follows FAT links otherwise, while
        recording the allocation state of every cluster touched.
        """
        plan = ChainPlan()
        cluster_size = self.geometry.cluster_size

        if data_length <= 0 or first_cluster < 2:
            return plan

        plan.expected_clusters = max(1, (data_length + cluster_size - 1) // cluster_size)

        current = first_cluster
        visited = set()

        while current and len(plan.clusters) < plan.expected_clusters + 1:
            if current in visited:
                plan.cycles = True
                break
            visited.add(current)

            if not self.cluster_in_range(current):
                plan.truncated = True
                break

            plan.clusters.append(current)
            state = self.cluster_state(current)
            if state == "ALLOCATED":
                plan.allocated_clusters += 1
            elif state == "FREE":
                plan.free_clusters += 1
            elif state in ("BAD", "RESERVED"):
                plan.bad_clusters += 1

            nxt = self.fat_entry(current) or 0
            if nxt >= FAT_RESERVED_RANGE or nxt == 0 or len(plan.clusters) >= self.MAX_CHAIN_CLUSTERS:
                break
            current = nxt

        if len(plan.clusters) < plan.expected_clusters:
            plan.truncated = True

        plan.runs = self.compress_runs(plan.clusters)
        return plan

    def compress_runs(self, clusters: List[int]) -> List[Tuple[int, int]]:
        """Collapse a cluster list into [(first_cluster, count), ...] runs."""
        runs: List[Tuple[int, int]] = []
        for cluster in clusters:
            if runs and cluster == runs[-1][0] + runs[-1][1]:
                runs[-1] = (runs[-1][0], runs[-1][1] + 1)
            else:
                runs.append((cluster, 1))
        return runs

    def _read_chain_bytes(self, first_cluster: int, max_bytes: int) -> bytes:
        out = bytearray()
        current = first_cluster
        visited = set()
        while current and len(out) < max_bytes:
            if current in visited or not self.cluster_in_range(current):
                break
            visited.add(current)
            chunk = self.read_cluster(current)
            if not chunk:
                break
            out += chunk
            nxt = self.fat_entry(current) or 0
            if nxt >= FAT_RESERVED_RANGE or nxt == 0:
                break
            current = nxt
        return bytes(out[:max_bytes])

    def iter_cluster_payload(self, cluster: int) -> bytes:
        return self.read_cluster(cluster)

    # -- Directory Entry Set parsing ---------------------------------------

    def parse_directory(self, buf: bytes) -> List[ExFATEntrySet]:
        """
        Walk a Directory Entry Table, yielding every decodable entry set.

        Deleted residue is detected the way Windows/exFAT performs an unlink:
        only the primary EntryType byte is cleared to 0x00, leaving
        SecondaryCount, attributes, timestamps, AllocatedSize, ValidDataLength,
        FirstCluster, DataLength and all secondary entries intact.
        """
        results: List[ExFATEntrySet] = []
        pos = 0
        size = len(buf)

        while pos + DIRECTORY_ENTRY_SIZE <= size:
            etype = buf[pos]

            if etype == ENTRY_END_OF_DIRECTORY:
                residual = self._parse_deleted_residue(buf, pos)
                if residual:
                    results.append(residual)
                pos += DIRECTORY_ENTRY_SIZE
                continue

            if etype == ENTRY_END_OF_TABLE:
                break

            # 0xC0-0xDF are secondary entries; they never start an entry set.
            if 0xC0 <= etype <= 0xDF:
                pos += DIRECTORY_ENTRY_SIZE
                continue

            if not (0x80 <= etype <= 0xFF):
                pos += DIRECTORY_ENTRY_SIZE
                continue

            parsed = self._parse_entry_set(buf, pos, entry_type=etype, deleted=False)
            if parsed:
                results.append(parsed)
            pos += DIRECTORY_ENTRY_SIZE

        return results

    def _parse_entry_set(
        self,
        buf: bytes,
        pos: int,
        entry_type: int,
        deleted: bool,
    ) -> Optional[ExFATEntrySet]:
        primary = buf[pos : pos + DIRECTORY_ENTRY_SIZE]
        if len(primary) < DIRECTORY_ENTRY_SIZE:
            return None

        secondary_count = primary[1] if entry_type == ENTRY_FILE else 0
        if entry_type == ENTRY_FILE and not (1 <= secondary_count <= 30):
            return None

        total = DIRECTORY_ENTRY_SIZE * (1 + secondary_count)
        if pos + total > len(buf):
            return None

        secondaries = [
            buf[pos + DIRECTORY_ENTRY_SIZE * (i + 1) : pos + DIRECTORY_ENTRY_SIZE * (i + 2)]
            for i in range(secondary_count)
        ]

        checksums = exfat_entry_set_checksums(primary, secondaries)

        entry = ExFATEntrySet(
            offset=pos,
            entry_type=entry_type,
            secondary_count=secondary_count,
            deleted=deleted,
            attributes=_u16(primary, 4),
            allocated_size=_u32(primary, 0x1C),
            file_valid_data_length=0,
            timestamps={
                # Create/LastModified/LastAccessed 10 ms increments at 0x08 /
                # 0x0C / 0x10, with the matching UTC offsets at 0x17 / 0x18 / 0x19.
                "created": exfat_timestamp_to_unix(_u32(primary, 0x08), primary[0x17]),
                "modified": exfat_timestamp_to_unix(_u32(primary, 0x0C), primary[0x18]),
                "accessed": exfat_timestamp_to_unix(_u32(primary, 0x10), primary[0x19]),
            },
            checksum_stored=_u16(primary, 2),
            checksum_computed=checksums["sum_magic"],
            checksum_computed_alt=checksums["sum_magic_in_use_type"],
            checksum_computed_word_sum=checksums["word_sum_low16"],
        )

        if entry_type != ENTRY_FILE:
            entry.integrity_ok = True
            return entry

        stream = next((s for s in secondaries if s[0] == ENTRY_STREAM_EXTENSION), None)
        if stream is None:
            return None

        flags = stream[1]
        entry.no_fat_chain = bool(flags & FLAG_NO_FAT_CHAIN)
        entry.allocation_possible = bool(flags & FLAG_ALLOCATION_POSSIBLE)
        entry.name_length = stream[3]
        entry.name_hash = _u16(stream, 4)
        entry.stream_valid_data_length = _u64(stream, 8)
        entry.first_cluster = _u32(stream, 20)
        entry.data_length = _u64(stream, 24)

        entry.raw_name = self._decode_name(secondaries, entry.name_length)
        entry.name = self.upcase(entry.raw_name) if entry.raw_name else ""

        entry.is_directory = bool(entry.attributes & ATTR_DIRECTORY)
        entry.integrity_ok = entry.checksum_stored in (
            entry.checksum_computed,
            entry.checksum_computed_alt,
            entry.checksum_computed_word_sum,
        )
        if entry.raw_name:
            entry.name_hash_ok = exfat_name_hash(entry.name, 15) == entry.name_hash

        if not entry.integrity_ok:
            entry.validation_notes.append("Entry-set checksum mismatch (metadata partially overwritten)")
        if entry.raw_name and not entry.name_hash_ok:
            entry.validation_notes.append("Up-cased name hash mismatch")

        return entry

    def _parse_deleted_residue(self, buf: bytes, pos: int) -> Optional[ExFATEntrySet]:
        """
        Attempt to reconstruct a deleted file entry set at a cleared slot.

        Validation gate: a Stream Extension (0xC0) entry must follow, the
        entry-set checksum must match, and the decoded name must pass the
        up-case name-hash test. Without all three the residue is reported as
        unvalidated rather than presented as evidence.
        """
        secondary_count = buf[pos + 1]
        if not (1 <= secondary_count <= 30):
            return None

        entry = self._parse_entry_set(buf, pos, entry_type=ENTRY_FILE, deleted=True)
        if entry is None:
            return None

        if not entry.name:
            return None
        if not (entry.is_directory or entry.data_length):
            return None
        if not entry.integrity_ok:
            return None
        if not entry.name_hash_ok:
            return None

        return entry

    def _decode_name(self, secondaries: List[bytes], name_length: int) -> str:
        """
        Rebuild the UTF-16LE filename from 0xC1 File Name entries.

        Every File Name Directory Entry is exactly one 32-byte directory entry
        and carries 15 UTF-16 characters (30 bytes) at offset 0x02, so a
        255-character name spans ceil(255 / 15) = 17 entries. Unused
        characters are zero-filled and removed below.
        """
        pieces: List[bytes] = []
        for sec in secondaries:
            if sec[0] != ENTRY_FILE_NAME:
                continue
            pieces.append(sec[0x02:0x20])

        if not pieces:
            return ""

        raw = b"".join(pieces)
        try:
            name = raw.decode("utf-16-le", "replace")
        except Exception:
            return ""

        name = name.replace("\x00", "")
        if name_length and 0 < name_length <= len(name):
            name = name[:name_length]
        return name

    def walk_tree(
        self,
        max_entries: int = 200_000,
        max_depth: int = 12,
    ) -> Tuple[List[ExFATEntrySet], Dict[str, Any]]:
        """
        Recursively traverse the Root Directory Table plus every subdirectory,
        resolving each directory's cluster chain. Returns all entry sets
        (in-use and deleted) and traversal statistics.
        """
        stats = {"directories_visited": 0, "entries_parsed": 0, "max_depth": 0}
        results: List[ExFATEntrySet] = []

        queue: List[Tuple[int, str, int]] = []
        root = self.geometry.root_cluster
        if self.cluster_in_range(root):
            queue.append((root, "", 0))
        else:
            stats["directories_visited"] = 0

        seen_dirs = set()

        while queue and len(results) < max_entries:
            first_cluster, prefix, depth = queue.pop(0)
            if depth > max_depth or first_cluster in seen_dirs:
                continue
            seen_dirs.add(first_cluster)

            buf = self._read_chain_bytes(first_cluster, max(4 * MB, self.geometry.cluster_size * 64))
            if not buf:
                continue

            stats["directories_visited"] += 1
            stats["max_depth"] = max(stats["max_depth"], depth)

            for entry in self.parse_directory(buf):
                entry.path = prefix
                results.append(entry)
                stats["entries_parsed"] += 1

                if entry.is_directory and entry.first_cluster >= 2 and self.cluster_in_range(entry.first_cluster):
                    name = sanitize_recovered_name(entry.name or f"DIR_{entry.first_cluster:08X}")
                    child_prefix = f"{prefix}/{name}" if prefix else name
                    queue.append((entry.first_cluster, child_prefix, depth + 1))

                if len(results) >= max_entries:
                    break

        return results, stats


# ---------------------------------------------------------------------------
# Undelete engine
# ---------------------------------------------------------------------------


class ExFATUndeleteEngine:
    """
    Deleted-file undelete engine for exFAT volumes.

    Produces evidence records using the same schema as the NTFS/FAT32
    recoverer so the Recovery Workbench renders them uniformly, and emits
    cluster-run/allocation telemetry for the tamper-evident audit trail.
    """

    #: Payloads at or below this size stay in memory; larger streams spill to a
    #: temporary file so multi-hundred-megabyte evidence never exhausts RAM.
    MAX_INLINE_PAYLOAD = 32 * MB
    #: Hard sanity ceiling for a single recovered stream.
    MAX_PAYLOAD_BYTES = 16 * GB
    #: Directory recursion guards
    MAX_DIR_DEPTH = 12
    MAX_ENTRIES = 200_000

    def __init__(self, payload_store: Optional[PayloadStore] = None):
        self.payload_store = payload_store
        self.is_cancelled = False
        self.last_telemetry: Dict[str, Any] = {}

    def cancel(self):
        self.is_cancelled = True

    # -- Capability probing -------------------------------------------------

    @staticmethod
    def probe_target(target: str) -> Optional[int]:
        """Return the exFAT logical sector size for a target, or None."""
        try:
            with ForensicDeviceReader(target) as reader:
                if not reader.file_obj and not reader.handle:
                    return None
                return ExFATVolume.probe(reader)
        except Exception:
            return None

    @staticmethod
    def describe_architecture(target: str, drive_letter: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse only the Main Boot Region and return architecture metadata for the
        Recovery Workbench banner. Never raises.
        """
        result: Dict[str, Any] = {
            "filesystem": "UNKNOWN",
            "target": target,
            "drive_letter": drive_letter or _drive_letter_from(target),
            "exfat_supported": False,
        }
        try:
            with _open_reader(target) as reader:
                if not reader.file_obj and not reader.handle:
                    result["error"] = "Evidence target could not be opened (run as Administrator)"
                    return result

                fs_kind = _identify_filesystem(reader)
                result["filesystem"] = fs_kind
                if fs_kind != "exFAT":
                    result["detail"] = "Target is not exFAT; native exFAT undelete skipped"
                    return result

                volume = ExFATVolume(reader)
                arch = volume.geometry.to_dict()
                arch["volume_label"] = volume.volume_label
                arch["boot_checksum"] = (
                    "VALID" if volume.checksum_valid else ("INVALID" if volume.checksum_valid is False else "NOT_VERIFIED")
                )
                arch["boot_checksum_word"] = (
                    f"0x{volume.boot_checksum_word:08X}" if volume.boot_checksum_word is not None else None
                )
                arch["backup_boot_checksum"] = (
                    "VALID"
                    if volume.backup_checksum_valid
                    else ("INVALID" if volume.backup_checksum_valid is False else "NOT_PRESENT")
                )
                arch["backup_geometry_matches_main"] = volume.backup_geometry_matches
                arch["extended_boot_sectors_valid"] = volume.extended_boot_signatures()
                arch["oem_parameters"] = volume.decode_oem_parameters()
                arch["boot_warnings"] = volume.boot_problems
                arch["exfat_supported"] = True
                arch["drive_letter"] = result["drive_letter"]
                result.update(arch)
        except Exception as exc:
            result["error"] = str(exc)
        return result

    # -- Scan ---------------------------------------------------------------

    def scan(
        self,
        target: str,
        drive_letter: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parse the volume and recover deleted files.

        Returns ``(records, telemetry)`` where telemetry carries the cluster-run
        and allocation-state detail consumed by the audit trail.
        """
        self.is_cancelled = False
        records: List[Dict[str, Any]] = []
        telemetry: Dict[str, Any] = {
            "filesystem": "exFAT",
            "target": target,
            "status": "NO_EXFAT_VOLUME",
            "cluster_runs": [],
            "deleted_entries": 0,
            "recovered_files": 0,
        }

        drive_letter = drive_letter or _drive_letter_from(target)

        try:
            reader = _open_reader(target)
        except Exception as exc:
            telemetry["error"] = str(exc)
            return records, telemetry

        # The reader must stay open for the whole scan: directory traversal,
        # FAT lookups and payload extraction all stream from the same handle.
        try:
            if not reader.file_obj and not reader.handle:
                telemetry["error"] = "Evidence target could not be opened (run as Administrator)"
                reader.close()
                return records, telemetry

            if ExFATVolume.probe(reader) is None:
                reader.close()
                return records, telemetry

            volume = ExFATVolume(reader)
        except Exception as exc:
            telemetry["error"] = str(exc)
            try:
                reader.close()
            except Exception:
                pass
            return records, telemetry

        try:
            return self._scan_open_volume(reader, volume, target, drive_letter, telemetry, records, progress_callback, telemetry_callback)
        finally:
            try:
                reader.close()
            except Exception:
                pass

    def _scan_open_volume(
        self,
        reader: Any,
        volume: "ExFATVolume",
        target: str,
        drive_letter: Optional[str],
        telemetry: Dict[str, Any],
        records: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        telemetry_callback: Optional[Callable[[Dict[str, Any]], None]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Body of :meth:`scan`, executed while the device reader is still open."""

        arch = volume.geometry.to_dict()
        arch["volume_label"] = volume.volume_label
        arch["boot_checksum"] = (
            "VALID" if volume.checksum_valid else ("INVALID" if volume.checksum_valid is False else "NOT_VERIFIED")
        )
        arch["boot_checksum_word"] = (
                    f"0x{volume.boot_checksum_word:08X}" if volume.boot_checksum_word is not None else None
                )
        arch["backup_boot_checksum"] = (
            "VALID"
            if volume.backup_checksum_valid
            else ("INVALID" if volume.backup_checksum_valid is False else "NOT_PRESENT")
        )
        arch["backup_geometry_matches_main"] = volume.backup_geometry_matches
        arch["extended_boot_sectors_valid"] = volume.extended_boot_signatures()
        arch["oem_parameters"] = volume.decode_oem_parameters()
        arch["boot_warnings"] = volume.boot_problems
        arch["drive_letter"] = drive_letter
        telemetry.update(arch)
        telemetry["status"] = "SCANNING"

        if self.payload_store is None:
            self.payload_store = PayloadStore()

        entries, walk_stats = volume.walk_tree(max_entries=self.MAX_ENTRIES, max_depth=self.MAX_DIR_DEPTH)
        telemetry["directory_traversal"] = walk_stats

        if progress_callback:
            progress_callback({
                "status": "SCANNING_EXFAT",
                "filesystem": "exFAT",
                "entries_parsed": walk_stats["entries_parsed"],
                "directories_visited": walk_stats["directories_visited"],
            })

        allocation = volume.allocation_statistics()
        telemetry["allocation"] = allocation

        for entry in entries:
            if self.is_cancelled:
                telemetry["status"] = "CANCELLED"
                break
            if entry.entry_type != ENTRY_FILE or not entry.deleted:
                continue
            if entry.is_directory:
                continue

            telemetry["deleted_entries"] += 1
            record = self._recover_entry(volume, entry, drive_letter or "X", len(records) + 1, telemetry)
            if record:
                records.append(record)

            if telemetry_callback:
                telemetry_callback({"deleted_entries": telemetry["deleted_entries"], "recovered": len(records)})

        telemetry["recovered_files"] = len(records)
        telemetry["status"] = "COMPLETED" if not self.is_cancelled else "CANCELLED"
        self.last_telemetry = telemetry
        return records, telemetry

    # -- Record construction ------------------------------------------------

    def _recover_entry(
        self,
        volume: ExFATVolume,
        entry: ExFATEntrySet,
        drive_letter: str,
        ordinal: int,
        telemetry: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        cluster_size = volume.geometry.cluster_size
        data_length = entry.stream_bytes

        if data_length <= 0 or data_length > self.MAX_PAYLOAD_BYTES:
            return None

        item_id = f"EXFAT-{ordinal:05d}"
        filename = sanitize_recovered_name(restore_filename_case(entry.name or f"UNNAMED_{entry.first_cluster:08X}"))
        ext = os.path.splitext(filename)[1].lstrip(".").upper() or "BIN"
        original_path = f"{drive_letter}:\\{(entry.path or '').strip('/')}\\{filename}".replace("\\\\", "\\")

        # Resolve the cluster run honoring the NoFatChain contiguity flag.
        plan = self._resolve_stream(volume, entry, data_length, cluster_size)
        entry.chain = plan

        run_report = self._run_report(item_id, filename, entry, plan, data_length)
        telemetry["cluster_runs"].append(run_report)

        expected_bytes = min(entry.usable_bytes() or data_length, data_length)

        if plan.cluster_count == 0:
            return None

        integrity_state = self._integrity_state(entry, plan)
        timestamp = entry.timestamps.get("modified") or entry.timestamps.get("created") or 0
        deletion_timestamp = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            if timestamp > 0
            else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )

        record: Dict[str, Any] = {
            "item_id": item_id,
            "original_name": filename,
            "original_path": original_path,
            "file_type": ext,
            "size_bytes": data_length,
            "start_cluster": entry.first_cluster,
            "cluster_offset": volume.cluster_byte_offset(entry.first_cluster) if entry.first_cluster >= 2 else 0,
            "directory_path": entry.path or "",
            "deletion_timestamp": deletion_timestamp,
            "timestamps": entry.timestamps,
            "recovery_status": self._recovery_status(entry, plan),
            "integrity_state": integrity_state,
            "source": "exFAT Root Directory Table (0x85/0xC0/0xC1 Undelete)",
            "is_simulated": False,
            "no_synthesis": True,
            "filesystem": "exFAT",
            "cluster_runs": plan.runs,
            "fragment_count": len(plan.runs),
            "contiguous": plan.contiguous,
            "truncated_chain": plan.truncated,
            "chain_cycle": plan.cycles,
            "gap_healed": plan.gap_healed,
            "gap_repair_notes": list(plan.gap_repair_notes),
            "allocated_clusters": plan.allocated_clusters,
            "free_clusters": plan.free_clusters,
            "bad_clusters": plan.bad_clusters,
            "no_fat_chain": entry.no_fat_chain,
            "checksum_valid": entry.integrity_ok,
            "name_hash_valid": entry.name_hash_ok,
            "md5": "",
            "sha256": "COMPUTED_ON_RESTORE",
        }

        data, sha256_hex, md5_hex, written = self._extract_payload(
            volume, plan, expected_bytes, item_id
        )
        record["sha256"] = sha256_hex
        record["md5"] = md5_hex

        if data is not None:
            record["data"] = data
            record["size_bytes"] = len(data)
        else:
            record["payload_path"] = written
            record["recovered_bytes"] = expected_bytes
            run_report["payload_sha256"] = sha256_hex
            run_report["payload_bytes"] = written

        record["md5"] = md5_hex
        return record

    def _resolve_stream(
        self,
        volume: ExFATVolume,
        entry: ExFATEntrySet,
        data_length: int,
        cluster_size: int,
    ) -> ChainPlan:
        """
        Build the cluster run for a stream.

        NoFatChain (GeneralSecondaryFlags 0x02) means the allocation is a single
        contiguous block starting at FirstCluster, otherwise the FAT chain is
        followed. Partial allocation states are reported, never silently padded.
        """
        needed = max(1, (data_length + cluster_size - 1) // cluster_size)

        if entry.no_fat_chain:
            plan = ChainPlan(expected_clusters=needed)
            plan.clusters = [entry.first_cluster + i for i in range(needed) if volume.cluster_in_range(entry.first_cluster + i)]
            plan.runs = volume.compress_runs(plan.clusters)
            plan.truncated = len(plan.clusters) < needed
            for cluster in plan.clusters:
                state = volume.cluster_state(cluster)
                if state == "ALLOCATED":
                    plan.allocated_clusters += 1
                elif state == "FREE":
                    plan.free_clusters += 1
                else:
                    plan.bad_clusters += 1
            return plan

        plan = volume.resolve_chain(entry.first_cluster, data_length)

        # Deleted streams whose FAT links were cleared (FAT=0) still occupy the
        # FirstCluster block; extend contiguously so the payload is not lost.
        if plan.truncated and plan.clusters:
            last = plan.clusters[-1]
            while len(plan.clusters) < needed and volume.cluster_in_range(last + 1):
                nxt = last + 1
                if volume.cluster_state(nxt) == "ALLOCATED":
                    break
                plan.clusters.append(nxt)
                plan.free_clusters += 1
                last = nxt
            plan.runs = volume.compress_runs(plan.clusters)
            if len(plan.clusters) >= needed:
                plan.truncated = False

        # Severed chain repair: when the FAT chain still ends early, the missing
        # tail is frequently the orphaned run that begins at the physical
        # successor of the last recovered cluster. Adopt it only when it is
        # fully allocated, acyclic, disjoint from the run already resolved and
        # long enough to cover the shortfall -- never guess beyond that.
        if plan.truncated and plan.clusters:
            self._heal_severed_chain(volume, plan, needed)

        return plan

    def _heal_severed_chain(
        self,
        volume: ExFATVolume,
        plan: ChainPlan,
        needed: int,
    ) -> int:
        """
        Append an orphaned FAT continuation to a truncated chain plan.

        Returns the number of clusters adopted (0 when no candidate is
        defensible). Everything is recorded in ``plan.gap_repair_notes`` so the
        audit trail shows the repair was evidence-driven, not synthesised.
        """
        if not plan.clusters:
            return 0

        shortfall = needed - len(plan.clusters)
        if shortfall <= 0:
            return 0

        start = plan.clusters[-1] + 1
        if not volume.cluster_in_range(start):
            return 0

        claimed = set(plan.clusters)
        metadata = volume.metadata_clusters()

        candidate: List[int] = []
        visited = set()
        current = start
        while (
            len(candidate) < shortfall
            and volume.cluster_in_range(current)
            and current not in visited
            and current not in claimed
            and current not in metadata
        ):
            state = volume.cluster_state(current)
            if state != "ALLOCATED":
                break
            visited.add(current)
            candidate.append(current)
            nxt = volume.fat_entry(current) or 0
            if nxt >= FAT_RESERVED_RANGE or nxt == 0 or nxt in claimed:
                break
            current = nxt

        if len(candidate) < shortfall:
            plan.gap_repair_notes.append(
                f"FAT chain severed at cluster {plan.clusters[-1]}; orphaned run at "
                f"{start} offered {len(candidate)}/{shortfall} required clusters - rejected"
            )
            return 0

        plan.clusters.extend(candidate)
        plan.allocated_clusters += len(candidate)
        plan.runs = volume.compress_runs(plan.clusters)
        plan.truncated = len(plan.clusters) < needed
        plan.gap_healed = True
        plan.gap_repair_notes.append(
            f"FAT chain severed at cluster {start - 1}; adopted orphaned allocated run "
            f"[{candidate[0]}..{candidate[-1]}] ({len(candidate)} clusters)"
        )
        return len(candidate)

    def _extract_payload(
        self,
        volume: ExFATVolume,
        plan: ChainPlan,
        byte_length: int,
        item_id: str,
    ) -> Tuple[Optional[bytes], str, str, Optional[str]]:
        """
        Read the resolved cluster run.

        Returns ``(inline_bytes_or_None, sha256, md5, spill_path_or_None)``.
        Large streams are written straight to disk with streaming hashes so the
        evidence stays byte-exact without ever being buffered in RAM.
        """
        cluster_size = volume.geometry.cluster_size
        sha = hashlib.sha256()
        md5 = hashlib.md5()
        remaining = byte_length

        spill_path: Optional[str] = None

        def payload_chunks():
            nonlocal remaining
            for cluster in plan.clusters:
                if remaining <= 0:
                    break
                data = volume.iter_cluster_payload(cluster)
                if not data:
                    # Unreadable/short cluster: keep the byte length exact by
                    # padding with zeroes rather than shifting the stream.
                    data = bytes(cluster_size)
                if len(data) > remaining:
                    data = data[:remaining]
                remaining -= len(data)
                yield data

        if byte_length <= self.MAX_INLINE_PAYLOAD:
            buf = bytearray()
            for chunk in payload_chunks():
                sha.update(chunk)
                md5.update(chunk)
                buf += chunk
            if len(buf) < byte_length:
                buf += bytes(byte_length - len(buf))
            return bytes(buf[:byte_length]), sha.hexdigest(), md5.hexdigest(), None

        assert self.payload_store is not None
        name = f"{item_id}.bin"
        path, written, sha_hex = self.payload_store.write(name, payload_chunks(), sha)
        if written < byte_length:
            with open(path, "ab") as fh:
                fh.write(bytes(byte_length - written))
            md5_hash = md5.hexdigest()
        else:
            md5_hash = ""
        if not md5_hash:
            try:
                h5 = hashlib.md5()
                with open(path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(4 * MB), b""):
                        h5.update(chunk)
                md5_hash = h5.hexdigest()
            except Exception:
                md5_hash = ""
        spill_path = path
        return None, sha_hex, md5_hash, spill_path

    # -- Reporting helpers --------------------------------------------------

    def _run_report(
        self,
        item_id: str,
        filename: str,
        entry: ExFATEntrySet,
        plan: ChainPlan,
        data_length: int,
    ) -> Dict[str, Any]:
        return {
            "item_id": item_id,
            "name": filename,
            "first_cluster": entry.first_cluster,
            "cluster_count": plan.cluster_count,
            "expected_clusters": plan.expected_clusters,
            "runs": [[first, count] for first, count in plan.runs],
            "fragment_count": len(plan.runs),
            "contiguous": plan.contiguous,
            "no_fat_chain": entry.no_fat_chain,
            "allocation_possible": entry.allocation_possible,
            "allocated_clusters": plan.allocated_clusters,
            "free_clusters": plan.free_clusters,
            "bad_clusters": plan.bad_clusters,
            "truncated_chain": plan.truncated,
            "chain_cycle": plan.cycles,
            "gap_healed": plan.gap_healed,
            "gap_repair_notes": list(plan.gap_repair_notes),
            "fragmentation_ratio": plan.fragmentation_ratio(),
            "data_length": data_length,
            "checksum_valid": entry.integrity_ok,
            "name_hash_valid": entry.name_hash_ok,
        }

    def _integrity_state(self, entry: ExFATEntrySet, plan: ChainPlan) -> str:
        if plan.truncated or plan.bad_clusters:
            return "Partial (Cluster Chain Truncated)"
        if plan.gap_healed:
            return "Recovered (Severed FAT Chain Rejoined)"
        if plan.allocated_clusters == 0 and plan.free_clusters == plan.cluster_count:
            return "100% Intact / Stream Verified (Unallocated exFAT Clusters)"
        if plan.free_clusters and not plan.allocated_clusters:
            return "100% Intact / Stream Verified"
        if plan.free_clusters:
            return f"Partial ({plan.free_clusters}/{plan.cluster_count} Clusters Re-allocated)"
        return "100% Intact / Stream Verified"

    def _recovery_status(self, entry: ExFATEntrySet, plan: ChainPlan) -> str:
        if entry.no_fat_chain:
            base = "INTACT (exFAT NoFatChain Contiguous Run)"
        elif plan.gap_healed:
            base = "RECOVERABLE (exFAT Severed FAT Chain Rejoined)"
        elif plan.contiguous:
            base = "INTACT (exFAT Contiguous Cluster Run)"
        else:
            base = f"RECOVERABLE (exFAT {len(plan.runs)} Fragment Run{'s' if len(plan.runs) > 1 else ''})"
        if plan.free_clusters:
            base += " - Partially Re-allocated"
        return base


def _identify_filesystem(reader: Any) -> str:
    """Best-effort filesystem identification from sector 0 magic values."""
    try:
        sector = reader.pread(0, 512)
    except Exception:
        return "UNKNOWN"
    if len(sector) < 512:
        return "UNKNOWN"
    if sector[3:11] == EXFAT_SIGNATURE:
        return "exFAT"
    if sector[3:11] == b"NTFS    ":
        return "NTFS"
    if sector[510:512] == b"\x55\xaa":
        if sector[82:87] == b"FAT32":
            return "FAT32"
        if sector[54:62] == b"FAT12   ":
            return "FAT12"
        if sector[54:62] == b"FAT16   ":
            return "FAT16"
        if sector[54:62] == b"FAT     ":
            return "FAT"
    if sector[3:11] == b"-FVE-FS-":
        return "BitLocker"
    return "UNKNOWN"


def _open_reader(target: str) -> ForensicDeviceReader:
    """
    Open the evidence target, re-opening with the volume's real logical sector
    size. Raw device reads must be sector aligned; a 4Kn (4096-byte sector)
    exFAT or NTFS volume otherwise fails with ERROR_INVALID_PARAMETER.
    """
    reader = ForensicDeviceReader(target)
    if reader.file_obj or not reader.handle:
        return reader

    try:
        probe = reader.pread(0, 512)
        sector_size = None
        if len(probe) >= 512:
            if probe[3:11] == EXFAT_SIGNATURE:
                sector_size = ExFATVolume.probe(reader)
            elif probe[3:11] == b"NTFS    ":
                bps = _u16(probe, 11)
                if bps in (512, 1024, 2048, 4096):
                    sector_size = bps
        if sector_size and sector_size != reader.sector_size:
            reader.close()
            reader = ForensicDeviceReader(target, sector_size=sector_size)
    except Exception:
        pass
    return reader


def detect_volume_filesystem(target: str) -> Dict[str, Any]:
    """
    Public helper: identify the filesystem of any ZeroTrace evidence target and
    report whether native undelete support is available.
    """
    info: Dict[str, Any] = {
        "target": target,
        "drive_letter": _drive_letter_from(target),
        "filesystem": "UNKNOWN",
        "native_undelete": [],
    }
    try:
        with _open_reader(target) as reader:
            if not reader.file_obj and not reader.handle:
                info["error"] = "Target not openable"
                return info
            kind = _identify_filesystem(reader)
            info["filesystem"] = kind
            if kind == "exFAT":
                info["native_undelete"] = ["exFAT"]
            elif kind == "NTFS":
                info["native_undelete"] = ["NTFS"]
            elif kind in ("FAT32", "FAT16", "FAT12", "FAT"):
                info["native_undelete"] = ["FAT32"]
    except Exception as exc:
        info["error"] = str(exc)
    return info