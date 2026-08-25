"""
Pre-execution defensive firewall for AUTONOMY_ENGINE.

This module is an additive preventive safety boundary.

Authority model
---------------
- REOS_CONTROL_CENTER remains authoritative.
- This firewall never mutates controller state.
- This firewall never executes an executor.
- This firewall never discovers an executor.
- This firewall never grants authority.
- This firewall never retries an operation.
- Existing AUTONOMY_ENGINE modules remain unchanged.

Purpose
-------
Reject unsafe execution requests BEFORE they reach the execution pipeline.

The firewall is intentionally independent from the mutation executor.
It validates structural, authorization, replay, architecture, executor,
and evidence preconditions without crossing the execution boundary.

Fail-closed principle
---------------------
Every safety condition must be explicitly acceptable.

Missing information is unsafe.
Malformed information is unsafe.
Contradictory information is unsafe.
Unknown information is unsafe.

A firewall PASS means only that the request is eligible to proceed to the
next safety boundary. It does NOT authorize execution by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from orchestration.execution_coordinator import ExecutionContext
from protocols.action_protocol import ActionProposal, ProtocolDecision
from protocols.action_protocol import validate_proposal


class FirewallStatus(str, Enum):
    """Deterministic firewall decision status."""

    BLOCKED = "BLOCKED"
    CLEARED = "CLEARED"


class FirewallBlockReason(str, Enum):
    """Machine-readable reasons for firewall rejection."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    POLICY_DENIED = "POLICY_DENIED"
    RISK_DENIED = "RISK_DENIED"
    GUARD_DENIED = "GUARD_DENIED"
    IDEMPOTENCY_BLOCKED = "IDEMPOTENCY_BLOCKED"
    TRIPWIRE_BLOCKED = "TRIPWIRE_BLOCKED"
    ARCHITECTURE_LOCKED = "ARCHITECTURE_LOCKED"
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    EXECUTOR_INVALID = "EXECUTOR_INVALID"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    POSTFLIGHT_INVALID = "POSTFLIGHT_INVALID"
    ALREADY_CHECKED = "ALREADY_CHECKED"


@dataclass(frozen=True)
class FirewallDecision:
    """Immutable result of one pre-execution firewall evaluation."""

    status: FirewallStatus
    action_id: str
    allowed: bool
    reason: str
    checks: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "checks": list(self.checks),
            "failures": list(self.failures),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FirewallRequest:
    """
    Explicit request envelope for pre-execution validation.

    The firewall does not infer missing values.
    """

    proposal: ActionProposal
    context: ExecutionContext
    executor: Any = None
    postflight: Mapping[str, bool] | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)


