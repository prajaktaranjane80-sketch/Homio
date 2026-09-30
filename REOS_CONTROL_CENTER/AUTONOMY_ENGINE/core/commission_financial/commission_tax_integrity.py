from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_tax import CommissionTaxAssessment
from .commission_tax_snapshot import CommissionTaxSnapshot


class CommissionTaxIntegrityError(
    ValueError
):
    """Tax assessment integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionTaxIntegrityReport:
    valid: bool
    assessment_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "assessment_fingerprint": (
                self.assessment_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    assessment: CommissionTaxAssessment,
    snapshot: CommissionTaxSnapshot,
) -> CommissionTaxIntegrityReport:
    if not isinstance(
        assessment,
        CommissionTaxAssessment,
    ):
        raise CommissionTaxIntegrityError(
            "assessment must be CommissionTaxAssessment."
        )

    if not isinstance(
        snapshot,
        CommissionTaxSnapshot,
    ):
        raise CommissionTaxIntegrityError(
            "snapshot must be CommissionTaxSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        assessment.immutable_fingerprint
    )

    if (
        assessment.assessment_id
        != snapshot.assessment_id
    ):
        reasons.append(
            "assessment_id mismatch"
        )

    if (
        assessment.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        assessment.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        assessment.invoice_id
        != snapshot.invoice_id
    ):
        reasons.append(
            "invoice_id mismatch"
        )

    if (
        assessment.assessment_version
        != snapshot.assessment_version
    ):
        reasons.append(
            "assessment_version mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionTaxSnapshot.from_assessment(
            assessment
        )
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "assessment does not match snapshot"
        )

    return CommissionTaxIntegrityReport(
        valid=not reasons,
        assessment_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    assessment: CommissionTaxAssessment,
    snapshot: CommissionTaxSnapshot,
) -> None:
    report = inspect_integrity(
        assessment,
        snapshot,
    )

    if not report.valid:
        raise CommissionTaxIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionTaxIntegrityError",
    "CommissionTaxIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
