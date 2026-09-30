"""
ZeroTrace Core - Case and Evidence Management
Inspired by Autopsy digital forensic case workflows.
Manages investigation cases, evidence acquisition records, and chain-of-custody metadata.
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from core.crypto import sha256_file

CASES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "forensic_cases.json")


class CaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_path: str = CASES_FILE):
        if self._initialized:
            return
        self.storage_path = storage_path
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.active_case_id: str = "CASE-ZT-2026-001"
        self._load()
        self._initialized = True

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cases = data.get("cases", {})
                    self.active_case_id = data.get("active_case_id", "CASE-ZT-2026-001")
                    if self.cases:
                        return
            except Exception as e:
                print(f"[CASE] Warning loading cases ({e}), creating default.")

        # Default ZeroTrace Case
        self.create_case(
            case_id="CASE-ZT-2026-001",
            title="ZeroTrace Digital Forensic Investigation & Media Sanitization",
            agency="ZeroTrace Forensic Laboratories",
            investigator=os.environ.get("USERNAME", "Lead Investigator"),
            description="Forensic examination and secure sanitization verification audit.",
        )

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"active_case_id": self.active_case_id, "cases": self.cases}, f, indent=2)

            # Sync to frontend public folder for live dashboard view
            public_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "platform", "frontend", "public", "forensic_cases.json")
            )
            os.makedirs(os.path.dirname(public_path), exist_ok=True)
            with open(public_path, "w", encoding="utf-8") as f:
                json.dump({"active_case_id": self.active_case_id, "cases": self.cases}, f, indent=2)
        except Exception as e:
            print(f"[CASE] Error saving cases: {e}")

    def create_case(
        self,
        case_id: str,
        title: str,
        agency: str = "ZeroTrace Forensic Labs",
        investigator: str = "Investigator",
        description: str = "",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        case_data = {
            "case_id": case_id,
            "title": title,
            "agency": agency,
            "investigator": investigator,
            "description": description,
            "created_at": now,
            "status": "OPEN",
            "evidence_items": [],
            "recovered_files_count": 0,
            "sanitizations_count": 0,
        }
        self.cases[case_id] = case_data
        self.active_case_id = case_id
        self._save()
        return case_data

    def get_active_case(self) -> Dict[str, Any]:
        if self.active_case_id not in self.cases:
            self.active_case_id = list(self.cases.keys())[0] if self.cases else "CASE-ZT-2026-001"
        return self.cases.get(self.active_case_id, {})

    def set_active_case(self, case_id: str) -> bool:
        if case_id in self.cases:
            self.active_case_id = case_id
            self._save()
            return True
        return False

    def add_evidence(
        self,
        target_path: str,
        evidence_type: str,
        label: str,
        size_bytes: int = 0,
        calculate_hash: bool = False,
    ) -> Dict[str, Any]:
        """Register a new piece of forensic evidence to the active case."""
        case = self.get_active_case()
        now = datetime.now(timezone.utc).isoformat()

        sha256 = ""
        if calculate_hash and os.path.isfile(target_path):
            sha256 = sha256_file(target_path)

        evidence = {
            "evidence_id": f"EVID-{len(case.get('evidence_items', [])) + 1:04d}",
            "label": label,
            "target_path": target_path,
            "evidence_type": evidence_type,  # PHYSICAL_DRIVE, VOLUME, DISK_IMAGE, FOLDER
            "size_bytes": size_bytes,
            "sha256": sha256,
            "acquired_at": now,
            "acquired_by": case.get("investigator", "Investigator"),
            "status": "SECURED",
        }

        case.setdefault("evidence_items", []).append(evidence)
        self._save()
        return evidence

    def list_cases(self) -> List[Dict[str, Any]]:
        return list(self.cases.values())
