from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceAuthority(str, Enum):
    CANONICAL_STATE = "CANONICAL_STATE"
    RESUME_SAFETY = "RESUME_SAFETY"
    EXECUTION_AUTHORIZATION = "EXECUTION_AUTHORIZATION"
    CHANGE_IMPACT = "CHANGE_IMPACT"
    TEST_DIAGNOSIS = "TEST_DIAGNOSIS"
    VERIFIED_REPAIR = "VERIFIED_REPAIR"
    GIT_TRANSACTION = "GIT_TRANSACTION"
    EXECUTION_CHECKPOINT = "EXECUTION_CHECKPOINT"
    GENERAL_EVIDENCE = "GENERAL_EVIDENCE"


class EvidenceType(str, Enum):
    STATE = "STATE"
    RESUME = "RESUME"
    AUTHORIZATION = "AUTHORIZATION"
    IMPACT = "IMPACT"
    DIAGNOSIS = "DIAGNOSIS"
    REPAIR = "REPAIR"
    GIT = "GIT"
    CHECKPOINT = "CHECKPOINT"
    GENERAL = "GENERAL"


class EvidenceStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class ResolutionDecision(str, Enum):
    RESOLVED = "RESOLVED"
    READ_ONLY = "READ_ONLY"
    BLOCKED = "BLOCKED"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"
    STALE = "STALE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: str
    subject: str

    evidence_type: EvidenceType
    authority: EvidenceAuthority
    status: EvidenceStatus

    source_layer: str
    source_name: str

    content_fingerprint: str

    sequence: int

    immutable: bool = True
    canonical: bool = False

    metadata_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "subject": self.subject,
            "evidence_type": self.evidence_type.value,
            "authority": self.authority.value,
            "status": self.status.value,
            "source_layer": self.source_layer,
            "source_name": self.source_name,
            "content_fingerprint": self.content_fingerprint,
            "sequence": self.sequence,
            "immutable": self.immutable,
            "canonical": self.canonical,
            "metadata_fingerprint": self.metadata_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ResolutionRequest:
    resolution_id: str
    subject: str

    evidence_ids: tuple[str, ...]

    preferred_authorities: tuple[
        EvidenceAuthority, ...
    ] = ()

    require_current: bool = True
    require_canonical_when_available: bool = True

    request_fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "subject": self.subject,
            "evidence_ids": list(self.evidence_ids),
            "preferred_authorities": [
                item.value
                for item in self.preferred_authorities
            ],
            "require_current": self.require_current,
            "require_canonical_when_available": (
                self.require_canonical_when_available
            ),
            "request_fingerprint": self.request_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    schema_version: str
    decision: ResolutionDecision

    resolution_id: str
    subject: str

    selected_evidence: EvidenceReference | None
    candidates: tuple[
        EvidenceReference, ...
    ]

    rejected_evidence: tuple[
        EvidenceReference, ...
    ]

    conflicting_evidence: tuple[
        EvidenceReference, ...
    ]

    stale_evidence: tuple[
        EvidenceReference, ...
    ]

    missing_evidence_ids: tuple[str, ...]

    request_fingerprint: str
    resolution_fingerprint: str

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "resolution_id": self.resolution_id,
            "subject": self.subject,
            "selected_evidence": (
                self.selected_evidence.to_dict()
                if self.selected_evidence
                else None
            ),
            "candidates": [
                item.to_dict()
                for item in self.candidates
            ],
            "rejected_evidence": [
                item.to_dict()
                for item in self.rejected_evidence
            ],
            "conflicting_evidence": [
                item.to_dict()
                for item in self.conflicting_evidence
            ],
            "stale_evidence": [
                item.to_dict()
                for item in self.stale_evidence
            ],
            "missing_evidence_ids": list(
                self.missing_evidence_ids
            ),
            "request_fingerprint": (
                self.request_fingerprint
            ),
            "resolution_fingerprint": (
                self.resolution_fingerprint
            ),
            "explanation": self.explanation,
        }
