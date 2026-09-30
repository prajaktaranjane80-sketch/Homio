from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_reconciliation import (
    CommissionReconciliation,
)


class CommissionReconciliationHistoryError(
    ValueError
):
    """Invalid reconciliation history."""


@dataclass(frozen=True, slots=True)
class CommissionReconciliationHistoryEntry:
    reconciliation_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    reconciliation_version: int
    state: str
    match_type: str
    variance_amount: str
    reconciliation_fingerprint: str

    @classmethod
    def from_reconciliation(
        cls,
        reconciliation: CommissionReconciliation,
    ) -> "CommissionReconciliationHistoryEntry":
        if not isinstance(
            reconciliation,
            CommissionReconciliation,
        ):
            raise CommissionReconciliationHistoryError(
                "reconciliation must be "
                "CommissionReconciliation."
            )

        return cls(
            reconciliation_id=(
                reconciliation.reconciliation_id
            ),
            tenant_id=reconciliation.tenant_id,
            commission_id=(
                reconciliation.commission_id
            ),
            settlement_id=(
                reconciliation.settlement_id
            ),
            reconciliation_version=(
                reconciliation.reconciliation_version
            ),
            state=reconciliation.state.value,
            match_type=reconciliation.match_type.value,
            variance_amount=format(
                reconciliation.variance_amount.amount,
                "f",
            ),
            reconciliation_fingerprint=(
                reconciliation.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconciliation_id": (
                self.reconciliation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "settlement_id": (
                self.settlement_id
            ),
            "reconciliation_version": (
                self.reconciliation_version
            ),
            "state": self.state,
            "match_type": self.match_type,
            "variance_amount": (
                self.variance_amount
            ),
            "reconciliation_fingerprint": (
                self.reconciliation_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionReconciliationHistory:
    entries: tuple[
        CommissionReconciliationHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        reconciliation: CommissionReconciliation,
    ) -> "CommissionReconciliationHistory":
        entry = (
            CommissionReconciliationHistoryEntry
            .from_reconciliation(reconciliation)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.reconciliation_id
                != entry.reconciliation_id
            ):
                raise CommissionReconciliationHistoryError(
                    "Reconciliation history identity mismatch."
                )

            if (
                entry.reconciliation_version
                < latest.reconciliation_version
            ):
                raise CommissionReconciliationHistoryError(
                    "Reconciliation version cannot move backwards."
                )

            if (
                entry.reconciliation_version
                == latest.reconciliation_version
                and (
                    entry.reconciliation_fingerprint
                    != latest.reconciliation_fingerprint
                )
            ):
                raise CommissionReconciliationHistoryError(
                    "Same reconciliation version contains "
                    "conflicting content."
                )

            if (
                entry.reconciliation_fingerprint
                == latest.reconciliation_fingerprint
            ):
                return self

        return CommissionReconciliationHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionReconciliationHistoryEntry | None:
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
    "CommissionReconciliationHistoryError",
    "CommissionReconciliationHistoryEntry",
    "CommissionReconciliationHistory",
]
