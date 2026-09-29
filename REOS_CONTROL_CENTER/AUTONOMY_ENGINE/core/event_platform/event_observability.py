from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from .event_domain import EventEnvelope


class EvidenceType(str, Enum):
    PUBLISHED = "PUBLISHED"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"
    REPLAYED = "REPLAYED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class EventEvidence:
    evidence_id: UUID
    event_id: UUID
    tenant_id: UUID
    evidence_type: EvidenceType
    recorded_at: datetime
    producer_id: UUID | None = None
    consumer_id: UUID | None = None
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    trace_id: str | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class DeliveryMetric:
    tenant_id: UUID
    event_id: UUID
    consumer_id: UUID
    attempt: int
    acknowledged: bool
    duration_ms: int | None = None


class EventEvidenceFactory:
    """
    Creates immutable evidence records.

    This is NOT an audit engine.
    """

    def create(
        self,
        *,
        evidence_id: UUID,
        event: EventEnvelope,
        evidence_type: EvidenceType,
        consumer_id: UUID | None = None,
        detail: str = "",
    ) -> EventEvidence:
        trace_id = None

        if event.trace_context is not None:
            trace_id = (
                event.trace_context.trace_id
            )

        return EventEvidence(
            evidence_id=evidence_id,
            event_id=event.event_id,
            tenant_id=event.tenant_id,
            evidence_type=evidence_type,
            recorded_at=datetime.now(
                timezone.utc
            ),
            producer_id=event.producer_id,
            consumer_id=consumer_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            trace_id=trace_id,
            detail=detail,
        )


def validate_evidence_tenant(
    *,
    evidence: EventEvidence,
    event: EventEnvelope,
) -> None:
    if evidence.event_id != event.event_id:
        raise ValueError(
            "evidence event identity mismatch"
        )

    if evidence.tenant_id != event.tenant_id:
        raise ValueError(
            "evidence crosses tenant boundary"
        )


__all__ = [
    "EvidenceType",
    "EventEvidence",
    "DeliveryMetric",
    "EventEvidenceFactory",
    "validate_evidence_tenant",
]
