from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_entitlement import (
    CommissionEntitlement,
)


class CommissionEntitlementHistoryError(
    ValueError
):
    """Invalid entitlement history."""


@dataclass(frozen=True, slots=True)
class CommissionEntitlementHistoryEntry:
    entitlement_id: str
    tenant_id: str
    commission_id: str
    calculation_id: str
    entitlement_fingerprint: str

    @classmethod
    def from_entitlement(
        cls,
        entitlement: CommissionEntitlement,
    ) -> "CommissionEntitlementHistoryEntry":
        if not isinstance(
            entitlement,
            CommissionEntitlement,
        ):
            raise CommissionEntitlementHistoryError(
                "entitlement must be CommissionEntitlement."
            )

        return cls(
            entitlement_id=(
                entitlement.entitlement_id
            ),
            tenant_id=entitlement.tenant_id,
            commission_id=(
                entitlement.commission_id
            ),
            calculation_id=(
                entitlement.calculation_id
            ),
            entitlement_fingerprint=(
                entitlement.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entitlement_id": (
                self.entitlement_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "calculation_id": (
                self.calculation_id
            ),
            "entitlement_fingerprint": (
                self.entitlement_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionEntitlementHistory:
    entries: tuple[
        CommissionEntitlementHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        entitlement: CommissionEntitlement,
    ) -> "CommissionEntitlementHistory":
        entry = (
            CommissionEntitlementHistoryEntry
            .from_entitlement(entitlement)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.commission_id
                != entry.commission_id
                or latest.entitlement_id
                != entry.entitlement_id
            ):
                raise CommissionEntitlementHistoryError(
                    "Entitlement history identity mismatch."
                )

            if (
                latest.entitlement_fingerprint
                == entry.entitlement_fingerprint
            ):
                return self

        return CommissionEntitlementHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionEntitlementHistoryEntry | None:
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
    "CommissionEntitlementHistoryError",
    "CommissionEntitlementHistoryEntry",
    "CommissionEntitlementHistory",
]
