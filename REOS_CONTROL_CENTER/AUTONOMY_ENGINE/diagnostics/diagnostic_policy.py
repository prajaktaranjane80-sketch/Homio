"""
REOS Diagnostic Safety Policy
=============================

Fail-closed policy for the diagnostic surface.

The diagnostic subsystem must never convert an uncertain condition into
PASS merely to make the system look healthy.
"""

from __future__ import annotations

from .diagnostic_contract import (
    REQUIRED_CHECKS,
    validate_check_keys,
    validate_unique_check_keys,
)
from .diagnostic_models import (
    DiagnosticCheck,
    DiagnosticReport,
    RESULT_BLOCKED,
    RESULT_PASS,
)


class DiagnosticPolicy:
    """
    Applies safety rules to diagnostic results.
    """

    def evaluate(
        self,
        checks: tuple[DiagnosticCheck, ...],
    ) -> str:
        keys = tuple(
            check.key
            for check in checks
        )

        validate_check_keys(keys)
        validate_unique_check_keys(keys)

        blocked = any(
            check.blocked
            for check in checks
        )

        return (
            RESULT_BLOCKED
            if blocked
            else RESULT_PASS
        )

    def enforce(
        self,
        report: DiagnosticReport,
    ) -> DiagnosticReport:
        """
        Defensive final validation.

        A report cannot claim PASS while containing BLOCKED checks.
        """

        expected = self.evaluate(report.checks)

        if expected == report.result:
            return report

        return DiagnosticReport(
            schema_version=report.schema_version,
            result=expected,
            checks=report.checks,
            position=report.position,
            fingerprint=report.fingerprint,
            metadata={
                **report.metadata,
                "policy_reconciled": True,
            },
        )
