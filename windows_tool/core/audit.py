"""
ZeroTrace Core - Tamper-Evident Hash-Chained Audit Logging
Maintains an immutable cryptographic hash chain where each event's hash
incorporates the hash of the preceding event, ensuring tamper-evidence.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable, Optional
from core.crypto import sha256_bytes, generate_tamper_signature

AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audit_trail.json")
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AuditService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_path: str = AUDIT_LOG_FILE, mirror_to_frontend: bool = True):
        if self._initialized:
            return
        self.log_path = log_path
        # The dashboard mirror is on by default for live feeds; harnesses and
        # offline analyses switch it off so test runs never overwrite the
        # committed frontend audit trail.
        self.mirror_to_frontend = mirror_to_frontend
        self.events: List[Dict[str, Any]] = []
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self._load_or_initialize()
        self._initialized = True

    def _load_or_initialize(self):
        """Load existing chain from file or create genesis block."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.events = data
                        return
            except Exception as e:
                print(f"[AUDIT] Warning: Could not read audit log ({e}), initializing fresh chain.")

        self.events = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Create genesis block for the hash chain."""
        now = datetime.now(timezone.utc).isoformat()
        operator = os.environ.get("USERNAME", "FORENSIC_INVESTIGATOR")
        payload = {
            "index": 0,
            "timestamp": now,
            "case_id": "DEFAULT-CASE",
            "operator": operator,
            "action": "SYSTEM_GENESIS",
            "target": "ZeroTrace Platform",
            "details": {"system": "ZeroTrace Digital Forensics Platform Initialized"},
            "prev_hash": GENESIS_HASH,
        }
        serialized = json.dumps(payload, sort_keys=True)
        event_hash = sha256_bytes(serialized.encode("utf-8"))
        payload["event_hash"] = event_hash
        payload["signature"] = generate_tamper_signature(event_hash)
        self.events.append(payload)
        self._persist()

    def log_event(
        self,
        action: str,
        target: str,
        details: Dict[str, Any],
        case_id: str = "DEFAULT-CASE",
        operator: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Append a new tamper-evident event to the hash chain.
        """
        if not operator:
            operator = os.environ.get("USERNAME", "FORENSIC_INVESTIGATOR")

        now = datetime.now(timezone.utc).isoformat()
        prev_hash = self.events[-1]["event_hash"] if self.events else GENESIS_HASH
        index = len(self.events)

        event = {
            "index": index,
            "timestamp": now,
            "case_id": case_id,
            "operator": operator,
            "action": action,
            "target": target,
            "details": details,
            "prev_hash": prev_hash,
        }

        serialized = json.dumps(event, sort_keys=True)
        event_hash = sha256_bytes(serialized.encode("utf-8"))
        event["event_hash"] = event_hash
        event["signature"] = generate_tamper_signature(event_hash)

        self.events.append(event)
        self._persist()

        # Notify active UI subscribers
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception:
                pass

        return event

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to real-time audit events for UI feeds."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _persist(self):
        """Save audit chain to disk."""
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=2)
            
            # Sync to frontend public folder for live dashboard view
            if not self.mirror_to_frontend:
                return
            public_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "platform", "frontend", "public", "audit_trail.json")
            )
            os.makedirs(os.path.dirname(public_path), exist_ok=True)
            with open(public_path, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            print(f"[AUDIT] Error persisting audit trail: {e}")

    def verify_chain(self) -> Dict[str, Any]:
        """
        Cryptographically verify the integrity of the entire audit chain.
        Detects tampering, deleted events, modified timestamps or details.
        """
        if not self.events:
            return {"valid": False, "reason": "Audit chain is empty", "tampered_index": None}

        expected_prev_hash = GENESIS_HASH

        for i, event in enumerate(self.events):
            if event.get("index") != i:
                return {
                    "valid": False,
                    "reason": f"Index sequence broken at block {i}",
                    "tampered_index": i,
                }

            if event.get("prev_hash") != expected_prev_hash:
                return {
                    "valid": False,
                    "reason": f"Hash chain broken at block {i}: prev_hash mismatch",
                    "tampered_index": i,
                }

            # Re-compute hash
            test_payload = {
                "index": event["index"],
                "timestamp": event["timestamp"],
                "case_id": event["case_id"],
                "operator": event["operator"],
                "action": event["action"],
                "target": event["target"],
                "details": event["details"],
                "prev_hash": event["prev_hash"],
            }
            serialized = json.dumps(test_payload, sort_keys=True)
            recalculated_hash = sha256_bytes(serialized.encode("utf-8"))

            if recalculated_hash != event.get("event_hash"):
                return {
                    "valid": False,
                    "reason": f"Block content tampered at block {i}",
                    "tampered_index": i,
                }

            expected_prev_hash = event["event_hash"]

        return {
            "valid": True,
            "total_blocks": len(self.events),
            "latest_hash": self.events[-1]["event_hash"],
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.events[-limit:]

    def log_filesystem_analysis(
        self,
        target: str,
        architecture: Dict[str, Any],
        cluster_runs: Optional[List[Dict[str, Any]]] = None,
        records_recovered: int = 0,
        case_id: str = "DEFAULT-CASE",
        max_runs_logged: int = 200,
    ) -> Dict[str, Any]:
        """
        Append the filesystem architecture, cluster runs and allocation states of
        a recovery scan to the hash chain.

        Every payload is folded through SHA-256 before it is signed, so the
        recorded allocation state of a volume cannot be altered without
        invalidating the chain (see :meth:`verify_chain`).
        """
        cluster_runs = list(cluster_runs or [])

        allocation = architecture.get("allocation") or {}
        geometry = {
            key: architecture.get(key)
            for key in (
                "filesystem",
                "revision",
                "serial_number",
                "sector_size",
                "cluster_size",
                "cluster_count",
                "usable_clusters",
                "fat_offset_bytes",
                "fat_length_bytes",
                "cluster_heap_offset_bytes",
                "root_cluster",
                "volume_label",
                "volume_bytes",
                "boot_checksum",
                "boot_warnings",
                "geometry_source",
            )
        }
        geometry = {k: v for k, v in geometry.items() if v not in (None, "", [], {})}

        allocation_state = {
            "allocated": allocation.get("allocated", 0),
            "free": allocation.get("free", 0),
            "bad": allocation.get("bad", 0),
            "reserved": allocation.get("reserved", 0),
        }

        fragment_summary = {
            "total_runs": len(cluster_runs),
            "contiguous": sum(1 for r in cluster_runs if r.get("contiguous")),
            "fragmented": sum(1 for r in cluster_runs if not r.get("contiguous")),
            "no_fat_chain": sum(1 for r in cluster_runs if r.get("no_fat_chain")),
            "truncated_chains": sum(1 for r in cluster_runs if r.get("truncated_chain")),
            "severed_chains_rejoined": sum(1 for r in cluster_runs if r.get("gap_healed")),
        }

        details = {
            "geometry": geometry,
            "allocation_state": allocation_state,
            "fragmentation": fragment_summary,
            "records_recovered": records_recovered,
        }

        summary_event = self.log_event(
            action="FILESYSTEM_ARCHITECTURE_ANALYZED",
            target=target,
            details=details,
            case_id=case_id,
        )

        truncated_note = (
            f" (first {max_runs_logged} of {len(cluster_runs)})"
            if len(cluster_runs) > max_runs_logged
            else ""
        )
        for run in cluster_runs[:max_runs_logged]:
            run_payload = {
                "item_id": run.get("item_id"),
                "name": run.get("name"),
                "first_cluster": run.get("first_cluster"),
                "cluster_count": run.get("cluster_count"),
                "fragment_count": run.get("fragment_count"),
                "runs": run.get("runs"),
                "contiguous": run.get("contiguous"),
                "no_fat_chain": run.get("no_fat_chain"),
                "allocated_clusters": run.get("allocated_clusters"),
                "free_clusters": run.get("free_clusters"),
                "bad_clusters": run.get("bad_clusters"),
                "truncated_chain": run.get("truncated_chain"),
                "gap_healed": run.get("gap_healed", False),
                "gap_repair_notes": run.get("gap_repair_notes") or [],
                "data_length": run.get("data_length"),
                "checksum_valid": run.get("checksum_valid"),
                "name_hash_valid": run.get("name_hash_valid"),
            }
            self.log_event(
                action="CLUSTER_RUN_ALLOCATION_RECORDED",
                target=f"{target}::{run.get('item_id')}",
                details={
                    "cluster_run": run_payload,
                    "payload_sha256": run.get("payload_sha256", ""),
                    "cluster_run_sha256": sha256_bytes(
                        json.dumps(run_payload, sort_keys=True).encode("utf-8")
                    ),
                },
                case_id=case_id,
            )

        return summary_event
