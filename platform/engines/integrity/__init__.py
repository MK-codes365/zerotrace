"""
ZEROTrace — Integrity Engine
SHA-256/SHA-512 hashing, Merkle Tree, and tamper-evident Hash Chain.
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger("integrity")


# ═══════════════════════════════════════════════════════════
# Hashing
# ═══════════════════════════════════════════════════════════

def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha512(data: bytes) -> str:
    """Compute SHA-512 hash of raw bytes."""
    return hashlib.sha512(data).hexdigest()


def compute_file_hash(
    file_path: str,
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Compute hash of a file by streaming chunks.
    Supports sha256 and sha512.
    """
    hasher = hashlib.new(algorithm)
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_buffer_hash(
    buffer: bytes,
    offset: int,
    size: int,
    algorithm: str = "sha256",
) -> str:
    """Compute hash of a specific region within a buffer."""
    hasher = hashlib.new(algorithm)
    hasher.update(buffer[offset : offset + size])
    return hasher.hexdigest()


# ═══════════════════════════════════════════════════════════
# Merkle Tree
# ═══════════════════════════════════════════════════════════

class MerkleTree:
    """
    Merkle Tree implementation for evidence/artifact integrity.
    
    Structure:
                    ROOT
                   /    \\
                 H12    H34
                /  \\    /  \\
              H1   H2  H3   H4
    """

    def __init__(self, leaves: list[str]):
        """
        Build a Merkle Tree from a list of hash strings.
        
        Args:
            leaves: List of SHA-256 hex-digest strings
        """
        if not leaves:
            raise ValueError("Cannot build Merkle tree from empty leaves")
        self.leaves = leaves
        self.tree: list[list[str]] = []
        self.root: str = ""
        self._build()

    def _hash_pair(self, left: str, right: str) -> str:
        """Hash two node hashes together."""
        combined = (left + right).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    def _build(self):
        """Build the Merkle tree bottom-up."""
        current_level = list(self.leaves)

        # If odd number of leaves, duplicate the last one
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])

        self.tree.append(current_level)

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_pair(left, right))

            if len(next_level) > 1 and len(next_level) % 2 != 0:
                next_level.append(next_level[-1])

            self.tree.append(next_level)
            current_level = next_level

        self.root = current_level[0]

    def get_root(self) -> str:
        """Return the Merkle root hash."""
        return self.root

    def get_proof(self, leaf_index: int) -> list[dict]:
        """
        Get the proof path for a specific leaf.
        Returns list of {hash, position} pairs.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"Leaf index {leaf_index} out of range")

        proof = []
        idx = leaf_index

        for level in self.tree[:-1]:
            if idx % 2 == 0:
                sibling_idx = idx + 1
                position = "right"
            else:
                sibling_idx = idx - 1
                position = "left"

            if sibling_idx < len(level):
                proof.append({
                    "hash": level[sibling_idx],
                    "position": position,
                })
            idx //= 2

        return proof

    def verify_proof(
        self, leaf_hash: str, proof: list[dict], root: str
    ) -> bool:
        """Verify a Merkle proof against the root."""
        current = leaf_hash
        for step in proof:
            if step["position"] == "right":
                current = self._hash_pair(current, step["hash"])
            else:
                current = self._hash_pair(step["hash"], current)
        return current == root

    def to_dict(self) -> dict:
        """Serialize the tree."""
        return {
            "root": self.root,
            "leaf_count": len(self.leaves),
            "depth": len(self.tree),
            "leaves": self.leaves,
        }


# ═══════════════════════════════════════════════════════════
# Hash Chain (tamper-evident audit log)
# ═══════════════════════════════════════════════════════════

class HashChain:
    """
    Tamper-evident hash chain for audit events.
    
    Event1 → H1
    Event2 + H1 → H2
    Event3 + H2 → H3
    
    If an old audit event changes, the chain verification fails.
    """

    def __init__(self):
        self.chain: list[dict] = []
        self.current_hash: Optional[str] = None

    def add_event(self, event_data: dict) -> dict:
        """
        Append an event to the hash chain.
        Returns the chain entry with hashes.
        """
        import copy
        previous_hash = self.current_hash or ("0" * 64)

        # Deterministic serialization with isolated copy
        event_copy = copy.deepcopy(event_data)
        event_str = json.dumps(event_copy, sort_keys=True, default=str)
        payload = f"{previous_hash}:{event_str}"
        current_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        entry = {
            "index": len(self.chain),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_copy,
            "previous_hash": previous_hash,
            "current_hash": current_hash,
        }

        self.chain.append(entry)
        self.current_hash = current_hash
        return entry

    def verify_chain(self) -> dict:
        """
        Verify the entire hash chain.
        Returns verification result with details.
        """
        if not self.chain:
            return {"valid": True, "length": 0, "message": "Empty chain"}

        errors = []
        for i, entry in enumerate(self.chain):
            expected_previous = (
                self.chain[i - 1]["current_hash"] if i > 0 else ("0" * 64)
            )

            if entry["previous_hash"] != expected_previous:
                errors.append({
                    "index": i,
                    "error": "Previous hash mismatch",
                    "expected": expected_previous,
                    "found": entry["previous_hash"],
                })

            # Recompute current hash
            event_str = json.dumps(entry["event"], sort_keys=True, default=str)
            payload = f"{entry['previous_hash']}:{event_str}"
            recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            if entry["current_hash"] != recomputed:
                errors.append({
                    "index": i,
                    "error": "Current hash mismatch (tampered event)",
                    "expected": recomputed,
                    "found": entry["current_hash"],
                })

        return {
            "valid": len(errors) == 0,
            "length": len(self.chain),
            "errors": errors,
            "head_hash": self.chain[0]["current_hash"] if self.chain else None,
            "tail_hash": self.chain[-1]["current_hash"] if self.chain else None,
        }

    def get_latest_hash(self) -> Optional[str]:
        return self.current_hash

    def to_list(self) -> list[dict]:
        return list(self.chain)
