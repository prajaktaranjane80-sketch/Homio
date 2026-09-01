"""ACRL T12 — Resume-Safety Validation.

Additive-only safety validation layer.

T12 determines whether an autonomous execution sequence may
safely resume from reconstructed state.

Architecture rules:
    - T01-T11 are not modified.
    - __init__.py is not modified.
    - T12 does not mutate authoritative state.
    - T12 does not perform recovery itself.
    - T12 only validates whether resume is safe.
    - Any unresolved authority/integrity/drift ambiguity
      fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class ResumeSafetyError(RuntimeError):
    """Base T12 error."""


class ResumeSafetyValidationError(
    ResumeSafetyError
):
    """Invalid resume-safety input."""


class ResumeSafetyAuthorityError(
    ResumeSafetyError
):
    """Resume authority is invalid."""


class ResumeSafetyIntegrityError(
    ResumeSafetyError
):
    """Resume integrity is invalid."""


class ResumeSafetyBlockedError(
    ResumeSafetyError
):
    """Resume operation is blocked."""


class ResumeDecision(str, Enum):
    """Canonical resume decisions."""

    SAFE_TO_RESUME = "SAFE_TO_RESUME"
    BLOCK_RESUME = "BLOCK_RESUME"
    FAIL_CLOSED = "FAIL_CLOSED"


class ResumeSafetyReason(str, Enum):
    """Canonical resume-safety reasons."""

    VALID = "VALID"
    MISSING_CHECKPOINT = "MISSING_CHECKPOINT"
    CHECKPOINT_INVALID = "CHECKPOINT_INVALID"
    STATE_INVALID = "STATE_INVALID"
    GATE_INVALID = "GATE_INVALID"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    ARCHITECTURE_DRIFT = "ARCHITECTURE_DRIFT"
    RECOVERY_UNSAFE = "RECOVERY_UNSAFE"
    AMBIGUOUS_STATE = "AMBIGUOUS_STATE"
    STALE_STATE = "STALE_STATE"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True)
class ResumeSafetyRequest:
    """Immutable resume-safety validation request."""

    checkpoint_available: bool
    checkpoint_valid: bool
    state_available: bool
    state_valid: bool
    gate_available: bool
    gate_valid: bool
    authority_valid: bool
    integrity_valid: bool
    architecture_stable: bool
    recovery_safe: bool
    state_ambiguous: bool = False
    state_stale: bool = False
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_available": (
                self.checkpoint_available
            ),
            "checkpoint_valid": self.checkpoint_valid,
            "state_available": self.state_available,
            "state_valid": self.state_valid,
            "gate_available": self.gate_available,
            "gate_valid": self.gate_valid,
            "authority_valid": self.authority_valid,
            "integrity_valid": self.integrity_valid,
            "architecture_stable": (
                self.architecture_stable
            ),
            "recovery_safe": self.recovery_safe,
            "state_ambiguous": self.state_ambiguous,
            "state_stale": self.state_stale,
            "metadata": (
                dict(self.metadata)
                if self.metadata is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class ResumeSafetyReport:
    """Immutable T12 validation result."""

    schema_version: str
    authority: str
    decision: ResumeDecision
    reason: ResumeSafetyReason
    request_fingerprint: str
    validated: bool
    fail_closed: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "request_fingerprint": (
                self.request_fingerprint
            ),
            "validated": self.validated,
            "fail_closed": self.fail_closed,
            "explanation": self.explanation,
        }


class ResumeSafetyValidator:
    """Deterministic resume-safety validation engine."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @classmethod
    def canonicalize(
        cls,
        value: Any,
    ) -> str:
        """Return deterministic JSON representation."""

        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise ResumeSafetyValidationError(
                "Resume-safety input cannot be canonicalized."
            ) from exc

    @classmethod
    def fingerprint(
        cls,
        value: Any,
    ) -> str:
        """Create deterministic SHA-256 fingerprint."""

        return hashlib.sha256(
            cls.canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _validate_request(
        cls,
        request: ResumeSafetyRequest,
    ) -> None:
        if not isinstance(
            request,
            ResumeSafetyRequest,
        ):
            raise ResumeSafetyValidationError(
                "Invalid resume-safety request."
            )

        if not request.authority_valid:
            raise ResumeSafetyAuthorityError(
                "Resume authority is invalid."
            )

        if not request.integrity_valid:
            raise ResumeSafetyIntegrityError(
                "Resume integrity is invalid."
            )

    @classmethod
    def _fail_closed(
        cls,
        *,
        reason: ResumeSafetyReason,
        fingerprint: str,
        explanation: str,
    ) -> ResumeSafetyReport:
        return ResumeSafetyReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=ResumeDecision.FAIL_CLOSED,
            reason=reason,
            request_fingerprint=fingerprint,
            validated=True,
            fail_closed=True,
            explanation=explanation,
        )

    @classmethod
    def _block_resume(
        cls,
        *,
        reason: ResumeSafetyReason,
        fingerprint: str,
        explanation: str,
    ) -> ResumeSafetyReport:
        return ResumeSafetyReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=ResumeDecision.BLOCK_RESUME,
            reason=reason,
            request_fingerprint=fingerprint,
            validated=True,
            fail_closed=False,
            explanation=explanation,
        )

    @classmethod
    def validate(
        cls,
        request: ResumeSafetyRequest,
    ) -> ResumeSafetyReport:
        """Validate whether execution may safely resume."""

        cls._validate_request(request)

        fingerprint = cls.fingerprint(
            request.to_dict()
        )

        # ---------------------------------------------------------
        # FAIL-CLOSED SECURITY PRECEDENCE
        # ---------------------------------------------------------

        if not request.integrity_valid:
            return cls._fail_closed(
                reason=ResumeSafetyReason.INTEGRITY_FAILURE,
                fingerprint=fingerprint,
                explanation=(
                    "Integrity cannot be established; "
                    "resume is fail-closed."
                ),
            )

        if not request.authority_valid:
            return cls._fail_closed(
                reason=ResumeSafetyReason.AUTHORITY_CONFLICT,
                fingerprint=fingerprint,
                explanation=(
                    "Authoritative resume context is invalid."
                ),
            )

        if not request.architecture_stable:
            return cls._fail_closed(
                reason=ResumeSafetyReason.ARCHITECTURE_DRIFT,
                fingerprint=fingerprint,
                explanation=(
                    "Architecture stability cannot be "
                    "established; resume is blocked."
                ),
            )

        if request.state_ambiguous:
            return cls._fail_closed(
                reason=ResumeSafetyReason.AMBIGUOUS_STATE,
                fingerprint=fingerprint,
                explanation=(
                    "Execution state is ambiguous; "
                    "automatic resume is unsafe."
                ),
            )

        # ---------------------------------------------------------
        # CHECKPOINT VALIDATION
        # ---------------------------------------------------------

        if not request.checkpoint_available:
            return cls._block_resume(
                reason=ResumeSafetyReason.MISSING_CHECKPOINT,
                fingerprint=fingerprint,
                explanation=(
                    "No authoritative checkpoint is "
                    "available for safe resume."
                ),
            )

        if not request.checkpoint_valid:
            return cls._fail_closed(
                reason=ResumeSafetyReason.CHECKPOINT_INVALID,
                fingerprint=fingerprint,
                explanation=(
                    "Checkpoint validation failed; "
                    "resume is fail-closed."
                ),
            )

        # ---------------------------------------------------------
        # STATE VALIDATION
        # ---------------------------------------------------------

        if not request.state_available:
            return cls._block_resume(
                reason=ResumeSafetyReason.STATE_INVALID,
                fingerprint=fingerprint,
                explanation=(
                    "Execution state is unavailable."
                ),
            )

        if not request.state_valid:
            return cls._fail_closed(
                reason=ResumeSafetyReason.STATE_INVALID,
                fingerprint=fingerprint,
                explanation=(
                    "Execution state is invalid; "
                    "resume is fail-closed."
                ),
            )

        # ---------------------------------------------------------
        # GATE / SUBTASK VALIDATION
        # ---------------------------------------------------------

        if not request.gate_available:
            return cls._block_resume(
                reason=ResumeSafetyReason.GATE_INVALID,
                fingerprint=fingerprint,
                explanation=(
                    "Gate continuity is unavailable."
                ),
            )

        if not request.gate_valid:
            return cls._fail_closed(
                reason=ResumeSafetyReason.GATE_INVALID,
                fingerprint=fingerprint,
                explanation=(
                    "Gate continuity validation failed."
                ),
            )

        # ---------------------------------------------------------
        # RECOVERY VALIDATION
        # ---------------------------------------------------------

        if not request.recovery_safe:
            return cls._block_resume(
                reason=ResumeSafetyReason.RECOVERY_UNSAFE,
                fingerprint=fingerprint,
                explanation=(
                    "Previous recovery status is not "
                    "safe for autonomous resume."
                ),
            )

        # ---------------------------------------------------------
        # STALE STATE
        # ---------------------------------------------------------

        if request.state_stale:
            return cls._block_resume(
                reason=ResumeSafetyReason.STALE_STATE,
                fingerprint=fingerprint,
                explanation=(
                    "Execution state is stale and must "
                    "be reconciled before resume."
                ),
            )

        # ---------------------------------------------------------
        # ALL SAFETY CONDITIONS SATISFIED
        # ---------------------------------------------------------

        return ResumeSafetyReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=ResumeDecision.SAFE_TO_RESUME,
            reason=ResumeSafetyReason.VALID,
            request_fingerprint=fingerprint,
            validated=True,
            fail_closed=False,
            explanation=(
                "Checkpoint, state, gate, authority, "
                "integrity, architecture, and recovery "
                "conditions are valid for safe resume."
            ),
        )

    @classmethod
    def validate_or_raise(
        cls,
        request: ResumeSafetyRequest,
    ) -> ResumeSafetyReport:
        """Validate and raise if resume is unsafe."""

        report = cls.validate(request)

        if report.decision != ResumeDecision.SAFE_TO_RESUME:
            raise ResumeSafetyBlockedError(
                report.explanation
            )

        return report

    @classmethod
    def is_safe(
        cls,
        report: ResumeSafetyReport,
    ) -> bool:
        """Return True only for a validated safe resume."""

        if not isinstance(
            report,
            ResumeSafetyReport,
        ):
            raise ResumeSafetyValidationError(
                "Invalid resume-safety report."
            )

        if not report.validated:
            raise ResumeSafetyValidationError(
                "Resume-safety report is not validated."
            )

        return (
            report.decision
            == ResumeDecision.SAFE_TO_RESUME
            and not report.fail_closed
        )


def validate_resume_safety(
    request: ResumeSafetyRequest,
) -> ResumeSafetyReport:
    """Convenience API for T12 validation."""

    return ResumeSafetyValidator.validate(
        request
    )


def is_safe_to_resume(
    report: ResumeSafetyReport,
) -> bool:
    """Convenience API for safe-resume verification."""

    return ResumeSafetyValidator.is_safe(
        report
    )


__all__ = [
    "ResumeDecision",
    "ResumeSafetyAuthorityError",
    "ResumeSafetyBlockedError",
    "ResumeSafetyError",
    "ResumeSafetyIntegrityError",
    "ResumeSafetyReason",
    "ResumeSafetyReport",
    "ResumeSafetyRequest",
    "ResumeSafetyValidationError",
    "ResumeSafetyValidator",
    "is_safe_to_resume",
    "validate_resume_safety",
]