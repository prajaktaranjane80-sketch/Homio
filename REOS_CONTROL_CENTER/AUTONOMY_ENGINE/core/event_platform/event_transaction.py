from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol
from uuid import UUID


class TransactionBoundaryError(ValueError):
    """Base transactional-boundary error."""


class InvalidPublicationStateError(
    TransactionBoundaryError
):
    """Raised for invalid publication state transitions."""


class PublicationState(str, Enum):
    CREATED = "CREATED"
    COMMITTED = "COMMITTED"
    PUBLISHED = "PUBLISHED"
    RECOVERABLE = "RECOVERABLE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class OutboxContract:
    """
    Transactional publication contract.

    This is a boundary contract, not an outbox implementation.
    """

    publication_id: UUID
    event_id: UUID
    tenant_id: UUID
    event_fingerprint: str
    created_at: datetime
    state: PublicationState = PublicationState.CREATED


class TransactionalPublicationBoundary(Protocol):
    """
    Infrastructure must implement this boundary.

    CORE-002 does not own database transactions.
    """

    def stage(
        self,
        contract: OutboxContract,
    ) -> None:
        ...

    def commit(
        self,
        publication_id: UUID,
    ) -> None:
        ...

    def mark_published(
        self,
        publication_id: UUID,
    ) -> None:
        ...

    def recover_unpublished(
        self,
        *,
        tenant_id: UUID,
    ) -> list[OutboxContract]:
        ...


class PublicationStateMachine:
    """
    Deterministic state transition validator.
    """

    _TRANSITIONS = {
        PublicationState.CREATED: {
            PublicationState.COMMITTED,
            PublicationState.FAILED,
        },
        PublicationState.COMMITTED: {
            PublicationState.PUBLISHED,
            PublicationState.RECOVERABLE,
            PublicationState.FAILED,
        },
        PublicationState.RECOVERABLE: {
            PublicationState.PUBLISHED,
            PublicationState.FAILED,
        },
        PublicationState.PUBLISHED: set(),
        PublicationState.FAILED: set(),
    }

    @classmethod
    def transition(
        cls,
        current: PublicationState,
        target: PublicationState,
    ) -> PublicationState:
        allowed = cls._TRANSITIONS.get(
            current,
            set(),
        )

        if target not in allowed:
            raise InvalidPublicationStateError(
                f"invalid publication transition: "
                f"{current.value} -> {target.value}"
            )

        return target


def build_publication_contract(
    *,
    publication_id: UUID,
    event_id: UUID,
    tenant_id: UUID,
    event_fingerprint: str,
) -> OutboxContract:
    if not isinstance(
        publication_id,
        UUID,
    ):
        raise TypeError(
            "publication_id must be UUID"
        )

    if not isinstance(
        event_id,
        UUID,
    ):
        raise TypeError(
            "event_id must be UUID"
        )

    if not isinstance(
        tenant_id,
        UUID,
    ):
        raise TypeError(
            "tenant_id must be UUID"
        )

    if not isinstance(
        event_fingerprint,
        str,
    ) or not event_fingerprint:
        raise ValueError(
            "event_fingerprint is required"
        )

    return OutboxContract(
        publication_id=publication_id,
        event_id=event_id,
        tenant_id=tenant_id,
        event_fingerprint=event_fingerprint,
        created_at=datetime.now(timezone.utc),
    )


__all__ = [
    "TransactionBoundaryError",
    "InvalidPublicationStateError",
    "PublicationState",
    "OutboxContract",
    "TransactionalPublicationBoundary",
    "PublicationStateMachine",
    "build_publication_contract",
]
