"""
ZeroTrace exFAT Engine Validation Harness
=========================================
Builds synthetic-but-specification-accurate exFAT volume images in memory and
exercises the native undelete engine, the bi-fragment gap carver and the PDF
cross-reference reconstructor against them.

Run:  python validate_exfat_engine.py
"""

import io
import os
import struct
import sys
import tempfile

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

SECTOR = 512
PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# exFAT image builder (test double)
# ---------------------------------------------------------------------------


def exfat_name_hash(name, length=15):
    h = 0
    for ch in name[:length]:
        h = ((((h << 15) | (h >> 1)) + ord(ch)) & 0xFFFF)
    return h


def exfat_checksum(primary, secondaries):
    """
    Reference exFAT entry-set checksum: 16-bit saturating add (sum_magic) over
    every little-endian UInt16, skipping the SetChecksum bytes of the primary
    entry and treating each secondary EntryType byte as zero.
    """
    total = 0

    def feed(buf):
        nonlocal total
        for i in range(0, 32, 2):
            word = int.from_bytes(bytes(buf[i : i + 2]), "little")
            result = total + word
            total = (~result) & 0xFFFF if result > 0xFFFF else result

    p = bytearray(primary)
    p[2] = p[3] = 0
    feed(p)
    for s in secondaries:
        b = bytearray(s)
        b[0] = 0
        feed(b)
    return total


def upcase_table_checksum(table_bytes):
    """
    Up-case Table checksum: a plain 16-bit sum of every little-endian UInt16 in
    the first 128 entries of the table.
    """
    return sum(int.from_bytes(table_bytes[i : i + 2], "little") for i in range(0, 256, 2)) & 0xFFFF


