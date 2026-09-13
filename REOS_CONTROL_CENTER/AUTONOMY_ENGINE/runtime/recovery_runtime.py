from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    status: str
    retry_allowed: bool
    recoverable: bool
    escalate: bool
    reason: str


class RecoveryRuntime:
    """Fail-closed recovery classification. No blind retries."""

    TERMINAL = frozenset(
        {
            "STATE_INTEGRITY_FAILURE",
            "ARCHITECTURE_DRIFT",
            "AUTHORIZATION_FAILURE",
            "UNKNOWN_EXECUTOR",
            "POSTFLIGHT_FAILURE",
            "AMBIGUOUS_AUTHORITY",
        }
    )

    RECOVERABLE = frozenset(
        {
            "TEMPORARY_IO",
            "TRANSIENT_TIMEOUT",
            "DEPENDENCY_UNAVAILABLE",
        }
    )

    def classify(
        self,
        failure_code: str,
    ) -> RecoveryDecision:
        code = failure_code.strip().upper()

        if code in self.TERMINAL:
            return RecoveryDecision(
                "ESCALATE",
                False,
                False,
                True,
                code,
            )

        if code in self.RECOVERABLE:
            return RecoveryDecision(
                "RECOVERABLE",
                False,
                True,
                False,
                (
                    "A new validated cycle is required; "
                    "implicit retry is prohibited."
                ),
            )

        return RecoveryDecision(
            "UNKNOWN",
            False,
            False,
            True,
            "UNKNOWN_FAILURE_CLASSIFICATION",
        )
