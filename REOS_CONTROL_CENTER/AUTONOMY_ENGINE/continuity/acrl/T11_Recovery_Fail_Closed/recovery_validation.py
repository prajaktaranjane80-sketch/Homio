"""ACRL T11 — Recovery validation."""

from __future__ import annotations

from typing import Any, Mapping

from .recovery_guard import (
    RecoveryReport,
    RecoveryRequest,
)
from .recovery_policy import (
    RecoveryPolicy,
    RecoveryPolicyEngine,
)


class RecoveryValidationError(RuntimeError):
    """Recovery validation failure."""


class RecoveryValidationEngine:
    """Fail-closed validation boundary."""

    @classmethod
    def validate_request(
        cls,
        request: RecoveryRequest,
        policy: RecoveryPolicy | None = None,
    ) -> bool:
        if not isinstance(
            request,
            RecoveryRequest,
        ):
            raise RecoveryValidationError(
                "Invalid recovery request."
            )

        active_policy = (
            policy
            if policy is not None
            else RecoveryPolicyEngine.default()
        )

        RecoveryPolicyEngine.validate(
            active_policy
        )

        if not request.failure_type.strip():
            raise RecoveryValidationError(
                "failure_type cannot be empty."
            )

        if not request.component.strip():
            raise RecoveryValidationError(
                "component cannot be empty."
            )

        if active_policy.authority_required:
            if not request.authoritative:
                raise RecoveryValidationError(
                    "Authoritative context is required."
                )

        if active_policy.integrity_required:
            if not request.integrity_verified:
                raise RecoveryValidationError(
                    "Verified integrity is required."
                )

        if (
            request.destructive
            and not active_policy.destructive_recovery_allowed
        ):
            raise RecoveryValidationError(
                "Destructive recovery is forbidden."
            )

        return True

    @classmethod
    def validate_report(
        cls,
        report: RecoveryReport,
    ) -> bool:
        if not isinstance(
            report,
            RecoveryReport,
        ):
            raise RecoveryValidationError(
                "Invalid recovery report."
            )

        if report.authority != (
            "REOS_CONTROL_CENTER"
        ):
            raise RecoveryValidationError(
                "Invalid recovery authority."
            )

        if len(report.request_fingerprint) != 64:
            raise RecoveryValidationError(
                "Invalid request fingerprint."
            )

        if not report.validated:
            raise RecoveryValidationError(
                "Recovery report is not validated."
            )

        if report.fail_closed:
            if report.action is not None:
                raise RecoveryValidationError(
                    "Fail-closed report cannot contain an action."
                )
            return True

        if report.action is None:
            raise RecoveryValidationError(
                "Recoverable report requires an action."
            )

        if report.action.destructive:
            raise RecoveryValidationError(
                "Destructive recovery action is forbidden."
            )

        return True

    @classmethod
    def validate_details(
        cls,
        details: Mapping[str, Any] | None,
    ) -> bool:
        if details is None:
            return True

        if not isinstance(details, Mapping):
            raise RecoveryValidationError(
                "Recovery details must be a mapping."
            )

        return True


__all__ = [
    "RecoveryValidationEngine",
    "RecoveryValidationError",
]