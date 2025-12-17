import sys
import os
from cx_Freeze import setup, Executable

dll_path = "wiper_core.dll"
dll_exists = os.path.exists(dll_path)

build_exe_options = {
    "packages": ["customtkinter", "wmi", "win32com", "fpdf", "os", "sys", "threading", "tkinter", "ctypes"],
    "excludes": [],
    "include_files": [
        ("disk_manager.py", "disk_manager.py"),
        ("wiper.py", "wiper.py"),
        ("certificate.py", "certificate.py"),
        ("icon.ico", "icon.ico")
    ] + ([(dll_path, dll_path)] if dll_exists else [])
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ZeroTrace",
    version="1.4.0",
    description="Secure Data Wiping Tool with Partition Support",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="ZeroTrace.exe", shortcut_name="ZeroTrace", shortcut_dir="DesktopFolder", icon="icon.ico")]
)
