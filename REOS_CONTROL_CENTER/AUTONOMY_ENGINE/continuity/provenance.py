"""Provenance tracking for AUTONOMY_ENGINE V6.

Records where an execution input, decision, artifact, or state transition
originated from without becoming an authority itself.

This module is additive and must not mutate the existing AUTONOMY_ENGINE
foundation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
import hashlib
import json


def _utc_now() -> str:
    """Return a deterministic ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    """Serialize a value deterministically for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _digest(value: Any) -> str:
    """Create a SHA-256 digest of canonical data."""
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ProvenanceRecord:
    """Immutable provenance record for an engine-relevant observation."""

    record_id: str
    source_type: str
    source_ref: str
    subject_type: str
    subject_ref: str
    captured_at: str
    content_hash: str
    metadata: Mapping[str, Any]
    parent_record_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


class ProvenanceTracker:
    """Create and verify immutable provenance records.

    The tracker deliberately does not decide whether a source is trusted.
    Trust, authorization, governance, and execution remain separate concerns.
    """

    def __init__(self) -> None:
        self._records: dict[str, ProvenanceRecord] = {}

    def record(
        self,
        *,
        record_id: str,
        source_type: str,
        source_ref: str,
        subject_type: str,
        subject_ref: str,
        content: Any,
        metadata: Mapping[str, Any] | None = None,
        parent_record_id: str | None = None,
    ) -> ProvenanceRecord:
        """Create and retain a provenance record.

        Duplicate record IDs are rejected unless the existing record is
        byte-for-byte equivalent.
        """
        record = ProvenanceRecord(
            record_id=record_id,
            source_type=source_type,
            source_ref=source_ref,
            subject_type=subject_type,
            subject_ref=subject_ref,
            captured_at=_utc_now(),
            content_hash=_digest(content),
            metadata=dict(metadata or {}),
            parent_record_id=parent_record_id,
        )

        existing = self._records.get(record_id)

        if existing is not None:
            if existing.content_hash != record.content_hash:
                raise ValueError(
                    f"Provenance record collision: {record_id}"
                )
            return existing

        if parent_record_id is not None:
            if parent_record_id not in self._records:
                raise ValueError(
                    f"Unknown parent provenance record: {parent_record_id}"
                )

        self._records[record_id] = record
        return record

    def get(self, record_id: str) -> ProvenanceRecord | None:
        """Return a provenance record by ID."""
        return self._records.get(record_id)

    def verify(self, record_id: str, content: Any) -> bool:
        """Verify that content still matches the recorded provenance hash."""
        record = self._records.get(record_id)

        if record is None:
            return False

        return record.content_hash == _digest(content)

    def lineage(self, record_id: str) -> list[ProvenanceRecord]:
        """Return the parent lineage from oldest known record to the target."""
        lineage: list[ProvenanceRecord] = []
        current = self._records.get(record_id)

        while current is not None:
            lineage.append(current)

            if current.parent_record_id is None:
                break

            current = self._records.get(current.parent_record_id)

        lineage.reverse()
        return lineage

    def export(self) -> list[dict[str, Any]]:
        """Export records in deterministic record-ID order."""
        return [
            self._records[key].to_dict()
            for key in sorted(self._records)
        ]

    def digest(self) -> str:
        """Return a deterministic digest of the complete provenance set."""
        return _digest(self.export())

    def clear(self) -> None:
        """Clear in-memory records.

        Persistence remains an external responsibility; this method exists
        primarily for isolated tests and lifecycle management.
        """
        self._records.clear()