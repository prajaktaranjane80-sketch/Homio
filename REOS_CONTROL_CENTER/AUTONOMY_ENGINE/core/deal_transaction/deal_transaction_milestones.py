from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .deal_contract import DealStatus, utc_datetime


class DealMilestoneTransitionError(ValueError):
    pass


TRANSACTION_STATUSES = frozenset({
    DealStatus.BOOKING_PENDING,
    DealStatus.BOOKED,
    DealStatus.AGREEMENT_PENDING,
    DealStatus.AGREED,
    DealStatus.REGISTRATION_PENDING,
    DealStatus.REGISTERED,
    DealStatus.COMPLETION_PENDING,
    DealStatus.COMPLETED,
})


@dataclass(frozen=True)
class DealTransactionMilestone:
    milestone_id: str
    deal_id: str
    tenant_id: str
    from_status: DealStatus
    to_status: DealStatus
    sequence: int
    deal_version: int
    occurred_at: datetime
    reference_id: str | None = None
    evidence_required: bool = True

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise DealMilestoneTransitionError(
                "sequence must be >= 1."
            )

        if self.deal_version < 1:
            raise DealMilestoneTransitionError(
                "deal_version must be >= 1."
            )

        object.__setattr__(
            self,
            "from_status",
            DealStatus(self.from_status),
        )

        object.__setattr__(
            self,
            "to_status",
            DealStatus(self.to_status),
        )

        object.__setattr__(
            self,
            "occurred_at",
            utc_datetime(self.occurred_at),
        )

        if self.to_status not in TRANSACTION_STATUSES:
            raise DealMilestoneTransitionError(
                "Target is not a transaction status."
            )

    @classmethod
    def create(
        cls,
        *,
        deal_id: str,
        tenant_id: str,
        from_status: DealStatus,
        to_status: DealStatus,
        sequence: int,
        deal_version: int,
        reference_id: str | None = None,
        occurred_at: Any = None,
        evidence_required: bool = True,
    ) -> "DealTransactionMilestone":
        return cls(
            milestone_id=str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            from_status=from_status,
            to_status=to_status,
            sequence=sequence,
            deal_version=deal_version,
            occurred_at=utc_datetime(occurred_at),
            reference_id=reference_id,
            evidence_required=evidence_required,
        )

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
            raise DealMilestoneTransitionError(
                "Milestone crosses Deal or tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "sequence": self.sequence,
            "deal_version": self.deal_version,
            "occurred_at": self.occurred_at.isoformat(),
            "reference_id": self.reference_id,
            "evidence_required": self.evidence_required,
        }
