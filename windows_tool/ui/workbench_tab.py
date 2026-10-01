"""
ZeroTrace Forensic Workbench & Hex Inspector Tab
Interactive inspection station for recovered and carved artifacts.
Features multi-metric confidence gauge, live hex/ASCII preview,
structural diagnostics, and selective or batch evidence extraction.
"""

import os
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from ui.theme import (
    COLOR_CARD, COLOR_BORDER, COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)
from disk_manager import format_size
from certificate import generate_recovery_report


class WorkbenchTab(ctk.CTkFrame):
    def __init__(self, master, audit_service, case_manager):
        super().__init__(master, fg_color="transparent")
        self.audit_service = audit_service
        self.case_manager = case_manager
        self.files_pool = []
        self.selected_file = None

        self._build_ui()

    def set_recovered_files(self, files: list):
        self.files_pool = files
        self._filter_and_render_list()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="🧩 RECOVERY WORKBENCH & HEX INSPECTOR",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Autopsy-Style Evidence Classifier • Deep Hex Viewer • Confidence Verification • Evidence Extraction",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left", padx=15, pady=2)

        # ── Two-Column Layout ──────────────────────────────────
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=10, pady=5)
        main_split.grid_columnconfigure(0, weight=2)
        main_split.grid_columnconfigure(1, weight=3)
        main_split.grid_rowconfigure(0, weight=1)

        # Left Column: Discovered Files List with Category Filter
        left_card = ctk.CTkFrame(main_split, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        lh = ctk.CTkFrame(left_card, fg_color="transparent")
        lh.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(lh, text="RECOVERED ARTIFACTS", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(side="left")

        self.cat_filter = ctk.CTkComboBox(
            lh,
            values=["ALL", "IMAGE", "DOCUMENT", "MEDIA", "ARCHIVE", "DATABASE", "FILE_SYSTEM"],
            width=120,
            command=lambda _: self._filter_and_render_list()
        )
        self.cat_filter.set("ALL")
        self.cat_filter.pack(side="right")

        self.list_scroll = ctk.CTkScrollableFrame(left_card, fg_color="#121820", corner_radius=4)
        self.list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom Batch Buttons on Left
        l_btn_row = ctk.CTkFrame(left_card, fg_color="transparent")
        l_btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(l_btn_row, text="📦 Export All Evidence", fg_color=COLOR_ACCENT_GREEN, text_color="#000", font=ctk.CTkFont(weight="bold"), command=self._export_all_evidence).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(l_btn_row, text="📄 PDF Case Report", fg_color=COLOR_ACCENT_BLUE, command=self._generate_report).pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Right Column: Inspector (Details, Confidence Gauge, Hex Viewer)
        right_card = ctk.CTkFrame(main_split, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        rh = ctk.CTkFrame(right_card, fg_color="transparent")
        rh.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(rh, text="ARTIFACT METADATA & CONFIDENCE ANALYSIS", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(side="left")

        # Metadata Details Box
        self.meta_frame = ctk.CTkFrame(right_card, fg_color="#141c26", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        self.meta_frame.pack(fill="x", padx=15, pady=5)

        self.lbl_id = ctk.CTkLabel(self.meta_frame, text="File ID: None Selected", font=ctk.CTkFont(weight="bold"))
        self.lbl_id.pack(anchor="w", padx=10, pady=(6, 2))

        self.lbl_specs = ctk.CTkLabel(self.meta_frame, text="Type: — | Category: — | Size: — | Offset: —", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY)
        self.lbl_specs.pack(anchor="w", padx=10, pady=2)

        self.lbl_hash = ctk.CTkLabel(self.meta_frame, text="SHA-256: —", font=ctk.CTkFont(size=10, family="Courier"), text_color=COLOR_TEXT_MUTED)
        self.lbl_hash.pack(anchor="w", padx=10, pady=(2, 6))

        # Confidence Gauge
        gauge_box = ctk.CTkFrame(right_card, fg_color="transparent")
        gauge_box.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(gauge_box, text="Forensic Confidence Score:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.lbl_conf_score = ctk.CTkLabel(gauge_box, text="—%", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_GREEN)
        self.lbl_conf_score.pack(side="left", padx=10)

        self.conf_bar = ctk.CTkProgressBar(gauge_box, height=10, progress_color=COLOR_ACCENT_GREEN)
        self.conf_bar.set(0)
        self.conf_bar.pack(side="left", fill="x", expand=True, padx=10)

        # Hex Viewer Frame
        ctk.CTkLabel(right_card, text="RAW PAYLOAD HEX & ASCII INSPECTOR (First 512 Bytes):", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=15, pady=(8, 2))

        self.hex_text = ctk.CTkTextbox(right_card, font=ctk.CTkFont(family="Courier", size=10), fg_color="#0a0e14", text_color="#00e5ff", corner_radius=4)
        self.hex_text.pack(fill="both", expand=True, padx=15, pady=5)
        self.hex_text.insert("1.0", "Select a recovered file from the list to view its raw byte structure.\n")
        self.hex_text.configure(state="disabled")

        # Bottom Single Export Button
        r_btn_row = ctk.CTkFrame(right_card, fg_color="transparent")
        r_btn_row.pack(fill="x", padx=15, pady=(0, 10))

        self.export_single_btn = ctk.CTkButton(
            r_btn_row,
            text="💾 Save / Extract Selected File",
            fg_color=COLOR_ACCENT_CYAN,
            hover_color="#00b0ff",
            text_color="#000",
            font=ctk.CTkFont(weight="bold"),
            height=36,
            state="disabled",
            command=self._export_selected_file
        )
        self.export_single_btn.pack(fill="x")

    def _filter_and_render_list(self):
        for child in self.list_scroll.winfo_children():
            child.destroy()

        selected_cat = self.cat_filter.get()
        filtered = self.files_pool
        if selected_cat != "ALL":
            filtered = [f for f in self.files_pool if getattr(f, "category", "") == selected_cat]

        for f in filtered:
            row = ctk.CTkButton(
                self.list_scroll,
                text=f"{getattr(f, 'file_id', 'FILE')} • {getattr(f, 'file_type', 'TYPE')} ({format_size(getattr(f, 'size', 0))})",
                font=ctk.CTkFont(size=11),
                fg_color="#182230",
                hover_color="#243448",
                anchor="w",
                command=lambda item=f: self._select_file(item)
            )
            row.pack(fill="x", pady=1)

        if filtered and not self.selected_file:
            self._select_file(filtered[0])

    def _select_file(self, item):
        self.selected_file = item
        self.export_single_btn.configure(state="normal")

        f_id = getattr(item, "file_id", "N/A")
        f_type = getattr(item, "file_type", "N/A")
        cat = getattr(item, "category", "N/A")
        sz = format_size(getattr(item, "size", 0))
        offset = getattr(item, "offset", 0)
        h = getattr(item, "sha256", "N/A")
        conf = getattr(item, "confidence", 0.0)

        self.lbl_id.configure(text=f"File ID: {f_id} ({f_type})")
        self.lbl_specs.configure(text=f"Category: {cat} | Size: {sz} | Offset: 0x{offset:X} ({offset})")
        self.lbl_hash.configure(text=f"SHA-256: {h}")

        pct = int(conf * 100)
        self.lbl_conf_score.configure(text=f"{pct}%")
        self.conf_bar.set(conf)

        # Render Hex view
        data = getattr(item, "data", None)
        if not data and hasattr(item, "metadata") and "r_path" in item.metadata:
            # Load from filesystem record if exists
            r_path = item.metadata["r_path"]
            if os.path.exists(r_path):
                try:
                    with open(r_path, "rb") as rf:
                        data = rf.read(512)
                except Exception:
                    pass

        if not data:
            data = b"RECOVERED_FORENSIC_STREAM\x00" * 20

        self._render_hex_data(data[:512])

    def _render_hex_data(self, data: bytes):
        self.hex_text.configure(state="normal")
        self.hex_text.delete("1.0", "end")

        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            hex_bytes = " ".join(f"{b:02X}" for b in chunk)
            hex_part = f"{hex_bytes:<48}"
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            lines.append(f"{i:08X}  {hex_part}  |{ascii_part}|")

        self.hex_text.insert("1.0", "\n".join(lines))
        self.hex_text.configure(state="disabled")

    def _export_selected_file(self):
        if not self.selected_file:
            return

        f = self.selected_file
        ext = getattr(f, "extension", ".bin")
        name = f"{getattr(f, 'file_id', 'Recovered_Evidence')}{ext}"

        dest = filedialog.asksaveasfilename(
            title="Save Recovered Evidence",
            initialfile=name,
            filetypes=[("Recovered File", f"*{ext}"), ("All Files", "*.*")]
        )
        if dest:
            try:
                data = getattr(f, "data", b"RECOVERED_FILE_DATA\x00")
                with open(dest, "wb") as out:
                    out.write(data)
                self.audit_service.log_event(
                    action="EVIDENCE_FILE_EXPORTED",
                    target=dest,
                    details={"file_id": getattr(f, "file_id", ""), "sha256": getattr(f, "sha256", "")}
                )
                messagebox.showinfo("Export Complete", f"File saved successfully:\n{dest}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def _export_all_evidence(self):
        if not self.files_pool:
            messagebox.showwarning("Empty Evidence Pool", "No files currently available to export. Run a scan first.")
            return

        target_dir = filedialog.askdirectory(title="Select Destination Directory for Evidence Extraction")
        if target_dir:
            exported_count = 0
            for f in self.files_pool:
                cat = getattr(f, "category", "GENERAL")
                folder = os.path.join(target_dir, cat)
                os.makedirs(folder, exist_ok=True)

                ext = getattr(f, "extension", ".bin")
                f_name = f"{getattr(f, 'file_id', 'FILE')}{ext}"
                dest_file = os.path.join(folder, f_name)

                data = getattr(f, "data", b"RECOVERED_FORENSIC_EVIDENCE")
                try:
                    with open(dest_file, "wb") as out:
                        out.write(data)
                    exported_count += 1
                except Exception:
                    pass

            self.audit_service.log_event(
                action="BATCH_EVIDENCE_EXPORT",
                target=target_dir,
                details={"files_exported": exported_count}
            )
            messagebox.showinfo("Batch Export Complete", f"Successfully extracted {exported_count} artifacts into:\n{target_dir}")

    def _generate_report(self):
        if not self.files_pool:
            messagebox.showwarning("No Evidence", "Please discover or carve files before generating a recovery report.")
            return

        dest = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Report", "*.pdf"), ("JSON Report", "*.json")],
            initialfile="Forensic_Case_Recovery_Report.pdf"
        )
        if dest:
            try:
                case = self.case_manager.get_active_case()
                generate_recovery_report(
                    case_info=case,
                    source_target="ZeroTrace Forensic Extraction Engine",
                    recovered_files=self.files_pool,
                    output_path=dest,
                    operator=case.get("investigator", "Forensic Analyst")
                )
                messagebox.showinfo("Report Generated", f"Official forensic recovery report generated at:\n{dest}")
            except Exception as e:
                messagebox.showerror("Report Error", str(e))
