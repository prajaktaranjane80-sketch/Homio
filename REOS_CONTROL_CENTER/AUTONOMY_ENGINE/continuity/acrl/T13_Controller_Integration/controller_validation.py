"""ACRL T13 — Controller Integration.

Read-only integration boundary between the REOS Control Center
and ACRL continuity.

T13 may:

- inspect controller and ACRL continuity evidence
- validate integration inputs
- reconcile continuity
- detect conflicts
- authorize safe continuity/resume
- produce deterministic evidence

T13 must never:

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
    """Base T13 exception."""


class ControllerIntegrationValidationError(
    ControllerIntegrationError
):
    """Raised for structurally invalid integration input."""


class ControllerIntegrationAuthorityError(
    ControllerIntegrationValidationError
):
    """Raised for invalid authority."""


class ControllerIntegrationConflictError(
    ControllerIntegrationError
):
    """Raised by integrate_or_raise for unsafe integration."""


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

    if isinstance(
        value,
        (str, int, float, bool),
    ) or value is None:
        return value

    raise TypeError(
        "Unsupported value for canonicalization: "
        f"{type(value).__name__}"
    )


@dataclass(frozen=True)
class ControllerStateView:
    """Immutable controller evidence."""

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
    """Immutable ACRL continuity evidence."""

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
        """Validate basic request structure and authority."""

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

    @classmethod
    def _validate_with_t13_validator(
        cls,
        request: ControllerIntegrationRequest,
    ) -> None:
        """Execute structural T13 validation."""

        from .controller_validation import (
            ControllerValidationEngine,
        )

        try:
            ControllerValidationEngine.validate_request(
                request
            )
        except ValueError as exc:
            message = str(exc).lower()

            if "authority" in message:
                raise ControllerIntegrationAuthorityError(
                    str(exc)
                ) from exc

            raise ControllerIntegrationValidationError(
                str(exc)
            ) from exc

    @classmethod
    def _build_report(
        cls,
        request: ControllerIntegrationRequest,
        fingerprint: str,
        decision: IntegrationDecision,
        reason: IntegrationReason,
        *,
        validated: bool,
        fail_closed: bool,
        resume_authorized: bool,
        explanation: str,
    ) -> ControllerIntegrationReport:
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
        """Perform read-only T13 controller/ACRL integration."""

        cls._validate_request(request)

        cls._validate_with_t13_validator(request)

        controller = request.controller
        acrl = request.acrl

        fingerprint = cls.fingerprint(
            request.to_dict()
        )

        if not controller.authoritative:
            raise ControllerIntegrationAuthorityError(
                "Controller authority is invalid."
            )

        if not acrl.authority_valid:
            raise ControllerIntegrationAuthorityError(
                "ACRL authority is invalid."
            )

        if not controller.current_gate:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.CONTROLLER_UNAVAILABLE,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller current gate is unavailable."
                ),
            )

        if not controller.current_task:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.CONTROLLER_STATE_INVALID,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller current task is unavailable."
                ),
            )

        if (
            controller.architecture_locked
            != acrl.architecture_locked
        ):
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.ARCHITECTURE_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL architecture lock "
                    "states conflict."
                ),
            )

        if not controller.architecture_locked:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.BLOCKED,
                IntegrationReason.ARCHITECTURE_CONFLICT,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Architecture is not locked."
                ),
            )

        if controller.current_gate != acrl.current_gate:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.GATE_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL current gates conflict."
                ),
            )

        if (
            controller.current_subtask
            != acrl.current_subtask
        ):
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.SUBTASK_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL current subtasks "
                    "conflict."
                ),
            )

        if (
            controller.checkpoint_id
            != acrl.checkpoint_id
        ):
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.BLOCKED,
                IntegrationReason.CHECKPOINT_CONFLICT,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Controller and ACRL checkpoint identities "
                    "conflict."
                ),
            )

        if not acrl.integrity_valid:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.FAIL_CLOSED,
                IntegrationReason.INTEGRITY_CONFLICT,
                validated=True,
                fail_closed=True,
                resume_authorized=False,
                explanation=(
                    "ACRL integrity evidence is invalid."
                ),
            )

        if not acrl.resume_safe:
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.BLOCKED,
                IntegrationReason.RESUME_NOT_SAFE,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "ACRL resume safety did not authorize "
                    "resume."
                ),
            )

        if (
            controller.status
            not in cls.SAFE_CONTROLLER_STATUSES
        ):
            return cls._build_report(
                request,
                fingerprint,
                IntegrationDecision.BLOCKED,
                IntegrationReason.CONTROLLER_STATE_INVALID,
                validated=True,
                fail_closed=False,
                resume_authorized=False,
                explanation=(
                    "Controller status is not an accepted "
                    "safe integration state."
                ),
            )

        return cls._build_report(
            request,
            fingerprint,
            IntegrationDecision.INTEGRATED,
            IntegrationReason.VALID,
            validated=True,
            fail_closed=False,
            resume_authorized=True,
            explanation=(
                "Controller and ACRL continuity are "
                "consistent and safe to resume."
            ),
        )

    @classmethod
    def integrate_or_raise(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIntegrationReport:
        """Integrate and raise for BLOCKED/FAIL_CLOSED results."""

        report = cls.integrate(request)

        if report.decision != IntegrationDecision.INTEGRATED:
            raise ControllerIntegrationConflictError(
                f"T13 integration blocked: "
                f"{report.reason.value}"
            )

        return report


def integrate_controller(
    request: ControllerIntegrationRequest,
) -> ControllerIntegrationReport:
    """Public T13 integration helper."""

    return ControllerIntegrationEngine.integrate(
        request
    )


def controller_resume_authorized(
    report: ControllerIntegrationReport,
) -> bool:
    """Return whether T13 authorized safe continuity resume."""

    if not isinstance(
        report,
        ControllerIntegrationReport,
    ):
        return False

    return (
        report.decision
        is IntegrationDecision.INTEGRATED
        and report.resume_authorized is True
        and report.execution_authorized is False
        and report.fail_closed is False
    )


__all__ = [
    "SCHEMA_VERSION",
    "AUTHORITY",
    "HASH_ALGORITHM",
    "ControllerIntegrationError",
    "ControllerIntegrationValidationError",
    "ControllerIntegrationAuthorityError",
    "ControllerIntegrationConflictError",
    "IntegrationDecision",
    "IntegrationReason",
    "ControllerStateView",
    "ACRLContinuityView",
    "ControllerIntegrationRequest",
    "ControllerIntegrationReport",
    "ControllerIntegrationEngine",
    "integrate_controller",
    "controller_resume_authorized",
]
