"""
ZEROTrace — Forensic Services
Audit logging, Chain of Custody, and Reporting.
"""

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from engines.integrity import HashChain, MerkleTree, compute_sha256
from app.core.config import settings
from app.core.logging_config import get_logger, forensic_log

logger = get_logger("forensic")


# ═══════════════════════════════════════════════════════════
# Audit Service
# ═══════════════════════════════════════════════════════════

class AuditService:
    """
    Tamper-evident audit logging with hash chain.
    Every audit event is chained — tampering breaks verification.
    """

    def __init__(self):
        self.hash_chain = HashChain()
        self.events: list[dict] = []

    def log_event(
        self,
        event_type: str,
        action: str,
        *,
        case_id: str = None,
        evidence_id: str = None,
        job_id: str = None,
        user_id: str = None,
        operator: str = None,
        description: str = None,
        severity: str = "INFO",
        metadata: dict = None,
    ) -> dict:
        """Log a tamper-evident audit event."""
        event_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "action": action,
            "case_id": case_id,
            "evidence_id": evidence_id,
            "job_id": job_id,
            "user_id": user_id,
            "operator": operator,
            "description": description,
            "severity": severity,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add to hash chain
        chain_entry = self.hash_chain.add_event(event_data)
        event_data["previous_hash"] = chain_entry["previous_hash"]
        event_data["current_hash"] = chain_entry["current_hash"]

        self.events.append(event_data)

        forensic_log(
            event_type,
            case_id=case_id,
            evidence_id=evidence_id,
            job_id=job_id,
            operator=operator,
            level=severity.lower() if severity in ("INFO", "WARNING", "ERROR") else "info",
            action=action,
        )

        return event_data

    def verify_chain(self) -> dict:
        """Verify the entire audit hash chain."""
        return self.hash_chain.verify_chain()

    def get_events(
        self,
        case_id: str = None,
        evidence_id: str = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get audit events with optional filtering."""
        filtered = self.events
        if case_id:
            filtered = [e for e in filtered if e.get("case_id") == case_id]
        if evidence_id:
            filtered = [e for e in filtered if e.get("evidence_id") == evidence_id]
        return filtered[-limit:]


# ═══════════════════════════════════════════════════════════
# Chain of Custody Service
# ═══════════════════════════════════════════════════════════

class ChainOfCustodyService:
    """
    Track every evidence action with full chain of custody.
    Each entry is hash-linked for tamper detection.
    """

    def __init__(self):
        self.entries: list[dict] = []
        self._last_hash: str = "0" * 64

    def add_entry(
        self,
        case_id: str,
        evidence_id: str,
        operator: str,
        action: str,
        source: str = None,
        destination: str = None,
        notes: str = None,
        metadata: dict = None,
    ) -> dict:
        """Add a chain of custody entry."""
        entry = {
            "entry_id": str(uuid.uuid4()),
            "case_id": case_id,
            "evidence_id": evidence_id,
            "operator": operator,
            "action": action,
            "source": source,
            "destination": destination,
            "notes": notes,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": self._last_hash,
        }

        # Compute current hash
        payload = json.dumps(entry, sort_keys=True, default=str)
        entry["current_hash"] = hashlib.sha256(
            f"{self._last_hash}:{payload}".encode()
        ).hexdigest()

        self._last_hash = entry["current_hash"]
        self.entries.append(entry)
        return entry

    def verify_chain(self, evidence_id: str = None) -> dict:
        """Verify the chain of custody integrity."""
        chain = self.entries
        if evidence_id:
            chain = [e for e in chain if e["evidence_id"] == evidence_id]

        if not chain:
            return {"valid": True, "length": 0}

        errors = []
        for i in range(1, len(chain)):
            if chain[i]["previous_hash"] != chain[i - 1]["current_hash"]:
                errors.append({
                    "index": i,
                    "error": "Chain break detected",
                    "entry_id": chain[i]["entry_id"],
                })

        return {
            "valid": len(errors) == 0,
            "length": len(chain),
            "errors": errors,
        }

    def get_chain(self, evidence_id: str) -> list[dict]:
        return [e for e in self.entries if e["evidence_id"] == evidence_id]


# ═══════════════════════════════════════════════════════════
# Report Generator
# ═══════════════════════════════════════════════════════════

class ReportGenerator:
    """
    Generate forensic reports in JSON, CSV, and PDF formats.
    """

    def generate_forensic_report(
        self,
        case_info: dict,
        evidence_info: dict,
        recovery_results: dict,
        audit_events: list[dict],
        custody_chain: list[dict],
        format: str = "JSON",
    ) -> dict:
        """Generate a complete forensic report."""
        report = {
            "report_id": str(uuid.uuid4()),
            "report_type": "FORENSIC",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": {
                "1_case_information": case_info,
                "2_evidence_information": evidence_info,
                "3_acquisition_details": {
                    "method": evidence_info.get("acquisition_method", "N/A"),
                    "timestamp": evidence_info.get("acquisition_timestamp", "N/A"),
                    "investigator": evidence_info.get("investigator", "N/A"),
                },
                "4_evidence_hash": {
                    "sha256": evidence_info.get("sha256_hash", "N/A"),
                    "sha512": evidence_info.get("sha512_hash", "N/A"),
                    "original_hash": evidence_info.get("original_hash", "N/A"),
                },
                "5_processing_timeline": {
                    "started_at": recovery_results.get("started_at", "N/A"),
                    "completed_at": recovery_results.get("completed_at", "N/A"),
                    "duration_seconds": recovery_results.get("processing_time_seconds", 0),
                },
                "6_recovery_method": {
                    "strategy": "Consensus Multi-Strategy Recovery",
                    "workers_used": recovery_results.get("workers_used", 0),
                    "total_chunks": recovery_results.get("total_chunks", 0),
                    "throughput_mbps": recovery_results.get("throughput_mbps", 0),
                },
                "7_recovered_files": recovery_results.get("artifacts", []),
                "8_validation_results": {
                    "total_artifacts": recovery_results.get("total_artifacts", 0),
                    "valid": sum(
                        1 for a in recovery_results.get("artifacts", [])
                        if a.get("validation_status") == "VALID"
                    ),
                    "partially_valid": sum(
                        1 for a in recovery_results.get("artifacts", [])
                        if a.get("validation_status") == "PARTIALLY_VALID"
                    ),
                    "corrupted": sum(
                        1 for a in recovery_results.get("artifacts", [])
                        if a.get("validation_status") == "CORRUPTED"
                    ),
                },
                "9_confidence_scores": {
                    "average_confidence": (
                        sum(a.get("confidence", 0) for a in recovery_results.get("artifacts", []))
                        / max(len(recovery_results.get("artifacts", [])), 1)
                    ),
                    "high_confidence_count": sum(
                        1 for a in recovery_results.get("artifacts", [])
                        if a.get("confidence", 0) >= 0.8
                    ),
                },
                "10_integrity_verification": {
                    "merkle_root": recovery_results.get("merkle_root", ""),
                },
                "11_chain_of_custody": custody_chain,
                "12_audit_trail": audit_events[-50:],  # Last 50 events
                "13_errors_limitations": {
                    "errors": recovery_results.get("errors", []),
                    "limitations": [
                        "SAFE_DEMO_MODE active" if settings.SAFE_DEMO_MODE else None,
                        "Fragment reconstruction may have gaps",
                        "Confidence scores are estimates",
                    ],
                },
                "14_summary": {
                    "total_recovered": recovery_results.get("total_artifacts", 0),
                    "merkle_root": recovery_results.get("merkle_root", ""),
                    "overall_status": "COMPLETED",
                },
            },
        }

        # Compute report hash
        report_str = json.dumps(report, sort_keys=True, default=str)
        report["report_hash"] = compute_sha256(report_str.encode())

        if format == "JSON":
            return report
        elif format == "CSV":
            return self._to_csv(report)
        elif format == "PDF":
            return self._to_pdf_data(report)

        return report

    def generate_sanitization_certificate(
        self,
        operation: dict,
        verification: dict,
        device_info: dict,
    ) -> dict:
        """Generate a sanitization certificate."""
        cert = {
            "certificate_id": f"CERT-{uuid.uuid4().hex[:12].upper()}",
            "certificate_type": "SANITIZATION",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "device": {
                "device_id": device_info.get("id", "N/A"),
                "device_type": device_info.get("device_type", "N/A"),
                "capacity": device_info.get("capacity_bytes", 0),
                "serial_number": device_info.get("serial_number", "N/A"),
            },
            "sanitization": {
                "method": operation.get("method", "N/A"),
                "passes_completed": operation.get("passes_completed", 0),
                "start_time": operation.get("started_at", "N/A"),
                "end_time": operation.get("completed_at", "N/A"),
                "operator": operation.get("operator", "N/A"),
                "is_simulated": operation.get("is_simulated", True),
            },
            "verification": {
                "method": verification.get("verification_method", "N/A"),
                "result": verification.get("overall_pass", False),
                "all_zero": verification.get("all_zero", None),
                "sample_count": verification.get("sample_count", 0),
                "verified_at": verification.get("verified_at", "N/A"),
            },
            "limitations": [],
        }

        if operation.get("is_simulated"):
            cert["limitations"].append(
                "SAFE_DEMO_MODE: This is a SIMULATED sanitization. "
                "No actual data was erased from the device."
            )

        if not verification.get("overall_pass"):
            cert["limitations"].append(
                "Verification did not pass. Sanitization may be incomplete."
            )

        cert_str = json.dumps(cert, sort_keys=True, default=str)
        cert["certificate_hash"] = compute_sha256(cert_str.encode())

        return cert

    def _to_csv(self, report: dict) -> dict:
        """Convert artifact list to CSV format."""
        artifacts = report["sections"].get("7_recovered_files", [])
        if not artifacts:
            return {**report, "csv_data": ""}

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "artifact_id", "file_type", "extension", "category",
                "offset", "size", "sha256", "confidence",
                "validation_status", "recovery_method",
            ],
        )
        writer.writeheader()
        for a in artifacts:
            writer.writerow({k: a.get(k, "") for k in writer.fieldnames})

        report["csv_data"] = output.getvalue()
        return report

    def _to_pdf_data(self, report: dict) -> dict:
        """Generate PDF report data (structure for PDF generation)."""
        # In a full implementation, this would use reportlab
        # For now, return structured data suitable for PDF generation
        report["pdf_ready"] = True
        report["pdf_sections"] = list(report["sections"].keys())
        return report
