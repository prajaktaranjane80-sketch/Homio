"""
REOS Diagnostic Formatter
=========================

Human and machine output surfaces.

The compact formatter is intentionally small because diagnostics are
supposed to reduce context consumption, not create another giant log.
"""

from __future__ import annotations

import json
from typing import Any

from .diagnostic_models import DiagnosticReport


class DiagnosticFormatter:
    """
    Stable output formatter.
    """

    HEADER = "REOS HEALTH"
    SEPARATOR = "────────────────────────"

    @classmethod
    def compact(
        cls,
        report: DiagnosticReport,
    ) -> str:
        lines = [
            cls.HEADER,
            cls.SEPARATOR,
        ]

        for check in report.checks:
            lines.append(
                f"{check.key:<18} {check.status}"
            )

        lines.extend(
            [
                cls.SEPARATOR,
                f"{'RESULT':<18} {report.result}",
            ]
        )

        position = report.position.compact()

        if report.result == "PASS":
            if position:
                lines.append(
                    f"{'CURRENT':<18} {position}"
                )

        else:
            failed = report.failed_checks[0]

            lines.append(
                f"{'FAILED':<18} {failed.key}"
            )

            if failed.cause:
                lines.append(
                    f"{'CAUSE':<18} {failed.cause}"
                )

            if failed.next_action:
                lines.append(
                    f"{'NEXT':<18} {failed.next_action}"
                )

        if report.fingerprint:
            lines.append(
                f"{'FINGERPRINT':<18} "
                f"{report.fingerprint[:16]}"
            )

        return "\n".join(lines)

    @staticmethod
    def json(
        report: DiagnosticReport,
    ) -> str:
        return json.dumps(
            report.as_dict(),
            indent=2,
            sort_keys=True,
        )

    @staticmethod
    def one_line(
        report: DiagnosticReport,
    ) -> str:
        """
        Ultra-compact machine/operator status.
        """

        if report.result == "PASS":
            return "REOS_HEALTH PASS"

        failed = (
            report.failed_checks[0].key
            if report.failed_checks
            else "UNKNOWN"
        )

        return (
            f"REOS_HEALTH BLOCKED "
            f"FAILED={failed}"
        )
