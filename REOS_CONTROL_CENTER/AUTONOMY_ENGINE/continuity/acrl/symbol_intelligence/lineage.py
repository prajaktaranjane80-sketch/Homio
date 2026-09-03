"""T16 PART-03 — Evidence lineage and confidence model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceKind(str, Enum):
    """How repository intelligence was established."""

    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    """Confidence associated with an intelligence record."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EvidenceLineage:
    """Immutable provenance record."""

    evidence_kind: EvidenceKind
    confidence: ConfidenceLevel
    source: str
    explanation: str


def observed_evidence(
    source: str,
    explanation: str,
) -> EvidenceLineage:
    """Create high-confidence directly observed evidence."""

    return EvidenceLineage(
        evidence_kind=EvidenceKind.OBSERVED,
        confidence=ConfidenceLevel.HIGH,
        source=source,
        explanation=explanation,
    )


def derived_evidence(
    source: str,
    explanation: str,
) -> EvidenceLineage:
    """Create derived evidence from deterministic processing."""

    return EvidenceLineage(
        evidence_kind=EvidenceKind.DERIVED,
        confidence=ConfidenceLevel.HIGH,
        source=source,
        explanation=explanation,
    )


def inferred_evidence(
    source: str,
    explanation: str,
) -> EvidenceLineage:
    """Create explicitly inferred evidence."""

    return EvidenceLineage(
        evidence_kind=EvidenceKind.INFERRED,
        confidence=ConfidenceLevel.MEDIUM,
        source=source,
        explanation=explanation,
    )


def unknown_evidence(
    source: str,
    explanation: str,
) -> EvidenceLineage:
    """Create explicit unknown evidence."""

    return EvidenceLineage(
        evidence_kind=EvidenceKind.UNKNOWN,
        confidence=ConfidenceLevel.UNKNOWN,
        source=source,
        explanation=explanation,
    )


__all__ = [
    "ConfidenceLevel",
    "EvidenceKind",
    "EvidenceLineage",
    "derived_evidence",
    "inferred_evidence",
    "observed_evidence",
    "unknown_evidence",
]