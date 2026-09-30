from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_reconciliation import (
    CommissionReconciliation,
)
from .commission_reconciliation_snapshot import (
    CommissionReconciliationSnapshot,
)


class CommissionReconciliationIntegrityError(
    ValueError
):
    """Reconciliation integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionReconciliationIntegrityReport:
    valid: bool
    reconciliation_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "reconciliation_fingerprint": (
                self.reconciliation_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    reconciliation: CommissionReconciliation,
    snapshot: CommissionReconciliationSnapshot,
) -> CommissionReconciliationIntegrityReport:
    if not isinstance(
        reconciliation,
        CommissionReconciliation,
    ):
        raise CommissionReconciliationIntegrityError(
            "reconciliation must be "
            "CommissionReconciliation."
        )

    if not isinstance(
        snapshot,
        CommissionReconciliationSnapshot,
    ):
        raise CommissionReconciliationIntegrityError(
            "snapshot must be "
            "CommissionReconciliationSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        reconciliation.immutable_fingerprint
    )

    if (
        reconciliation.reconciliation_id
        != snapshot.reconciliation_id
    ):
        reasons.append(
            "reconciliation_id mismatch"
        )

    if (
        reconciliation.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        reconciliation.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        reconciliation.settlement_id
        != snapshot.settlement_id
    ):
        reasons.append(
            "settlement_id mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionReconciliationSnapshot
        .from_reconciliation(
            reconciliation
        )
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "reconciliation does not match snapshot"
        )

    return CommissionReconciliationIntegrityReport(
        valid=not reasons,
        reconciliation_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    reconciliation: CommissionReconciliation,
    snapshot: CommissionReconciliationSnapshot,
) -> None:
    report = inspect_integrity(
        reconciliation,
        snapshot,
    )

    if not report.valid:
        raise CommissionReconciliationIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionReconciliationIntegrityError",
    "CommissionReconciliationIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