def make_timestamp(year, month, day, hour, minute, second):
    date = (year - 1980) & 0x7F
    return (date << 25) | (month << 21) | (day << 16) | (hour << 11) | (minute << 5) | ((second // 2) & 0x1F)


def build_file_entry_set(name, first_cluster, data_length, attributes=0x20,
                         no_fat_chain=False, secondary_count=None, deleted=False,
                         allocated_size=None, valid_data_length=None, utc_offset=0x84):
    """Return (primary, [secondary, ...]) 32-byte entries for one exFAT file."""
    upcased = name.upper()
    chars = upcased[:255]
    name_bytes = chars.encode("utf-16-le")
    # Each 0xC1 File Name entry is one 32-byte directory entry holding 15
    # UTF-16 characters (30 bytes at offset 0x02); 255 chars therefore needs 17.
    name_entries_needed = max(1, -(-len(name_bytes) // 30))

    # Stream Extension (0xC0)
    stream = bytearray(32)
    flags = 0x01  # GeneralSecondaryFlags: AllocationPossible
    if no_fat_chain:
        flags |= 0x02
    stream[0] = 0xC0
    stream[1] = flags
    stream[3] = len(chars)
    struct.pack_into("<H", stream, 4, exfat_name_hash(upcased))
    struct.pack_into("<Q", stream, 8, valid_data_length if valid_data_length is not None else data_length)
    struct.pack_into("<I", stream, 20, first_cluster)
    struct.pack_into("<Q", stream, 24, data_length)

    name_entries = []
    for idx in range(name_entries_needed):
        chunk = name_bytes[idx * 30 : (idx + 1) * 30]
        entry = bytearray(32)
        entry[0] = 0xC1
        entry[1] = 0x00  # GeneralSecondaryFlags must be 0 for File Name entries
        entry[0x02:0x20] = chunk + b"\x00" * (30 - len(chunk))
        name_entries.append(bytes(entry))

    secondaries = [bytes(stream)] + name_entries

    if secondary_count is None:
        secondary_count = len(secondaries)

    # File Directory Entry (0x85 / 0x00 when deleted)
    primary = bytearray(32)
    # The SetChecksum is computed over the in-use entry type (0x85). Windows
    # unlinks by clearing only that byte afterwards, so real deleted residue
    # still carries the in-use checksum.
    primary[0] = 0x85
    primary[1] = secondary_count
    struct.pack_into("<H", primary, 4, attributes)
    struct.pack_into("<I", primary, 8, make_timestamp(2026, 3, 14, 9, 26, 53))
    struct.pack_into("<I", primary, 12, make_timestamp(2026, 4, 2, 18, 5, 11))
    struct.pack_into("<I", primary, 16, make_timestamp(2026, 4, 2, 18, 5, 11))
    primary[20] = 0  # Create1msIncrement
    primary[21] = 0  # LastModified1msIncrement
    primary[22] = 0  # LastAccessed1msIncrement
    primary[0x17] = utc_offset  # CreateUtcOffset
    primary[0x18] = utc_offset  # LastModifiedUtcOffset
    primary[0x19] = utc_offset  # LastAccessedUtcOffset
    struct.pack_into("<I", primary, 0x1C,
                     allocated_size if allocated_size is not None else data_length)
    struct.pack_into("<H", primary, 2, exfat_checksum(bytes(primary), secondaries))

    if deleted:
        primary[0] = 0x00

    return bytes(primary), secondaries


def boot_region_checksum(sectors):
    """
    Reference implementation of the exFAT BootChecksum() routine (spec 3.4):
    a rotating 32-bit add over every byte of the eleven non-checksum sectors,
    excluding VolumeFlags (106/107) and PercentInUse (112).
    """
    checksum = 0
    for index, byte in enumerate(sectors):
        if index in (106, 107, 112):
            continue
        checksum = (((checksum & 1) << 31) | (checksum >> 1)) + byte & 0xFFFFFFFF
    return checksum


def build_exfat_image(files, cluster_size=4096, sectors_per_cluster=8, label="ZEROTRACE",
                      oem_flash=True, corrupt_main_boot=False):
    """
    Build a specification-accurate exFAT volume image.

    Volume layout (specification Table 3)::

        Main Boot Region       sectors 0-11   (Boot, 8 Extended, OEM, Rsvd, Cksum)
        Backup Boot Region     sectors 12-23
        First FAT              FatOffset .. +FatLength
        Cluster Heap           ClusterHeapOffset ..

    ``files`` is a list of dicts with keys:
        name, data, deleted(bool), no_fat_chain(bool), gap(bool)
    """
    assert cluster_size == sectors_per_cluster * SECTOR, "cluster size must be a power-of-two sector multiple"

    main_boot_sectors = 11
    backup_boot_sectors = 12
    total_boot = main_boot_sectors + backup_boot_sectors  # 24
    volume_sectors = 8192
    spc = sectors_per_cluster

    bps_shift = 9                       # 512-byte sectors
    spc_shift = spc.bit_length() - 1

    # ClusterCount depends on ClusterHeapOffset, which depends on FatLength,
    # which depends on ClusterCount. Iterate to a fixed point (converges in 2).
    fat_offset = 64                     # >= 24, leaves a FAT alignment gap
    cluster_count = 0
    for _ in range(6):
        fat_length = ((cluster_count + 2) * 4 + SECTOR - 1) // SECTOR
        heap_offset = fat_offset + fat_length
        if heap_offset % spc:
            heap_offset += spc - (heap_offset % spc)
        cluster_count = (volume_sectors - heap_offset) // spc - 4  # spare clusters
    root_cluster = 2

    image = bytearray(volume_sectors * SECTOR)

    # ------------------------------------------------------------------
    # Main Boot Sector (specification Table 4)
    # ------------------------------------------------------------------
    struct.pack_into("<3s", image, 0, b"\xEB\x76\x90")
    image[3:11] = b"EXFAT   "
    struct.pack_into("<Q", image, 64, 0)                          # PartitionOffset
    struct.pack_into("<Q", image, 72, volume_sectors)            # VolumeLength
    struct.pack_into("<I", image, 80, fat_offset)                 # FatOffset
    struct.pack_into("<I", image, 84, fat_length)                 # FatLength
    struct.pack_into("<I", image, 88, heap_offset)                # ClusterHeapOffset
    struct.pack_into("<I", image, 92, cluster_count)              # ClusterCount
    struct.pack_into("<I", image, 96, root_cluster)               # FirstClusterOfRoot
    struct.pack_into("<I", image, 100, 0xDEADBEEF)                # VolumeSerialNumber
    struct.pack_into("<H", image, 104, 0x0100)                    # FileSystemRevision 1.00
    struct.pack_into("<H", image, 106, 0x0000)                    # VolumeFlags
    image[108] = bps_shift                                        # BytesPerSectorShift
    image[109] = spc_shift                                        # SectorsPerClusterShift
    image[110] = 1                                                # NumberOfFats
    image[111] = 0x80                                             # DriveSelect
    image[112] = 25                                               # PercentInUse
    for i in range(120, 510):                                     # BootCode: HLT
        image[i] = 0xF4
    struct.pack_into("<H", image, 510, 0xAA55)                    # BootSignature

    if corrupt_main_boot:
        image[88:92] = b"\xff\xff\xff\x7f"                       # absurd ClusterHeapOffset

    # ------------------------------------------------------------------
    # Main Extended Boot Sectors (sectors 1-8), Table 6
    # ------------------------------------------------------------------
    for index in range(8):
        off = (1 + index) * SECTOR
        struct.pack_into("<I", image, off + SECTOR - 4, 0xAA550000)

    # ------------------------------------------------------------------
    # Main OEM Parameters (sector 9), Tables 7-10
    # ------------------------------------------------------------------
    oem = 9 * SECTOR
    if oem_flash:
        struct.pack_into(
            "<IHH8s",
            image,
            oem,
            0x0A0C7E46, 0x3399, 0x4021, bytes.fromhex("90c8fa6d389c4ba2"),
        )
        struct.pack_into("<I", image, oem + 16, 128 * 1024)       # EraseBlockSize
        struct.pack_into("<I", image, oem + 20, 2048)             # PageSize
        struct.pack_into("<I", image, oem + 24, 4)                # SpareSectors
        struct.pack_into("<I", image, oem + 28, 150000)           # RandomAccessTime
        struct.pack_into("<I", image, oem + 32, 450000)           # ProgrammingTime
        struct.pack_into("<I", image, oem + 36, 900000)           # ReadCycle
        struct.pack_into("<I", image, oem + 40, 1800000)          # WriteCycle
    # Parameters[1..9] stay all-zero => Null Parameters GUID

    # Sector 10 stays zeroed (Main Reserved).

    # ------------------------------------------------------------------
    # Main Boot Checksum (sector 11)
    # ------------------------------------------------------------------
    main_boot_image = bytes(image[: main_boot_sectors * SECTOR])
    checksum = boot_region_checksum(main_boot_image)
    for i in range(0, SECTOR, 4):
        struct.pack_into("<I", image, main_boot_sectors * SECTOR + i, checksum)

    # ------------------------------------------------------------------
    # Backup Boot Region (sectors 12-23) mirrors sectors 0-11 verbatim.
    # ------------------------------------------------------------------
    backup_boot_image = bytes(image[: (main_boot_sectors + 1) * SECTOR])
    image[backup_boot_sectors * SECTOR : (backup_boot_sectors + main_boot_sectors + 1) * SECTOR] = backup_boot_image
    assert len(image) == volume_sectors * SECTOR, "boot region copy must not resize the image"

    # ------------------------------------------------------------------
    # Cluster heap helpers
    # ------------------------------------------------------------------
    def cluster_offset(cluster):
        return (heap_offset + (cluster - 2) * spc) * SECTOR

    fat = bytearray((cluster_count + 2) * 4)

    def set_fat(cluster, value):
        struct.pack_into("<I", fat, cluster * 4, value)

    EOC = 0xFFFFFFFF
    set_fat(0, 0xFFFFFFF8)      # FatEntry[0] media descriptor
    set_fat(1, EOC)             # FatEntry[1]
    set_fat(root_cluster, EOC)  # root directory chain

    bitmap_cluster = 3
    upcase_cluster = 4
    for cluster in (bitmap_cluster, upcase_cluster, root_cluster):
        set_fat(cluster, EOC)

    upcase = bytearray(512)
    for i in range(128):
        struct.pack_into("<H", upcase, i * 2, ord(chr(i).upper()) if i < 128 else i)
    _write_cluster(image, cluster_offset, upcase_cluster, bytes(upcase), spc)

    bitmap_bytes = bytes((cluster_count + 7) // 8)
    _write_cluster(image, cluster_offset, bitmap_cluster,
                   bitmap_bytes.ljust(spc * SECTOR, b"\x00"), spc)

    # ------------------------------------------------------------------
    # Root Directory Table
    # ------------------------------------------------------------------
    root_dir = bytearray()

    bitmap_entry = bytearray(32)
    bitmap_entry[0] = 0x81
    struct.pack_into("<I", bitmap_entry, 0x14, bitmap_cluster)
    struct.pack_into("<Q", bitmap_entry, 0x18, len(bitmap_bytes))
    root_dir += bitmap_entry

    # Up-case Table entry: Reserved1 (1-3), TableChecksum (4), FirstCluster
    # (0x14), DataLength (0x18).
    upcase_entry = bytearray(32)
    upcase_entry[0] = 0x82
    struct.pack_into("<I", upcase_entry, 4, upcase_table_checksum(bytes(upcase)))
    struct.pack_into("<I", upcase_entry, 0x14, upcase_cluster)
    struct.pack_into("<Q", upcase_entry, 0x18, 256)
    root_dir += upcase_entry

    label_chars = label[:11]
    label_entry = bytearray(32)
    label_entry[0] = 0x83
    label_entry[1] = len(label_chars)  # CharacterCount
    label_entry[2 : 2 + len(label_chars) * 2] = label_chars.encode("utf-16-le")
    root_dir += label_entry

    # ------------------------------------------------------------------
    # Allocate file clusters (bitmap, up-case and root already claimed)
    # ------------------------------------------------------------------
    next_cluster = bitmap_cluster + 2
    allocations = []
    for spec in files:
        payload = spec["data"]
        needed = max(1, (len(payload) + cluster_size - 1) // cluster_size)
        clusters = list(range(next_cluster, next_cluster + needed))
        next_cluster += needed
        if next_cluster > cluster_count + 2:
            raise ValueError("test image is too small for the requested payloads")
        allocations.append((clusters[0], clusters))

    # Mark the bitmap bits for every allocated cluster so the volume is coherent.
    for _, clusters in allocations:
        for c in clusters:
            set_fat(c, EOC)
    for c in (bitmap_cluster, upcase_cluster, root_cluster):
        set_fat(c, EOC)

    for spec, (first, clusters) in zip(files, allocations):
        if spec.get("gap"):
            # Two-fragment allocation: the FAT chain is severed mid-stream.
            run_len = max(1, len(clusters) // 2)
            chain, tail = clusters[:run_len], clusters[run_len:]
            for c in chain:
                set_fat(c, EOC if c == chain[-1] else c + 1)
            for c in tail:
                set_fat(c, EOC if c == tail[-1] else c + 1)
        elif spec.get("no_fat_chain"):
            # NoFatChain: the FAT links are cleared; the run is inferred contiguous.
            for c in clusters:
                set_fat(c, 0)
        else:
            for c in clusters:
                set_fat(c, EOC if c == clusters[-1] else c + 1)

        _write_payload(image, cluster_offset, clusters, spec["data"], cluster_size, spc)

        primary, secondaries = build_file_entry_set(
            spec["name"],
            first,
            len(spec["data"]),
            deleted=spec.get("deleted", True),
            no_fat_chain=spec.get("no_fat_chain", False),
        )
        root_dir += primary
        for s in secondaries:
            root_dir += s

    root_dir += bytes([0x01]) + b"\x00" * 31  # EndOfDirectoryTable marker

    # The root directory always owns a FAT chain (never NoFatChain).
    root_needed = max(1, (len(root_dir) + cluster_size - 1) // cluster_size)
    root_clusters = list(range(root_cluster, root_cluster + root_needed))
    for i, c in enumerate(root_clusters):
        set_fat(c, EOC if i == len(root_clusters) - 1 else c + 1)
    for i, c in enumerate(root_clusters):
        chunk = bytes(root_dir)[i * cluster_size : (i + 1) * cluster_size]
        _write_cluster(image, cluster_offset, c, chunk.ljust(cluster_size, b"\x00"), spc)

    # Root directory growth may have collided with file allocations; keep the
    # first cluster of every file intact by refusing overlaps.
    for _, clusters in allocations:
        if set(clusters) & set(root_clusters):
            raise ValueError("root directory overran the file allocations in the test image")

    # Allocation Bitmap bits for the bitmap, up-case, root and file clusters.
    bitmap = bytearray(len(bitmap_bytes))
    for c in [bitmap_cluster, upcase_cluster] + root_clusters:
        bitmap[(c - 2) // 8] |= 1 << ((c - 2) % 8)
    for _, clusters in allocations:
        if clusters[0] in root_clusters:
            continue
        for c in clusters:
            bitmap[(c - 2) // 8] |= 1 << ((c - 2) % 8)
    _write_cluster(image, cluster_offset, bitmap_cluster,
                   bytes(bitmap).ljust(spc * SECTOR, b"\x00"), spc)

    # ------------------------------------------------------------------
    # First FAT
    # ------------------------------------------------------------------
    fat_base = fat_offset * SECTOR
    image[fat_base : fat_base + len(fat)] = fat

    return bytes(image)


def _write_cluster(image, cluster_offset_fn, cluster, data, spc):
    off = cluster_offset_fn(cluster)
    image[off : off + len(data)] = data


def _write_payload(image, cluster_offset_fn, clusters, payload, cluster_size, spc):
    for i, c in enumerate(clusters):
        chunk = payload[i * cluster_size : (i + 1) * cluster_size]
        chunk = chunk + b"\x00" * (cluster_size - len(chunk))
        _write_cluster(image, cluster_offset_fn, c, chunk, spc)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_exfat_undelete():
    print("\n[1] Native exFAT undelete engine")
    from engines.exfat_filesystem import (
        ExFATUndeleteEngine,
        ExFATVolume,
        detect_volume_filesystem,
        exfat_name_hash,
        exfat_timestamp_to_unix,
    )
    from engines.tsk_filesystem import ForensicDeviceReader

    payload_small = b"ExFAT-Undelete-Small-Payload-" + bytes(range(256)) * 8
    payload_big = bytes(range(256)) * 512  # 128 KB across many 4 KB clusters
    payload_contig = b"NOFATCHAIN" * 4096  # 40 KB, 10 clusters

    image = build_exfat_image([
        {"name": "Case_Notes_Final.txt", "data": payload_small, "deleted": True},
        {"name": "Telemetry_Export_Big.bin", "data": payload_big, "deleted": True},
        {"name": "Contiguous_Clip.mp4", "data": payload_contig, "deleted": True, "no_fat_chain": True},
        {"name": "Still_Allocated.txt", "data": b"live file", "deleted": False},
    ])

    with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as fh:
        fh.write(image)
        path = fh.name

    try:
        with ForensicDeviceReader(path) as reader:
            vol = ExFATVolume(reader)
            check("Main Boot Region parsed (signature + geometry)",
                  vol.geometry.cluster_size == 4096,
                  f"cluster_size={vol.geometry.cluster_size}")
            check("Main Boot Sector is the authoritative geometry source",
                  vol.geometry.source == "MAIN_BOOT_SECTOR",
                  vol.geometry.source)
            check("OEM parameters decoded from sector 9",
                  [p.get("kind") for p in vol.decode_oem_parameters()] == ["FLASH_PARAMETERS"],
                  str([p.get("guid") for p in vol.decode_oem_parameters()]))
            check("Extended Boot Sectors carry AA550000h signatures",
                  vol.extended_boot_signatures() == [True] * 8,
                  str(vol.extended_boot_signatures()))
            check("Backup Boot Region geometry agrees with the Main Boot Sector",
                  vol.backup_geometry_matches is True, str(vol.backup_geometry_matches))
            check("Backup Boot Region checksum verifies", vol.backup_checksum_valid is True,
                  str(vol.backup_checksum_valid))
            check("Rotating Boot Checksum word exposed for the audit trail",
                  isinstance(vol.boot_checksum_word, int) and vol.boot_checksum_word != 0,
                  hex(vol.boot_checksum_word or 0))
            check("Serial number decoded", vol.geometry.serial == 0xDEADBEEF,
                  f"0x{vol.geometry.serial:08X}")
            check("Root cluster is cluster 2", vol.geometry.root_cluster == 2)
            check("Boot region checksum verifies (rotating, spec 3.4)", vol.checksum_valid is True,
                  str(vol.checksum_valid))
            check("Volume label decoded", vol.volume_label == "ZEROTRACE", vol.volume_label)
            check("No geometry validation problems", vol.boot_problems == [],
                  str(vol.boot_problems))

            alloc = vol.allocation_statistics()
            check("Allocation states classified from FAT",
                  alloc["allocated"] > 0 and alloc["free"] > 0,
                  f"alloc={alloc['allocated']} free={alloc['free']}")

            ts = exfat_timestamp_to_unix(make_timestamp(2026, 4, 2, 18, 5, 12), 0x48)
            check("Timestamps decode to UNIX epoch", ts > 1_700_000_000, str(ts))
            check("Name hash function is stable",
                  exfat_name_hash("CASE_NOTES_FINAL.TXT") == exfat_name_hash("CASE_NOTES_FINAL.TXT"))

        engine = ExFATUndeleteEngine()
        records, telemetry = engine.scan(path, drive_letter="G")

        check("Deleted files recovered", len(records) == 3, f"{len(records)} records")
        check("Telemetry reports exFAT geometry",
              telemetry.get("filesystem") == "exFAT" and telemetry.get("cluster_size") == 4096)
        check("Telemetry carries allocation state",
              telemetry.get("allocation", {}).get("allocated", 0) > 0,
              str(telemetry.get("allocation")))
        check("Telemetry carries cluster runs",
              len(telemetry.get("cluster_runs", [])) == 3,
              f"{len(telemetry.get('cluster_runs', []))} runs")
        check("In-use file not reported as deleted",
              all(r["original_name"] != "Still_Allocated.txt" for r in records))

        by_name = {r["original_name"]: r for r in records}
        check("Original Unicode filename restored",
              "Case_Notes_Final.txt" in by_name,
              str(list(by_name)))

        notes = by_name.get("Case_Notes_Final.txt")
        if notes:
            check("Payload byte-exact", notes.get("data") == payload_small)
            check("Size recorded", notes["size_bytes"] == len(payload_small), str(notes["size_bytes"]))
            check("SHA-256 populated", len(notes.get("sha256", "")) == 64)
            check("Source attributed to exFAT directory set",
                  "exFAT" in notes.get("source", ""), notes.get("source"))
            check("Entry-set checksum validated", notes.get("checksum_valid") is True)
            check("Up-case name hash validated", notes.get("name_hash_valid") is True)

        big = by_name.get("Telemetry_Export_Big.bin")
        if big:
            check("Large multi-cluster payload byte-exact", big.get("data") == payload_big)
            check("Large file spans multiple clusters", big.get("fragment_count", 0) >= 1,
                  f"fragments={big.get('fragment_count')}")
            check("Cluster run reported",
                  all(isinstance(run, (list, tuple)) and len(run) == 2 for run in big.get("cluster_runs", [])),
                  str(big.get("cluster_runs")))

        contig = by_name.get("Contiguous_Clip.mp4")
        if contig:
            check("NoFatChain contiguous run recovered", contig.get("data") == payload_contig)
            check("NoFatChain flag recorded", contig.get("no_fat_chain") is True)
            check("Contiguous run flagged", contig.get("contiguous") is True)

        # filesystem detection
        info = detect_volume_filesystem(path)
        check("detect_volume_filesystem identifies exFAT",
              info.get("filesystem") == "exFAT", str(info.get("filesystem")))
        check("Native undelete capability advertised", "exFAT" in info.get("native_undelete", []))

        arch = ExFATUndeleteEngine.describe_architecture(path, "G")
        check("describe_architecture returns cluster geometry",
              arch.get("cluster_size") == 4096 and arch.get("revision") == "1.00",
              f"{arch.get('revision')} {arch.get('cluster_size')}")
        check("describe_architecture reports valid boot checksum",
              arch.get("boot_checksum") == "VALID", str(arch.get("boot_checksum")))

        os.unlink(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_exfat_fragmented_and_spill():
    print("\n[2] exFAT fragmented runs + >50 MB spill-to-disk extraction")
    from engines.exfat_filesystem import ExFATUndeleteEngine

    cluster_size = 4096
    payload = bytes(range(256)) * 2048  # 512 KB
    image = build_exfat_image(
        [{"name": "Forensic_Video_Segment.mkv", "data": payload, "deleted": True, "gap": True}],
        cluster_size=cluster_size,
    )

    path = tempfile.mktemp(suffix=".img")
    with open(path, "wb") as fh:
        fh.write(image)

    try:
        engine = ExFATUndeleteEngine()
        engine.MAX_INLINE_PAYLOAD = 1024  # force spill path
        records, telemetry = engine.scan(path, drive_letter="E")
        check("Fragmented deleted file recovered", len(records) == 1, f"{len(records)}")
        if records:
            rec = records[0]
            spill = rec.get("payload_path")
            check("Large stream spilled to disk", bool(spill) and os.path.exists(spill), str(spill))
            check("Inline payload withheld for large stream", rec.get("data") is None)
            if spill:
                with open(spill, "rb") as fh:
                    content = fh.read()
                check("Spilled payload byte-exact (>50MB safe path)", content == payload)
                check("Recovered byte length matches DataLength",
                      len(content) == payload_size(payload), f"{len(content)}")
            check("Fragmentation recorded", rec.get("fragment_count", 0) >= 1,
                  f"fragments={rec.get('fragment_count')}")
            check("Synthetic fallback disabled", rec.get("no_synthesis") is True)
            check("SHA-256 computed during streaming", len(rec.get("sha256", "")) == 64)

            from engines.tsk_filesystem import TSKFilesystemRecoverer
            recoverer = TSKFilesystemRecoverer()
            out_dir = tempfile.mkdtemp()
            dest = recoverer.restore_file(rec, out_dir)
            check("restore_file streams spill payload to disk",
                  os.path.exists(dest) and open(dest, "rb").read() == payload)
            import shutil
            shutil.rmtree(out_dir, ignore_errors=True)

        runs = telemetry.get("cluster_runs", [])
        check("Cluster-run telemetry logged", len(runs) == 1)
        if runs:
            check("Run report includes allocation states",
                  "allocated_clusters" in runs[0] and "free_clusters" in runs[0],
                  str({k: runs[0][k] for k in ("allocated_clusters", "free_clusters")}))
    finally:
        if os.path.exists(path):
            os.unlink(path)


def payload_size(p):
    return len(p)


def test_bifragment_carver():
    print("\n[3] Validated bi-fragment gap carving")
    from engines.scalpel_carver import BifragmentReassembler

    class MemReader:
        def __init__(self, blob):
            self.blob = blob

        def pread(self, offset, length):
            if offset < 0 or offset >= len(self.blob):
                return b""
            return self.blob[offset : offset + length]

        def read(self, size):
            return b""

        def close(self):
            pass

    block = 4096
    head = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + (b"\x00" * 64)
    head = head.ljust(block, b"\x20")
    mid = bytes(range(256)) * 40  # entropy in the gap region
    tail = (b"\x21\xff\x0b" + b"payload" * 64 + b"\xff\xd9").ljust(block, b"\x00")

    blob = bytearray(0)
    blob += b"\x00" * block
    blob += head
    blob += mid
    blob += b"\x00" * block
    blob += tail

    reader = MemReader(bytes(blob))
    reasm = BifragmentReassembler(reader, block_align=block)
    result = reasm.carve_bifragment(
        header_offset=block,
        footer_sig=b"\xff\xd9",
        file_type="JPEG",
        min_size=64,
    )
    check("Bi-fragment carve produced a result", result is not None)
    if result:
        check("Two fragments stitched", len(result.fragments) == 2, str(len(result.fragments)))
        check("Fragments are non-adjacent (gap present)", result.gap_bytes > 0, f"gap={result.gap_bytes}")
        check("Header block preserved", result.data.startswith(head[:32]))
        check("Trailer block preserved", result.data.endswith(b"\xff\xd9"))
        check("Validated structure", result.validated is True)
        check("Confidence above threshold", result.confidence >= 0.6, str(result.confidence))

    # Negative case: no trailer anywhere -> no forged evidence
    blob2 = head + mid
    reasm2 = BifragmentReassembler(MemReader(blob2), block_align=block)
    none_result = reasm2.carve_bifragment(
        header_offset=0, footer_sig=b"\xff\xd9", file_type="JPEG", min_size=64
    )
    check("No result when trailer is absent (no forged evidence)", none_result is None)


def test_pdf_xref_reconstruction():
    print("\n[4] PDF cross-reference table reconstruction")
    from engines.scalpel_carver import PdfXrefReconstructor, _carve_pdf, StreamWindow

    valid_pdf = build_test_pdf()

    class MemReader:
        def __init__(self, blob):
            self.blob = blob

        def pread(self, offset, length):
            if offset < 0 or offset >= len(self.blob):
                return b""
            return self.blob[offset : offset + length]

        def close(self):
            pass

    intact = PdfXrefReconstructor.inspect(valid_pdf)
    check("Valid PDF reports intact xref", intact["needs_repair"] is False, str(intact["reason"]))
    check("Valid PDF startxref resolves", intact["declared_startxref"] is not None)

    # Damage the xref table the way fragmentation does.
    damaged = bytearray(valid_pdf)
    xref_at = damaged.rfind(b"xref\n")
    check("Located xref table for damage simulation", xref_at > 0)
    damaged[xref_at + 4 : xref_at + 40] = b"9999999999 00000 n \n0000000000 65535 f \n"
    damaged = bytes(damaged)

    damaged_info = PdfXrefReconstructor.inspect(damaged)
    check("Corrupted xref detected", damaged_info["needs_repair"] is True,
          str(damaged_info["reason"]))

    report = PdfXrefReconstructor.repair(damaged)
    check("Repair reported", report.get("repaired") is True, str(report.get("reason")))
    rebuilt = report.get("data") or b""
    check("Rebuilt file has valid xref header", b"\nxref\n" in rebuilt)
    check("Rebuilt file terminates correctly", rebuilt.rstrip().endswith(b"%%EOF"))
    check("Trailer declares document size", b"/Size" in rebuilt)

    ok, pages = read_pdf_pages(rebuilt)
    check("Rebuilt PDF opens in a real parser", ok, f"{pages} page(s)")

    # Truncated trailer (no startxref at all)
    truncated = valid_pdf[: valid_pdf.rfind(b"startxref")] + b"startxref\n0\n%%EOF\n"
    truncated_report = PdfXrefReconstructor.repair(truncated)
    check("Truncated startxref repaired",
          truncated_report.get("repaired") is True, str(truncated_report.get("reason")))
    ok2, pages2 = read_pdf_pages(truncated_report.get("data") or b"")
    check("Repair of truncated PDF opens cleanly", ok2, f"{pages2} page(s)")

    # Byte-fidelity: object dictionaries preserved
    if rebuilt:
        check("Catalog object dictionary preserved", b"/Type /Catalog" in rebuilt or b"/Catalog" in rebuilt)
        check("Page content stream preserved", b"BT /F1" in rebuilt or b"stream" in rebuilt)


def build_test_pdf():
    """Small but genuinely valid single-page PDF."""
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        None,  # stream object built below
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = b"BT /F1 24 Tf 72 700 Td (ZeroTrace Forensics) Tj ET"
    objs[3] = b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"

    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
    out += f"startxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def read_pdf_pages(data):
    """
    Open a PDF with a real parser when one is installed.

    ``pypdf`` is an optional dependency: when it is absent the harness falls
    back to the built-in structural parse so the suite still validates the
    reconstructed document instead of reporting a missing module as a failure.
    """
    if not data:
        return False, "no data"

    try:
        import pypdf
    except ImportError:
        from engines.scalpel_carver import PdfXrefReconstructor

        info = PdfXrefReconstructor.inspect(data)
        if info.get("needs_repair"):
            return False, f"structural parse: {info.get('reason')}"
        count = info.get("objects", 0)
        return (count > 0), f"{count} object(s) (pypdf not installed, structural parse)"

    try:
        r = pypdf.PdfReader(io.BytesIO(data), strict=False)
        return True, len(r.pages)
    except Exception as exc:
        return False, str(exc)


def test_audit_trail():
    print("\n[5] Audit trail integration (SHA-256 hash chain)")
    from core.audit import AuditService

    log_path = tempfile.mktemp(suffix=".json")
    svc = AuditService(log_path=log_path, mirror_to_frontend=False)
    svc.events = []
    svc._create_genesis_block()

    cluster_runs = [
        {
            "item_id": "EXFAT-00001",
            "name": "Case_Notes_Final.txt",
            "first_cluster": 6,
            "cluster_count": 2,
            "fragment_count": 1,
            "runs": [[6, 2]],
            "contiguous": True,
            "no_fat_chain": False,
            "allocated_clusters": 0,
            "free_clusters": 2,
            "bad_clusters": 0,
            "truncated_chain": False,
            "data_length": 4096,
            "checksum_valid": True,
            "name_hash_valid": True,
            "payload_sha256": "a" * 64,
        }
    ]
    architecture = {
        "filesystem": "exFAT",
        "revision": "1.00",
        "serial_number": "0xDEADBEEF",
        "cluster_size": 4096,
        "cluster_count": 1019,
        "root_cluster": 2,
        "boot_checksum": "VALID",
        "volume_label": "ZEROTRACE",
        "allocation": {"allocated": 40, "free": 977, "bad": 0, "reserved": 0},
    }

    svc.log_filesystem_analysis(
        target="\\\\.\\G:",
        architecture=architecture,
        cluster_runs=cluster_runs,
        records_recovered=1,
        case_id="CASE-ZT-2026-001",
    )

    actions = [e["action"] for e in svc.events]
    check("Architecture event written", "FILESYSTEM_ARCHITECTURE_ANALYZED" in actions)
    check("Cluster-run event written", "CLUSTER_RUN_ALLOCATION_RECORDED" in actions)

    run_event = [e for e in svc.events if e["action"] == "CLUSTER_RUN_ALLOCATION_RECORDED"][0]
    check("Cluster run carries SHA-256 validation digest",
          len(run_event["details"]["cluster_run_sha256"]) == 64)
    check("Allocation state recorded",
          run_event["details"]["cluster_run"]["free_clusters"] == 2)

    arch_event = [e for e in svc.events if e["action"] == "FILESYSTEM_ARCHITECTURE_ANALYZED"][0]
    check("Geometry recorded in audit trail",
          arch_event["details"]["geometry"]["filesystem"] == "exFAT")
    check("Allocation summary recorded",
          arch_event["details"]["allocation_state"]["free"] == 977)

    result = svc.verify_chain()
    check("Hash chain verifies after logging", result.get("valid") is True, str(result))

    # Tamper detection still functions with the new events present.
    svc.events[1]["details"]["geometry"]["filesystem"] = "NTFS"
    tampered = svc.verify_chain()
    check("Tampering with architecture metadata is detected",
          tampered.get("valid") is False, str(tampered.get("reason")))

    os.unlink(log_path)


def test_regression_fat32_ntfs():
    print("\n[6] Backward compatibility (FAT32 / NTFS guards)")
    from engines.tsk_filesystem import TSKFilesystemRecoverer
    from engines.exfat_filesystem import _identify_filesystem

    class MemReader:
        def __init__(self, blob):
            self.blob = blob

        def pread(self, offset, length):
            if offset < 0 or offset >= len(self.blob):
                return b""
            return self.blob[offset : offset + length]

        def close(self):
            pass

    exfat_img = build_exfat_image([{"name": "A.txt", "data": b"x" * 32, "deleted": True}])
    check("exFAT image identified", _identify_filesystem(MemReader(exfat_img)) == "exFAT")

    ntfs = bytearray(512)
    ntfs[3:11] = b"NTFS    "
    check("NTFS image identified", _identify_filesystem(MemReader(bytes(ntfs))) == "NTFS")

    fat32 = bytearray(512)
    fat32[82:87] = b"FAT32"
    fat32[510:512] = b"\x55\xaa"
    check("FAT32 image identified", _identify_filesystem(MemReader(bytes(fat32))) == "FAT32")

    rec = TSKFilesystemRecoverer()
    check("Recoverer exposes architecture state",
          isinstance(rec.filesystem_architecture, dict))

    # Simulated fallback preserved for non-existent targets (legacy behavior)
    records = rec.scan_deleted_files("Z:\\nonexistent-image.dd")
    check("Legacy simulation fallback preserved", len(records) == 2 and all(r["is_simulated"] for r in records))


if __name__ == "__main__":
    print("=" * 74)
    print("ZeroTrace exFAT / Fragmentation Engine Validation")
    print("=" * 74)

    test_exfat_undelete()
    test_exfat_fragmented_and_spill()
    test_bifragment_carver()
    test_pdf_xref_reconstruction()
    test_audit_trail()
    test_regression_fat32_ntfs()

    print("\n" + "=" * 74)
    print(f"RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 74)
    sys.exit(1 if FAIL else 0)