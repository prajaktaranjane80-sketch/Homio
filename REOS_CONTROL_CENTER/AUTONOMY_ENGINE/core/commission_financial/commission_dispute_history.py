from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_dispute import CommissionDispute


class CommissionDisputeHistoryError(
    ValueError
):
    """Invalid dispute history."""


@dataclass(frozen=True, slots=True)
class CommissionDisputeHistoryEntry:
    dispute_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    dispute_version: int
    state: str
    resolution: str
    dispute_fingerprint: str

    @classmethod
    def from_dispute(
        cls,
        dispute: CommissionDispute,
    ) -> "CommissionDisputeHistoryEntry":
        if not isinstance(
            dispute,
            CommissionDispute,
        ):
            raise CommissionDisputeHistoryError(
                "dispute must be CommissionDispute."
            )

        return cls(
            dispute_id=dispute.dispute_id,
            tenant_id=dispute.tenant_id,
            commission_id=dispute.commission_id,
            settlement_id=dispute.settlement_id,
            dispute_version=dispute.dispute_version,
            state=dispute.state.value,
            resolution=dispute.resolution.value,
            dispute_fingerprint=(
                dispute.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dispute_id": self.dispute_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "settlement_id": self.settlement_id,
            "dispute_version": self.dispute_version,
            "state": self.state,
            "resolution": self.resolution,
            "dispute_fingerprint": (
                self.dispute_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionDisputeHistory:
    entries: tuple[
        CommissionDisputeHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        dispute: CommissionDispute,
    ) -> "CommissionDisputeHistory":
        entry = (
            CommissionDisputeHistoryEntry
            .from_dispute(dispute)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.dispute_id
                != entry.dispute_id
            ):
                raise CommissionDisputeHistoryError(
                    "Dispute history identity mismatch."
                )

            if (
                entry.dispute_version
                != latest.dispute_version + 1
            ):
                if (
                    entry.dispute_version
                    == latest.dispute_version
                    and entry.dispute_fingerprint
                    == latest.dispute_fingerprint
                ):
                    return self

                raise CommissionDisputeHistoryError(
                    "Dispute history versions must advance "
                    "sequentially."
                )

        elif entry.dispute_version != 1:
            raise CommissionDisputeHistoryError(
                "First dispute version must be 1."
            )

        return CommissionDisputeHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionDisputeHistoryEntry | None:
        return (
            self.entries[-1]
            if self.entries
            else None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionDisputeHistoryError",
    "CommissionDisputeHistoryEntry",
    "CommissionDisputeHistory",
]
