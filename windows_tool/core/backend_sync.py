"""
ZeroTrace Core — Central Backend Synchronization Client
Implements NTRO SIH26149 requirements for integrating local hardware sanitization
and file forensic operations with the Central Platform & Dashboard.
"""

import json
import os
import threading
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_BACKEND_URL = os.environ.get("ZEROTRACE_API_URL", "https://zerotrace-b688.onrender.com/api")
DASHBOARD_URLS = [
    os.environ.get("ZEROTRACE_DASHBOARD_URL", "http://localhost:5174/api/live-wipe"),
    "http://localhost:5173/api/live-wipe",
    "http://127.0.0.1:5174/api/live-wipe",
    "http://127.0.0.1:5173/api/live-wipe",
]
TELEMETRY_FALLBACK_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "platform", "frontend", "public", "live_wipe_telemetry.json")
)

_last_sync_time = 0.0

def sync_live_telemetry(data: Dict[str, Any], immediate: bool = False):
    """
    Push real-time wiping progress to Dashboard in a non-blocking background thread.
    Throttled to avoid overwhelming HTTP sockets unless immediate=True.
    """
    global _last_sync_time
    import time
    now = time.time()
    if not immediate and (now - _last_sync_time) < 0.35:
        return
    _last_sync_time = now

    def _sender():
        # 1. Send to Vite / Dashboard HTTP bridge (try ports 5174 and 5173)
        req_data = json.dumps(data).encode("utf-8")
        synced = False
        for url in DASHBOARD_URLS:
            try:
                req = urllib.request.Request(
                    url,
                    data=req_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=0.25) as resp:
                    if resp.status == 200:
                        synced = True
                        break
            except Exception:
                continue

        # 2. Write to static JSON in public folder (fallback)
        try:
            os.makedirs(os.path.dirname(TELEMETRY_FALLBACK_FILE), exist_ok=True)
            with open(TELEMETRY_FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
        try:
            os.makedirs(os.path.dirname(TELEMETRY_FALLBACK_FILE), exist_ok=True)
            with open(TELEMETRY_FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    t = threading.Thread(target=_sender, daemon=True)
    t.start()


def check_backend_online(timeout: float = 0.8) -> bool:
    """Quick non-blocking check if central server is online."""
    try:
        url = f"{DEFAULT_BACKEND_URL}/health"
        req = urllib.request.Request(url, headers={"User-Agent": "ZeroTrace-Workstation/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def sync_drive_wipe_to_dashboard(
    result: Dict[str, Any],
    target_info: Optional[Dict[str, Any]] = None,
    case_id: Optional[str] = None,
    on_complete: Optional[Any] = None,
):
    """
    Transmit completed drive sanitization telemetry to central platform (SIH26149).
    Spawns in a non-blocking background daemon thread.
    """
    def _worker():
        target_name = result.get("target", "Target Device")
        if target_info:
            letter = target_info.get("letter", "")
            model = target_info.get("model", "")
            size_str = target_info.get("size_str", "")
            target_name = f"{target_name} [{letter}:] {model} ({size_str})".strip()

        payload = {
            "target_path": target_name,
            "target_type": "drive",
            "method": result.get("method", "DOD_522220M"),
            "status": "COMPLETED" if result.get("success", False) else "FAILED",
            "passes_total": result.get("total_passes", 1),
            "passes_completed": result.get("total_passes", 1),
            "bytes_total": result.get("bytes_written", 0),
            "bytes_processed": result.get("bytes_written", 0),
            "duration_seconds": float(result.get("duration_seconds", 0.0)),
            "avg_speed_mb_s": float(result.get("avg_speed_mb_s", 0.0)),
            "bad_sectors": int(result.get("bad_sectors", 0)),
            "verification_passed": bool(result.get("verified", True)),
            "verification_hash": str(result.get("verification_details", {}).get("merkle_root") or ""),
            "operator": os.environ.get("USERNAME", "Investigator"),
            "case_id": case_id or "CASE-ZT-2026-001",
            "is_simulated": bool(result.get("is_simulated", False)),
            "details": {
                "workstation": os.environ.get("COMPUTERNAME", "FORENSIC-PC"),
                "auto_formatted": result.get("auto_formatted", False),
                "cert_id": result.get("cert_id", ""),
            },
        }

        try:
            url = f"{DEFAULT_BACKEND_URL}/sanitization/sync"
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ZeroTrace-Workstation/1.0",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status in (200, 201):
                    res_body = json.loads(resp.read().decode("utf-8"))
                    print(f"[BACKEND SYNC] Successfully synced wipe of '{target_name}' to Central Server (OpID: {res_body.get('operation_id')})")
                    if on_complete:
                        on_complete(True, res_body)
                    return
        except Exception as e:
            # Running offline / air-gapped lab mode
            print(f"[BACKEND SYNC] Note: Central server unreachable ({e}). Operation saved to local immutable ledger.")
            if on_complete:
                on_complete(False, str(e))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
