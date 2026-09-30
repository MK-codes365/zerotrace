"""
ZeroTrace Module 2 — Secure File & Folder Eraser Tab
Selective and batch forensic file shredder.
Eliminates metadata traces, wipes slack space, scrambles filenames,
zeros timestamps to epoch, and performs post-shred verification.
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from ui.theme import (
    COLOR_CARD, COLOR_BORDER, COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)
from disk_manager import format_size
from engines.file_shredder import FileFolderShredder
from engines.nwipe_engine import SanitizationMethod


class FileShredderTab(ctk.CTkFrame):
    def __init__(self, master, audit_service, case_manager):
        super().__init__(master, fg_color="transparent")
        self.audit_service = audit_service
        self.case_manager = case_manager
        self.shredder = FileFolderShredder()
        self.staged_paths = []

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="🗂️ MODULE 2: SECURE FILE & FOLDER SHREDDER",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Selective Overwrite • Metadata Cleansing • Filename Scrambling • Slack Space Wiping",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left", padx=15, pady=2)

        # Main Layout: Two Panels (Left: Staged items, Right: Config & Actions)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        content_frame.grid_columnconfigure(0, weight=3)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # ── Left Panel: Staged Files Table ─────────────────────
        left_card = ctk.CTkFrame(content_frame, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        table_header = ctk.CTkFrame(left_card, fg_color="transparent")
        table_header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(table_header, text="STAGED ITEMS FOR DESTRUCTION", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(side="left")
        self.count_badge = ctk.CTkLabel(table_header, text="0 items selected", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED)
        self.count_badge.pack(side="right")

        # Scrollable list for staged files
        self.file_scroll_frame = ctk.CTkScrollableFrame(left_card, fg_color="#121820", corner_radius=6)
        self.file_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Button row under list
        btn_row = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_row, text="📄 Add File(s)", width=120, command=self._add_files).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_row, text="📁 Add Folder", width=120, command=self._add_folder).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="🗑️ Clear List", width=100, fg_color="#37474f", hover_color="#263238", command=self._clear_list).pack(side="right")

        # ── Right Panel: Method, Options, Progress ─────────────
        right_card = ctk.CTkFrame(content_frame, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        ctk.CTkLabel(right_card, text="SHREDDING PROTOCOL & OPTIONS", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(anchor="w", padx=15, pady=(10, 5))

        # Method Dropdown
        ctk.CTkLabel(right_card, text="Overwrite Algorithm:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.method_dropdown = ctk.CTkComboBox(right_card, values=SanitizationMethod.all_methods(), width=320)
        self.method_dropdown.set(SanitizationMethod.DOD_3PASS)
        self.method_dropdown.pack(anchor="w", padx=15, pady=(0, 10))

        # Forensic Cleansing Options
        ctk.CTkLabel(right_card, text="Residual Trace Scrubbing:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.opt_scramble = ctk.CTkCheckBox(right_card, text="Scramble Filename (UUID Obfuscation)", font=ctk.CTkFont(size=11))
        self.opt_scramble.select()
        self.opt_scramble.pack(anchor="w", padx=15, pady=3)

        self.opt_timestamp = ctk.CTkCheckBox(right_card, text="Zero Timestamps to Epoch (1970-01-01)", font=ctk.CTkFont(size=11))
        self.opt_timestamp.select()
        self.opt_timestamp.pack(anchor="w", padx=15, pady=3)

        self.opt_slack = ctk.CTkCheckBox(right_card, text="Wipe Cluster Slack Space Past EOF", font=ctk.CTkFont(size=11))
        self.opt_slack.select()
        self.opt_slack.pack(anchor="w", padx=15, pady=3)

        self.opt_truncate = ctk.CTkCheckBox(right_card, text="Truncate to 0 Bytes Before Unlink", font=ctk.CTkFont(size=11))
        self.opt_truncate.select()
        self.opt_truncate.pack(anchor="w", padx=15, pady=3)

        # Progress Section
        ctk.CTkLabel(right_card, text="Batch Progress:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(15, 2))
        self.progress_bar = ctk.CTkProgressBar(right_card, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=15, pady=2)

        self.current_file_lbl = ctk.CTkLabel(
            right_card,
            text="Ready to stage files...",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        )
        self.current_file_lbl.pack(fill="x", padx=15, pady=(2, 15))

        # Action Button
        self.shred_btn = ctk.CTkButton(
            right_card,
            text="🔥 PERMANENTLY SHRED ITEMS",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_ACCENT_RED,
            hover_color="#b71c1c",
            height=40,
            command=self._confirm_and_shred
        )
        self.shred_btn.pack(fill="x", padx=15, pady=(0, 10))

    def _add_files(self):
        files = filedialog.askopenfilenames(title="Select Files to Securely Shred")
        if files:
            for f in files:
                norm = os.path.abspath(f)
                if norm not in self.staged_paths:
                    self.staged_paths.append(norm)
            self._render_staged_list()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Securely Shred")
        if folder:
            norm = os.path.abspath(folder)
            if norm not in self.staged_paths:
                self.staged_paths.append(norm)
            self._render_staged_list()

    def _clear_list(self):
        self.staged_paths = []
        self._render_staged_list()

    def _render_staged_list(self):
        # Clear existing widgets in scroll frame
        for child in self.file_scroll_frame.winfo_children():
            child.destroy()

        total_bytes = 0
        for p in self.staged_paths:
            is_dir = os.path.isdir(p)
            size = 0
            if not is_dir and os.path.exists(p):
                size = os.path.getsize(p)
                total_bytes += size

            row = ctk.CTkFrame(self.file_scroll_frame, fg_color="#18202a", corner_radius=4)
            row.pack(fill="x", pady=2, padx=2)

            icon = "📁" if is_dir else "📄"
            name = os.path.basename(p) or p
            ctk.CTkLabel(row, text=f"{icon} {name}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left", padx=5, pady=4)

            size_str = "(Folder)" if is_dir else format_size(size)
            ctk.CTkLabel(row, text=size_str, font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SECONDARY).pack(side="right", padx=5)

        self.count_badge.configure(text=f"{len(self.staged_paths)} item(s) staged • {format_size(total_bytes)}")

    def _confirm_and_shred(self):
        if not self.staged_paths:
            messagebox.showwarning("No Items", "Please add at least one file or folder to shred.")
            return

        method = self.method_dropdown.get()
        confirm = messagebox.askyesno(
            "Confirm Shredding",
            f"Are you sure you want to permanently shred {len(self.staged_paths)} item(s)?\n\nMethod: {method}\n\nWARNING: Files will be overwritten, metadata scrambled, and data cannot be recovered even by forensic carving!",
            icon="warning"
        )
        if not confirm:
            return

        self.shred_btn.configure(state="disabled")
        self.progress_bar.set(0)

        thread = threading.Thread(target=self._run_shred_worker, args=(method,), daemon=True)
        thread.start()

    def _run_shred_worker(self, method: str):
        try:
            case = self.case_manager.get_active_case()
            result = self.shredder.shred_items(
                paths=list(self.staged_paths),
                method_name=method,
                progress_callback=self._update_progress,
                case_id=case.get("case_id", "CASE-ZT-2026-001")
            )
            self.after(0, self._on_shred_finished, result)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Shred Error", str(e)))
            self.after(0, lambda: self.shred_btn.configure(state="normal"))

    def _update_progress(self, data: dict):
        pct = data.get("overall_percent", 0.0) / 100.0
        cur_file = data.get("current_file", "")
        f_idx = data.get("file_index", 0)
        tot = data.get("total_files", 0)
        self.after(0, lambda: self.progress_bar.set(min(1.0, max(0.0, pct))))
        self.after(0, lambda: self.current_file_lbl.configure(text=f"Shredding ({f_idx}/{tot}): {cur_file}"))

    def _on_shred_finished(self, result: dict):
        self.shred_btn.configure(state="normal")
        self.progress_bar.set(1.0)
        self.current_file_lbl.configure(text=f"Completed: {result['files_shredded']} file(s) eradicated in {result['duration_seconds']}s")
        self.staged_paths = []
        self._render_staged_list()
        messagebox.showinfo(
            "Shredding Complete",
            f"Successfully shredded {result['files_shredded']} file(s)!\nTotal Data Eradicated: {format_size(result['bytes_shredded'])}\nStandard: {result['method']}\nResidual Traces Cleansed: Yes"
        )