class PreExecutionFirewall:
    """
    Deterministic preventive firewall.

    This class performs validation only. It never invokes the executor.
    """

    def __init__(self) -> None:
        self._checked_action_ids: set[str] = set()

    def inspect(
        self,
        request: FirewallRequest,
    ) -> FirewallDecision:
        """
        Inspect a request without executing anything.

        The order is deliberate:

        1. request structure
        2. proposal protocol
        3. replay protection
        4. execution context
        5. authorization
        6. capability
        7. policy
        8. risk
        9. guard
        10. idempotency
        11. tripwires
        12. architecture
        13. executor availability
        14. evidence
        15. postflight contract
        """

        proposal = request.proposal
        action_id = self._safe_action_id(proposal)

        if action_id in self._checked_action_ids:
            return self._blocked(
                action_id,
                FirewallBlockReason.ALREADY_CHECKED,
                "Action has already been inspected by this firewall instance.",
            )

        if not isinstance(request, FirewallRequest):
            return self._blocked(
                action_id,
                FirewallBlockReason.INVALID_CONTEXT,
                "Firewall request must be a FirewallRequest.",
            )

        protocol: ProtocolDecision = validate_proposal(proposal)

        if not protocol.valid:
            return self._blocked(
                action_id,
                FirewallBlockReason.INVALID_PROPOSAL,
                "; ".join(protocol.errors),
            )

        context = request.context

        if not isinstance(context, ExecutionContext):
            return self._blocked(
                action_id,
                FirewallBlockReason.INVALID_CONTEXT,
                "Execution context must be an ExecutionContext.",
            )

        gates = (
            (
                "authorization",
                context.authorized,
                FirewallBlockReason.AUTHORIZATION_DENIED,
            ),
            (
                "capability",
                context.capability_available,
                FirewallBlockReason.CAPABILITY_DENIED,
            ),
            (
                "policy",
                context.policy_allowed,
                FirewallBlockReason.POLICY_DENIED,
            ),
            (
                "risk",
                context.risk_allowed,
                FirewallBlockReason.RISK_DENIED,
            ),
            (
                "guard",
                context.guard_allowed,
                FirewallBlockReason.GUARD_DENIED,
            ),
            (
                "idempotency",
                context.idempotency_clear,
                FirewallBlockReason.IDEMPOTENCY_BLOCKED,
            ),
            (
                "tripwires",
                context.tripwires_clear,
                FirewallBlockReason.TRIPWIRE_BLOCKED,
            ),
        )

        for name, value, reason in gates:
            if value is not True:
                return self._blocked(
                    action_id,
                    reason,
                    f"Pre-execution {name} gate was not explicitly cleared.",
                )

        if context.architecture_locked is not False:
            return self._blocked(
                action_id,
                FirewallBlockReason.ARCHITECTURE_LOCKED,
                "Frozen architecture cannot cross the execution firewall.",
            )

        if request.executor is None:
            return self._blocked(
                action_id,
                FirewallBlockReason.EXECUTOR_MISSING,
                "An explicit authoritative executor is required.",
            )

        if not callable(request.executor):
            return self._blocked(
                action_id,
                FirewallBlockReason.EXECUTOR_INVALID,
                "The supplied executor is not callable.",
            )

        evidence = dict(request.evidence)

        if not isinstance(evidence, dict):
            return self._blocked(
                action_id,
                FirewallBlockReason.EVIDENCE_INVALID,
                "Evidence must be a mapping.",
            )

        if not isinstance(request.postflight, Mapping):
            return self._blocked(
                action_id,
                FirewallBlockReason.POSTFLIGHT_INVALID,
                "Postflight contract must be supplied as a mapping.",
            )

        postflight = request.postflight

        required_postflight_keys = (
            "evidence_complete",
            "provenance_valid",
            "state_consistent",
        )

        missing_postflight = tuple(
            key
            for key in required_postflight_keys
            if key not in postflight
        )

        if missing_postflight:
            return self._blocked(
                action_id,
                FirewallBlockReason.POSTFLIGHT_INVALID,
                "Required postflight fields are missing.",
                metadata={
                    "missing_fields": missing_postflight,
                },
            )

        self._checked_action_ids.add(action_id)

        return FirewallDecision(
            status=FirewallStatus.CLEARED,
            action_id=action_id,
            allowed=True,
            reason=(
                "Pre-execution firewall cleared the request for the next "
                "execution safety boundary."
            ),
            checks=(
                "proposal_protocol",
                "authorization",
                "capability",
                "policy",
                "risk",
                "guard",
                "idempotency",
                "tripwires",
                "architecture",
                "executor",
                "evidence",
                "postflight_contract",
            ),
            metadata={
                "executor_invoked": False,
                "mutation_executed": False,
                "controller_state_mutated": False,
            },
        )

    def checked(self, action_id: str) -> bool:
        """Return whether an action passed firewall inspection."""

        return action_id in self._checked_action_ids

    def reset(self) -> None:
        """
        Clear only local firewall inspection memory.

        This does not clear controller state or persistent replay protection.
        """

        self._checked_action_ids.clear()

    @staticmethod
    def _safe_action_id(proposal: Any) -> str:
        """Extract an action id safely from potentially malformed input."""

        try:
            action_id = proposal.action_id
        except Exception:
            return "<invalid-action-id>"

        if isinstance(action_id, str) and action_id:
            return action_id

        return "<invalid-action-id>"

    @staticmethod
    def _blocked(
        action_id: str,
        reason: FirewallBlockReason,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> FirewallDecision:
        """Construct a deterministic fail-closed decision."""

        return FirewallDecision(
            status=FirewallStatus.BLOCKED,
            action_id=action_id,
            allowed=False,
            reason=message,
            failures=(reason.value,),
            metadata=dict(metadata or {}),
        )
