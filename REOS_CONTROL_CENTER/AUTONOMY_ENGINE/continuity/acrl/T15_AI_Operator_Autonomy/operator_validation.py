
"""
ACRL T15 — AI Operator Autonomy Validation.

Defensive validation for T15 operator proposals.

This module validates structure and safety boundaries only.
It does not execute, approve, or mutate anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .operator_policy import (
    OperatorActionType,
    OperatorPolicy,
    OperatorPolicyError,
    OperatorRisk,
)


class OperatorValidationError(ValueError):
    """Raised when T15 operator input is invalid."""


@dataclass(frozen=True)
class OperatorContext:
    """Immutable bounded context supplied to T15."""

    gate: str
    subtask: str | None
    task: str
    state_available: bool
    state_valid: bool
    architecture_stable: bool
    authority_valid: bool
    integrity_valid: bool
    evidence_available: bool
    metadata: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable context."""

        return {
            "gate": self.gate,
            "subtask": self.subtask,
            "task": self.task,
            "state_available": self.state_available,
            "state_valid": self.state_valid,
            "architecture_stable": self.architecture_stable,
            "authority_valid": self.authority_valid,
            "integrity_valid": self.integrity_valid,
            "evidence_available": self.evidence_available,
            "metadata": (
                dict(self.metadata)
                if self.metadata is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class OperatorProposal:
    """Immutable bounded T15 proposal."""

    action_type: OperatorActionType
    description: str
    risk: OperatorRisk
    reversible: bool
    requires_authorization: bool
    evidence_basis: tuple[str, ...]
    context_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable proposal."""

        return {
            "action_type": self.action_type.value,
            "description": self.description,
            "risk": self.risk.value,
            "reversible": self.reversible,
            "requires_authorization": self.requires_authorization,
            "evidence_basis": list(self.evidence_basis),
            "context_fingerprint": self.context_fingerprint,
        }


class OperatorValidationEngine:
    """Defensive T15 validator."""

    MAX_DESCRIPTION_LENGTH = 4096
    MAX_EVIDENCE_ITEMS = 64
    MAX_EVIDENCE_LENGTH = 512

    @classmethod
    def validate_context(
        cls,
        context: OperatorContext,
    ) -> bool:
        """Validate operator context."""

        if not isinstance(context, OperatorContext):
            raise OperatorValidationError(
                "Invalid OperatorContext."
            )

        string_fields = (
            ("gate", context.gate),
            ("task", context.task),
        )

        for field_name, value in string_fields:
            if not isinstance(value, str) or not value.strip():
                raise OperatorValidationError(
                    f"{field_name} must be a non-empty string."
                )

        if (
            context.subtask is not None
            and (
                not isinstance(context.subtask, str)
                or not context.subtask.strip()
            )
        ):
            raise OperatorValidationError(
                "subtask must be None or a non-empty string."
            )

        boolean_fields = (
            "state_available",
            "state_valid",
            "architecture_stable",
            "authority_valid",
            "integrity_valid",
            "evidence_available",
        )

        for field_name in boolean_fields:
            value = getattr(context, field_name)
            if not isinstance(value, bool):
                raise OperatorValidationError(
                    f"{field_name} must be boolean."
                )

        if context.metadata is not None and not isinstance(
            context.metadata,
            Mapping,
        ):
            raise OperatorValidationError(
                "metadata must be a mapping or None."
            )

        return True

    @classmethod
    def validate_proposal(
        cls,
        proposal: OperatorProposal,
        policy: OperatorPolicy | None = None,
    ) -> bool:
        """Validate proposal structure and policy compliance."""

        if not isinstance(
            proposal,
            OperatorProposal,
        ):
            raise OperatorValidationError(
                "Invalid OperatorProposal."
            )

        if not isinstance(
            proposal.action_type,
            OperatorActionType,
        ):
            raise OperatorValidationError(
                "Invalid proposal action type."
            )

        if (
            not isinstance(proposal.description, str)
            or not proposal.description.strip()
        ):
            raise OperatorValidationError(
                "Proposal description must be non-empty."
            )

        if len(proposal.description) > cls.MAX_DESCRIPTION_LENGTH:
            raise OperatorValidationError(
                "Proposal description exceeds maximum length."
            )

        if not isinstance(
            proposal.risk,
            OperatorRisk,
        ):
            raise OperatorValidationError(
                "Invalid proposal risk."
            )

        if not isinstance(proposal.reversible, bool):
            raise OperatorValidationError(
                "Proposal reversible must be boolean."
            )

        if not isinstance(
            proposal.requires_authorization,
            bool,
        ):
            raise OperatorValidationError(
                "Proposal authorization flag must be boolean."
            )

        if not isinstance(
            proposal.evidence_basis,
            tuple,
        ):
            raise OperatorValidationError(
                "evidence_basis must be a tuple."
            )

        if len(proposal.evidence_basis) > cls.MAX_EVIDENCE_ITEMS:
            raise OperatorValidationError(
                "Too many evidence items."
            )

        for evidence in proposal.evidence_basis:
            if not isinstance(evidence, str):
                raise OperatorValidationError(
                    "Evidence items must be strings."
                )

            if not evidence.strip():
                raise OperatorValidationError(
                    "Evidence items must not be empty."
                )

            if len(evidence) > cls.MAX_EVIDENCE_LENGTH:
                raise OperatorValidationError(
                    "Evidence item exceeds maximum length."
                )

        if (
            not isinstance(proposal.context_fingerprint, str)
            or len(proposal.context_fingerprint) != 64
        ):
            raise OperatorValidationError(
                "Invalid context fingerprint."
            )

        active_policy = (
            policy
            if policy is not None
            else OperatorPolicy()
        )

        try:
            permitted = active_policy.permits(
                proposal.action_type,
                proposal.risk,
            )
        except OperatorPolicyError as exc:
            raise OperatorValidationError(
                str(exc)
            ) from exc

        if not permitted:
            raise OperatorValidationError(
                "Proposal violates T15 policy risk boundary."
            )

        # T15 may propose, but authorization must remain external.
        if not proposal.requires_authorization:
            raise OperatorValidationError(
                "Every T15 proposal requires external authorization."
            )

        # T15 proposals must be bounded and reversible unless
        # the action is explicitly observational/analytical.
        non_mutating = {
            OperatorActionType.OBSERVE,
            OperatorActionType.VERIFY,
            OperatorActionType.ANALYZE,
            OperatorActionType.TEST,
            OperatorActionType.REQUEST_HUMAN_DECISION,
        }

        if (
            proposal.action_type
            not in non_mutating
            and not proposal.reversible
        ):
            raise OperatorValidationError(
                "Non-reversible proposal is outside T15 boundary."
            )

        return True


__all__ = [
    "OperatorContext",
    "OperatorProposal",
    "OperatorValidationEngine",
    "OperatorValidationError",
]
