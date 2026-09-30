from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_dispute import CommissionDispute
from .commission_dispute_snapshot import (
    CommissionDisputeSnapshot,
)


class CommissionDisputeIntegrityError(
    ValueError
):
    """Dispute integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionDisputeIntegrityReport:
    valid: bool
    dispute_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "dispute_fingerprint": (
                self.dispute_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    dispute: CommissionDispute,
    snapshot: CommissionDisputeSnapshot,
) -> CommissionDisputeIntegrityReport:
    if not isinstance(
        dispute,
        CommissionDispute,
    ):
        raise CommissionDisputeIntegrityError(
            "dispute must be CommissionDispute."
        )

    if not isinstance(
        snapshot,
        CommissionDisputeSnapshot,
    ):
        raise CommissionDisputeIntegrityError(
            "snapshot must be CommissionDisputeSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        dispute.immutable_fingerprint
    )

    if (
        dispute.dispute_id
        != snapshot.dispute_id
    ):
        reasons.append("dispute_id mismatch")

    if (
        dispute.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append("tenant_id mismatch")

    if (
        dispute.commission_id
        != snapshot.commission_id
    ):
        reasons.append("commission_id mismatch")

    if (
        dispute.settlement_id
        != snapshot.settlement_id
    ):
        reasons.append("settlement_id mismatch")

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionDisputeSnapshot
        .from_dispute(dispute)
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "dispute does not match snapshot"
        )

    return CommissionDisputeIntegrityReport(
        valid=not reasons,
        dispute_fingerprint=current_fingerprint,
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    dispute: CommissionDispute,
    snapshot: CommissionDisputeSnapshot,
) -> None:
    report = inspect_integrity(
        dispute,
        snapshot,
    )

    if not report.valid:
        raise CommissionDisputeIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionDisputeIntegrityError",
    "CommissionDisputeIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
