"""
Controlled mutation boundary for AUTONOMY_ENGINE.

This module is additive and intentionally does not modify or bypass the
existing REOS_CONTROL_CENTER authority.

Design guarantees
-----------------
- No direct state.json mutation.
- No implicit controller command execution.
- Default-deny execution.
- Explicit authorization required.
- Action proposal must validate before mutation.
- Capability must be explicitly granted.
- Policy/risk/guard decisions must be supplied by the caller.
- Idempotency is checked before execution.
- A mutation executor is dependency-injected; this module never invents
  the controller's mutation API.
- Successful and failed attempts produce deterministic evidence.
- Execution is single-shot per adapter instance.
- No retry loop is built into the mutation boundary.
- Existing AUTONOMY_ENGINE modules remain untouched.

The adapter is therefore a safety boundary, not an authority source.

Future controller integration must provide an explicit executor callable
through the MutationRequest.executor field. The executor remains responsible
for invoking the authoritative REOS_CONTROL_CENTER mutation mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from protocols.action_protocol import ActionProposal, ProtocolDecision
from protocols.action_protocol import validate_proposal


class MutationStatus(str, Enum):
    """Deterministic lifecycle states for a mutation attempt."""

    BLOCKED = "BLOCKED"
    READY = "READY"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class MutationBlockReason(str, Enum):
    """Machine-readable reasons for refusing a mutation."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    POLICY_DENIED = "POLICY_DENIED"
    RISK_DENIED = "RISK_DENIED"
    GUARD_DENIED = "GUARD_DENIED"
    IDEMPOTENCY_BLOCKED = "IDEMPOTENCY_BLOCKED"
    TRIPWIRE_BLOCKED = "TRIPWIRE_BLOCKED"
    ARCHITECTURE_LOCKED = "ARCHITECTURE_LOCKED"
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    EXECUTOR_INVALID = "EXECUTOR_INVALID"
    ALREADY_ATTEMPTED = "ALREADY_ATTEMPTED"


@dataclass(frozen=True)
class MutationDecision:
    """Immutable decision returned before any mutation occurs."""

    status: MutationStatus
    action_id: str
    allowed: bool
    reason: str = ""
    block_reason: MutationBlockReason | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "block_reason": (
                self.block_reason.value
                if self.block_reason is not None
                else None
            ),
        }


@dataclass(frozen=True)
class MutationResult:
    """Immutable result of one controlled mutation attempt."""

    decision: MutationDecision
    executed: bool
    result: Any = None
    error: str = ""
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "decision": self.decision.to_dict(),
            "executed": self.executed,
            "result": self.result,
            "error": self.error,
            "evidence": dict(self.evidence),
        }


MutationExecutor = Callable[[ActionProposal], Any]


@dataclass(frozen=True)
class MutationRequest:
    """
    Explicit authorization envelope for one mutation attempt.

    All safety decisions are supplied explicitly. The adapter never guesses
    whether a mutation is safe.
    """

    proposal: ActionProposal
    authorized: bool = False
    capability_available: bool = False
    policy_allowed: bool = False
    risk_allowed: bool = False
    guard_allowed: bool = False
    idempotency_clear: bool = False
    tripwires_clear: bool = False
    architecture_locked: bool = True
    executor: MutationExecutor | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)


