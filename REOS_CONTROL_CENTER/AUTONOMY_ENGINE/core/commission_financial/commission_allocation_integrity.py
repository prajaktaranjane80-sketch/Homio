from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_allocation import (
    CommissionAllocation,
)
from .commission_allocation_snapshot import (
    CommissionAllocationSnapshot,
)


class CommissionAllocationIntegrityError(
    ValueError
):
    """Allocation integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionAllocationIntegrityReport:
    valid: bool
    allocation_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "allocation_fingerprint": (
                self.allocation_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    allocation: CommissionAllocation,
    snapshot: CommissionAllocationSnapshot,
) -> CommissionAllocationIntegrityReport:
    if not isinstance(
        allocation,
        CommissionAllocation,
    ):
        raise CommissionAllocationIntegrityError(
            "allocation must be CommissionAllocation."
        )

    if not isinstance(
        snapshot,
        CommissionAllocationSnapshot,
    ):
        raise CommissionAllocationIntegrityError(
            "snapshot must be CommissionAllocationSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        allocation.immutable_fingerprint
    )

    if (
        allocation.allocation_set_id
        != snapshot.allocation_set_id
    ):
        reasons.append(
            "allocation_set_id mismatch"
        )

    if (
        allocation.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        allocation.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        allocation.calculation_id
        != snapshot.calculation_id
    ):
        reasons.append(
            "calculation_id mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionAllocationSnapshot
        .from_allocation(
            allocation
        )
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "allocation does not match snapshot"
        )

    return CommissionAllocationIntegrityReport(
        valid=not reasons,
        allocation_fingerprint=current_fingerprint,
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    allocation: CommissionAllocation,
    snapshot: CommissionAllocationSnapshot,
) -> None:
    report = inspect_integrity(
        allocation,
        snapshot,
    )

    if not report.valid:
        raise CommissionAllocationIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionAllocationIntegrityError",
    "CommissionAllocationIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
