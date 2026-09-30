"""
ZEROTrace — Demo Service
Generates synthetic forensic images and runs the complete pipeline.
"""

import hashlib
import io
import os
import random
import secrets
import struct
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("demo")


class SyntheticImageGenerator:
    """
    Generate synthetic forensic test images containing:
    - Deleted JPEG, PNG, PDF files
    - Fragmented files
    - Corrupted files
    - Extension-mismatched files
    - Random padding/noise
    
    No real user data is used.
    """

    def generate_test_image(
        self,
        size_mb: int = 8,
        include_types: list[str] = None,
    ) -> tuple[bytes, list[dict]]:
        """
        Generate a synthetic forensic disk image.
        Returns (image_bytes, embedded_files_manifest).
        """
        if include_types is None:
            include_types = ["JPEG", "PNG", "PDF", "ZIP", "GIF"]

        image_size = size_mb * 1024 * 1024
        image = bytearray(image_size)
        manifest = []

        # Fill with pseudo-random data (simulates used disk)
        for i in range(0, image_size, 4096):
            chunk_size = min(4096, image_size - i)
            if random.random() < 0.3:
                # Some sectors are zeroed (simulates unused space)
                image[i : i + chunk_size] = b"\x00" * chunk_size
            else:
                image[i : i + chunk_size] = secrets.token_bytes(chunk_size)

        offset = 4096  # Start after "boot sector"

        # ── Embed synthetic files ─────────────────────

        if "JPEG" in include_types:
            jpeg_data = self._create_synthetic_jpeg(640, 480)
            offset = self._embed_file(image, offset, jpeg_data, "normal")
            manifest.append({
                "type": "JPEG",
                "offset": offset - len(jpeg_data),
                "size": len(jpeg_data),
                "state": "normal",
                "description": "Normal JPEG image",
            })

            # Deleted JPEG (overwritten directory entry but data intact)
            jpeg2 = self._create_synthetic_jpeg(320, 240)
            offset += random.randint(512, 4096)
            offset = self._embed_file(image, offset, jpeg2, "deleted")
            manifest.append({
                "type": "JPEG",
                "offset": offset - len(jpeg2),
                "size": len(jpeg2),
                "state": "deleted",
                "description": "Deleted JPEG - directory entry removed",
            })

        if "PNG" in include_types:
            png_data = self._create_synthetic_png(256, 256)
            offset += random.randint(1024, 8192)
            offset = self._embed_file(image, offset, png_data, "normal")
            manifest.append({
                "type": "PNG",
                "offset": offset - len(png_data),
                "size": len(png_data),
                "state": "normal",
                "description": "Normal PNG image",
            })

        if "PDF" in include_types:
            pdf_data = self._create_synthetic_pdf()
            offset += random.randint(2048, 16384)
            offset = self._embed_file(image, offset, pdf_data, "deleted")
            manifest.append({
                "type": "PDF",
                "offset": offset - len(pdf_data),
                "size": len(pdf_data),
                "state": "deleted",
                "description": "Deleted PDF document",
            })

        if "ZIP" in include_types:
            zip_data = self._create_synthetic_zip()
            offset += random.randint(4096, 32768)
            offset = self._embed_file(image, offset, zip_data, "normal")
            manifest.append({
                "type": "ZIP",
                "offset": offset - len(zip_data),
                "size": len(zip_data),
                "state": "normal",
                "description": "ZIP archive",
            })

        if "GIF" in include_types:
            gif_data = self._create_synthetic_gif(100, 100)
            offset += random.randint(512, 4096)
            offset = self._embed_file(image, offset, gif_data, "deleted")
            manifest.append({
                "type": "GIF",
                "offset": offset - len(gif_data),
                "size": len(gif_data),
                "state": "deleted",
                "description": "Deleted GIF image",
            })

        # Corrupted JPEG (partial header)
        if "JPEG" in include_types:
            corrupted = self._create_synthetic_jpeg(200, 200)
            corrupted = corrupted[:len(corrupted) // 2]  # Truncate
            offset += random.randint(2048, 8192)
            offset = self._embed_file(image, offset, corrupted, "corrupted")
            manifest.append({
                "type": "JPEG",
                "offset": offset - len(corrupted),
                "size": len(corrupted),
                "state": "corrupted",
                "description": "Corrupted JPEG - truncated file",
            })

        # Extension mismatch: PDF data but would have .jpg extension
        if "PDF" in include_types:
            pdf_mismatch = self._create_synthetic_pdf()
            offset += random.randint(4096, 16384)
            offset = self._embed_file(image, offset, pdf_mismatch, "mismatch")
            manifest.append({
                "type": "PDF",
                "offset": offset - len(pdf_mismatch),
                "size": len(pdf_mismatch),
                "state": "extension_mismatch",
                "description": "PDF file with .jpg extension (mismatch)",
            })

        logger.info(
            "synthetic_image_generated",
            size_mb=size_mb,
            embedded_files=len(manifest),
        )

        return bytes(image), manifest

    def _embed_file(
        self,
        image: bytearray,
        offset: int,
        data: bytes,
        state: str,
    ) -> int:
        """Embed file data into the image at the given offset."""
        # Align to sector boundary
        offset = ((offset + 511) // 512) * 512

        if offset + len(data) > len(image):
            return offset  # Don't overflow

        image[offset : offset + len(data)] = data
        return offset + len(data)

    def _create_synthetic_jpeg(self, width: int, height: int) -> bytes:
        """Create a minimal valid JPEG file."""
        buf = io.BytesIO()

        # SOI marker
        buf.write(b"\xFF\xD8")

        # APP0 JFIF marker
        buf.write(b"\xFF\xE0")
        jfif_data = b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        buf.write(struct.pack(">H", len(jfif_data) + 2))
        buf.write(jfif_data)

        # DQT (Quantization table)
        buf.write(b"\xFF\xDB")
        qt = bytes(range(64))
        buf.write(struct.pack(">H", 67))
        buf.write(b"\x00")
        buf.write(qt)

        # SOF0 (Start of Frame)
        buf.write(b"\xFF\xC0")
        buf.write(struct.pack(">H", 11))
        buf.write(struct.pack("B", 8))  # precision
        buf.write(struct.pack(">H", height))
        buf.write(struct.pack(">H", width))
        buf.write(struct.pack("B", 1))  # components
        buf.write(b"\x01\x11\x00")  # component 1

        # DHT (Huffman table)
        buf.write(b"\xFF\xC4")
        ht_data = b"\x00" + bytes(16) + b"\x00"
        buf.write(struct.pack(">H", len(ht_data) + 2))
        buf.write(ht_data)

        # SOS (Start of Scan)
        buf.write(b"\xFF\xDA")
        buf.write(struct.pack(">H", 8))
        buf.write(b"\x01\x01\x00\x00\x3F\x00")

        # Scan data (random but valid-ish)
        scan_data = secrets.token_bytes(random.randint(1024, 4096))
        # Escape any 0xFF bytes in scan data
        scan_data = scan_data.replace(b"\xFF", b"\xFF\x00")
        buf.write(scan_data)

        # EOI marker
        buf.write(b"\xFF\xD9")

        return buf.getvalue()

    def _create_synthetic_png(self, width: int, height: int) -> bytes:
        """Create a minimal valid PNG file."""
        buf = io.BytesIO()

        # PNG signature
        buf.write(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A")

        # IHDR chunk
        ihdr_data = struct.pack(">II", width, height)
        ihdr_data += struct.pack("BBBBB", 8, 2, 0, 0, 0)  # 8-bit RGB
        self._write_png_chunk(buf, b"IHDR", ihdr_data)

        # IDAT chunk (minimal compressed data)
        import zlib
        raw_row = b"\x00" + secrets.token_bytes(width * 3)
        raw_data = raw_row * min(height, 10)  # Only a few rows for demo
        compressed = zlib.compress(raw_data)
        self._write_png_chunk(buf, b"IDAT", compressed)

        # IEND chunk
        self._write_png_chunk(buf, b"IEND", b"")

        return buf.getvalue()

    def _write_png_chunk(self, buf: io.BytesIO, chunk_type: bytes, data: bytes):
        """Write a PNG chunk with CRC."""
        import zlib
        buf.write(struct.pack(">I", len(data)))
        buf.write(chunk_type)
        buf.write(data)
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        buf.write(struct.pack(">I", crc))

    def _create_synthetic_pdf(self) -> bytes:
        """Create a minimal valid PDF file."""
        content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 44 >>\nstream\n"
            b"BT /F1 12 Tf 100 700 Td (ZEROTrace Demo) Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000214 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n308\n"
            b"%%EOF"
        )
        return content

    def _create_synthetic_zip(self) -> bytes:
        """Create a minimal valid ZIP file."""
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("demo.txt", "ZEROTrace Synthetic Test File\n")
            zf.writestr("data.csv", "id,name,value\n1,test,100\n")
        return buf.getvalue()

    def _create_synthetic_gif(self, width: int, height: int) -> bytes:
        """Create a minimal valid GIF file."""
        buf = io.BytesIO()
        # Header
        buf.write(b"GIF89a")
        buf.write(struct.pack("<HH", width, height))
        buf.write(b"\x80\x00\x00")  # GCT flag, bg color, aspect
        # Global Color Table (2 colors)
        buf.write(b"\x00\x00\x00")  # Black
        buf.write(b"\xFF\xFF\xFF")  # White
        # Image Descriptor
        buf.write(b"\x2C")
        buf.write(struct.pack("<HHHH", 0, 0, width, height))
        buf.write(b"\x00")  # No LCT
        # Image Data
        buf.write(b"\x02")  # LZW min code size
        buf.write(b"\x02\x4C\x01")  # Minimal LZW data
        buf.write(b"\x00")  # Block terminator
        # Trailer
        buf.write(b"\x3B")
        return buf.getvalue()


class DemoRunner:
    """
    One-click demo that runs the complete forensic pipeline.
    Creates synthetic evidence → registers → hashes → recovers →
    validates → classifies → generates Merkle tree → creates report.
    """

    def __init__(self):
        self.image_generator = SyntheticImageGenerator()

    def run_full_demo(
        self,
        progress_callback=None,
    ) -> dict:
        """Execute the complete demo pipeline."""
        from engines.integrity import compute_sha256, compute_sha512, MerkleTree, HashChain
        from workers.master_controller import MasterController
        from forensic import AuditService, ChainOfCustodyService, ReportGenerator

        start_time = time.time()
        steps_completed = []
        case_id = str(uuid.uuid4())
        evidence_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())

        audit = AuditService()
        custody = ChainOfCustodyService()
        report_gen = ReportGenerator()

        def _step(name: str):
            steps_completed.append(name)
            if progress_callback:
                progress_callback(name, len(steps_completed))

        # 1. Create synthetic evidence
        _step("Creating synthetic forensic image")
        image_data, manifest = self.image_generator.generate_test_image(size_mb=4)

        # 2. Register evidence
        _step("Registering evidence")
        case_info = {
            "case_id": case_id,
            "case_number": f"CASE-{datetime.now().strftime('%Y%m%d')}-DEMO",
            "title": "ZEROTrace Forensic Demo",
            "investigator": "Demo Operator",
            "status": "IN_PROGRESS",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        evidence_info = {
            "evidence_id": evidence_id,
            "evidence_number": f"EVD-{datetime.now().year}-DEMO",
            "case_id": case_id,
            "source_device": "Synthetic Test Image",
            "device_type": "FORENSIC_IMAGE",
            "capacity_bytes": len(image_data),
            "acquisition_method": "synthetic_generation",
            "investigator": "Demo Operator",
            "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        audit.log_event("EVIDENCE", "REGISTERED", case_id=case_id, evidence_id=evidence_id)
        custody.add_entry(case_id, evidence_id, "Demo Operator", "REGISTERED",
                         source="Synthetic Generator")

        # 3. Calculate hash
        _step("Computing SHA-256 hash")
        sha256 = compute_sha256(image_data)
        sha512 = compute_sha512(image_data)
        evidence_info["sha256_hash"] = sha256
        evidence_info["sha512_hash"] = sha512
        evidence_info["original_hash"] = sha256

        audit.log_event("INTEGRITY", "HASHED", case_id=case_id, evidence_id=evidence_id,
                       metadata={"sha256": sha256})
        custody.add_entry(case_id, evidence_id, "Demo Operator", "HASHED")

        # 4. Start recovery
        _step("Starting recovery job")
        audit.log_event("RECOVERY", "JOB_STARTED", case_id=case_id,
                       evidence_id=evidence_id, job_id=job_id)

        # 5-7. MapReduce processing
        _step("Processing with worker pool (MapReduce)")
        controller = MasterController(max_workers=min(4, settings.MAX_WORKERS))

        recovery_results = controller.execute_recovery_job(
            evidence_data=image_data,
            evidence_id=evidence_id,
            job_id=job_id,
            progress_callback=lambda p: _step(f"Chunk {p.processed_chunks}/{p.total_chunks}") if p.processed_chunks % 2 == 0 else None,
        )

        _step(f"Recovered {recovery_results['total_artifacts']} artifacts")

        # 8. Validate files
        _step("Validating recovered files")
        audit.log_event("VALIDATION", "COMPLETED", case_id=case_id,
                       evidence_id=evidence_id, job_id=job_id,
                       metadata={"artifacts": recovery_results["total_artifacts"]})

        # 9. Calculate confidence
        _step("Computing confidence scores")

        # 10. Generate Merkle root
        _step("Building Merkle tree")
        merkle_root = recovery_results.get("merkle_root", "")

        # 11. Create audit chain
        _step("Creating tamper-evident audit chain")
        audit.log_event("INTEGRITY", "MERKLE_TREE_BUILT", case_id=case_id,
                       evidence_id=evidence_id,
                       metadata={"merkle_root": merkle_root})
        chain_verification = audit.verify_chain()
        custody.add_entry(case_id, evidence_id, "Demo Operator", "VALIDATED")

        # 12. Generate report
        _step("Generating forensic report")
        recovery_results["started_at"] = case_info["created_at"]
        recovery_results["completed_at"] = datetime.now(timezone.utc).isoformat()

        report = report_gen.generate_forensic_report(
            case_info=case_info,
            evidence_info=evidence_info,
            recovery_results=recovery_results,
            audit_events=audit.get_events(),
            custody_chain=custody.get_chain(evidence_id),
        )

        audit.log_event("REPORT", "GENERATED", case_id=case_id,
                       evidence_id=evidence_id,
                       metadata={"report_id": report["report_id"]})

        # 13. Display results
        _step("Demo complete")

        total_time = time.time() - start_time

        return {
            "status": "COMPLETED",
            "case_id": case_id,
            "case_number": case_info["case_number"],
            "evidence_id": evidence_id,
            "evidence_number": evidence_info["evidence_number"],
            "job_id": job_id,
            "steps_completed": steps_completed,
            "image_size_bytes": len(image_data),
            "embedded_files": len(manifest),
            "manifest": manifest,
            "recovered_files": recovery_results["total_artifacts"],
            "artifacts": recovery_results["artifacts"],
            "merkle_root": merkle_root,
            "evidence_sha256": sha256,
            "audit_chain_valid": chain_verification["valid"],
            "audit_events_count": len(audit.get_events()),
            "custody_chain": custody.get_chain(evidence_id),
            "report_id": report["report_id"],
            "report": report,
            "duration_seconds": total_time,
            "throughput_mbps": recovery_results.get("throughput_mbps", 0),
            "workers_used": recovery_results.get("workers_used", 0),
        }
