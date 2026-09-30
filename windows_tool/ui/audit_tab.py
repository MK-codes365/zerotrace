"""
ZeroTrace Forensic Audit Trail & Case Management Tab
Maintains cryptographic chain-of-custody, case metadata,
and displays the immutable tamper-evident hash chain with one-click verification.
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from ui.theme import (
    COLOR_CARD, COLOR_BORDER, COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)


class AuditTab(ctk.CTkFrame):
    def __init__(self, master, audit_service, case_manager):
        super().__init__(master, fg_color="transparent")
        self.audit_service = audit_service
        self.case_manager = case_manager

        self._build_ui()
        self.audit_service.subscribe(self._on_audit_event_logged)
        self.refresh_logs()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="📜 FORENSIC AUDIT TRAIL & EVIDENCE CHAIN OF CUSTODY",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Cryptographic Hash Chaining (SHA-256) • Tamper-Evident Ledger • Court-Admissible Compliance",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left", padx=15, pady=2)

        # Case Card
        case_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        case_card.pack(fill="x", padx=10, pady=5)

        case = self.case_manager.get_active_case()
        c_row = ctk.CTkFrame(case_card, fg_color="transparent")
        c_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(c_row, text=f"Active Case: {case.get('case_id')}", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(side="left")
        ctk.CTkLabel(c_row, text=f"Agency: {case.get('agency')}", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=15)
        ctk.CTkLabel(c_row, text=f"Investigator: {case.get('investigator')}", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=15)

        # Audit Chain Action & Verification Bar
        act_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        act_card.pack(fill="x", padx=10, pady=5)

        a_row = ctk.CTkFrame(act_card, fg_color="transparent")
        a_row.pack(fill="x", padx=15, pady=8)

        ctk.CTkButton(
            a_row,
            text="🔒 Verify Cryptographic Hash Chain",
            font=ctk.CTkFont(weight="bold"),
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#00c853",
            text_color="#000",
            command=self._verify_chain
        ).pack(side="left", padx=(0, 10))

        self.verify_badge = ctk.CTkLabel(a_row, text="Status: Unverified in current session", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)
        self.verify_badge.pack(side="left")

        ctk.CTkButton(
            a_row,
            text="💾 Export Audit Trail (JSON)",
            fg_color="#37474f",
            hover_color="#263238",
            command=self._export_audit_trail
        ).pack(side="right")

        # Scrollable Audit Logs Feed
        log_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        log_card.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(log_card, text="IMMUTABLE TAMPER-EVIDENT HASH-CHAINED EVENT LOGS:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 5))

        self.log_scroll = ctk.CTkScrollableFrame(log_card, fg_color="#10151c", corner_radius=4)
        self.log_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def refresh_logs(self):
        for child in self.log_scroll.winfo_children():
            child.destroy()

        events = self.audit_service.get_events(limit=50)
        for ev in reversed(events):
            self._render_event_box(ev)

    def _render_event_box(self, ev: dict):
        box = ctk.CTkFrame(self.log_scroll, fg_color="#182230", corner_radius=4, border_width=1, border_color="#243448")
        box.pack(fill="x", pady=2, padx=2)

        idx = ev.get("index", 0)
        action = ev.get("action", "EVENT")
        ts = ev.get("timestamp", "").replace("T", " ")[:19]
        target = ev.get("target", "N/A")
        h = ev.get("event_hash", "0" * 64)
        prev_h = ev.get("prev_hash", "0" * 64)

        top_row = ctk.CTkFrame(box, fg_color="transparent")
        top_row.pack(fill="x", padx=8, pady=(4, 0))

        ctk.CTkLabel(top_row, text=f"#{idx:03d} • {action}", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(side="left")
        ctk.CTkLabel(top_row, text=ts, font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED).pack(side="right")

        ctk.CTkLabel(box, text=f"Target: {target}", font=ctk.CTkFont(size=10), anchor="w").pack(fill="x", padx=8, pady=1)

        hash_line = f"Prev Hash: {prev_h[:16]}... ──▶ Event Hash: {h[:24]}..."
        ctk.CTkLabel(box, text=hash_line, font=ctk.CTkFont(size=9, family="Courier"), text_color=COLOR_TEXT_MUTED, anchor="w").pack(fill="x", padx=8, pady=(0, 4))

    def _on_audit_event_logged(self, ev: dict):
        self.after(0, self.refresh_logs)

    def _verify_chain(self):
        res = self.audit_service.verify_chain()
        if res.get("valid"):
            total = res.get("total_blocks", 0)
            self.verify_badge.configure(
                text=f"✅ Cryptographically Verified: All {total} blocks match hash signatures with zero tampering.",
                text_color=COLOR_ACCENT_GREEN
            )
            messagebox.showinfo("Verification Passed", f"Audit Chain Integrity Verified!\n\nTotal Blocks: {total}\nIntegrity State: 100% Intact & Untampered\nAlgorithm: SHA-256 Hash Chain")
        else:
            self.verify_badge.configure(
                text=f"❌ Verification FAILED: {res.get('reason')}",
                text_color=COLOR_ACCENT_RED
            )
            messagebox.showerror("Verification Failed", f"Tampering Detected in Audit Log!\n\nReason: {res.get('reason')}\nTampered Index: {res.get('tampered_index')}")

    def _export_audit_trail(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="Audit_Trail_Verified.json"
        )
        if dest:
            try:
                events = self.audit_service.get_events(limit=1000)
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2)
                messagebox.showinfo("Export Successful", f"Audit ledger exported to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))
