from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_settlement import CommissionSettlement


class CommissionSettlementHistoryError(
    ValueError
):
    """Invalid settlement history."""


@dataclass(frozen=True, slots=True)
class CommissionSettlementHistoryEntry:
    settlement_id: str
    tenant_id: str
    commission_id: str
    allocation_set_id: str
    settlement_version: int
    settlement_fingerprint: str
    state: str

    @classmethod
    def from_settlement(
        cls,
        settlement: CommissionSettlement,
    ) -> "CommissionSettlementHistoryEntry":
        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise CommissionSettlementHistoryError(
                "settlement must be CommissionSettlement."
            )

        return cls(
            settlement_id=(
                settlement.settlement_id
            ),
            tenant_id=settlement.tenant_id,
            commission_id=(
                settlement.commission_id
            ),
            allocation_set_id=(
                settlement.allocation_set_id
            ),
            settlement_version=(
                settlement.settlement_version
            ),
            settlement_fingerprint=(
                settlement.immutable_fingerprint
            ),
            state=settlement.state.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "settlement_id": (
                self.settlement_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "settlement_version": (
                self.settlement_version
            ),
            "settlement_fingerprint": (
                self.settlement_fingerprint
            ),
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class CommissionSettlementHistory:
    entries: tuple[
        CommissionSettlementHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        settlement: CommissionSettlement,
    ) -> "CommissionSettlementHistory":
        entry = (
            CommissionSettlementHistoryEntry
            .from_settlement(settlement)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.settlement_id
                != entry.settlement_id
            ):
                raise CommissionSettlementHistoryError(
                    "Settlement history identity mismatch."
                )

            if (
                entry.settlement_version
                != latest.settlement_version
            ):
                raise CommissionSettlementHistoryError(
                    "Settlement history cannot mix "
                    "different settlement versions."
                )

            if (
                latest.settlement_fingerprint
                == entry.settlement_fingerprint
            ):
                return self

        return CommissionSettlementHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionSettlementHistoryEntry | None:
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
    "CommissionSettlementHistoryError",
    "CommissionSettlementHistoryEntry",
    "CommissionSettlementHistory",
]
