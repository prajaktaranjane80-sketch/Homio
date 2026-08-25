"""Action protocol primitives for AUTONOMY_ENGINE V6.

Defines a deterministic boundary between an action proposal and execution.
This module does not execute actions and does not replace the existing
AUTONOMY_ENGINE execution gateway.

Validation is fail-closed: malformed external/untrusted values must produce
a deterministic invalid decision rather than an uncontrolled exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4


_ALLOWED_STATUSES = frozenset(
    {
        "PROPOSED",
        "APPROVED",
        "REJECTED",
        "BLOCKED",
        "EXECUTED",
    }
)


@dataclass(frozen=True)
class ActionProposal:
    """Immutable proposal describing an intended engine action."""

    action_id: str
    action: str
    target: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    requester: str = ""
    tenant_id: str | None = None
    status: str = "PROPOSED"
    reason: str = ""

    @classmethod
    def create(
        cls,
        *,
        action: str,
        target: str,
        parameters: Mapping[str, Any] | None = None,
        requester: str = "",
        tenant_id: str | None = None,
        reason: str = "",
    ) -> "ActionProposal":
        """Create a new proposal with a unique action identifier."""
        return cls(
            action_id=str(uuid4()),
            action=action,
            target=target,
            parameters=dict(parameters or {}),
            requester=requester,
            tenant_id=tenant_id,
            status="PROPOSED",
            reason=reason,
        )

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        """Validate proposal shape without executing anything.

        Validation is deliberately defensive because proposals may originate
        outside trusted internal code.
        """
        errors: list[str] = []

        if not isinstance(self.action_id, str) or not self.action_id.strip():
            errors.append("action_id is required.")

        if not isinstance(self.action, str) or not self.action.strip():
            errors.append("action is required.")

        if not isinstance(self.target, str) or not self.target.strip():
            errors.append("target is required.")

        if not isinstance(self.status, str):
            errors.append("status must be a string.")
        elif self.status not in _ALLOWED_STATUSES:
            errors.append(
                f"Unsupported status: {self.status!r}."
            )

        if not isinstance(self.parameters, Mapping):
            errors.append("parameters must be a mapping.")

        return not errors, tuple(errors)

    def with_status(
        self,
        status: str,
        *,
        reason: str = "",
    ) -> "ActionProposal":
        """Return a new proposal with an updated lifecycle status."""
        normalized = status.upper()

        if normalized not in _ALLOWED_STATUSES:
            raise ValueError(
                f"Unsupported action status: {status!r}"
            )

        return ActionProposal(
            action_id=self.action_id,
            action=self.action,
            target=self.target,
            parameters=dict(self.parameters),
            requester=self.requester,
            tenant_id=self.tenant_id,
            status=normalized,
            reason=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "action_id": self.action_id,
            "action": self.action,
            "target": self.target,
            "parameters": dict(self.parameters),
            "requester": self.requester,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ProtocolDecision:
    """Deterministic protocol validation result."""

    valid: bool
    action_id: str
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "valid": self.valid,
            "action_id": self.action_id,
            "errors": list(self.errors),
        }


def validate_proposal(
    proposal: ActionProposal,
) -> ProtocolDecision:
    """Validate an action proposal before governance/execution."""
    if not isinstance(proposal, ActionProposal):
        return ProtocolDecision(
            valid=False,
            action_id="",
            errors=("proposal must be an ActionProposal.",),
        )

    valid, errors = proposal.validate()

    return ProtocolDecision(
        valid=valid,
        action_id=proposal.action_id
        if isinstance(proposal.action_id, str)
        else "",
        errors=errors,
    )