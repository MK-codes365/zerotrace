"""
ZeroTrace Core - Cryptographic and Hashing Utilities
Provides SHA-256, SHA-512, Shannon Entropy, Merkle Root calculation,
and digital signature verification for evidential integrity.
"""

import os
import math
import hashlib
import hmac
import secrets
from typing import List, Optional


def sha256_bytes(data: bytes) -> str:
    """Calculate SHA-256 hex digest of byte data."""
    return hashlib.sha256(data).hexdigest()


def sha512_bytes(data: bytes) -> str:
    """Calculate SHA-512 hex digest of byte data."""
    return hashlib.sha512(data).hexdigest()


def sha256_file(filepath: str, chunk_size: int = 4 * 1024 * 1024) -> str:
    """Calculate SHA-256 hash of a file or stream in chunks."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"


def sha512_file(filepath: str, chunk_size: int = 4 * 1024 * 1024) -> str:
    """Calculate SHA-512 hash of a file or stream in chunks."""
    h = hashlib.sha512()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"


def calculate_entropy(data: bytes) -> float:
    """
    Calculate Shannon entropy of byte data (0.0 to 8.0).
    - Close to 0: highly repetitive (e.g. zeros or uniform pattern)
    - 3.0 to 6.0: plain text, code, structured documents
    - 7.5 to 8.0: compressed or encrypted data (or cryptographic PRNG wipe)
    """
    if not data:
        return 0.0

    length = len(data)
    frequencies = [0] * 256
    for b in data:
        frequencies[b] += 1

    entropy = 0.0
    for count in frequencies:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)

    return round(entropy, 4)


def compute_merkle_root(leaf_hashes: List[str]) -> str:
    """
    Compute Merkle Root hash from a list of leaf SHA-256 digests.
    Ensures verifiable tamper-evident block integrity.
    """
    if not leaf_hashes:
        return hashlib.sha256(b"EMPTY_MERKLE_TREE").hexdigest()

    current_level = [bytes.fromhex(h) if len(h) == 64 else hashlib.sha256(h.encode()).digest() for h in leaf_hashes]

    while len(current_level) > 1:
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])

        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            parent_hash = hashlib.sha256(combined).digest()
            next_level.append(parent_hash)
        current_level = next_level

    return current_level[0].hex()


def generate_tamper_signature(data_str: str, secret_key: Optional[bytes] = None) -> str:
    """
    Generate cryptographic signature for audit records or certificates.
    Uses HMAC-SHA256 with machine-derived hardware seed or provided key.
    """
    if secret_key is None:
        # Hardware-bound pseudo seed for local forensic machine identity
        seed = f"ZEROTRACE-FORENSIC-{os.environ.get('COMPUTERNAME', 'WORKSTATION')}".encode()
        secret_key = hashlib.sha256(seed).digest()

    return hmac.new(secret_key, data_str.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_random_bytes(length: int) -> bytes:
    """Generate cryptographically secure random bytes for wiping passes."""
    return secrets.token_bytes(length)
