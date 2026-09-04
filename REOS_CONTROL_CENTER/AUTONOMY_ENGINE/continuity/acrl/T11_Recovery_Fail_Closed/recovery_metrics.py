"""ACRL T11 — Recovery metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .recovery_guard import (
    RecoveryReport,
)


@dataclass(frozen=True)
class RecoveryMetrics:
    decision: str
    reason: str
    fail_closed: bool
    automatic: bool
    destructive: bool
    requires_human: bool
    fingerprint_length: int

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "fail_closed": self.fail_closed,
            "automatic": self.automatic,
            "destructive": self.destructive,
            "requires_human": self.requires_human,
            "fingerprint_length": (
                self.fingerprint_length
            ),
        }


class RecoveryMetricsEngine:
    """Observational-only recovery metrics."""

    @classmethod
    def collect(
        cls,
        report: RecoveryReport,
    ) -> RecoveryMetrics:
        if not isinstance(
            report,
            RecoveryReport,
        ):
            raise TypeError(
                "Expected RecoveryReport."
            )

        action = report.action

        return RecoveryMetrics(
            decision=report.decision.value,
            reason=report.reason.value,
            fail_closed=report.fail_closed,
            automatic=(
                action.automatic
                if action is not None
                else False
            ),
            destructive=(
                action.destructive
                if action is not None
                else False
            ),
            requires_human=(
                action.requires_human
                if action is not None
                else False
            ),
            fingerprint_length=(
                len(report.request_fingerprint)
            ),
        )


__all__ = [
    "RecoveryMetrics",
    "RecoveryMetricsEngine",
]