"""
ZEROTrace — Unit Tests
Tests for hashing, carving, validation, classification, reconstruction,
integrity (Merkle tree, hash chain), and sanitization.
"""

import hashlib
import json
import struct
import io
import sys
import os
import zipfile

# Ensure platform and backend roots are on sys.path
_platform_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend_root = os.path.join(_platform_root, "backend")
if _platform_root not in sys.path:
    sys.path.insert(0, _platform_root)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)



# ─── Integrity Engine Tests ──────────────────────────────

def test_sha256_hashing():
    from engines.integrity import compute_sha256
    data = b"ZEROTrace test data"
    expected = hashlib.sha256(data).hexdigest()
    assert compute_sha256(data) == expected


def test_sha512_hashing():
    from engines.integrity import compute_sha512
    data = b"ZEROTrace test data"
    expected = hashlib.sha512(data).hexdigest()
    assert compute_sha512(data) == expected


def test_merkle_tree_single():
    from engines.integrity import MerkleTree
    tree = MerkleTree(["abc123"])
    assert tree.get_root() is not None
    assert len(tree.get_root()) == 64


def test_merkle_tree_multiple():
    from engines.integrity import MerkleTree
    leaves = [hashlib.sha256(f"file{i}".encode()).hexdigest() for i in range(8)]
    tree = MerkleTree(leaves)
    root = tree.get_root()
    assert root is not None
    assert len(root) == 64
    assert tree.to_dict()["leaf_count"] == 8


def test_merkle_proof():
    from engines.integrity import MerkleTree
    leaves = [hashlib.sha256(f"item{i}".encode()).hexdigest() for i in range(4)]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(0)
    assert tree.verify_proof(leaves[0], proof, tree.get_root())


def test_merkle_proof_invalid():
    from engines.integrity import MerkleTree
    leaves = [hashlib.sha256(f"item{i}".encode()).hexdigest() for i in range(4)]
    tree = MerkleTree(leaves)
    proof = tree.get_proof(0)
    assert not tree.verify_proof("badhash", proof, tree.get_root())


def test_hash_chain():
    from engines.integrity import HashChain
    chain = HashChain()
    chain.add_event({"action": "REGISTERED", "case_id": "case1"})
    chain.add_event({"action": "HASHED", "case_id": "case1"})
    chain.add_event({"action": "ANALYZED", "case_id": "case1"})
    result = chain.verify_chain()
    assert result["valid"] is True
    assert result["length"] == 3


def test_hash_chain_tamper_detection():
    from engines.integrity import HashChain
    chain = HashChain()
    chain.add_event({"action": "REGISTERED"})
    chain.add_event({"action": "HASHED"})
    # Tamper with the first event
    chain.chain[0]["event"]["action"] = "TAMPERED"
    result = chain.verify_chain()
    assert result["valid"] is False


# ─── Carving Engine Tests ────────────────────────────────

