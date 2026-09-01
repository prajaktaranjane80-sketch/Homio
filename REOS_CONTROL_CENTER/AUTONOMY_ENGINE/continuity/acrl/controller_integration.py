"""ACRL T13 — Controller Integration.

Additive bridge between ACRL continuity/safety layers and the
REOS_CONTROL_CENTER authoritative execution state.

Design rules:
    - Existing controller files are not modified.
    - ACRL __init__.py is not modified.
    - T13 does not mutate controller state.
    - T13 does not execute project tasks.
    - T13 does not invent the next task.
    - REOS_CONTROL_CENTER remains execution authority.
    - T13 only reconciles and authorizes continuity state.
    - Any unresolved critical conflict fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class ControllerIntegrationError(RuntimeError):
    """Base T13 integration error."""


class ControllerIntegrationValidationError(
    ControllerIntegrationError
):
    """Invalid controller integration input."""


class ControllerIntegrationAuthorityError(
    ControllerIntegrationError
):
    """Controller authority validation failure."""


class ControllerIntegrationIntegrityError(
    ControllerIntegrationError
):
    """Controller integration integrity failure."""


class ControllerIntegrationConflictError(
    ControllerIntegrationError
):
    """Controller and ACRL state conflict."""


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
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    GATE_CONFLICT = "GATE_CONFLICT"
    SUBTASK_CONFLICT = "SUBTASK_CONFLICT"
    CHECKPOINT_CONFLICT = "CHECKPOINT_CONFLICT"
    INTEGRITY_CONFLICT = "INTEGRITY_CONFLICT"
    ARCHITECTURE_CONFLICT = "ARCHITECTURE_CONFLICT"
    RESUME_NOT_SAFE = "RESUME_NOT_SAFE"
    STATE_AMBIGUOUS = "STATE_AMBIGUOUS"


@dataclass(frozen=True)
class ControllerStateView:
    """Read-only representation of controller authority."""

    current_gate: str
    current_subtask: str | None
    current_task: str
    status: str
    state_hash: str | None
    architecture_locked: bool
    authoritative: bool
    checkpoint_id: str | None = None
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
            "metadata": (
                dict(self.metadata)
                if self.metadata is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class ACRLContinuityView:
    """Read-only representation of ACRL continuity authority."""

    current_gate: str
    current_subtask: str | None
    current_task: str | None
    checkpoint_id: str | None
    architecture_locked: bool
    authority_valid: bool
    integrity_valid: bool
    resume_safe: bool
    fingerprint: str | None = None
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
            "metadata": (
                dict(self.metadata)
                if self.metadata is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class ControllerIntegrationRequest:
    """Immutable T13 integration request."""

    controller: ControllerStateView
    acrl: ACRLContinuityView
    expected_authority: str = "REOS_CONTROL_CENTER"

    def to_dict(self) -> dict[str, Any]:
        return {
            "controller": self.controller.to_dict(),
            "acrl": self.acrl.to_dict(),
            "expected_authority": self.expected_authority,
        }


@dataclass(frozen=True)
class ControllerIntegrationReport:
    """Immutable result of T13 reconciliation."""

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
    """Deterministic ACRL → Controller integration engine."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    SAFE_CONTROLLER_STATUSES = frozenset(
        {
            "CONTROL_CENTER_DRIVEN",
            "READY_FOR_APPROVAL",
            "CURRENT",
        }
    )

    @classmethod
    def canonicalize(
        cls,
        value: Any,
    ) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise ControllerIntegrationValidationError(
                "Integration input cannot be canonicalized."
            ) from exc

    @classmethod
    def fingerprint(
        cls,
        value: Any,
    ) -> str:
        return hashlib.sha256(
            cls.canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _validate_request(
        cls,
        request: ControllerIntegrationRequest,
    ) -> None:
        if not isinstance(
            request,
            ControllerIntegrationRequest,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid controller integration request."
            )

        if not isinstance(
            request.controller,
            ControllerStateView,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid controller state."
            )

        if not isinstance(
            request.acrl,
            ACRLContinuityView,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid ACRL continuity state."
            )

        if (
            request.expected_authority
            != cls.AUTHORITY
        ):
            raise ControllerIntegrationAuthorityError(
                "Unexpected controller authority."
            )

        if not request.controller.authoritative:
            raise ControllerIntegrationAuthorityError(
                "Controller state is not authoritative."
            )

        if not request.acrl.authority_valid:
            raise ControllerIntegrationAuthorityError(
                "ACRL authority validation failed."
            )

    @classmethod
    def _report(
        cls,
        *,
        request: ControllerIntegrationRequest,
        fingerprint: str,
        decision: IntegrationDecision,
        reason: IntegrationReason,
        fail_closed: bool,
        resume_authorized: bool,
        execution_authorized: bool,
        explanation: str,
    ) -> ControllerIntegrationReport:
        return ControllerIntegrationReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=decision,
            reason=reason,
            request_fingerprint=fingerprint,
            validated=True,
            fail_closed=fail_closed,
            controller_gate=(
                request.controller.current_gate
            ),
            acrl_gate=request.acrl.current_gate,
            controller_subtask=(
                request.controller.current_subtask
            ),
            acrl_subtask=request.acrl.current_subtask,
            resume_authorized=resume_authorized,
            execution_authorized=execution_authorized,
            explanation=explanation,
        )

    @classmethod
    def integrate(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIntegrationReport:
        """Reconcile ACRL continuity with controller authority."""

        cls._validate_request(request)

        fingerprint = cls.fingerprint(
            request.to_dict()
        )

        controller = request.controller
        acrl = request.acrl

        # ---------------------------------------------------------
        # CONTROLLER AVAILABILITY
        # ---------------------------------------------------------

        if not controller.current_gate.strip():
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .CONTROLLER_UNAVAILABLE
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller gate is unavailable."
                ),
            )

        if not controller.current_task.strip():
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .CONTROLLER_STATE_INVALID
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller current task is unavailable."
                ),
            )

        # ---------------------------------------------------------
        # ARCHITECTURE CONSISTENCY
        # ---------------------------------------------------------

        if (
            controller.architecture_locked
            != acrl.architecture_locked
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .ARCHITECTURE_CONFLICT
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller and ACRL architecture "
                    "lock state conflict."
                ),
            )

        if not controller.architecture_locked:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=(
                    IntegrationReason
                    .ARCHITECTURE_CONFLICT
                ),
                fail_closed=False,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Architecture lock is not established."
                ),
            )

        # ---------------------------------------------------------
        # GATE AUTHORITY
        # ---------------------------------------------------------

        if (
            controller.current_gate
            != acrl.current_gate
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .GATE_CONFLICT
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller and ACRL disagree "
                    "on the authoritative gate."
                ),
            )

        # ---------------------------------------------------------
        # SUBTASK AUTHORITY
        # ---------------------------------------------------------

        if (
            controller.current_subtask
            != acrl.current_subtask
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .SUBTASK_CONFLICT
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller and ACRL disagree "
                    "on the current authoritative subtask."
                ),
            )

        # ---------------------------------------------------------
        # CHECKPOINT CONTINUITY
        # ---------------------------------------------------------

        if (
            controller.checkpoint_id
            != acrl.checkpoint_id
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=(
                    IntegrationReason
                    .CHECKPOINT_CONFLICT
                ),
                fail_closed=False,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Checkpoint continuity cannot be established."
                ),
            )

        # ---------------------------------------------------------
        # STATE INTEGRITY
        # ---------------------------------------------------------

        if not acrl.integrity_valid:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.FAIL_CLOSED,
                reason=(
                    IntegrationReason
                    .INTEGRITY_CONFLICT
                ),
                fail_closed=True,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "ACRL integrity validation failed."
                ),
            )

        # ---------------------------------------------------------
        # RESUME SAFETY
        # ---------------------------------------------------------

        if not acrl.resume_safe:
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=(
                    IntegrationReason
                    .RESUME_NOT_SAFE
                ),
                fail_closed=False,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "T12 did not authorize safe resume."
                ),
            )

        # ---------------------------------------------------------
        # CONTROLLER STATUS
        # ---------------------------------------------------------

        if (
            controller.status
            not in cls.SAFE_CONTROLLER_STATUSES
        ):
            return cls._report(
                request=request,
                fingerprint=fingerprint,
                decision=IntegrationDecision.BLOCKED,
                reason=(
                    IntegrationReason
                    .CONTROLLER_STATE_INVALID
                ),
                fail_closed=False,
                resume_authorized=False,
                execution_authorized=False,
                explanation=(
                    "Controller status does not permit "
                    "autonomous continuity."
                ),
            )

        # ---------------------------------------------------------
        # SUCCESS
        # ---------------------------------------------------------

        return cls._report(
            request=request,
            fingerprint=fingerprint,
            decision=IntegrationDecision.INTEGRATED,
            reason=IntegrationReason.VALID,
            fail_closed=False,
            resume_authorized=True,
            execution_authorized=False,
            explanation=(
                "ACRL continuity is reconciled with the "
                "authoritative REOS_CONTROL_CENTER state. "
                "Resume is authorized; task execution remains "
                "under Controller authority."
            ),
        )

    @classmethod
    def integrate_or_raise(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIntegrationReport:
        report = cls.integrate(request)

        if report.decision != IntegrationDecision.INTEGRATED:
            raise ControllerIntegrationConflictError(
                report.explanation
            )

        return report

    @classmethod
    def can_resume(
        cls,
        report: ControllerIntegrationReport,
    ) -> bool:
        if not isinstance(
            report,
            ControllerIntegrationReport,
        ):
            raise ControllerIntegrationValidationError(
                "Invalid integration report."
            )

        return (
            report.validated
            and report.decision
            == IntegrationDecision.INTEGRATED
            and report.resume_authorized
            and not report.fail_closed
        )


def integrate_controller(
    request: ControllerIntegrationRequest,
) -> ControllerIntegrationReport:
    """Convenience T13 API."""

    return ControllerIntegrationEngine.integrate(
        request
    )


def controller_resume_authorized(
    report: ControllerIntegrationReport,
) -> bool:
    """Return True only when T13 authorizes safe continuity."""

    return ControllerIntegrationEngine.can_resume(
        report
    )


__all__ = [
    "ACRLContinuityView",
    "ControllerIntegrationAuthorityError",
    "ControllerIntegrationConflictError",
    "ControllerIntegrationEngine",
    "ControllerIntegrationError",
    "ControllerIntegrationIntegrityError",
    "ControllerIntegrationRequest",
    "ControllerIntegrationValidationError",
    "ControllerStateView",
    "IntegrationDecision",
    "IntegrationReason",
    "ControllerIntegrationReport",
    "controller_resume_authorized",
    "integrate_controller",
]