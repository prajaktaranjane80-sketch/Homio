from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Callable
from uuid import UUID

from .event_domain import EventEnvelope


class EventSecurityError(ValueError):
    """Base event security error."""


class CrossTenantEventError(EventSecurityError):
    """Event attempted to cross tenant boundary."""


class ProducerAuthorizationError(
    EventSecurityError
):
    """Producer is not authorized."""


class ConsumerAuthorizationError(
    EventSecurityError
):
    """Consumer is not authorized."""


class EventIntegrityError(EventSecurityError):
    """Event integrity verification failed."""


@dataclass(frozen=True, slots=True)
class ProducerIdentity:
    producer_id: UUID
    tenant_id: UUID


@dataclass(frozen=True, slots=True)
class ConsumerIdentity:
    consumer_id: UUID
    tenant_id: UUID


class EventSecurityBoundary:
    """
    CORE-002 security boundary.

    Identity and authorization decisions are delegated to
    supplied authorities.
    """

    def __init__(
        self,
        *,
        producer_authorizer: Callable[
            [UUID, UUID],
            bool,
        ],
        consumer_authorizer: Callable[
            [UUID, UUID],
            bool,
        ],
    ) -> None:
        self._producer_authorizer = (
            producer_authorizer
        )
        self._consumer_authorizer = (
            consumer_authorizer
        )

    def validate_producer(
        self,
        *,
        event: EventEnvelope,
    ) -> None:
        if not self._producer_authorizer(
            event.tenant_id,
            event.producer_id,
        ):
            raise ProducerAuthorizationError(
                "producer is not authorized "
                "for event tenant"
            )

    def validate_consumer(
        self,
        *,
        event: EventEnvelope,
        consumer_id: UUID,
        consumer_tenant_id: UUID,
    ) -> None:
        if event.tenant_id != consumer_tenant_id:
            raise CrossTenantEventError(
                "consumer tenant does not match event tenant"
            )

        if not self._consumer_authorizer(
            event.tenant_id,
            consumer_id,
        ):
            raise ConsumerAuthorizationError(
                "consumer is not authorized "
                "for event tenant"
            )

    def integrity_digest(
        self,
        event: EventEnvelope,
    ) -> str:
        return sha256(
            event.serialize().encode("utf-8")
        ).hexdigest()

    def verify_integrity(
        self,
        *,
        event: EventEnvelope,
        expected_digest: str,
    ) -> None:
        if not isinstance(
            expected_digest,
            str,
        ):
            raise TypeError(
                "expected_digest must be string"
            )

        actual = self.integrity_digest(event)

        if actual != expected_digest:
            raise EventIntegrityError(
                "event integrity verification failed"
            )


__all__ = [
    "EventSecurityError",
    "CrossTenantEventError",
    "ProducerAuthorizationError",
    "ConsumerAuthorizationError",
    "EventIntegrityError",
    "ProducerIdentity",
    "ConsumerIdentity",
    "EventSecurityBoundary",
]
