"""
ZEROTrace — Forensic & Sanitization Processing Engines
"""
import sys
import os

_platform_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend_root = os.path.join(_platform_root, "backend")

if _platform_root not in sys.path:
    sys.path.insert(0, _platform_root)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)
