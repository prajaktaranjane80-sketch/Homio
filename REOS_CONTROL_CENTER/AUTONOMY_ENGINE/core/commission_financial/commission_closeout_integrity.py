from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_closeout import CommissionCloseout
from .commission_closeout_snapshot import (
    CommissionCloseoutSnapshot,
)


class CommissionCloseoutIntegrityError(
    ValueError
):
    """Closeout integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionCloseoutIntegrityReport:
    valid: bool
    closeout_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "closeout_fingerprint": (
                self.closeout_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    closeout: CommissionCloseout,
    snapshot: CommissionCloseoutSnapshot,
) -> CommissionCloseoutIntegrityReport:
    if not isinstance(
        closeout,
        CommissionCloseout,
    ):
        raise CommissionCloseoutIntegrityError(
            "closeout must be CommissionCloseout."
        )

    if not isinstance(
        snapshot,
        CommissionCloseoutSnapshot,
    ):
        raise CommissionCloseoutIntegrityError(
            "snapshot must be CommissionCloseoutSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        closeout.immutable_fingerprint
    )

    if (
        closeout.closeout_id
        != snapshot.closeout_id
    ):
        reasons.append("closeout_id mismatch")

    if (
        closeout.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append("tenant_id mismatch")

    if (
        closeout.commission_id
        != snapshot.commission_id
    ):
        reasons.append("commission_id mismatch")

    if (
        closeout.statement_id
        != snapshot.statement_id
    ):
        reasons.append("statement_id mismatch")

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionCloseoutSnapshot
        .from_closeout(closeout)
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "closeout does not match snapshot"
        )

    return CommissionCloseoutIntegrityReport(
        valid=not reasons,
        closeout_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    closeout: CommissionCloseout,
    snapshot: CommissionCloseoutSnapshot,
) -> None:
    report = inspect_integrity(
        closeout,
        snapshot,
    )

    if not report.valid:
        raise CommissionCloseoutIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionCloseoutIntegrityError",
    "CommissionCloseoutIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
