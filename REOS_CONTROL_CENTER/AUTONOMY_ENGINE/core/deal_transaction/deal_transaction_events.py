from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping

from .deal_contract import DealStatus
from .deal_transaction_milestones import (
    DealTransactionMilestone,
)


class DealTransactionEventType(str, Enum):
    DEAL_CREATED = "DEAL_CREATED"
    DEAL_STATE_CHANGED = "DEAL_STATE_CHANGED"
    OFFER_CREATED = "OFFER_CREATED"
    OFFER_STATE_CHANGED = "OFFER_STATE_CHANGED"
    BOOKING_STATE_CHANGED = "BOOKING_STATE_CHANGED"
    MILESTONE_COMPLETED = "MILESTONE_COMPLETED"
    OWNERSHIP_REFERENCE_CHANGED = (
        "OWNERSHIP_REFERENCE_CHANGED"
    )
    EVIDENCE_ATTACHED = "EVIDENCE_ATTACHED"


@dataclass(frozen=True)
class DealTransactionEvent:
    event_id: str
    event_type: DealTransactionEventType
    deal_id: str
    tenant_id: str
    deal_version: int
    occurred_at: str
    payload: Mapping[str, Any] = field(
        default_factory=dict
    )
    source_of_truth: str = "deal"
    schema_version: str = "1.0"
    idempotency_key: str = ""

    def __post_init__(self) -> None:
        if self.deal_version < 1:
            raise ValueError(
                "deal_version must be >= 1."
            )

        object.__setattr__(
            self,
            "event_type",
            DealTransactionEventType(
                self.event_type
            ),
        )

        key = (
            self.idempotency_key
            or self.event_id
        )

        if key != self.event_id:
            raise ValueError(
                "idempotency_key must equal event_id."
            )

        object.__setattr__(
            self,
            "idempotency_key",
            key,
        )

    @property
    def payload_hash(self) -> str:
        body = json.dumps(
            dict(self.payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return sha256(
            body.encode("utf-8")
        ).hexdigest()

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if (
            self.deal_id != deal_id
            or self.tenant_id != tenant_id
        ):
            raise ValueError(
                "Event crosses Deal or tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "source_of_truth": self.source_of_truth,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "deal_version": self.deal_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "payload_hash": self.payload_hash,
            "idempotency_key": self.idempotency_key,
        }

    @classmethod
    def from_milestone(
        cls,
        milestone: DealTransactionMilestone,
        *,
        event_type: DealTransactionEventType = (
            DealTransactionEventType.MILESTONE_COMPLETED
        ),
    ) -> "DealTransactionEvent":
        return cls(
            event_id=milestone.milestone_id,
            event_type=event_type,
            deal_id=milestone.deal_id,
            tenant_id=milestone.tenant_id,
            deal_version=milestone.deal_version,
            occurred_at=(
                milestone.occurred_at.isoformat()
            ),
            payload={
                "milestone_id": milestone.milestone_id,
                "from_status": (
                    milestone.from_status.value
                ),
                "to_status": (
                    milestone.to_status.value
                ),
                "sequence": milestone.sequence,
                "reference_id": (
                    milestone.reference_id
                ),
                "evidence_required": (
                    milestone.evidence_required
                ),
            },
        )


def transaction_event_from_milestone(
    milestone: DealTransactionMilestone,
) -> DealTransactionEvent:
    return DealTransactionEvent.from_milestone(
        milestone
    )


def transaction_event_from_deal_state(
    *,
    deal_id: str,
    tenant_id: str,
    deal_version: int,
    occurred_at: str,
    from_status: DealStatus,
    to_status: DealStatus,
) -> DealTransactionEvent:
    return DealTransactionEvent(
        event_id=(
            f"{deal_id}:"
            f"{deal_version}:"
            f"{to_status.value}"
        ),
        event_type=(
            DealTransactionEventType.DEAL_STATE_CHANGED
        ),
        deal_id=deal_id,
        tenant_id=tenant_id,
        deal_version=deal_version,
        occurred_at=occurred_at,
        payload={
            "from_status": DealStatus(
                from_status
            ).value,
            "to_status": DealStatus(
                to_status
            ).value,
        },
    )
