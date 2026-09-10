from __future__ import annotations

from .impact_errors import (
    ChangeImpactCompatibilityError,
    ChangeImpactIntegrityError,
    ChangeImpactSecurityError,
    ChangeImpactValidationError,
)

from .impact_identity import fingerprint_report

from .impact_models import ChangeImpactReport


def validate_report_contract(
    engine,
    report: ChangeImpactReport,
) -> None:
    if not isinstance(
        report,
        ChangeImpactReport,
    ):
        raise ChangeImpactValidationError(
            "Invalid T17 report."
        )

    if report.schema_version != "1.0":
        raise ChangeImpactCompatibilityError(
            "Unsupported T17 schema."
        )

    if (
        report.state_mutated
        or report.execution_authorized
    ):
        raise ChangeImpactSecurityError(
            "T17 report violates read-only boundary."
        )

    expected = fingerprint_report(
        report
    )

    if expected != report.fingerprint:
        raise ChangeImpactIntegrityError(
            "T17 fingerprint mismatch."
        )


__all__ = [
    "validate_report_contract",
]
