from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class DealTransactionMilestoneError(ValueError):
    pass


def _status(value: Any) -> str:
    return getattr(value, "value", value)


def _ts(value: datetime | str | None) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    elif isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class DealTransactionMilestone:
    milestone_id: str
    deal_id: str
    tenant_id: str
    from_status: str
    to_status: str
    sequence: int
    deal_version: int
    occurred_at: datetime
    reference_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "milestone_id",
            "deal_id",
            "tenant_id",
            "from_status",
            "to_status",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise DealTransactionMilestoneError(
                    f"{name} is required."
                )

        if self.sequence < 1 or self.deal_version < 1:
            raise DealTransactionMilestoneError(
                "sequence and deal_version must be >= 1."
            )

        if self.occurred_at.tzinfo is None:
            raise DealTransactionMilestoneError(
                "occurred_at must be timezone-aware."
            )

    @classmethod
    def create(
        cls,
        *,
        deal_id: str,
        tenant_id: str,
        from_status: Any,
        to_status: Any,
        sequence: int,
        deal_version: int,
        occurred_at: datetime | str | None = None,
        reference_id: str | None = None,
        milestone_id: str | None = None,
    ) -> "DealTransactionMilestone":
        return cls(
            milestone_id or str(uuid4()),
            deal_id,
            tenant_id,
            _status(from_status),
            _status(to_status),
            sequence,
            deal_version,
            _ts(occurred_at),
            reference_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "sequence": self.sequence,
            "deal_version": self.deal_version,
            "occurred_at": self.occurred_at.isoformat(),
            "reference_id": self.reference_id,
        }


__all__ = [
    "DealTransactionMilestone",
    "DealTransactionMilestoneError",
]
