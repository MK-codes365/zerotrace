"""
ZeroTrace Module 3 — Advanced File Carving & Forensic Recovery Tab
Integrates Scalpel signature carving, SleuthKit filesystem undelete,
and TestDisk structure validation into an interactive forensic extraction station.
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from ui.theme import (
    COLOR_CARD, COLOR_BORDER, COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)
from disk_manager import list_all_wipeable_targets, format_size
from engines.scalpel_carver import ScalpelCarver, CarvedFile
from engines.tsk_filesystem import TSKFilesystemRecoverer
from engines.structure_validator import RecoveryStructureValidator


class CarverRecoveryTab(ctk.CTkFrame):
    def __init__(self, master, audit_service, case_manager, on_files_recovered_callback=None):
        super().__init__(master, fg_color="transparent")
        self.audit_service = audit_service
        self.case_manager = case_manager
        self.on_files_recovered_callback = on_files_recovered_callback

        self.scalpel_carver = ScalpelCarver()
        self.tsk_recoverer = TSKFilesystemRecoverer()

        self.targets = []
        self.custom_image_path = None
        self.discovered_files = []

        self._build_ui()
        self.refresh_targets()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="🔍 MODULE 3: ADVANCED FORENSIC CARVING & RECOVERY",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Scalpel Signature Engine • SleuthKit Filesystem Undelete • Structure Validation • Confidence Scoring",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left", padx=15, pady=2)

        # Source Selection & Configuration Card
        config_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        config_card.pack(fill="x", padx=10, pady=5)

        row1 = ctk.CTkFrame(config_card, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(row1, text="Evidence Source:", font=ctk.CTkFont(weight="bold"), width=140, anchor="w").pack(side="left")
        self.target_dropdown = ctk.CTkComboBox(row1, values=["Scanning storage..."], width=380, command=self._on_target_selected)
        self.target_dropdown.pack(side="left", padx=5)

        ctk.CTkButton(row1, text="📂 Load Image (.dd/.img)", width=170, command=self._load_disk_image).pack(side="left", padx=10)
        ctk.CTkButton(row1, text="🔄", width=40, command=self.refresh_targets).pack(side="left")

        # Row 2: Strategy Selector & Scope
        row2 = ctk.CTkFrame(config_card, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(row2, text="Recovery Engine:", font=ctk.CTkFont(weight="bold"), width=140, anchor="w").pack(side="left")
        self.engine_dropdown = ctk.CTkComboBox(
            row2,
            values=[
                "Scalpel Deep Signature Carving (Raw Unallocated Space)",
                "SleuthKit Filesystem Undelete (NTFS $MFT / FAT Records)",
                "Hybrid Consensus Mode (Both Scalpel + SleuthKit)"
            ],
            width=430
        )
        self.engine_dropdown.set("Hybrid Consensus Mode (Both Scalpel + SleuthKit)")
        self.engine_dropdown.pack(side="left", padx=5)

        # Scan limits
        ctk.CTkLabel(row2, text="Scan Window:", font=ctk.CTkFont(size=11), width=90, anchor="e").pack(side="left", padx=(10, 5))
        self.scan_size_dropdown = ctk.CTkComboBox(row2, values=["100 MB", "250 MB", "500 MB", "1 GB", "Full Media"], width=110)
        self.scan_size_dropdown.set("100 MB")
        self.scan_size_dropdown.pack(side="left")

        # Telemetry Bar
        t_bar = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        t_bar.pack(fill="x", padx=10, pady=5)

        tb_grid = ctk.CTkFrame(t_bar, fg_color="transparent")
        tb_grid.pack(fill="x", padx=15, pady=8)
        for i in range(4):
            tb_grid.grid_columnconfigure(i, weight=1)

        self.stat_speed = self._create_metric(tb_grid, 0, "CARVING THROUGHPUT", "0.00 MB/s", COLOR_ACCENT_CYAN)
        self.stat_scanned = self._create_metric(tb_grid, 1, "SCANNED VOLUME", "0 MB", COLOR_TEXT_PRIMARY)
        self.stat_found = self._create_metric(tb_grid, 2, "ARTIFACTS CARVED", "0 files", COLOR_ACCENT_GREEN)
        self.stat_time = self._create_metric(tb_grid, 3, "SCAN DURATION", "00:00:00", COLOR_ACCENT_AMBER)

        self.scan_pb = ctk.CTkProgressBar(t_bar, height=8, progress_color=COLOR_ACCENT_GREEN)
        self.scan_pb.set(0)
        self.scan_pb.pack(fill="x", padx=15, pady=(0, 8))

        # Real-time Results Table Frame
        table_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        table_card.pack(fill="both", expand=True, padx=10, pady=5)

        th = ctk.CTkFrame(table_card, fg_color="#182230")
        th.pack(fill="x", padx=5, pady=(5, 0))
        for col_name, w in [("FILE ID", 80), ("TYPE", 65), ("CATEGORY", 90), ("SIZE", 85), ("OFFSET", 95), ("CONFIDENCE", 95), ("STRUCTURE", 100), ("DIGEST (SHA-256)", 180)]:
            ctk.CTkLabel(th, text=col_name, font=ctk.CTkFont(size=10, weight="bold"), width=w, anchor="w").pack(side="left", padx=4, pady=3)

        self.results_scroll = ctk.CTkScrollableFrame(table_card, fg_color="#10151c", corner_radius=4)
        self.results_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Action Buttons Bottom
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.scan_btn = ctk.CTkButton(
            action_bar,
            text="🚀 START FORENSIC EXTRACTION",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#1565c0",
            height=38,
            command=self._start_scan
        )
        self.scan_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            action_bar,
            text="⏹️ STOP SCAN",
            fg_color="#37474f",
            hover_color="#263238",
            height=38,
            state="disabled",
            command=self._stop_scan
        )
        self.stop_btn.pack(side="left")

        self.view_wb_btn = ctk.CTkButton(
            action_bar,
            text="🧩 Open in Workbench & Hex Inspector",
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#00c853",
            text_color="#000",
            font=ctk.CTkFont(weight="bold"),
            height=38,
            state="disabled",
            command=self._open_workbench
        )
        self.view_wb_btn.pack(side="right")

    def _create_metric(self, parent, col, title, initial_val, color):
        frame = ctk.CTkFrame(parent, fg_color="#121820", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        frame.grid(row=0, column=col, padx=4, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(pady=(4, 0))
        val_lbl = ctk.CTkLabel(frame, text=initial_val, font=ctk.CTkFont(size=14, weight="bold"), text_color=color)
        val_lbl.pack(pady=(0, 4))
        return val_lbl

    def refresh_targets(self):
        try:
            self.targets = list_all_wipeable_targets()
            opts = [t.get("display_name", t["device_id"]) for t in self.targets]
            if self.custom_image_path:
                opts.insert(0, f"📁 [DISK IMAGE] {os.path.basename(self.custom_image_path)}")
            self.target_dropdown.configure(values=opts)
            if opts:
                self.target_dropdown.set(opts[0])
        except Exception:
            pass

    def _on_target_selected(self, choice):
        pass

    def _load_disk_image(self):
        img_path = filedialog.askopenfilename(
            title="Select Raw Forensic Disk Image",
            filetypes=[("Disk Images", "*.dd *.raw *.img *.vhd *.iso"), ("All Files", "*.*")]
        )
        if img_path:
            self.custom_image_path = os.path.abspath(img_path)
            self.refresh_targets()
            self.target_dropdown.set(f"📁 [DISK IMAGE] {os.path.basename(self.custom_image_path)}")

    def _start_scan(self):
        choice = self.target_dropdown.get()
        target_path = ""

        if self.custom_image_path and os.path.basename(self.custom_image_path) in choice:
            target_path = self.custom_image_path
        else:
            match = next((t for t in self.targets if t.get("display_name") == choice or t["device_id"] == choice), None)
            target_path = match["device_id"] if match else choice

        # Parse scan size limit
        size_str = self.scan_size_dropdown.get()
        size_map = {"100 MB": 100 * 1024 * 1024, "250 MB": 250 * 1024 * 1024, "500 MB": 500 * 1024 * 1024, "1 GB": 1024 * 1024 * 1024}
        max_bytes = size_map.get(size_str, 100 * 1024 * 1024)

        # Clear existing table rows
        for child in self.results_scroll.winfo_children():
            child.destroy()
        self.discovered_files = []

        self.scan_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.view_wb_btn.configure(state="disabled")
        self.scan_pb.set(0)

        strategy = self.engine_dropdown.get()
        thread = threading.Thread(target=self._run_carve_worker, args=(target_path, max_bytes, strategy), daemon=True)
        thread.start()

    def _stop_scan(self):
        self.scalpel_carver.cancel()
        self.tsk_recoverer.cancel()
        self.stop_btn.configure(state="disabled")

    def _run_carve_worker(self, target_path: str, max_bytes: int, strategy: str):
        try:
            case = self.case_manager.get_active_case()
            self.audit_service.log_event(
                action="FORENSIC_CARVE_STARTED",
                target=target_path,
                details={"strategy": strategy, "max_scan_bytes": max_bytes},
                case_id=case.get("case_id", "CASE-ZT-2026-001")
            )

            # 1. Run SleuthKit filesystem scan if requested
            if "SleuthKit" in strategy or "Hybrid" in strategy:
                tsk_items = self.tsk_recoverer.scan_deleted_files(target_path)
                for item in tsk_items:
                    c_file = CarvedFile(
                        file_id=item["item_id"],
                        file_type=item["file_type"],
                        extension=f".{item['file_type'].lower()}",
                        category="FILE_SYSTEM",
                        offset=0,
                        size=item["size_bytes"],
                        sha256="COMPUTED_ON_RESTORE",
                        confidence=1.0,
                        preview_snippet=item.get("original_name", ""),
                        source_target=target_path,
                        metadata=item
                    )
                    self._on_file_discovered(c_file)

            # 2. Run Scalpel deep carving if requested
            if "Scalpel" in strategy or "Hybrid" in strategy:
                self.scalpel_carver.carve_stream(
                    source_path=target_path,
                    total_bytes_to_scan=max_bytes,
                    progress_callback=self._update_progress,
                    file_found_callback=self._on_file_discovered
                )

            self.after(0, self._on_scan_finished)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Carving Error", str(e)))
            self.after(0, self._on_scan_finished)

    def _update_progress(self, data: dict):
        self.after(0, lambda: self._apply_telemetry(data))

    def _apply_telemetry(self, data: dict):
        speed = data.get("speed_mb_s", 0.0)
        self.stat_speed.configure(text=f"{speed:.2f} MB/s")

        scanned = data.get("bytes_scanned", 0)
        self.stat_scanned.configure(text=format_size(scanned))

        self.stat_found.configure(text=f"{len(self.discovered_files)} files")

        elapsed = data.get("elapsed_seconds", 0)
        m, s = divmod(elapsed, 60)
        h, m = divmod(m, 60)
        self.stat_time.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

        pct = data.get("percent", 0.0) / 100.0
        self.scan_pb.set(min(1.0, max(0.0, pct)))

    def _on_file_discovered(self, c_file: CarvedFile):
        # Validate structure if data available
        if c_file.data:
            val = RecoveryStructureValidator.validate_and_score(
                c_file.file_type, c_file.data, footer_matched=c_file.metadata.get("footer_matched", False)
            )
            c_file.confidence = val["confidence"]
            c_file.metadata["validation"] = val

        self.discovered_files.append(c_file)
        self.after(0, lambda: self._render_table_row(c_file))

    def _render_table_row(self, c: CarvedFile):
        row = ctk.CTkFrame(self.results_scroll, fg_color="#182230" if len(self.discovered_files) % 2 == 0 else "#141c26", corner_radius=2)
        row.pack(fill="x", pady=1)

        conf_pct = int(c.confidence * 100)
        conf_color = COLOR_ACCENT_GREEN if conf_pct >= 80 else (COLOR_ACCENT_AMBER if conf_pct >= 50 else COLOR_ACCENT_RED)

        struct_valid = "✅ Validated" if c.metadata.get("validation", {}).get("structural_check", True) else "⚠️ Raw"

        ctk.CTkLabel(row, text=c.file_id, font=ctk.CTkFont(size=10, weight="bold"), width=80, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=c.file_type, font=ctk.CTkFont(size=10), width=65, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=c.category, font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SECONDARY, width=90, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=format_size(c.size), font=ctk.CTkFont(size=10), width=85, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=f"0x{c.offset:X}", font=ctk.CTkFont(size=9, family="Courier"), width=95, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=f"{conf_pct}%", font=ctk.CTkFont(size=10, weight="bold"), text_color=conf_color, width=95, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=struct_valid, font=ctk.CTkFont(size=9), width=100, anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=c.sha256[:22] + "...", font=ctk.CTkFont(size=9, family="Courier"), text_color=COLOR_TEXT_MUTED, width=180, anchor="w").pack(side="left", padx=4)

    def _on_scan_finished(self):
        self.scan_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.view_wb_btn.configure(state="normal")
        self.scan_pb.set(1.0)
        self.stat_found.configure(text=f"{len(self.discovered_files)} files")

        if self.on_files_recovered_callback:
            self.on_files_recovered_callback(self.discovered_files)

        messagebox.showinfo(
            "Carving Completed",
            f"Forensic scan finished!\nDiscovered {len(self.discovered_files)} candidate artifacts.\nFiles are now ready for inspection and export in the Recovery Workbench."
        )

    def _open_workbench(self):
        # Notify master window to switch to workbench tab
        if hasattr(self.master.master, "select_tab"):
            self.master.master.select_tab("workbench")
