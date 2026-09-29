from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol
from uuid import UUID

from .event_domain import EventEnvelope
from .event_contract import EventContractRegistry


class DeliveryError(ValueError):
    """Base CORE-002 delivery error."""


class DeliveryAuthorizationError(DeliveryError):
    """Raised when delivery is not authorized."""


class DuplicateDeliveryError(DeliveryError):
    """Raised when an event was already acknowledged."""


class DeliveryStateError(DeliveryError):
    """Raised when delivery state transition is invalid."""


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    QUARANTINED = "QUARANTINED"


class DeliveryFailureClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    POISON = "POISON"
    AUTHORIZATION = "AUTHORIZATION"


@dataclass(frozen=True, slots=True)
class DeliveryAttempt:
    delivery_id: UUID
    event_id: UUID
    tenant_id: UUID
    consumer_id: UUID
    attempt_number: int
    attempted_at: datetime
    status: DeliveryStatus
    failure_class: DeliveryFailureClass | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    delivery_id: UUID
    event_id: UUID
    tenant_id: UUID
    consumer_id: UUID
    status: DeliveryStatus
    attempt_count: int
    last_attempt_at: datetime | None = None
    acknowledged_at: datetime | None = None
    failure_class: DeliveryFailureClass | None = None


class IdempotencyBoundary(Protocol):
    """
    Existing CORE idempotency authority.

    CORE-002 consumes this boundary.
    It does not create another idempotency engine.
    """

    def already_applied(
        self,
        *,
        tenant_id: UUID,
        consumer_id: UUID,
        idempotency_key: str,
    ) -> bool:
        ...

    def mark_applied(
        self,
        *,
        tenant_id: UUID,
        consumer_id: UUID,
        idempotency_key: str,
    ) -> None:
        ...


class ConsumerHandler(Protocol):
    def __call__(
        self,
        event: EventEnvelope,
    ) -> None:
        ...


class DeliveryPolicy:
    """
    Immutable delivery policy.

    Retry decisions are policy data only.
    Actual scheduling belongs outside CORE-002.
    """

    def __init__(
        self,
        *,
        max_attempts: int = 3,
    ) -> None:
        if (
            not isinstance(max_attempts, int)
            or max_attempts < 1
        ):
            raise ValueError(
                "max_attempts must be >= 1"
            )

        self.max_attempts = max_attempts

    def classify_failure(
        self,
        exc: Exception,
    ) -> DeliveryFailureClass:
        if isinstance(
            exc,
            DeliveryAuthorizationError,
        ):
            return DeliveryFailureClass.AUTHORIZATION

        if isinstance(
            exc,
            (TypeError, ValueError),
        ):
            return DeliveryFailureClass.PERMANENT

        return DeliveryFailureClass.TRANSIENT

    def should_retry(
        self,
        *,
        attempt_number: int,
        failure_class: DeliveryFailureClass,
    ) -> bool:
        if failure_class in {
            DeliveryFailureClass.PERMANENT,
            DeliveryFailureClass.POISON,
            DeliveryFailureClass.AUTHORIZATION,
        }:
            return False

        return attempt_number < self.max_attempts


class EventDeliveryCoordinator:
    """
    Transport-independent delivery boundary.

    Responsibilities:
    - contract validation
    - tenant validation
    - consumer dispatch
    - acknowledgement boundary
    - duplicate protection through injected idempotency authority
    - failure classification

    Not responsible for:
    - Kafka
    - database
    - outbox persistence
    - retry scheduling
    - DLQ storage
    - Control Center state
    """

    def __init__(
        self,
        *,
        contracts: EventContractRegistry,
        idempotency: IdempotencyBoundary,
        tenant_authorizer: Callable[
            [UUID, UUID],
            bool,
        ],
        policy: DeliveryPolicy | None = None,
    ) -> None:
        self._contracts = contracts
        self._idempotency = idempotency
        self._tenant_authorizer = tenant_authorizer
        self._policy = (
            policy
            if policy is not None
            else DeliveryPolicy()
        )

    def validate_delivery(
        self,
        *,
        event: EventEnvelope,
        consumer_id: UUID,
    ) -> None:
        if not isinstance(
            consumer_id,
            UUID,
        ):
            raise TypeError(
                "consumer_id must be UUID"
            )

        if not self._tenant_authorizer(
            event.tenant_id,
            consumer_id,
        ):
            raise DeliveryAuthorizationError(
                "consumer is not authorized for event tenant"
            )

        self._contracts.validate(event)

    def dispatch(
        self,
        *,
        event: EventEnvelope,
        consumer_id: UUID,
        handler: ConsumerHandler,
    ) -> DeliveryAttempt:
        self.validate_delivery(
            event=event,
            consumer_id=consumer_id,
        )

        if not callable(handler):
            raise TypeError(
                "handler must be callable"
            )

        if event.idempotency_key:
            if self._idempotency.already_applied(
                tenant_id=event.tenant_id,
                consumer_id=consumer_id,
                idempotency_key=event.idempotency_key,
            ):
                raise DuplicateDeliveryError(
                    "event delivery already acknowledged"
                )

        attempt_number = 1
        now = datetime.now(timezone.utc)

        try:
            handler(event)

            if event.idempotency_key:
                self._idempotency.mark_applied(
                    tenant_id=event.tenant_id,
                    consumer_id=consumer_id,
                    idempotency_key=event.idempotency_key,
                )

            return DeliveryAttempt(
                delivery_id=UUID(
                    str(event.event_id)
                ),
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                consumer_id=consumer_id,
                attempt_number=attempt_number,
                attempted_at=now,
                status=DeliveryStatus.ACKNOWLEDGED,
            )

        except Exception as exc:
            failure_class = (
                self._policy.classify_failure(exc)
            )

            status = (
                DeliveryStatus.RETRYABLE_FAILURE
                if self._policy.should_retry(
                    attempt_number=attempt_number,
                    failure_class=failure_class,
                )
                else DeliveryStatus.PERMANENT_FAILURE
            )

            return DeliveryAttempt(
                delivery_id=UUID(
                    str(event.event_id)
                ),
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                consumer_id=consumer_id,
                attempt_number=attempt_number,
                attempted_at=now,
                status=status,
                failure_class=failure_class,
                error_code=type(exc).__name__,
            )


__all__ = [
    "DeliveryError",
    "DeliveryAuthorizationError",
    "DuplicateDeliveryError",
    "DeliveryStateError",
    "DeliveryStatus",
    "DeliveryFailureClass",
    "DeliveryAttempt",
    "DeliveryRecord",
    "IdempotencyBoundary",
    "ConsumerHandler",
    "DeliveryPolicy",
    "EventDeliveryCoordinator",
]
