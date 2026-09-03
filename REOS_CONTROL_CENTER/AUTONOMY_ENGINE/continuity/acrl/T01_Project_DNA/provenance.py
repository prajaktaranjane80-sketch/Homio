"""ACRL T01 — Project DNA evidence provenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Iterable, Mapping


PROVENANCE_SCHEMA_VERSION = "1.0"


class EvidenceKind(str, Enum):
    """Evidence classification."""

    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable provenance record for a T01 observation or derivation."""

    evidence_id: str
    kind: EvidenceKind
    producer: str
    created_at: str
    source_fingerprint: str
    rule: str
    rule_version: str
    parent_evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": PROVENANCE_SCHEMA_VERSION,
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "producer": self.producer,
            "created_at": self.created_at,
            "source_fingerprint": self.source_fingerprint,
            "rule": self.rule,
            "rule_version": self.rule_version,
            "parent_evidence_ids": list(self.parent_evidence_ids),
        }


def _evidence_id(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def observed_evidence(
    *,
    source_fingerprint: str,
    producer: str = "ACRL.T01",
) -> EvidenceRecord:
    """Create deterministic evidence identity for one observation."""

    created_at = datetime.now(timezone.utc).isoformat()

    body = {
        "kind": EvidenceKind.OBSERVED.value,
        "producer": producer,
        "source_fingerprint": source_fingerprint,
        "rule": "DIRECT_SOURCE_OBSERVATION",
        "rule_version": "1.0",
    }

    return EvidenceRecord(
        evidence_id=_evidence_id(body),
        kind=EvidenceKind.OBSERVED,
        producer=producer,
        created_at=created_at,
        source_fingerprint=source_fingerprint,
        rule="DIRECT_SOURCE_OBSERVATION",
        rule_version="1.0",
        parent_evidence_ids=(),
    )


def derived_evidence(
    *,
    source_fingerprint: str,
    rule: str,
    rule_version: str,
    parent_evidence_ids: Iterable[str],
    producer: str = "ACRL.T01",
) -> EvidenceRecord:
    """Create provenance for a deterministic T01 derivation."""

    parents = tuple(sorted(set(parent_evidence_ids)))

    body = {
        "kind": EvidenceKind.DERIVED.value,
        "producer": producer,
        "source_fingerprint": source_fingerprint,
        "rule": rule,
        "rule_version": rule_version,
        "parent_evidence_ids": parents,
    }

    return EvidenceRecord(
        evidence_id=_evidence_id(body),
        kind=EvidenceKind.DERIVED,
        producer=producer,
        created_at=datetime.now(timezone.utc).isoformat(),
        source_fingerprint=source_fingerprint,
        rule=rule,
        rule_version=rule_version,
        parent_evidence_ids=parents,
    )


__all__ = [
    "EvidenceKind",
    "EvidenceRecord",
    "PROVENANCE_SCHEMA_VERSION",
    "derived_evidence",
    "observed_evidence",
]