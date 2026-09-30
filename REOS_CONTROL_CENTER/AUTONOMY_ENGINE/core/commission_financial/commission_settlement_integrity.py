from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_settlement import CommissionSettlement
from .commission_settlement_snapshot import (
    CommissionSettlementSnapshot,
)


class CommissionSettlementIntegrityError(
    ValueError
):
    """Settlement integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionSettlementIntegrityReport:
    valid: bool
    settlement_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "settlement_fingerprint": (
                self.settlement_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    settlement: CommissionSettlement,
    snapshot: CommissionSettlementSnapshot,
) -> CommissionSettlementIntegrityReport:
    if not isinstance(
        settlement,
        CommissionSettlement,
    ):
        raise CommissionSettlementIntegrityError(
            "settlement must be CommissionSettlement."
        )

    if not isinstance(
        snapshot,
        CommissionSettlementSnapshot,
    ):
        raise CommissionSettlementIntegrityError(
            "snapshot must be CommissionSettlementSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        settlement.immutable_fingerprint
    )

    if (
        settlement.settlement_id
        != snapshot.settlement_id
    ):
        reasons.append(
            "settlement_id mismatch"
        )

    if (
        settlement.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        settlement.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        settlement.allocation_set_id
        != snapshot.allocation_set_id
    ):
        reasons.append(
            "allocation_set_id mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionSettlementSnapshot
        .from_settlement(
            settlement
        )
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "settlement does not match snapshot"
        )

    return CommissionSettlementIntegrityReport(
        valid=not reasons,
        settlement_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    settlement: CommissionSettlement,
    snapshot: CommissionSettlementSnapshot,
) -> None:
    report = inspect_integrity(
        settlement,
        snapshot,
    )

    if not report.valid:
        raise CommissionSettlementIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionSettlementIntegrityError",
    "CommissionSettlementIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
