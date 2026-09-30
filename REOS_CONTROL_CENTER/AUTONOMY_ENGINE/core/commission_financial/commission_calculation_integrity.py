from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_calculation import (
    CommissionCalculation,
)
from .commission_calculation_snapshot import (
    CommissionCalculationSnapshot,
)


class CommissionCalculationIntegrityError(
    ValueError
):
    """Calculation integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionCalculationIntegrityReport:
    valid: bool
    calculation_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "calculation_fingerprint": (
                self.calculation_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    calculation: CommissionCalculation,
    snapshot: CommissionCalculationSnapshot,
) -> CommissionCalculationIntegrityReport:
    if not isinstance(
        calculation,
        CommissionCalculation,
    ):
        raise CommissionCalculationIntegrityError(
            "calculation must be CommissionCalculation."
        )

    if not isinstance(
        snapshot,
        CommissionCalculationSnapshot,
    ):
        raise CommissionCalculationIntegrityError(
            "snapshot must be CommissionCalculationSnapshot."
        )

    reasons: list[str] = []

    calculation_fingerprint = (
        calculation.immutable_fingerprint
    )

    if (
        calculation.calculation_id
        != snapshot.calculation_id
    ):
        reasons.append(
            "calculation_id mismatch"
        )

    if (
        calculation.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        calculation.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        calculation.contract_version
        != snapshot.contract_version
    ):
        reasons.append(
            "contract_version mismatch"
        )

    if (
        calculation.calculation_version
        != snapshot.calculation_version
    ):
        reasons.append(
            "calculation_version mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    current_snapshot = (
        CommissionCalculationSnapshot
        .from_calculation(
            calculation
        )
    )

    if (
        current_snapshot.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "calculation does not match snapshot"
        )

    return CommissionCalculationIntegrityReport(
        valid=not reasons,
        calculation_fingerprint=(
            calculation_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    calculation: CommissionCalculation,
    snapshot: CommissionCalculationSnapshot,
) -> None:
    report = inspect_integrity(
        calculation,
        snapshot,
    )

    if not report.valid:
        raise CommissionCalculationIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionCalculationIntegrityError",
    "CommissionCalculationIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