class ControlledMutationAdapter:
    """
    Fail-closed mutation boundary.

    This object does not become the controller authority. It only determines
    whether an already-authorized mutation may cross the execution boundary.
    """

    def __init__(self) -> None:
        self._attempted_action_ids: set[str] = set()

    def preflight(
        self,
        request: MutationRequest,
    ) -> MutationDecision:
        """
        Perform deterministic checks without executing the mutation.

        Ordering is intentional:
        1. proposal shape
        2. replay protection
        3. authority
        4. capability
        5. policy
        6. risk
        7. guard
        8. tripwires
        9. architecture lock
        10. executor availability
        """
        proposal = request.proposal

        protocol: ProtocolDecision = validate_proposal(proposal)

        if not protocol.valid:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.INVALID_PROPOSAL,
                "; ".join(protocol.errors),
            )

        if proposal.action_id in self._attempted_action_ids:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.ALREADY_ATTEMPTED,
                "Mutation action_id has already been attempted.",
            )

        if not request.idempotency_clear:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.IDEMPOTENCY_BLOCKED,
                "Idempotency clearance was not explicitly provided.",
            )

        if not request.authorized:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.NOT_AUTHORIZED,
                "Explicit mutation authorization is required.",
            )

        if not request.capability_available:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.CAPABILITY_DENIED,
                "Required capability was not explicitly granted.",
            )

        if not request.policy_allowed:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.POLICY_DENIED,
                "Governance policy did not explicitly allow the mutation.",
            )

        if not request.risk_allowed:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.RISK_DENIED,
                "Risk evaluation did not explicitly allow the mutation.",
            )

        if not request.guard_allowed:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.GUARD_DENIED,
                "Execution guard did not explicitly allow the mutation.",
            )

        if not request.tripwires_clear:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.TRIPWIRE_BLOCKED,
                "One or more security tripwires are blocking execution.",
            )

        if request.architecture_locked:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.ARCHITECTURE_LOCKED,
                "Frozen architecture cannot be mutated through this adapter.",
            )

        if request.executor is None:
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.EXECUTOR_MISSING,
                "No authoritative mutation executor was supplied.",
            )

        if not callable(request.executor):
            return self._blocked(
                proposal.action_id,
                MutationBlockReason.EXECUTOR_INVALID,
                "Mutation executor must be callable.",
            )

        return MutationDecision(
            status=MutationStatus.READY,
            action_id=proposal.action_id,
            allowed=True,
            reason="All explicit mutation preconditions passed.",
        )

    def execute(
        self,
        request: MutationRequest,
    ) -> MutationResult:
        """
        Execute exactly one mutation after successful preflight.

        The adapter records the action_id before crossing the execution
        boundary. This prevents a second call from silently replaying the
        same action through this adapter instance.

        Exceptions from the authoritative executor are captured and returned
        as a failed result. They are never converted into a successful
        mutation.
        """
        decision = self.preflight(request)

        if not decision.allowed:
            return MutationResult(
                decision=decision,
                executed=False,
                evidence=dict(request.evidence),
            )

        action_id = request.proposal.action_id

        # Mark before crossing the boundary. This is intentionally fail-closed:
        # an executor failure must not permit an automatic second attempt.
        self._attempted_action_ids.add(action_id)

        try:
            result = request.executor(request.proposal)

        except Exception as exc:
            failed_decision = MutationDecision(
                status=MutationStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Authoritative mutation executor failed.",
            )

            evidence = {
                **dict(request.evidence),
                "mutation_attempted": True,
                "mutation_succeeded": False,
                "failure_type": type(exc).__name__,
            }

            return MutationResult(
                decision=failed_decision,
                executed=False,
                error=str(exc),
                evidence=evidence,
            )

        executed_decision = MutationDecision(
            status=MutationStatus.EXECUTED,
            action_id=action_id,
            allowed=True,
            reason="Authoritative mutation executor completed.",
        )

        evidence = {
            **dict(request.evidence),
            "mutation_attempted": True,
            "mutation_succeeded": True,
        }

        return MutationResult(
            decision=executed_decision,
            executed=True,
            result=result,
            evidence=evidence,
        )

    def attempted(self, action_id: str) -> bool:
        """Return whether this adapter already attempted an action."""
        return action_id in self._attempted_action_ids

    def reset(self) -> None:
        """
        Clear local attempt memory.

        This method does NOT clear controller state or persistent idempotency
        records. Persistent replay protection must remain authoritative outside
        this adapter.
        """
        self._attempted_action_ids.clear()

    @staticmethod
    def _blocked(
        action_id: str,
        reason: MutationBlockReason,
        message: str,
    ) -> MutationDecision:
        """Construct a deterministic blocked decision."""
        return MutationDecision(
            status=MutationStatus.BLOCKED,
            action_id=action_id,
            allowed=False,
            reason=message,
            block_reason=reason,
        )