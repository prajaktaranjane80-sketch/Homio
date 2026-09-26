from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from .event_domain import EventEnvelope


class OrderingError(ValueError):
    """Base ordering/consistency error."""


class StaleEventError(OrderingError):
    """Event is older than the accepted stream version."""


class OutOfOrderEventError(OrderingError):
    """Event violates stream ordering."""


class OrderingViolation(str, Enum):
    STALE = "STALE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CONCURRENCY = "CONCURRENCY"


@dataclass(frozen=True, slots=True)
class StreamPosition:
    tenant_id: UUID
    ordering_key: str
    sequence: int


@dataclass(frozen=True, slots=True)
class OrderingDecision:
    accepted: bool
    violation: OrderingViolation | None = None
    expected_sequence: int | None = None
    received_sequence: int | None = None


class EventOrderingGuard:
    """
    Transport-independent ordering boundary.

    CORE-002 validates logical ordering only.
    Partitioning/stream transport remains outside this class.
    """

    def validate(
        self,
        *,
        event: EventEnvelope,
        expected_next_sequence: int | None,
    ) -> OrderingDecision:
        if event.ordering_key is None:
            if event.sequence is not None:
                raise OrderingError(
                    "sequence requires ordering_key"
                )

            return OrderingDecision(
                accepted=True
            )

        if event.sequence is None:
            return OrderingDecision(
                accepted=True
            )

        if expected_next_sequence is None:
            return OrderingDecision(
                accepted=True
            )

        if event.sequence < expected_next_sequence:
            return OrderingDecision(
                accepted=False,
                violation=OrderingViolation.STALE,
                expected_sequence=expected_next_sequence,
                received_sequence=event.sequence,
            )

        if event.sequence > expected_next_sequence:
            return OrderingDecision(
                accepted=False,
                violation=OrderingViolation.OUT_OF_ORDER,
                expected_sequence=expected_next_sequence,
                received_sequence=event.sequence,
            )

        return OrderingDecision(
            accepted=True,
            expected_sequence=expected_next_sequence,
            received_sequence=event.sequence,
        )

    def require_accepted(
        self,
        decision: OrderingDecision,
    ) -> None:
        if decision.accepted:
            return

        if decision.violation == (
            OrderingViolation.STALE
        ):
            raise StaleEventError(
                "event sequence is stale"
            )

        if decision.violation == (
            OrderingViolation.OUT_OF_ORDER
        ):
            raise OutOfOrderEventError(
                "event sequence is out of order"
            )

        raise OrderingError(
            "event ordering was rejected"
        )


def validate_stream_identity(
    *,
    event: EventEnvelope,
    tenant_id: UUID,
    ordering_key: str,
) -> None:
    if event.tenant_id != tenant_id:
        raise OrderingError(
            "event crosses tenant stream boundary"
        )

    if event.ordering_key != ordering_key:
        raise OrderingError(
            "event does not belong to requested stream"
        )


__all__ = [
    "OrderingError",
    "StaleEventError",
    "OutOfOrderEventError",
    "OrderingViolation",
    "StreamPosition",
    "OrderingDecision",
    "EventOrderingGuard",
    "validate_stream_identity",
]
