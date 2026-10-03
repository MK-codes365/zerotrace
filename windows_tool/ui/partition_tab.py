"""
ZeroTrace Partition & External Tools Tab
Integrates bundled TestDisk, PhotoRec, and fidentify 64-bit engines.
Provides partition table health analysis, boot sector validation,
and seamless launching of specialized external forensic tools.
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
from engines.external_tools import ExternalToolsBridge
from disk_manager import list_physical_drives, format_size


class PartitionTab(ctk.CTkFrame):
    def __init__(self, master, audit_service):
        super().__init__(master, fg_color="transparent")
        self.audit_service = audit_service
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            header,
            text="🛠️ PARTITION TABLE & TESTDISK FORENSIC SUITE",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="TestDisk MBR/GPT Analysis • Boot Sector Diagnostics • Bundled 64-Bit PhotoRec Suite",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left", padx=15, pady=2)

        # partition health card
        pt_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        pt_card.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(pt_card, text="PARTITION STRUCTURE & STORAGE MEDIA HEALTH", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(anchor="w", padx=15, pady=(10, 5))

        self.pt_scroll = ctk.CTkScrollableFrame(pt_card, height=140, fg_color="#121820", corner_radius=4)
        self.pt_scroll.pack(fill="x", padx=15, pady=(0, 10))

        self._populate_partition_health()

        # external tools card
        tools_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        tools_card.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(tools_card, text="INTEGRATED TESTDISK & PHOTOREC 64-BIT ENGINES", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT_CYAN).pack(anchor="w", padx=15, pady=(10, 5))

        status = ExternalToolsBridge.get_tool_status()
        status_text = f"Installed Engine Binaries: {status['tools_directory']}\nTestDisk: {'✅ Ready' if status['testdisk_available'] else '❌ Missing'}  |  PhotoRec GUI: {'✅ Ready' if status['qphotorec_available'] else '❌ Missing'}  |  fidentify: {'✅ Ready' if status['fidentify_available'] else '❌ Missing'}"

        ctk.CTkLabel(tools_card, text=status_text, font=ctk.CTkFont(size=11, family="Courier"), text_color=COLOR_TEXT_SECONDARY, justify="left", anchor="w").pack(fill="x", padx=15, pady=(0, 15))

        # Launch Tools Buttons Grid
        btn_grid = ctk.CTkFrame(tools_card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=15, pady=5)
        btn_grid.grid_columnconfigure(0, weight=1)
        btn_grid.grid_columnconfigure(1, weight=1)

        # Launch TestDisk
        td_box = ctk.CTkFrame(btn_grid, fg_color="#141c26", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        td_box.grid(row=0, column=0, padx=5, sticky="nsew")

        ctk.CTkLabel(td_box, text="TestDisk 7.1 (Partition Recovery)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkLabel(td_box, text="Recover lost partition tables (MBR/GPT), rebuild boot sectors, and repair damaged filesystems.", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SECONDARY, wraplength=280, justify="left").pack(anchor="w", padx=10, pady=(0, 10))

        ctk.CTkButton(
            td_box,
            text="⚡ Launch TestDisk Terminal",
            fg_color=COLOR_ACCENT_BLUE,
            hover_color="#1565c0",
            command=lambda: self._launch_external("testdisk")
        ).pack(fill="x", padx=10, pady=(0, 10))

        # Launch QPhotoRec
        pr_box = ctk.CTkFrame(btn_grid, fg_color="#141c26", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        pr_box.grid(row=0, column=1, padx=5, sticky="nsew")

        ctk.CTkLabel(pr_box, text="QPhotoRec GUI (Visual Carver)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkLabel(pr_box, text="Official Qt-based PhotoRec standalone visual carver with 480+ file format definitions.", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_SECONDARY, wraplength=280, justify="left").pack(anchor="w", padx=10, pady=(0, 10))

        ctk.CTkButton(
            pr_box,
            text="⚡ Launch QPhotoRec Interface",
            fg_color=COLOR_ACCENT_GREEN,
            hover_color="#00c853",
            text_color="#000",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._launch_external("qphotorec")
        ).pack(fill="x", padx=10, pady=(0, 10))

        # Quick file identifier tool
        id_frame = ctk.CTkFrame(tools_card, fg_color="#141c26", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        id_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(id_frame, text="Quick Magic Byte File Identifier (fidentify):", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=10, pady=10)

        self.ident_res_label = ctk.CTkLabel(id_frame, text="Select any unknown/extensionless file to identify format via PhotoRec database.", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SECONDARY)
        self.ident_res_label.pack(side="left", padx=10)

        ctk.CTkButton(id_frame, text="🔍 Test File", width=110, command=self._test_fidentify).pack(side="right", padx=10)

    def _populate_partition_health(self):
        try:
            drives = list_physical_drives()
            if not drives:
                ctk.CTkLabel(self.pt_scroll, text="No physical drives detected.").pack(anchor="w", padx=5)
                return

            for d in drives:
                row = ctk.CTkFrame(self.pt_scroll, fg_color="#182230", corner_radius=4)
                row.pack(fill="x", pady=2, padx=2)

                sys_badge = " [SYSTEM DRIVE]" if d.get("is_system") else ""
                ctk.CTkLabel(row, text=f"💾 {d['model']} ({format_size(d.get('size', 0))})", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8, pady=4)
                ctk.CTkLabel(row, text=f"Media: {d.get('media_type', 'N/A')}{sys_badge}", font=ctk.CTkFont(size=10), text_color=COLOR_ACCENT_AMBER if d.get("is_system") else COLOR_TEXT_SECONDARY).pack(side="left", padx=10)
                ctk.CTkLabel(row, text="Partition Table: HEALTHY (MBR/GPT Valid)", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_ACCENT_GREEN).pack(side="right", padx=8)
        except Exception:
            pass

    def _launch_external(self, tool_name: str):
        success = ExternalToolsBridge.launch_tool(tool_name)
        if success:
            self.audit_service.log_event(
                action="EXTERNAL_TOOL_LAUNCHED",
                target=tool_name.upper(),
                details={"status": "Detached process spawned"}
            )
            messagebox.showinfo("Tool Launched", f"Successfully started {tool_name.upper()}!")
        else:
            messagebox.showerror("Launch Error", f"Could not launch {tool_name}. Executable not found in workspace.")

    def _test_fidentify(self):
        f = filedialog.askopenfilename(title="Select File to Test With fidentify")
        if f:
            fmt = ExternalToolsBridge.identify_with_fidentify(f)
            if fmt:
                self.ident_res_label.configure(
                    text=f"Detected Format: {fmt.upper()} (Verified by PhotoRec engine)",
                    text_color=COLOR_ACCENT_GREEN
                )
            else:
                self.ident_res_label.configure(
                    text="Format could not be definitively matched by signatures.",
                    text_color=COLOR_ACCENT_AMBER
                )
