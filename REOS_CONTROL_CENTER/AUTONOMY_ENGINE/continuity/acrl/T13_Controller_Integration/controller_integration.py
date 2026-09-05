"""ACRL T13 — Controller Integration.

Read-only integration boundary between the REOS Control Center and ACRL.

T13 may:

    - inspect controller and ACRL continuity evidence
    - validate integration inputs
    - reconcile controller/ACRL continuity
    - detect conflicts
    - authorize safe continuity/resume
    - produce deterministic integration evidence

T13 MUST NOT:

    - mutate state.json
    - mutate the controller
    - mutate checkpoints
    - mutate architecture
    - execute tasks
    - approve business execution
    - perform recovery
    - replace the controller
    - promote authority
    - invent the next task
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
AUTHORITY = "REOS_CONTROL_CENTER"
HASH_ALGORITHM = "sha256"


class ControllerIntegrationError(ValueError):
    """Base exception for T13 controller integration."""


class ControllerIntegrationValidationError(
    ControllerIntegrationError
):
    """Raised when integration data is structurally invalid."""


class ControllerIntegrationAuthorityError(
    ControllerIntegrationValidationError
):
    """Raised when integration authority is invalid."""


class ControllerIntegrationConflictError(
    ControllerIntegrationError
):
    """Raised when integration detects an unsafe conflict."""


class IntegrationDecision(str, Enum):
    """Canonical T13 integration decisions."""

    INTEGRATED = "INTEGRATED"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class IntegrationReason(str, Enum):
    """Canonical T13 integration reasons."""

    VALID = "VALID"

    CONTROLLER_UNAVAILABLE = "CONTROLLER_UNAVAILABLE"
    CONTROLLER_STATE_INVALID = "CONTROLLER_STATE_INVALID"

    ARCHITECTURE_CONFLICT = "ARCHITECTURE_CONFLICT"
    GATE_CONFLICT = "GATE_CONFLICT"
    SUBTASK_CONFLICT = "SUBTASK_CONFLICT"
    CHECKPOINT_CONFLICT = "CHECKPOINT_CONFLICT"
    INTEGRITY_CONFLICT = "INTEGRITY_CONFLICT"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    RESUME_NOT_SAFE = "RESUME_NOT_SAFE"


@dataclass(frozen=True)
class ControllerStateView:
    """Immutable read-only controller evidence."""

    current_gate: str
    current_subtask: str | None
    current_task: str
    status: str
    state_hash: str | None
    architecture_locked: bool
    authoritative: bool
    checkpoint_id: str | None
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable controller evidence view."""

        return {
            "current_gate": self.current_gate,
            "current_subtask": self.current_subtask,
            "current_task": self.current_task,
            "status": self.status,
            "state_hash": self.state_hash,
            "architecture_locked": self.architecture_locked,
            "authoritative": self.authoritative,
            "checkpoint_id": self.checkpoint_id,
            "metadata": _canonicalize(self.metadata),
        }


@dataclass(frozen=True)
class ACRLContinuityView:
    """Immutable read-only ACRL continuity evidence."""

    current_gate: str
    current_subtask: str | None
    current_task: str | None
    checkpoint_id: str | None
    architecture_locked: bool
    authority_valid: bool
    integrity_valid: bool
    resume_safe: bool
    fingerprint: str | None
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable ACRL continuity view."""

        return {
            "current_gate": self.current_gate,
            "current_subtask": self.current_subtask,
            "current_task": self.current_task,
            "checkpoint_id": self.checkpoint_id,
            "architecture_locked": self.architecture_locked,
            "authority_valid": self.authority_valid,
            "integrity_valid": self.integrity_valid,
            "resume_safe": self.resume_safe,
            "fingerprint": self.fingerprint,
            "metadata": _canonicalize(self.metadata),
        }


@dataclass(frozen=True)
class ControllerIntegrationRequest:
    """Immutable T13 integration request."""

    controller: ControllerStateView
    acrl: ACRLContinuityView
    expected_authority: str = AUTHORITY

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable integration request."""

        return {
            "controller": self.controller.to_dict(),
            "acrl": self.acrl.to_dict(),
            "expected_authority": self.expected_authority,
        }


