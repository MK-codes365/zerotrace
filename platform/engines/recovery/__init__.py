"""
ZEROTrace — Recovery Engine (Consensus Recovery)
Combines multiple recovery strategies and computes consensus scores.
"""

from dataclasses import dataclass, field
from typing import Optional

from engines.carving import BlockScanner, CarvedCandidate, get_signature_registry
from engines.validation import FileValidator, ValidationReport
from engines.classification import ClassificationEngine, ClassificationResult
from engines.reconstruction import FragmentGraph, Fragment, ReconstructionPath
from engines.integrity import compute_sha256, MerkleTree
from app.core.logging_config import get_logger

logger = get_logger("recovery")


@dataclass
class RecoveryResult:
    """Complete recovery result for a single artifact."""
    artifact_id: str
    file_type: str
    extension: str
    mime_type: str
    category: str
    offset: int
    size: int
    sha256: str
    confidence: float
    is_fragmented: bool
    fragment_count: int
    recovery_method: str
    validation: Optional[ValidationReport] = None
    classification: Optional[ClassificationResult] = None
    method_scores: dict = field(default_factory=dict)
    consensus_score: float = 0.0
    data: Optional[bytes] = None


@dataclass
class RecoveryJobResult:
    """Complete result for a recovery job."""
    evidence_id: str
    total_candidates: int
    valid_recoveries: int
    partial_recoveries: int
    corrupted: int
    unknown: int
    artifacts: list[RecoveryResult] = field(default_factory=list)
    merkle_root: str = ""
    processing_time_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


class ConsensusRecoveryEngine:
    """
    Implements multi-strategy consensus recovery:
    
    Strategy 1: Signature carving
    Strategy 2: Structure-based reconstruction
    Strategy 3: Fragment graph reconstruction
    
    Compares outputs and computes consensus confidence.
    """

    def __init__(self):
        self.scanner = BlockScanner(get_signature_registry())
        self.validator = FileValidator()
        self.classifier = ClassificationEngine()
        self._artifact_counter = 0

    def _next_artifact_id(self) -> str:
        self._artifact_counter += 1
        return f"ART-{self._artifact_counter:06d}"

    def recover_from_chunk(
        self,
        data: bytes,
        base_offset: int = 0,
        file_types: Optional[list[str]] = None,
        evidence_id: str = "",
    ) -> list[RecoveryResult]:
        """
        Run the full recovery pipeline on a data chunk.
        
        1. Signature carving
        2. Structure validation
        3. Classification
        4. Consensus scoring
        """
        results = []

        # Strategy 1: Signature-based carving
        candidates = self.scanner.scan(data, base_offset, file_types)
        logger.info(
            "carving_complete",
            evidence_id=evidence_id,
            candidates=len(candidates),
            base_offset=base_offset,
        )

        for candidate in candidates:
            artifact_id = self._next_artifact_id()
            method_scores = {}

            # Score from carving
            method_scores["signature_carving"] = candidate.confidence

            # Get candidate data
            candidate_data = candidate.data
            if candidate_data is None:
                # Data too large to hold, skip detailed validation
                results.append(RecoveryResult(
                    artifact_id=artifact_id,
                    file_type=candidate.file_type,
                    extension=candidate.extension,
                    mime_type=candidate.mime_type,
                    category=candidate.category,
                    offset=candidate.offset,
                    size=candidate.size,
                    sha256="",
                    confidence=candidate.confidence,
                    is_fragmented=False,
                    fragment_count=1,
                    recovery_method="signature_carving",
                    method_scores=method_scores,
                    consensus_score=candidate.confidence,
                ))
                continue

            # Strategy 2: Structure-based validation
            validation = self.validator.validate(candidate_data, candidate.file_type)
            method_scores["structure_validation"] = (
                0.9 if validation.overall_status.value == "VALID"
                else 0.6 if validation.overall_status.value == "PARTIALLY_VALID"
                else 0.3
            )

            # Strategy 3: Classification cross-check
            classification = self.classifier.classify(
                candidate_data, declared_type=candidate.file_type
            )
            method_scores["classification"] = classification.confidence

            # Consensus score: weighted average
            weights = {
                "signature_carving": 0.35,
                "structure_validation": 0.40,
                "classification": 0.25,
            }
            consensus = sum(
                method_scores[k] * weights[k] for k in weights
            )

            # Boost/penalty from validation
            consensus = min(1.0, max(0.0, consensus + validation.confidence_boost))

            sha256 = validation.sha256 or compute_sha256(candidate_data)

            results.append(RecoveryResult(
                artifact_id=artifact_id,
                file_type=candidate.file_type,
                extension=candidate.extension,
                mime_type=candidate.mime_type,
                category=classification.category,
                offset=candidate.offset,
                size=candidate.size,
                sha256=sha256,
                confidence=consensus,
                is_fragmented=False,
                fragment_count=1,
                recovery_method="consensus_multi_strategy",
                validation=validation,
                classification=classification,
                method_scores=method_scores,
                consensus_score=consensus,
                data=candidate_data,
            ))

        return results

    def build_merkle_tree(self, artifacts: list[RecoveryResult]) -> MerkleTree:
        """Build a Merkle tree from all recovered artifact hashes."""
        hashes = [a.sha256 for a in artifacts if a.sha256]
        if not hashes:
            hashes = [compute_sha256(b"empty")]
        return MerkleTree(hashes)
