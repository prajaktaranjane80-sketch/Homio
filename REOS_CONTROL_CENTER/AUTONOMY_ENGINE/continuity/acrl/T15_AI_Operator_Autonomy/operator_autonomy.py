"""
ACRL T15 — AI Operator Autonomy.

First bounded implementation of the T15 operator capability.

T15:
    - observes immutable context,
    - validates authority/integrity/evidence boundaries,
    - produces deterministic bounded proposals,
    - never executes proposals,
    - never mutates authoritative state,
    - never self-approves,
    - never promotes authority.

REOS_CONTROL_CENTER remains authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from .operator_policy import (
    OperatorActionType,
    OperatorDecision,
    OperatorPolicy,
    OperatorRisk,
)
from .operator_validation import (
    OperatorContext,
    OperatorProposal,
    OperatorValidationEngine,
    OperatorValidationError,
)


class OperatorAutonomyError(RuntimeError):
    """Base T15 error."""


class OperatorAutonomyInputError(OperatorAutonomyError):
    """Invalid T15 operator input."""


class OperatorAutonomyBoundaryError(OperatorAutonomyError):
    """T15 autonomy boundary violation."""


@dataclass(frozen=True)
class OperatorRequest:
    """Immutable request to the T15 operator."""

    context: OperatorContext
    requested_action: OperatorActionType
    objective: str
    evidence: tuple[str, ...] = ()
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic request data."""

        return {
            "context": self.context.to_dict(),
            "requested_action": self.requested_action.value,
            "objective": self.objective,
            "evidence": list(self.evidence),
            "metadata": (
                dict(self.metadata)
                if self.metadata is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class OperatorReport:
    """Immutable T15 operator result."""

    schema_version: str
    authority: str
    decision: OperatorDecision
    risk: OperatorRisk
    request_fingerprint: str
    proposal: OperatorProposal | None
    execution_authorized: bool
    state_mutated: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic report data."""

        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision.value,
            "risk": self.risk.value,
            "request_fingerprint": self.request_fingerprint,
            "proposal": (
                self.proposal.to_dict()
                if self.proposal is not None
                else None
            ),
            "execution_authorized": self.execution_authorized,
            "state_mutated": self.state_mutated,
            "explanation": self.explanation,
        }


class OperatorAutonomyEngine:
    """Deterministic bounded T15 operator engine."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @classmethod
    def canonicalize(cls, value: Any) -> str:
        """Return deterministic JSON."""

        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise OperatorAutonomyInputError(
                "T15 input cannot be canonicalized."
            ) from exc

    @classmethod
    def fingerprint(cls, value: Any) -> str:
        """Return deterministic SHA-256 fingerprint."""

        return hashlib.sha256(
            cls.canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _validate_request(
        cls,
        request: OperatorRequest,
    ) -> None:
        """Validate request structure."""

        if not isinstance(
            request,
            OperatorRequest,
        ):
            raise OperatorAutonomyInputError(
                "Invalid OperatorRequest."
            )

        try:
            OperatorValidationEngine.validate_context(
                request.context
            )
        except OperatorValidationError as exc:
            raise OperatorAutonomyInputError(
                str(exc)
            ) from exc

        if not isinstance(
            request.requested_action,
            OperatorActionType,
        ):
            raise OperatorAutonomyInputError(
                "Invalid requested operator action."
            )

        if (
            not isinstance(request.objective, str)
            or not request.objective.strip()
        ):
            raise OperatorAutonomyInputError(
                "Operator objective must be non-empty."
            )

        if len(request.objective) > 4096:
            raise OperatorAutonomyInputError(
                "Operator objective exceeds maximum length."
            )

        if not isinstance(request.evidence, tuple):
            raise OperatorAutonomyInputError(
                "Operator evidence must be a tuple."
            )

        if len(request.evidence) > 64:
            raise OperatorAutonomyInputError(
                "Operator evidence exceeds maximum item count."
            )

        for item in request.evidence:
            if not isinstance(item, str) or not item.strip():
                raise OperatorAutonomyInputError(
                    "Operator evidence must contain non-empty strings."
                )

        if request.metadata is not None and not isinstance(
            request.metadata,
            Mapping,
        ):
            raise OperatorAutonomyInputError(
                "Operator metadata must be a mapping or None."
            )

    @classmethod
    def _fail_closed_report(
        cls,
        request_fingerprint: str,
        explanation: str,
    ) -> OperatorReport:
        """Create a fail-closed report."""

        return OperatorReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=OperatorDecision.FAIL_CLOSED,
            risk=OperatorRisk.CRITICAL,
            request_fingerprint=request_fingerprint,
            proposal=None,
            execution_authorized=False,
            state_mutated=False,
            explanation=explanation,
        )

    @classmethod
    def _blocked_report(
        cls,
        request_fingerprint: str,
        risk: OperatorRisk,
        explanation: str,
    ) -> OperatorReport:
        """Create a blocked report."""

        return OperatorReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=OperatorDecision.BLOCK,
            risk=risk,
            request_fingerprint=request_fingerprint,
            proposal=None,
            execution_authorized=False,
            state_mutated=False,
            explanation=explanation,
        )

    @classmethod
    def operate(
        cls,
        request: OperatorRequest,
        policy: OperatorPolicy | None = None,
    ) -> OperatorReport:
        """
        Produce one bounded operator proposal.

        The method does not execute the proposal and does not
        authorize execution.
        """

        cls._validate_request(request)

        request_fingerprint = cls.fingerprint(
            request.to_dict()
        )

        # ---------------------------------------------------------
        # HARD FAIL-CLOSED BOUNDARY
        # ---------------------------------------------------------

        if not request.context.authority_valid:
            return cls._fail_closed_report(
                request_fingerprint,
                "Authority validation failed; T15 is fail-closed.",
            )

        if not request.context.integrity_valid:
            return cls._fail_closed_report(
                request_fingerprint,
                "Integrity validation failed; T15 is fail-closed.",
            )

        if not request.context.architecture_stable:
            return cls._fail_closed_report(
                request_fingerprint,
                "Architecture stability is not established; "
                "T15 is fail-closed.",
            )

        if not request.context.state_available:
            return cls._blocked_report(
                request_fingerprint,
                OperatorRisk.MEDIUM,
                "Required state is unavailable; "
                "T15 cannot safely propose autonomous work.",
            )

        if not request.context.state_valid:
            return cls._fail_closed_report(
                request_fingerprint,
                "State validation failed; T15 is fail-closed.",
            )

        if not request.context.evidence_available:
            return cls._blocked_report(
                request_fingerprint,
                OperatorRisk.MEDIUM,
                "Required evidence is unavailable; "
                "T15 cannot safely propose work.",
            )

        active_policy = (
            policy
            if policy is not None
            else OperatorPolicy()
        )

        active_policy.validate()

        requested_action = request.requested_action

        # ---------------------------------------------------------
        # BOUNDED ACTION CLASSIFICATION
        # ---------------------------------------------------------

        observational_actions = {
            OperatorActionType.OBSERVE,
            OperatorActionType.VERIFY,
            OperatorActionType.ANALYZE,
            OperatorActionType.TEST,
        }

        if requested_action in observational_actions:
            risk = OperatorRisk.LOW
            reversible = True
        elif requested_action is OperatorActionType.REQUEST_HUMAN_DECISION:
            risk = OperatorRisk.MEDIUM
            reversible = True
        elif requested_action is OperatorActionType.PROPOSE_CHANGE:
            risk = OperatorRisk.MEDIUM
            reversible = True
        else:
            return cls._fail_closed_report(
                request_fingerprint,
                "Unsupported operator action boundary.",
            )

        if not active_policy.permits(
            requested_action,
            risk,
        ):
            return cls._blocked_report(
                request_fingerprint,
                risk,
                "Requested action exceeds the active T15 policy boundary.",
            )

        evidence_basis = tuple(request.evidence)

        if not evidence_basis:
            evidence_basis = (
                "validated_operator_context",
            )

        proposal = OperatorProposal(
            action_type=requested_action,
            description=request.objective,
            risk=risk,
            reversible=reversible,
            requires_authorization=True,
            evidence_basis=evidence_basis,
            context_fingerprint=cls.fingerprint(
                request.context.to_dict()
            ),
        )

        try:
            OperatorValidationEngine.validate_proposal(
                proposal,
                active_policy,
            )
        except OperatorValidationError as exc:
            raise OperatorAutonomyBoundaryError(
                str(exc)
            ) from exc

        return OperatorReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            decision=OperatorDecision.PROPOSE,
            risk=risk,
            request_fingerprint=request_fingerprint,
            proposal=proposal,
            execution_authorized=False,
            state_mutated=False,
            explanation=(
                "T15 produced a bounded proposal. "
                "External authority and execution layers are required "
                "before any operational action."
            ),
        )


def operate(
    request: OperatorRequest,
    policy: OperatorPolicy | None = None,
) -> OperatorReport:
    """Convenience API for T15 operator operation."""

    return OperatorAutonomyEngine.operate(
        request,
        policy,
    )


__all__ = [
    "OperatorAutonomyEngine",
    "OperatorAutonomyError",
    "OperatorAutonomyBoundaryError",
    "OperatorAutonomyInputError",
    "OperatorDecision",
    "OperatorReport",
    "OperatorRequest",
    "operate",
]
