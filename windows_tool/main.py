"""
ZeroTrace — Unified Defensive Forensics & Data Sanitization Workstation
Developed according to NTRO SIH26149 specifications.
Integrates:
1. Module 1: Secure Drive Eraser (Nwipe & ShredOS Inspired)
2. Module 2: Secure File & Folder Eraser (Selective Shredding & Metadata Cleansing)
3. Module 3: Advanced File Carving & Recovery (Scalpel & SleuthKit & TestDisk/PhotoRec)
4. Recovery Workbench & Hex Inspector
5. Partition Diagnostics & External Forensic Suite Launcher
6. Tamper-Evident Hash-Chained Audit Trail & Chain of Custody
"""

import os
import sys

# 1. Ensure local tool directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# 2. Check and add local .venv site-packages if present (handles running outside activated venv)
_venv_site = os.path.join(_current_dir, ".venv", "Lib", "site-packages")
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

# 3. Check and add user site-packages if running in an elevated Admin shell where user site is excluded
try:
    import site
    _user_site = site.getusersitepackages()
    if isinstance(_user_site, str) and os.path.isdir(_user_site) and _user_site not in sys.path:
        sys.path.insert(0, _user_site)
except Exception:
    pass

# 4. Check known user Python314 site-packages
for _cand in [
    os.path.expanduser(r"~\AppData\Local\Programs\Python\Python314\Lib\site-packages"),
    r"C:\Users\mukui\AppData\Local\Programs\Python\Python314\Lib\site-packages",
]:
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.append(_cand)

import tkinter as tk
from tkinter import messagebox

try:
    import customtkinter as ctk
except ModuleNotFoundError:
    import subprocess
    print("[*] customtkinter not found in current environment. Attempting automatic installation...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "wmi", "pywin32", "fpdf", "darkdetect", "pillow"])
        import customtkinter as ctk
    except Exception as _e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "ZeroTrace Dependency Error",
            f"Missing required package 'customtkinter'.\n\nPlease run:\n{sys.executable} -m pip install customtkinter\n\nError: {_e}"
        )
        sys.exit(1)

from ui.theme import (
    COLOR_BG_DARK, COLOR_SIDEBAR, COLOR_CARD, COLOR_BORDER,
    COLOR_ACCENT_CYAN, COLOR_ACCENT_GREEN, COLOR_ACCENT_RED, COLOR_ACCENT_AMBER,
    COLOR_ACCENT_BLUE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)
from core.audit import AuditService
from core.case_manager import CaseManager
from ui.drive_wiper_tab import DriveWiperTab
from ui.file_shredder_tab import FileShredderTab
from ui.carver_recovery_tab import CarverRecoveryTab
from ui.workbench_tab import WorkbenchTab
from ui.partition_tab import PartitionTab
from ui.audit_tab import AuditTab

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


class ZeroTraceForensicsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ZeroTrace — Defensive Cybersecurity, Forensics & Data Sanitization Platform")
        self.geometry("1180x760")
        self.minsize(1040, 680)

        # Set App Icon if present
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Core Services
        self.audit_service = AuditService()
        self.case_manager = CaseManager()

        # License state
        self.license_plan = "Enterprise Forensic Edition"

        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # sidebar navigation
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Sidebar Logo & Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=15, pady=(20, 15))

        ctk.CTkLabel(
            logo_frame,
            text="⚡ ZERO-TRACE",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_ACCENT_CYAN
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Defensive Forensic & Sanitization Suite",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(anchor="w")

        # Nav Buttons Container
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=10)

        self.nav_buttons = {}
        tabs = [
            ("drive_wiper", "🛡️ Secure Drive Eraser", "Module 1"),
            ("file_shredder", "🗂️ File & Folder Eraser", "Module 2"),
            ("carver", "🔍 File Carving & Recovery", "Module 3"),
            ("workbench", "🧩 Recovery Workbench", "Analyzer"),
            ("partition", "🛠️ Partition & TestDisk", "Diagnostics"),
            ("audit", "📜 Audit & Chain of Custody", "Compliance"),
        ]

        for tab_id, label, badge in tabs:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=f"{label}",
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                hover_color="#212a36",
                text_color=COLOR_TEXT_SECONDARY,
                height=42,
                corner_radius=6,
                command=lambda tid=tab_id: self.select_tab(tid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[tab_id] = btn

        # Sidebar Footer (Case & License details)
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="#10151c", corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=15)

        case = self.case_manager.get_active_case()
        ctk.CTkLabel(footer_frame, text=f"CASE: {case.get('case_id', 'DEFAULT')}", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_ACCENT_GREEN).pack(anchor="w", padx=10, pady=(6, 2))
        ctk.CTkLabel(footer_frame, text=f"Tier: {self.license_plan}", font=ctk.CTkFont(size=9), text_color=COLOR_TEXT_MUTED).pack(anchor="w", padx=10, pady=(0, 6))

        # main content area
        self.content_container = ctk.CTkFrame(self, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")

        # Top System Status Bar
        top_bar = ctk.CTkFrame(self.content_container, height=36, fg_color="#121820", corner_radius=0)
        top_bar.pack(fill="x")

        ctk.CTkLabel(
            top_bar,
            text="ZEROTRACE FORENSIC WORKSTATION • DEFENSIVE CYBERSECURITY & MEDIA SANITIZATION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=15, pady=8)

        self.sys_status_badge = ctk.CTkLabel(
            top_bar,
            text="🟢 SECURE SYSTEM READY",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLOR_ACCENT_GREEN
        )
        self.sys_status_badge.pack(side="right", padx=15, pady=8)

        # Tab Views Holder
        self.tab_views = {}

        self.drive_wiper_view = DriveWiperTab(self.content_container, self.audit_service, self.case_manager)
        self.tab_views["drive_wiper"] = self.drive_wiper_view

        self.file_shredder_view = FileShredderTab(self.content_container, self.audit_service, self.case_manager)
        self.tab_views["file_shredder"] = self.file_shredder_view

        self.workbench_view = WorkbenchTab(self.content_container, self.audit_service, self.case_manager)
        self.tab_views["workbench"] = self.workbench_view

        self.carver_view = CarverRecoveryTab(
            self.content_container,
            self.audit_service,
            self.case_manager,
            on_files_recovered_callback=self._on_files_recovered
        )
        self.tab_views["carver"] = self.carver_view

        self.partition_view = PartitionTab(self.content_container, self.audit_service)
        self.tab_views["partition"] = self.partition_view

        self.audit_view = AuditTab(self.content_container, self.audit_service, self.case_manager)
        self.tab_views["audit"] = self.audit_view

        # Default Tab
        self.current_tab_id = None
        self.select_tab("drive_wiper")

    def select_tab(self, tab_id: str):
        if self.current_tab_id == tab_id:
            return

        # Hide current tab
        if self.current_tab_id and self.current_tab_id in self.tab_views:
            self.tab_views[self.current_tab_id].pack_forget()
            self.nav_buttons[self.current_tab_id].configure(
                fg_color="transparent",
                text_color=COLOR_TEXT_SECONDARY
            )

        # Show new tab
        self.current_tab_id = tab_id
        if tab_id in self.tab_views:
            if tab_id == "workbench" and hasattr(self, "carver_view") and getattr(self.carver_view, "discovered_files", None):
                self.workbench_view.set_recovered_files(
                    self.carver_view.discovered_files,
                    fs_architecture=self.carver_view._current_architecture(),
                )
            self.tab_views[tab_id].pack(fill="both", expand=True)
            self.nav_buttons[tab_id].configure(
                fg_color="#1e293b",
                text_color=COLOR_ACCENT_CYAN
            )

    def _on_files_recovered(self, files: list, fs_architecture: dict = None):
        """Pass discovered files and volume architecture from Carver to Workbench."""
        self.workbench_view.set_recovered_files(files, fs_architecture=fs_architecture)


def main():
    app = ZeroTraceForensicsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
