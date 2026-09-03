"""ACRL T11 — Recovery / Fail-Closed Guard."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class RecoveryGuardError(RuntimeError):
    """Base T11 recovery error."""


class RecoveryValidationError(RecoveryGuardError):
    """Invalid recovery input."""


class RecoveryAuthorityError(RecoveryGuardError):
    """Invalid recovery authority."""


class RecoveryIntegrityError(RecoveryGuardError):
    """Recovery integrity failure."""


class RecoveryBlockedError(RecoveryGuardError):
    """Recovery operation is blocked."""


class RecoveryDecision(str, Enum):
    RECOVER = "RECOVER"
    BLOCK = "BLOCK"
    FAIL_CLOSED = "FAIL_CLOSED"


class RecoveryReason(str, Enum):
    NONE = "NONE"
    RECOVERABLE_EXECUTION_ERROR = "RECOVERABLE_EXECUTION_ERROR"
    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"
    INVALID_INPUT = "INVALID_INPUT"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    ARCHITECTURE_DRIFT = "ARCHITECTURE_DRIFT"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"
    DESTRUCTIVE_ACTION = "DESTRUCTIVE_ACTION"


@dataclass(frozen=True)
class RecoveryRequest:
    failure_type: str
    component: str
    recoverable: bool
    authoritative: bool
    destructive: bool = False
    integrity_verified: bool = True
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "component": self.component,
            "recoverable": self.recoverable,
            "authoritative": self.authoritative,
            "destructive": self.destructive,
            "integrity_verified": self.integrity_verified,
            "details": (
                dict(self.details)
                if self.details is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class RecoveryAction:
    action: str
    component: str
    automatic: bool
    destructive: bool = False
    requires_human: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "component": self.component,
            "automatic": self.automatic,
            "destructive": self.destructive,
            "requires_human": self.requires_human,
        }


@dataclass(frozen=True)
class RecoveryReport:
    schema_version: str
    authority: str
    decision: RecoveryDecision
    reason: RecoveryReason
    request_fingerprint: str
    action: RecoveryAction | None
    fail_closed: bool
    validated: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "request_fingerprint": self.request_fingerprint,
            "action": (
                self.action.to_dict()
                if self.action is not None
                else None
            ),
            "fail_closed": self.fail_closed,
            "validated": self.validated,
            "explanation": self.explanation,
        }


class RecoveryGuard:
    """Deterministic, fail-closed recovery decision engine."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    SAFE_AUTOMATIC_FAILURES = frozenset(
        {
            "transient",
            "timeout",
            "temporary",
            "retryable",
            "recoverable",
        }
    )

    UNSAFE_FAILURES = frozenset(
        {
            "architecture",
            "architecture_drift",
            "authority",
            "authority_conflict",
            "integrity",
            "tamper",
            "destructive",
            "unknown",
        }
    )

    @classmethod
    def canonicalize(cls, value: Any) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise RecoveryValidationError(
                "Recovery input cannot be canonicalized."
            ) from exc

    @classmethod
    def fingerprint(cls, value: Any) -> str:
        return hashlib.sha256(
            cls.canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _validate_request(
        cls,
        request: RecoveryRequest,
    ) -> None:
        if not isinstance(request, RecoveryRequest):
            raise RecoveryValidationError(
                "Invalid recovery request."
            )

        if not request.failure_type.strip():
            raise RecoveryValidationError(
                "failure_type cannot be empty."
            )

        if not request.component.strip():
            raise RecoveryValidationError(
                "component cannot be empty."
            )

        if not request.authoritative:
            raise RecoveryAuthorityError(
                "Recovery requires authoritative context."
            )

        if not request.integrity_verified:
            raise RecoveryIntegrityError(
                "Recovery requires verified integrity."
            )

    @classmethod
    def _normalize_failure_type(
        cls,
        failure_type: str,
    ) -> str:
        return (
            failure_type
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

    @classmethod
    def _build_action(
        cls,
        request: RecoveryRequest,
    ) -> RecoveryAction:
        return RecoveryAction(
            action="RETRY_SAFE_OPERATION",
            component=request.component,
            automatic=True,
            destructive=False,
            requires_human=False,
        )

    @classmethod
    def _fail_closed(
        cls,
        *,
        reason: RecoveryReason,
        fingerprint: str,
        explanation: str,
    ) -> RecoveryReport:
        return RecoveryReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=RecoveryDecision.FAIL_CLOSED,
            reason=reason,
            request_fingerprint=fingerprint,
            action=None,
            fail_closed=True,
            validated=True,
            explanation=explanation,
        )

    @classmethod
    def evaluate(
        cls,
        request: RecoveryRequest,
    ) -> RecoveryReport:
        """Evaluate recovery with strict fail-closed precedence."""

        cls._validate_request(request)

        fingerprint = cls.fingerprint(
            request.to_dict()
        )

        failure = cls._normalize_failure_type(
            request.failure_type
        )

        # ---------------------------------------------------------
        # SECURITY / AUTHORITY PRECEDENCE
        # These conditions ALWAYS override recoverable=True.
        # ---------------------------------------------------------

        if request.destructive:
            return cls._fail_closed(
                reason=RecoveryReason.DESTRUCTIVE_ACTION,
                fingerprint=fingerprint,
                explanation=(
                    "Destructive recovery is never "
                    "automatically authorized."
                ),
            )

        if failure in {
            "architecture",
            "architecture_drift",
        }:
            return cls._fail_closed(
                reason=RecoveryReason.ARCHITECTURE_DRIFT,
                fingerprint=fingerprint,
                explanation=(
                    "Architecture-related failure "
                    "cannot be automatically repaired."
                ),
            )

        if failure in {
            "authority",
            "authority_conflict",
        }:
            return cls._fail_closed(
                reason=RecoveryReason.AUTHORITY_CONFLICT,
                fingerprint=fingerprint,
                explanation=(
                    "Authority conflict requires "
                    "authoritative reconciliation."
                ),
            )

        if failure in {
            "integrity",
            "tamper",
        }:
            return cls._fail_closed(
                reason=RecoveryReason.INTEGRITY_FAILURE,
                fingerprint=fingerprint,
                explanation=(
                    "Integrity failure prevents "
                    "automatic recovery."
                ),
            )

        # UNKNOWN is explicitly fail-closed.
        if failure in {
            "unknown",
            "unknown_failure",
            "unclassified",
            "unclassified_failure",
        }:
            return cls._fail_closed(
                reason=RecoveryReason.UNKNOWN_FAILURE,
                fingerprint=fingerprint,
                explanation=(
                    "Failure cannot be safely classified; "
                    "execution is blocked."
                ),
            )

        # Any failure explicitly classified as unsafe
        # is never allowed to reach generic recovery logic.
        if failure in cls.UNSAFE_FAILURES:
            return cls._fail_closed(
                reason=RecoveryReason.UNKNOWN_FAILURE,
                fingerprint=fingerprint,
                explanation=(
                    "Failure belongs to an unsafe "
                    "recovery classification."
                ),
            )

        # ---------------------------------------------------------
        # SAFE AUTOMATIC RECOVERY
        # ---------------------------------------------------------

        if (
            request.recoverable
            and failure
            in cls.SAFE_AUTOMATIC_FAILURES
        ):
            action = cls._build_action(request)

            return RecoveryReport(
                schema_version=cls.SCHEMA_VERSION,
                authority=cls.AUTHORITY,
                decision=RecoveryDecision.RECOVER,
                reason=RecoveryReason.TRANSIENT_FAILURE,
                request_fingerprint=fingerprint,
                action=action,
                fail_closed=False,
                validated=True,
                explanation=(
                    "Failure is classified as safe "
                    "for automatic recovery."
                ),
            )

        # Explicitly recoverable custom execution failures.
        if request.recoverable:
            action = cls._build_action(request)

            return RecoveryReport(
                schema_version=cls.SCHEMA_VERSION,
                authority=cls.AUTHORITY,
                decision=RecoveryDecision.RECOVER,
                reason=(
                    RecoveryReason
                    .RECOVERABLE_EXECUTION_ERROR
                ),
                request_fingerprint=fingerprint,
                action=action,
                fail_closed=False,
                validated=True,
                explanation=(
                    "Failure is explicitly marked "
                    "recoverable and integrity is verified."
                ),
            )

        # ---------------------------------------------------------
        # DEFAULT = FAIL CLOSED
        # ---------------------------------------------------------

        return cls._fail_closed(
            reason=RecoveryReason.UNKNOWN_FAILURE,
            fingerprint=fingerprint,
            explanation=(
                "Failure is not safely classified; "
                "execution is blocked."
            ),
        )

    @classmethod
    def evaluate_or_raise(
        cls,
        request: RecoveryRequest,
    ) -> RecoveryReport:
        report = cls.evaluate(request)

        if report.decision in {
            RecoveryDecision.BLOCK,
            RecoveryDecision.FAIL_CLOSED,
        }:
            raise RecoveryBlockedError(
                report.explanation
            )

        return report

    @classmethod
    def validate_action(
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

        if not report.validated:
            raise RecoveryValidationError(
                "Recovery report is not validated."
            )

        if report.fail_closed:
            return False

        if (
            report.decision
            != RecoveryDecision.RECOVER
        ):
            return False

        if report.action is None:
            raise RecoveryIntegrityError(
                "Recover decision has no recovery action."
            )

        if report.action.destructive:
            raise RecoveryBlockedError(
                "Destructive recovery action blocked."
            )

        if report.action.requires_human:
            return False

        return True


def evaluate_recovery(
    request: RecoveryRequest,
) -> RecoveryReport:
    return RecoveryGuard.evaluate(request)


def validate_recovery(
    report: RecoveryReport,
) -> bool:
    return RecoveryGuard.validate_action(report)


__all__ = [
    "RecoveryAction",
    "RecoveryAuthorityError",
    "RecoveryBlockedError",
    "RecoveryDecision",
    "RecoveryGuard",
    "RecoveryGuardError",
    "RecoveryIntegrityError",
    "RecoveryReason",
    "RecoveryReport",
    "RecoveryRequest",
    "RecoveryValidationError",
    "evaluate_recovery",
    "validate_recovery",
]