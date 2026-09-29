from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .deal import DealStatus


class DealMilestoneError(ValueError):
    pass


class DealMilestoneTenantError(DealMilestoneError):
    pass


class DealMilestoneConcurrencyError(DealMilestoneError):
    pass


class DealMilestoneTransitionError(DealMilestoneError):
    pass


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
    """Immutable transaction milestone owned by the Deal aggregate."""

    milestone_id: str
    deal_id: str
    tenant_id: str
    from_status: "DealStatus"
    to_status: "DealStatus"
    sequence: int
    deal_version: int
    occurred_at: datetime
    reference_id: str | None = None

    def __post_init__(self) -> None:
        from .deal import DealStatus

        for name in (
            "milestone_id",
            "deal_id",
            "tenant_id",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise DealMilestoneError(
                    f"{name} is required."
                )

        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 1
        ):
            raise DealMilestoneError(
                "sequence must be an integer >= 1."
            )

        if (
            isinstance(self.deal_version, bool)
            or not isinstance(self.deal_version, int)
            or self.deal_version < 1
        ):
            raise DealMilestoneError(
                "deal_version must be an integer >= 1."
            )

        if (
            not isinstance(self.occurred_at, datetime)
            or self.occurred_at.tzinfo is None
        ):
            raise DealMilestoneError(
                "occurred_at must be timezone-aware."
            )

        from_status = DealStatus(self.from_status)
        to_status = DealStatus(self.to_status)

        if to_status.value not in _TRANSACTION_STATUS_VALUES:
            raise DealMilestoneTransitionError(
                f"{to_status.value} is not a transaction milestone."
            )

        object.__setattr__(
            self,
            "from_status",
            from_status,
        )
        object.__setattr__(
            self,
            "to_status",
            to_status,
        )

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if self.deal_id != deal_id:
            raise DealMilestoneTenantError(
                "Milestone belongs to a different deal."
            )

        if self.tenant_id != tenant_id:
            raise DealMilestoneTenantError(
                "Milestone belongs to a different tenant."
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
        }


__all__ = [
    "DealTransactionMilestone",
    "DealMilestoneConcurrencyError",
    "DealMilestoneError",
    "DealMilestoneTenantError",
    "DealMilestoneTransitionError",
]
