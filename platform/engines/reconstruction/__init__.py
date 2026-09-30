"""
ZEROTrace — Fragment Reconstruction Engine
Graph-based fragment assembly with compatibility scoring.
"""

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging_config import get_logger

logger = get_logger("reconstruction")


@dataclass
class Fragment:
    """A data fragment from carved evidence."""
    id: str
    offset: int
    size: int
    data: bytes
    entropy: float = 0.0
    file_type_hint: Optional[str] = None
    sha256: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class FragmentEdge:
    """Compatibility relationship between two fragments."""
    source_id: str
    target_id: str
    compatibility_score: float
    reason: str = ""


@dataclass
class ReconstructionPath:
    """A candidate reconstruction from assembled fragments."""
    fragments: list[str]
    total_size: int
    confidence: float
    file_type: Optional[str]
    data: Optional[bytes] = None
    metadata: dict = field(default_factory=dict)


def compute_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of a byte sequence (0.0 to 8.0)."""
    if not data:
        return 0.0
    freq = defaultdict(int)
    for byte in data:
        freq[byte] += 1
    length = len(data)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


class FragmentGraph:
    """
    Graph-based fragment reconstruction.
    
    Fragments are nodes, compatibility relationships are edges.
    Uses scoring to find the most plausible reconstruction paths.
    
    A → B (score: 0.9)
    A → C (score: 0.7)
    B → D (score: 0.85)
    
    Best path: A → B → D (avg: 0.875)
    """

    def __init__(self):
        self.fragments: dict[str, Fragment] = {}
        self.edges: list[FragmentEdge] = []
        self.adjacency: dict[str, list[FragmentEdge]] = defaultdict(list)

    def add_fragment(self, fragment: Fragment):
        """Add a fragment node to the graph."""
        if not fragment.sha256 and fragment.data:
            fragment.sha256 = hashlib.sha256(fragment.data).hexdigest()
        if fragment.data and fragment.entropy == 0:
            fragment.entropy = compute_entropy(fragment.data)
        self.fragments[fragment.id] = fragment

    def add_edge(self, source_id: str, target_id: str, score: float, reason: str = ""):
        """Add a compatibility edge between two fragments."""
        edge = FragmentEdge(
            source_id=source_id,
            target_id=target_id,
            compatibility_score=score,
            reason=reason,
        )
        self.edges.append(edge)
        self.adjacency[source_id].append(edge)

    def compute_compatibility(self, frag_a: Fragment, frag_b: Fragment) -> float:
        """
        Compute compatibility between two adjacent fragments.
        Based on: entropy similarity, byte patterns, and continuity.
        """
        score = 0.0
        factors = 0

        # Entropy similarity (similar entropy = likely same file)
        if frag_a.entropy > 0 and frag_b.entropy > 0:
            entropy_diff = abs(frag_a.entropy - frag_b.entropy)
            entropy_score = max(0, 1.0 - entropy_diff / 4.0)
            score += entropy_score
            factors += 1

        # Continuity: check if fragments are adjacent in offset
        if frag_a.offset + frag_a.size == frag_b.offset:
            score += 1.0  # Perfect continuity
            factors += 1
        elif abs((frag_a.offset + frag_a.size) - frag_b.offset) < 4096:
            score += 0.7  # Close proximity
            factors += 1

        # File type hint agreement
        if frag_a.file_type_hint and frag_b.file_type_hint:
            if frag_a.file_type_hint == frag_b.file_type_hint:
                score += 1.0
            factors += 1

        # Byte pattern continuity at boundary
        if frag_a.data and frag_b.data:
            tail = frag_a.data[-16:] if len(frag_a.data) >= 16 else frag_a.data
            head = frag_b.data[:16] if len(frag_b.data) >= 16 else frag_b.data
            # Check for no abrupt null transitions
            tail_zeros = sum(1 for b in tail if b == 0)
            head_zeros = sum(1 for b in head if b == 0)
            if abs(tail_zeros - head_zeros) <= 4:
                score += 0.5
            factors += 1

        return score / max(factors, 1)

    def build_edges_auto(self, threshold: float = 0.3):
        """
        Automatically compute compatibility between all fragment pairs
        and add edges above the threshold.
        """
        fragment_list = list(self.fragments.values())
        for i, frag_a in enumerate(fragment_list):
            for frag_b in fragment_list[i + 1:]:
                score = self.compute_compatibility(frag_a, frag_b)
                if score >= threshold:
                    self.add_edge(frag_a.id, frag_b.id, score, "auto_computed")
                    self.add_edge(frag_b.id, frag_a.id, score, "auto_computed")

    def find_best_paths(
        self,
        max_paths: int = 5,
        min_fragments: int = 2,
    ) -> list[ReconstructionPath]:
        """
        Find the best reconstruction paths using DFS with scoring.
        Returns top N paths sorted by confidence.
        """
        all_paths = []

        # Start from fragments that could be file headers
        start_nodes = self._find_start_nodes()

        for start_id in start_nodes:
            paths = self._dfs_paths(start_id, max_depth=20)
            for path in paths:
                if len(path["nodes"]) >= min_fragments:
                    all_paths.append(path)

        # Sort by average score
        all_paths.sort(key=lambda p: p["avg_score"], reverse=True)

        # Convert to ReconstructionPath objects
        results = []
        for path_data in all_paths[:max_paths]:
            fragments = path_data["nodes"]
            total_size = sum(
                self.fragments[fid].size for fid in fragments if fid in self.fragments
            )

            # Assemble data if all fragments have data
            assembled_data = None
            all_have_data = all(
                self.fragments[fid].data is not None
                for fid in fragments
                if fid in self.fragments
            )
            if all_have_data and total_size < 50 * 1024 * 1024:
                parts = [self.fragments[fid].data for fid in fragments if fid in self.fragments]
                assembled_data = b"".join(parts)

            file_type = None
            first_frag = self.fragments.get(fragments[0])
            if first_frag:
                file_type = first_frag.file_type_hint

            results.append(ReconstructionPath(
                fragments=fragments,
                total_size=total_size,
                confidence=path_data["avg_score"],
                file_type=file_type,
                data=assembled_data,
            ))

        logger.info(
            "reconstruction_complete",
            total_fragments=len(self.fragments),
            paths_found=len(results),
        )
        return results

    def _find_start_nodes(self) -> list[str]:
        """Find fragments likely to be file starts (low offset, have outgoing edges)."""
        candidates = []
        for fid, frag in self.fragments.items():
            if fid in self.adjacency and self.adjacency[fid]:
                candidates.append((fid, frag.offset))

        candidates.sort(key=lambda x: x[1])
        return [c[0] for c in candidates]

    def _dfs_paths(
        self, start: str, max_depth: int = 20
    ) -> list[dict]:
        """Depth-first search for paths from a start node."""
        results = []
        stack = [(start, [start], 0.0, 0)]

        while stack:
            current, path, total_score, depth = stack.pop()
            if depth >= max_depth:
                continue

            edges = self.adjacency.get(current, [])
            if not edges or depth > 0:
                # Record path if it has edges
                if len(path) >= 2:
                    results.append({
                        "nodes": list(path),
                        "avg_score": total_score / max(len(path) - 1, 1),
                        "total_score": total_score,
                    })

            for edge in edges:
                if edge.target_id not in path:
                    stack.append((
                        edge.target_id,
                        path + [edge.target_id],
                        total_score + edge.compatibility_score,
                        depth + 1,
                    ))

        return results

    def get_stats(self) -> dict:
        return {
            "total_fragments": len(self.fragments),
            "total_edges": len(self.edges),
            "connected_components": self._count_components(),
        }

    def _count_components(self) -> int:
        visited = set()
        components = 0
        for fid in self.fragments:
            if fid not in visited:
                components += 1
                stack = [fid]
                while stack:
                    node = stack.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    for edge in self.adjacency.get(node, []):
                        stack.append(edge.target_id)
        return components
