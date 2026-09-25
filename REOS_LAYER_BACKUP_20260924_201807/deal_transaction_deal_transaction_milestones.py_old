from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .deal import DealStatus


class DealMilestoneError(ValueError):
    """Base error for transaction milestone violations."""


class DealMilestoneTenantError(DealMilestoneError):
    """Raised when a milestone crosses its tenant boundary."""


class DealMilestoneConcurrencyError(DealMilestoneError):
    """Raised when a Deal version is stale."""


class DealMilestoneTransitionError(DealMilestoneError):
    """Raised when a target is not a transaction milestone."""


_TRANSACTION_STATUS_VALUES = frozenset(
    {
        "BOOKING_PENDING",
        "BOOKED",
        "AGREEMENT_PENDING",
        "AGREED",
        "REGISTRATION_PENDING",
        "REGISTERED",
        "COMPLETION_PENDING",
        "COMPLETED",
    }
)


@dataclass(frozen=True)
class DealTransactionMilestone:
    """Immutable transaction milestone evidence owned by the Deal."""

    milestone_id: str
    deal_id: str
    tenant_id: str
    from_status: DealStatus
    to_status: DealStatus
    sequence: int
    deal_version: int
    occurred_at: datetime
    reference_id: str | None = None

    def __post_init__(self) -> None:
        from .deal import DealStatus

        for field_name in (
            "milestone_id",
            "deal_id",
            "tenant_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise DealMilestoneError(f"{field_name} is required.")

        if self.sequence < 1:
            raise DealMilestoneError("sequence must be >= 1.")

        if self.deal_version < 1:
            raise DealMilestoneError("deal_version must be >= 1.")

        if self.occurred_at.tzinfo is None:
            raise DealMilestoneError(
                "occurred_at must be timezone-aware."
            )

        from_status = DealStatus(self.from_status)
        to_status = DealStatus(self.to_status)

        if to_status.value not in _TRANSACTION_STATUS_VALUES:
            raise DealMilestoneError(
                f"{to_status.value} is not a transaction milestone."
            )

        object.__setattr__(self, "from_status", from_status)
        object.__setattr__(self, "to_status", to_status)

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
        }


__all__ = [
    "DealTransactionMilestone",
    "DealMilestoneConcurrencyError",
    "DealMilestoneError",
    "DealMilestoneTenantError",
    "DealMilestoneTransitionError",
]