@dataclass(frozen=True)
class ControllerIntegrationReport:
    """Immutable deterministic T13 integration result."""

    schema_version: str
    authority: str
    decision: IntegrationDecision
    reason: IntegrationReason
    request_fingerprint: str
    validated: bool
    fail_closed: bool
    controller_gate: str
    acrl_gate: str
    controller_subtask: str | None
    acrl_subtask: str | None
    resume_authorized: bool
    execution_authorized: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic serializable representation."""

        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "request_fingerprint": self.request_fingerprint,
            "validated": self.validated,
            "fail_closed": self.fail_closed,
            "controller_gate": self.controller_gate,
            "acrl_gate": self.acrl_gate,
            "controller_subtask": self.controller_subtask,
            "acrl_subtask": self.acrl_subtask,
            "resume_authorized": self.resume_authorized,
            "execution_authorized": self.execution_authorized,
            "explanation": self.explanation,
        }


def _canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON data."""

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise TypeError(
        f"Unsupported value for canonicalization: "
        f"{type(value).__name__}"
    )


class ControllerIntegrationEngine:
    """Deterministic, read-only T13 integration engine."""

    SCHEMA_VERSION = SCHEMA_VERSION
    AUTHORITY = AUTHORITY
    HASH_ALGORITHM = HASH_ALGORITHM

    SAFE_CONTROLLER_STATUSES = frozenset(
        {
            "CONTROL_CENTER_DRIVEN",
            "READY_FOR_APPROVAL",
            "CURRENT",
        }
    )

    @classmethod
    def fingerprint(cls, value: Any) -> str:
        """Create deterministic SHA-256 fingerprint."""

        canonical = _canonicalize(value)

        payload = json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _validate_request(
        cls,
        request: ControllerIntegrationRequest,
    ) -> None:
        """Validate request structure and authority."""

        if not isinstance(
            request,
            ControllerIntegrationRequest,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid ControllerIntegrationRequest."
            )

        if request.expected_authority != cls.AUTHORITY:
            raise ControllerIntegrationAuthorityError(
                "Invalid expected authority."
            )

        if not isinstance(
            request.controller,
            ControllerStateView,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid ControllerStateView."
            )

        if not isinstance(
            request.acrl,
            ACRLContinuityView,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid ACRLContinuityView."
            )

        if not isinstance(
            request.controller.authoritative,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "Controller authoritative flag is invalid."
            )

        if not isinstance(
            request.acrl.authority_valid,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "ACRL authority flag is invalid."
            )

        if not isinstance(
            request.controller.architecture_locked,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "Controller architecture lock flag is invalid."
            )

        if not isinstance(
            request.acrl.architecture_locked,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "ACRL architecture lock flag is invalid."
            )

        if not isinstance(
            request.acrl.integrity_valid,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "ACRL integrity flag is invalid."
            )

        if not isinstance(
            request.acrl.resume_safe,
            bool,
        ):
            raise ControllerIntegrationValidationError(
                "ACRL resume-safety flag is invalid."
            )

        if not request.controller.authoritative:
            raise ControllerIntegrationAuthorityError(
                "Controller authority is invalid."
            )

        if not request.acrl.authority_valid:
            raise ControllerIntegrationAuthorityError(
                "ACRL authority is invalid."
            )

    @classmethod
    def _validate_with_t13_validator(
        cls,
        request: ControllerIntegrationRequest,
    ) -> None:
        """Run T13 structural validation without creating a cycle."""

        from .controller_validation import (
            ControllerValidationEngine,
        )

        ControllerValidationEngine.validate_request(request)

    @classmethod
    def _report(
        cls,
        *,
        request: ControllerIntegrationRequest,
        fingerprint: str,
        decision: IntegrationDecision,
        reason: IntegrationReason,
        validated: bool,
        fail_closed: bool,
        resume_authorized: bool,
        explanation: str,
    ) -> ControllerIntegrationReport:
        """Build immutable integration evidence."""

        return ControllerIntegrationReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=decision,
            reason=reason,
            request_fingerprint=fingerprint,
            validated=validated,
            fail_closed=fail_closed,
            controller_gate=request.controller.current_gate,
            acrl_gate=request.acrl.current_gate,
            controller_subtask=request.controller.current_subtask,
            acrl_subtask=request.acrl.current_subtask,
            resume_authorized=resume_authorized,
            execution_authorized=False,
            explanation=explanation,
        )

    @classmethod
    def integrate(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIntegrationReport:
        """Integrate controller and ACRL continuity evidence."""

        cls._validate_request(request)

        cls._validate_with_t13_validator(request)

        fingerprint = cls.fingerprint(
            request.to_dict()
        )

        controller = request.controller
        acrl = request.acrl

        # ---------------------------------------------------------------
        # Controller availability
        # ---------------------------------------------------------------

        if not controller.current_gate:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.CONTROLLER_UNAVAILABLE,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller current gate is unavailable."
                ),
            )

        # ---------------------------------------------------------------
        # Controller state
        # ---------------------------------------------------------------

        if not controller.current_task:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.CONTROLLER_STATE_INVALID,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller current task is unavailable."
                ),
            )

        # ---------------------------------------------------------------
        # Architecture
        # ---------------------------------------------------------------

        if (
            controller.architecture_locked
            != acrl.architecture_locked
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.ARCHITECTURE_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL architecture lock states "
                    "conflict."
                ),
            )

        if not controller.architecture_locked:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=IntegrationReason.ARCHITECTURE_CONFLICT,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Architecture is not locked."
                ),
            )

        # ---------------------------------------------------------------
        # Gate
        # ---------------------------------------------------------------

        if controller.current_gate != acrl.current_gate:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.GATE_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL current gates conflict."
                ),
            )

        # ---------------------------------------------------------------
        # Subtask
        # ---------------------------------------------------------------

        if (
            controller.current_subtask
            != acrl.current_subtask
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.SUBTASK_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL current subtasks conflict."
                ),
            )

        # ---------------------------------------------------------------
        # Checkpoint
        # ---------------------------------------------------------------

        if (
            controller.checkpoint_id
            != acrl.checkpoint_id
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=IntegrationReason.CHECKPOINT_CONFLICT,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL checkpoint identities "
                    "conflict."
                ),
            )

        # ---------------------------------------------------------------
        # Integrity
        # ---------------------------------------------------------------

        if not acrl.integrity_valid:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=IntegrationReason.INTEGRITY_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "ACRL integrity evidence is invalid."
                ),
            )

        # ---------------------------------------------------------------
        # Resume safety
        # ---------------------------------------------------------------

        if not acrl.resume_safe:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=IntegrationReason.RESUME_NOT_SAFE,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "ACRL resume-safety validation did not "
                    "authorize resume."
                ),
            )

        # ---------------------------------------------------------------
        # Controller operating status
        # ---------------------------------------------------------------

        if controller.status not in cls.SAFE_CONTROLLER_STATUSES:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=IntegrationReason.CONTROLLER_STATE_INVALID,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Controller status is not an accepted safe "
                    "integration state."
                ),
            )

        # ---------------------------------------------------------------
        # Successful integration
        # ---------------------------------------------------------------

        return cls._report(
            request=request,
            fingerprint=fingerprint,
            decision=IntegrationDecision.INTEGRATED,
            reason=IntegrationReason.VALID,
            validated=True,
            fail_closed=False,
            resume_authorized=True,
            explanation=(
                "Controller and ACRL continuity evidence are "
                "integrated and consistent. Resume is authorized; "
                "execution remains forbidden."
            ),
        )

    @classmethod
    def integrate_or_raise(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIntegrationReport:
        """Integrate and raise on non-integrated decisions."""

        report = cls.integrate(request)

        if report.decision != IntegrationDecision.INTEGRATED:
            raise ControllerIntegrationConflictError(
                f"T13 integration blocked: "
                f"{report.reason.value}"
            )

        return report

    @classmethod
    def can_resume(
        cls,
        report: ControllerIntegrationReport,
    ) -> bool:
        """Return whether T13 authorizes continuity resume."""

        if not isinstance(
            report,
            ControllerIntegrationReport,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid integration report."
            )

        if report.execution_authorized:
            return False

        if report.fail_closed:
            return False

        if report.decision != IntegrationDecision.INTEGRATED:
            return False

        if report.reason != IntegrationReason.VALID:
            return False

        if not report.validated:
            return False

        return report.resume_authorized

    @classmethod
    def is_safe(
        cls,
        report: ControllerIntegrationReport,
    ) -> bool:
        """Return whether the integration is safe for resume."""

        return cls.can_resume(report)


def integrate_controller(
    request: ControllerIntegrationRequest,
) -> ControllerIntegrationReport:
    """Public T13 controller integration entry point."""

    return ControllerIntegrationEngine.integrate(request)


def controller_resume_authorized(
    report: ControllerIntegrationReport,
) -> bool:
    """Public T13 resume authorization helper."""

    return ControllerIntegrationEngine.can_resume(report)


__all__ = [
    "ACRLContinuityView",
    "AUTHORITY",
    "ControllerIntegrationAuthorityError",
    "ControllerIntegrationConflictError",
    "ControllerIntegrationEngine",
    "ControllerIntegrationError",
    "ControllerIntegrationReport",
    "ControllerIntegrationRequest",
    "ControllerIntegrationValidationError",
    "ControllerStateView",
    "HASH_ALGORITHM",
    "IntegrationDecision",
    "IntegrationReason",
    "SCHEMA_VERSION",
    "controller_resume_authorized",
    "integrate_controller",
]