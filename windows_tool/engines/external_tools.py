"""
ZeroTrace External Forensic Tools Bridge
Integrates bundled TestDisk, PhotoRec, and fidentify 64-bit engines
located in the workspace into the desktop application.
"""

import os
import subprocess
from typing import Optional, Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
candidate_dirs = [
    os.path.join(WORKSPACE_ROOT, "reference_repos", "autopsy", "thirdparty", "photorec_exec", "64-bit", "bin"),
    os.path.join(WORKSPACE_ROOT, "autopsy", "thirdparty", "photorec_exec", "64-bit", "bin"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin"),
]
TOOLS_DIR = next((d for d in candidate_dirs if os.path.isdir(d)), candidate_dirs[0])

FIDENTIFY_EXE = os.path.join(TOOLS_DIR, "fidentify_win.exe")
PHOTOREC_EXE = os.path.join(TOOLS_DIR, "photorec_win.exe")
QPHOTOREC_EXE = os.path.join(TOOLS_DIR, "qphotorec_win.exe")
TESTDISK_EXE = os.path.join(TOOLS_DIR, "testdisk_win.exe")


class ExternalToolsBridge:
    """
    Bridge to PhotoRec, TestDisk, and fidentify executables.
    """

    @classmethod
    def get_tool_status(cls) -> Dict[str, Any]:
        """Check availability of external forensic binaries."""
        return {
            "tools_directory": TOOLS_DIR,
            "fidentify_available": os.path.isfile(FIDENTIFY_EXE),
            "photorec_available": os.path.isfile(PHOTOREC_EXE),
            "qphotorec_available": os.path.isfile(QPHOTOREC_EXE),
            "testdisk_available": os.path.isfile(TESTDISK_EXE),
        }

    @classmethod
    def identify_with_fidentify(cls, target_file: str) -> Optional[str]:
        """
        Run fidentify_win.exe to identify file format using PhotoRec's database.
        """
        if not os.path.isfile(FIDENTIFY_EXE) or not os.path.isfile(target_file):
            return None

        try:
            res = subprocess.run(
                [FIDENTIFY_EXE, target_file],
                cwd=TOOLS_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout:
                # Output format: <filepath>: <format_extension>
                lines = res.stdout.strip().split("\n")
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 1)
                        return parts[1].strip()
            return None
        except Exception:
            return None

    @classmethod
    def launch_tool(cls, tool_name: str) -> bool:
        """
        Launch external tool in detached process (e.g. QPhotoRec or TestDisk).
        """
        target_map = {
            "qphotorec": QPHOTOREC_EXE,
            "testdisk": TESTDISK_EXE,
            "photorec": PHOTOREC_EXE,
        }
        exe_path = target_map.get(tool_name.lower())
        if not exe_path or not os.path.isfile(exe_path):
            return False

        try:
            if tool_name.lower() in ("testdisk", "photorec"):
                # Console app launched in new terminal
                subprocess.Popen(
                    f'start "ZeroTrace - {tool_name.upper()}" "{exe_path}"',
                    cwd=TOOLS_DIR,
                    shell=True,
                )
            else:
                # GUI app (QPhotoRec)
                subprocess.Popen([exe_path], cwd=TOOLS_DIR)
            return True
        except Exception:
            return False