def _make_jpeg(width=100, height=100):
    buf = io.BytesIO()
    buf.write(b"\xFF\xD8\xFF\xE0")
    buf.write(struct.pack(">H", 16))
    buf.write(b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
    buf.write(b"\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00")
    buf.write(b"\x42" * 200)
    buf.write(b"\xFF\xD9")
    return buf.getvalue()


def _make_png():
    import zlib
    buf = io.BytesIO()
    buf.write(b"\x89PNG\r\n\x1a\n")
    ihdr = struct.pack(">II", 10, 10) + b"\x08\x02\x00\x00\x00"
    crc = zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF
    buf.write(struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + struct.pack(">I", crc))
    raw = (b"\x00" + b"\xFF" * 30) * 10
    compressed = zlib.compress(raw)
    crc2 = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    buf.write(struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", crc2))
    crc3 = zlib.crc32(b"IEND") & 0xFFFFFFFF
    buf.write(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", crc3))
    return buf.getvalue()


def _make_pdf():
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"2 0 obj\n<< /Length 0 >>\nstream\nendstream\nendobj\n"
        b"%%EOF"
    )


def test_carving_jpeg():
    from engines.carving import BlockScanner, get_signature_registry
    jpeg = _make_jpeg()
    data = b"\x00" * 512 + jpeg + b"\x00" * 512
    scanner = BlockScanner(get_signature_registry())
    candidates = scanner.scan(data, base_offset=0, file_types=["JPEG"])
    assert len(candidates) >= 1
    assert candidates[0].file_type == "JPEG"
    assert candidates[0].offset == 512


def test_carving_png():
    from engines.carving import BlockScanner, get_signature_registry
    png = _make_png()
    data = b"\x00" * 1024 + png + b"\x00" * 512
    scanner = BlockScanner(get_signature_registry())
    candidates = scanner.scan(data, base_offset=0, file_types=["PNG"])
    assert len(candidates) >= 1
    assert candidates[0].file_type == "PNG"


def test_carving_pdf():
    from engines.carving import BlockScanner, get_signature_registry
    pdf = _make_pdf()
    data = b"\x00" * 256 + pdf + b"\x00" * 256
    scanner = BlockScanner(get_signature_registry())
    candidates = scanner.scan(data, base_offset=0, file_types=["PDF"])
    assert len(candidates) >= 1
    assert candidates[0].file_type == "PDF"


def test_carving_multiple_types():
    from engines.carving import BlockScanner, get_signature_registry
    jpeg = _make_jpeg()
    pdf = _make_pdf()
    data = b"\x00" * 512 + jpeg + b"\x00" * 1024 + pdf + b"\x00" * 512
    scanner = BlockScanner(get_signature_registry())
    candidates = scanner.scan(data, base_offset=0)
    types = {c.file_type for c in candidates}
    assert "JPEG" in types
    assert "PDF" in types


# ─── Validation Engine Tests ─────────────────────────────

def test_validate_jpeg():
    from engines.validation import FileValidator
    jpeg = _make_jpeg()
    validator = FileValidator()
    report = validator.validate(jpeg, "JPEG")
    assert report.header_valid is True
    assert report.footer_valid is True
    assert report.sha256 != ""


def test_validate_png():
    from engines.validation import FileValidator
    png = _make_png()
    validator = FileValidator()
    report = validator.validate(png, "PNG")
    assert report.header_valid is True


def test_validate_pdf():
    from engines.validation import FileValidator
    pdf = _make_pdf()
    validator = FileValidator()
    report = validator.validate(pdf, "PDF")
    assert report.header_valid is True
    assert report.footer_valid is True


def test_validate_corrupted():
    from engines.validation import FileValidator, ValidationStatus
    validator = FileValidator()
    report = validator.validate(b"\x00" * 100, "JPEG")
    assert report.header_valid is False
    report.compute_status()
    assert report.overall_status in (ValidationStatus.CORRUPTED, ValidationStatus.UNKNOWN)


# ─── Classification Engine Tests ─────────────────────────

def test_classify_jpeg():
    from engines.classification import ClassificationEngine
    jpeg = _make_jpeg()
    engine = ClassificationEngine()
    result = engine.classify(jpeg)
    assert result.detected_type == "JPEG"
    assert result.category == "IMAGE"


def test_classify_pdf():
    from engines.classification import ClassificationEngine
    pdf = _make_pdf()
    engine = ClassificationEngine()
    result = engine.classify(pdf)
    assert result.detected_type == "PDF"
    assert result.category == "DOCUMENT"


def test_classify_extension_mismatch():
    from engines.classification import ClassificationEngine
    pdf = _make_pdf()
    engine = ClassificationEngine()
    result = engine.classify(pdf, original_filename="document.jpg")
    assert result.extension_mismatch is True


# ─── Reconstruction Engine Tests ─────────────────────────

def test_fragment_graph():
    from engines.reconstruction import FragmentGraph, Fragment
    graph = FragmentGraph()
    graph.add_fragment(Fragment(id="f1", offset=0, size=1024, data=b"\x01" * 1024, file_type_hint="JPEG"))
    graph.add_fragment(Fragment(id="f2", offset=1024, size=1024, data=b"\x02" * 1024, file_type_hint="JPEG"))
    graph.add_edge("f1", "f2", 0.85, "contiguous")
    paths = graph.find_best_paths(max_paths=3, min_fragments=2)
    assert len(paths) >= 1
    assert paths[0].fragments == ["f1", "f2"]


def test_entropy_computation():
    from engines.reconstruction import compute_entropy
    zeros = b"\x00" * 1024
    assert compute_entropy(zeros) == 0.0
    random_data = bytes(range(256)) * 4
    entropy = compute_entropy(random_data)
    assert entropy > 7.0  # High entropy for uniform distribution


# ─── Sanitization Tests ─────────────────────────────────

def test_strategy_recommender():
    from engines.sanitization import StrategyRecommender, DeviceInfo, MediaType
    recommender = StrategyRecommender()
    hdd = DeviceInfo(path="/dev/sda", name="HDD", media_type=MediaType.HDD, capacity_bytes=500_000_000_000)
    method, strategy = recommender.recommend(hdd)
    assert method == "DOD_522220M"

    ssd = DeviceInfo(path="/dev/nvme0n1", name="SSD", media_type=MediaType.SSD, capacity_bytes=256_000_000_000)
    method, strategy = recommender.recommend(ssd)
    assert method == "SECURE_ERASE_ATA"

    usb = DeviceInfo(path="/dev/sdb", name="USB", media_type=MediaType.USB, capacity_bytes=32_000_000_000)
    method, strategy = recommender.recommend(usb)
    assert method == "RANDOM_DATA"


def test_sanitization_simulation():
    from engines.sanitization import ZeroFillStrategy, DeviceInfo, MediaType
    strategy = ZeroFillStrategy()
    device = DeviceInfo(path="/dev/sdb", name="Test", media_type=MediaType.HDD, capacity_bytes=1_000_000)
    result = strategy.execute(device)
    assert result.success is True
    assert result.is_simulated is True


def test_file_eraser_preview():
    from engines.sanitization import FileEraser
    import tempfile, os
    eraser = FileEraser()
    # Create a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        path = f.name
    try:
        preview = eraser.preview(path)
        assert preview["type"] == "file"
        assert preview["files_count"] == 1
    finally:
        os.unlink(path)


# ─── Forensic Services Tests ────────────────────────────

def test_audit_service():
    from forensic import AuditService
    audit = AuditService()
    event = audit.log_event("TEST", "CREATED", case_id="case-1")
    assert event["event_type"] == "TEST"
    assert event["current_hash"] is not None
    result = audit.verify_chain()
    assert result["valid"] is True


def test_chain_of_custody():
    from forensic import ChainOfCustodyService
    custody = ChainOfCustodyService()
    custody.add_entry("case-1", "evd-1", "operator1", "REGISTERED")
    custody.add_entry("case-1", "evd-1", "operator1", "HASHED")
    chain = custody.get_chain("evd-1")
    assert len(chain) == 2
    result = custody.verify_chain("evd-1")
    assert result["valid"] is True


def test_report_generator():
    from forensic import ReportGenerator
    gen = ReportGenerator()
    report = gen.generate_forensic_report(
        case_info={"case_id": "c1", "title": "Test"},
        evidence_info={"sha256_hash": "abc"},
        recovery_results={"artifacts": [], "total_artifacts": 0, "merkle_root": ""},
        audit_events=[],
        custody_chain=[],
        format="JSON",
    )
    assert report["report_type"] == "FORENSIC"
    assert report["report_hash"] is not None


def test_sanitization_certificate():
    from forensic import ReportGenerator
    gen = ReportGenerator()
    cert = gen.generate_sanitization_certificate(
        operation={"method": "DOD_522220M", "passes_completed": 3, "is_simulated": True, "operator": "test"},
        verification={"verification_method": "random_sampling", "overall_pass": True, "sample_count": 5},
        device_info={"device_type": "HDD", "capacity_bytes": 500_000_000_000},
    )
    assert "certificate_id" in cert
    assert cert["sanitization"]["is_simulated"] is True


# ─── Demo Service Tests ─────────────────────────────────

def test_synthetic_image_generation():
    from backend.app.services.demo_service import SyntheticImageGenerator
    gen = SyntheticImageGenerator()
    image, manifest = gen.generate_test_image(size_mb=2)
    assert len(image) == 2 * 1024 * 1024
    assert len(manifest) > 0
    # Check that embedded files have correct types
    types = {m["type"] for m in manifest}
    assert "JPEG" in types


def test_synthetic_jpeg_valid():
    from backend.app.services.demo_service import SyntheticImageGenerator
    gen = SyntheticImageGenerator()
    jpeg = gen._create_synthetic_jpeg(100, 100)
    assert jpeg[:2] == b"\xFF\xD8"
    assert jpeg[-2:] == b"\xFF\xD9"


def test_synthetic_png_valid():
    from backend.app.services.demo_service import SyntheticImageGenerator
    gen = SyntheticImageGenerator()
    png = gen._create_synthetic_png(50, 50)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_synthetic_pdf_valid():
    from backend.app.services.demo_service import SyntheticImageGenerator
    gen = SyntheticImageGenerator()
    pdf = gen._create_synthetic_pdf()
    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf


# ─── Master Controller Tests ────────────────────────────

def test_chunk_generator():
    from workers.master_controller import ChunkGenerator
    gen = ChunkGenerator(chunk_size_bytes=1024, overlap_bytes=64)
    data = b"\x00" * 4096
    chunks = gen.generate_chunks(data)
    assert len(chunks) == 4
    # Verify overlap
    assert chunks[1].overlap_start > 0


def test_process_chunk_worker():
    from workers.master_controller import process_chunk_worker
    jpeg = _make_jpeg()
    data = b"\x00" * 512 + jpeg + b"\x00" * 512
    result = process_chunk_worker(data, 0, 0, ["JPEG"])
    assert result["candidates_found"] >= 1
    assert result["errors"] == []


# ─── End-to-End Pipeline Test ────────────────────────────

def test_e2e_recovery_pipeline():
    """
    End-to-end test:
    Create synthetic evidence → Hash → Carve → Recover →
    Validate → Classify → Hash → Report
    """
    from backend.app.services.demo_service import SyntheticImageGenerator
    from engines.integrity import compute_sha256, MerkleTree
    from workers.master_controller import MasterController
    from forensic import AuditService, ChainOfCustodyService, ReportGenerator

    # 1. Generate synthetic evidence
    gen = SyntheticImageGenerator()
    image, manifest = gen.generate_test_image(size_mb=2)
    assert len(manifest) > 0

    # 2. Hash evidence
    sha256 = compute_sha256(image)
    assert len(sha256) == 64

    # 3. Run recovery
    controller = MasterController(max_workers=2)
    results = controller.execute_recovery_job(
        evidence_data=image,
        evidence_id="test-evidence",
        job_id="test-job",
    )

    assert results["status"] == "COMPLETED"
    assert results["total_artifacts"] >= 0

    # 4. Build Merkle tree
    if results["total_artifacts"] > 0:
        hashes = [a["sha256"] for a in results["artifacts"] if a.get("sha256")]
        if hashes:
            tree = MerkleTree(hashes)
            assert len(tree.get_root()) == 64

    # 5. Audit chain
    audit = AuditService()
    audit.log_event("RECOVERY", "COMPLETED", evidence_id="test-evidence")
    assert audit.verify_chain()["valid"] is True

    # 6. Generate report
    report_gen = ReportGenerator()
    report = report_gen.generate_forensic_report(
        case_info={"case_id": "test", "title": "E2E Test"},
        evidence_info={"sha256_hash": sha256},
        recovery_results=results,
        audit_events=audit.get_events(),
        custody_chain=[],
    )
    assert report["report_hash"] is not None


if __name__ == "__main__":
    import traceback
    test_funcs = [
        obj for name, obj in list(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    passed = 0
    failed = 0
    print(f"Running {len(test_funcs)} ZEROTrace tests...\n")
    for fn in test_funcs:
        fn_name = fn.__name__
        try:
            fn()
            print(f"  [PASS] {fn_name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {fn_name}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)


