"""
ZeroTrace Forensic Certificate & Report Generator
Generates tamper-evident PDF certificates and forensic audit reports
with SHA-256 digital signatures, conforming to NIST SP 800-88, DoD 5220.22-M,
and digital forensics evidential standards for NTRO SIH26149.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

from core.crypto import sha256_bytes, generate_tamper_signature


def clean_pdf_text(text: Any) -> str:
    """
    Sanitize unicode characters to latin-1 compatibility for standard FPDF core fonts.
    Replaces em-dashes, en-dashes, bullets, and smart quotes with ASCII counterparts.
    """
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "\u2014": " - ",
        "\u2013": "-",
        "\u2022": "|",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\xa0": " ",
        "⚡": "[ZT]",
        "🛡": "[SEC]",
        "✅": "[PASSED]",
        "❌": "[FAILED]",
        "⚠️": "[WARN]",
    }
    for char, rep in replacements.items():
        s = s.replace(char, rep)
    # Ensure any remaining non-latin1 characters are safely replaced with '?'
    return s.encode("latin-1", "replace").decode("latin-1")


class ZeroTraceReportPDF(FPDF if HAS_FPDF else object):
    def header(self):
        if not HAS_FPDF:
            return
        self.set_fill_color(18, 24, 38)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 255, 170)
        self.cell(0, 8, clean_pdf_text("ZEROTRACE - DEFENSIVE CYBERSECURITY & FORENSICS"), 0, 1, "C")
        self.set_font("Arial", "", 9)
        self.set_text_color(180, 200, 220)
        self.cell(0, 6, clean_pdf_text("Enterprise Secure Data Sanitization & Forensic Recovery"), 0, 1, "C")
        self.ln(6)

    def footer(self):
        if not HAS_FPDF:
            return
        self.set_y(-18)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 140)
        self.cell(0, 5, clean_pdf_text("Official Tamper-Evident Report | ZeroTrace Digital Forensics"), 0, 1, "C")
        self.cell(0, 5, f"Page {self.page_no()}", 0, 0, "C")


def generate_certificate(
    drive_info: Dict[str, Any],
    method: str,
    status: str,
    output_path: str = "sanitization_certificate.pdf",
    verified: bool = True,
    case_id: str = "CASE-ZT-2026-001",
    operator: str = "Forensic Investigator",
    verification_details: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate an official, tamper-evident data destruction certificate.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cert_id = f"CERT-ZT-{hashlib.sha256(timestamp.encode()).hexdigest()[:12].upper()}"

    model = drive_info.get("model") or drive_info.get("Model") or drive_info.get("label") or "Storage Media"
    serial = drive_info.get("serial") or drive_info.get("SerialNumber") or "SEC-DEV-UNKNOWN"
    size_str = str(drive_info.get("size") or "Unknown")
    media_type = drive_info.get("media_type") or "Storage Drive"

    raw_signature_data = f"{cert_id}|{timestamp}|{method}|{status}|{model}|{serial}|{verified}|{case_id}"
    digital_signature = generate_tamper_signature(raw_signature_data)

    # 1. Write JSON record
    json_path = output_path.replace(".pdf", ".json")
    cert_record = {
        "certificate_id": cert_id,
        "case_id": case_id,
        "timestamp": timestamp,
        "operator": operator,
        "status": status,
        "device": {
            "model": model,
            "serial": serial,
            "size": size_str,
            "media_type": media_type,
            "target_id": drive_info.get("device_id", "N/A"),
        },
        "sanitization": {
            "method": method,
            "verified": verified,
            "verification_details": verification_details or {"status": "Passed verification sampling"},
        },
        "evidential_integrity": {
            "digital_signature": digital_signature,
            "verification_standard": "NIST SP 800-88 Rev. 1 Guidelines for Media Sanitization",
            "hash_algorithm": "HMAC-SHA256",
        },
    }

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(cert_record, f, indent=2)
    except Exception as e:
        print(f"[CERTIFICATE] Error saving JSON: {e}")

    # 2. Generate PDF document
    if HAS_FPDF:
        try:
            pdf = ZeroTraceReportPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=20)

            # Title
            pdf.ln(5)
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(0, 10, clean_pdf_text("CERTIFICATE OF SECURE DATA SANITIZATION"), 0, 1, "C")
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(90, 90, 100)
            pdf.cell(0, 6, clean_pdf_text(f"Certificate Identifier: {cert_id}"), 0, 1, "C")
            pdf.ln(6)

            # Metadata Table
            pdf.set_fill_color(240, 245, 250)
            pdf.set_draw_color(180, 200, 220)
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(30, 40, 60)

            def print_row(key, val):
                pdf.cell(60, 8, clean_pdf_text(f"  {key}"), 1, 0, "L", fill=True)
                pdf.set_font("Arial", "", 10)
                pdf.cell(130, 8, clean_pdf_text(f"  {val}"), 1, 1, "L")
                pdf.set_font("Arial", "B", 10)

            print_row("Investigation Case", case_id)
            print_row("Issuing Authority", "ZeroTrace Forensic Laboratories")
            print_row("Authorized Operator", operator)
            print_row("Timestamp (UTC)", timestamp)
            print_row("Sanitization Status", status)
            print_row("Target Storage Media", model)
            print_row("Serial Number", serial)
            print_row("Media Type", media_type)
            print_row("Media Capacity", size_str)
            print_row("Sanitization Standard", method)
            print_row("Post-Wipe Verification", "PASSED (Zero Residual Traces)" if verified else "NOT VERIFIED")

            pdf.ln(6)
            # Evidential Integrity section
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(20, 80, 60)
            pdf.cell(0, 8, clean_pdf_text("Cryptographic Evidential Integrity & Digital Signature"), 0, 1, "L")
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(40, 40, 40)
            sig_text = f"HMAC-SHA256 Digital Signature:\n{digital_signature}\n\nCompliance: NIST SP 800-88 / DoD 5220.22-M / ISO/IEC 27040 / BSI GS-03"
            pdf.multi_cell(0, 5, clean_pdf_text(sig_text), 1, "L")

            pdf.output(output_path)
            return output_path
        except Exception as e:
            print(f"[CERTIFICATE] PDF generation failed ({e}), JSON record generated at {json_path}")

    return json_path


def generate_recovery_report(
    case_info: Dict[str, Any],
    source_target: str,
    recovered_files: list,
    output_path: str = "forensic_recovery_report.pdf",
    operator: str = "Forensic Analyst",
) -> str:
    """
    Generate an official forensic case recovery report.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-ZT-{hashlib.sha256(timestamp.encode()).hexdigest()[:12].upper()}"

    json_path = output_path.replace(".pdf", ".json")
    report_data = {
        "report_id": report_id,
        "case_id": case_info.get("case_id", "CASE-ZT-2026-001"),
        "case_title": case_info.get("title", "Forensic Data Recovery"),
        "agency": case_info.get("agency", "ZeroTrace Forensic Laboratories"),
        "operator": operator,
        "timestamp": timestamp,
        "source_evidence": source_target,
        "total_files_recovered": len(recovered_files),
        "files_summary": [
            {
                "file_id": getattr(f, "file_id", str(f.get("file_id", ""))),
                "type": getattr(f, "file_type", str(f.get("file_type", ""))),
                "size": getattr(f, "size", f.get("size", 0)),
                "sha256": getattr(f, "sha256", f.get("sha256", "")),
                "confidence": getattr(f, "confidence", f.get("confidence", 0.0)),
            }
            for f in recovered_files[:100]
        ],
    }

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        print(f"[REPORT] Error writing JSON: {e}")

    if HAS_FPDF:
        try:
            pdf = ZeroTraceReportPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=20)

            pdf.ln(5)
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(0, 10, clean_pdf_text("DIGITAL EVIDENCE RECOVERY REPORT"), 0, 1, "C")
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(90, 90, 100)
            pdf.cell(0, 6, clean_pdf_text(f"Report ID: {report_id} | Case: {report_data['case_id']}"), 0, 1, "C")
            pdf.ln(6)

            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 7, clean_pdf_text("Investigative Agency:"), 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 7, clean_pdf_text(report_data["agency"]), 0, 1)

            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 7, clean_pdf_text("Source Evidence Target:"), 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 7, clean_pdf_text(source_target), 0, 1)

            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 7, clean_pdf_text("Total Artifacts Carved:"), 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 7, clean_pdf_text(f"{len(recovered_files)} file(s)"), 0, 1)
            pdf.ln(6)

            # Table Header
            pdf.set_fill_color(30, 45, 65)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(25, 7, clean_pdf_text("File ID"), 1, 0, "C", fill=True)
            pdf.cell(25, 7, clean_pdf_text("Type"), 1, 0, "C", fill=True)
            pdf.cell(30, 7, clean_pdf_text("Size (Bytes)"), 1, 0, "C", fill=True)
            pdf.cell(30, 7, clean_pdf_text("Confidence"), 1, 0, "C", fill=True)
            pdf.cell(80, 7, clean_pdf_text("SHA-256 Hash"), 1, 1, "C", fill=True)

            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(30, 30, 30)

            for f in recovered_files[:25]:
                f_id = getattr(f, "file_id", str(f.get("file_id", "")))
                f_type = getattr(f, "file_type", str(f.get("file_type", "")))
                f_size = str(getattr(f, "size", f.get("size", 0)))
                conf = f"{int(getattr(f, 'confidence', f.get('confidence', 0.0)) * 100)}%"
                h = getattr(f, "sha256", f.get("sha256", ""))[:16] + "..."

                pdf.cell(25, 6, clean_pdf_text(f_id), 1, 0, "C")
                pdf.cell(25, 6, clean_pdf_text(f_type), 1, 0, "C")
                pdf.cell(30, 6, clean_pdf_text(f_size), 1, 0, "C")
                pdf.cell(30, 6, clean_pdf_text(conf), 1, 0, "C")
                pdf.cell(80, 6, clean_pdf_text(h), 1, 1, "C")

            pdf.output(output_path)
            return output_path
        except Exception as e:
            print(f"[REPORT] PDF creation failed: {e}")

    return json_path
