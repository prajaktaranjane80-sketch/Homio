"""
Deterministic execution coordinator for AUTONOMY_ENGINE.

This module is an additive orchestration boundary.

Authority model
---------------
- REOS_CONTROL_CENTER remains the authoritative controller.
- This coordinator never becomes a controller.
- This coordinator never mutates controller state directly.
- This coordinator never discovers or invents an executor.
- All mutation execution remains dependency-injected.
- Existing AUTONOMY_ENGINE modules remain unchanged.

Execution model
---------------
ActionProposal
    -> validation
    -> approval/policy/risk/guard inputs
    -> enforcement preflight
    -> controlled mutation boundary
    -> authoritative executor
    -> postflight verification
    -> deterministic result

Safety principles
-----------------
- Fail closed.
- Default deny.
- No implicit authorization.
- No implicit capability grant.
- No implicit retry.
- No executor discovery.
- No controller command invention.
- No state.json mutation.
- No mutation before every required gate is positive.
- Failed execution is terminal for the coordinator instance.
- Evidence is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from execution.enforcement import EnforcementDecision
from execution.mutation_adapter import (
    ControlledMutationAdapter,
    MutationBlockReason,
    MutationRequest,
    MutationResult,
)
from protocols.action_protocol import (
    ActionProposal,
    ProtocolDecision,
    validate_proposal,
)


class CoordinationStatus(str, Enum):
    """Deterministic lifecycle status of one execution coordination attempt."""

    BLOCKED = "BLOCKED"
    READY = "READY"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class CoordinationBlockReason(str, Enum):
    """Machine-readable coordinator refusal reasons."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    ALREADY_COORDINATED = "ALREADY_COORDINATED"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    MUTATION_BLOCKED = "MUTATION_BLOCKED"
    POSTFLIGHT_BLOCKED = "POSTFLIGHT_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


@dataclass(frozen=True)
class ExecutionContext:
    """
    Explicit execution authorization context.

    Every safety decision must be supplied by an upstream authority.
    The coordinator never infers missing permissions.
    """

    authorized: bool = False
    capability_available: bool = False
    policy_allowed: bool = False
    risk_allowed: bool = False
    guard_allowed: bool = False
    idempotency_clear: bool = False
    tripwires_clear: bool = False
    architecture_locked: bool = True

    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CoordinationResult:
    """Immutable final result of one coordinated execution attempt."""

    status: CoordinationStatus
    action_id: str
    allowed: bool
    reason: str
    protocol: ProtocolDecision
    enforcement: EnforcementDecision | None = None
    mutation: MutationResult | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "protocol": {
                "valid": self.protocol.valid,
                "errors": list(self.protocol.errors),
            },
            "enforcement": (
                self.enforcement.to_dict()
                if self.enforcement is not None
                else None
            ),
            "mutation": (
                self.mutation.to_dict()
                if self.mutation is not None
                else None
            ),
            "evidence": dict(self.evidence),
        }


class ExecutionCoordinator:
    """
    Deterministic coordinator between safety boundaries.

    The coordinator is orchestration only. It does not own controller
    authority and cannot create a mutation executor by itself.
    """

    def __init__(
        self,
        mutation_adapter: ControlledMutationAdapter | None = None,
    ) -> None:
        self._mutation_adapter = (
            mutation_adapter
            if mutation_adapter is not None
            else ControlledMutationAdapter()
        )
        self._coordinated_action_ids: set[str] = set()

    def preflight(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
    ) -> tuple[ProtocolDecision, EnforcementDecision | None]:
        """
        Perform protocol and enforcement validation without mutation.

        This method must never invoke the mutation executor.
        """

        protocol = validate_proposal(proposal)

        if not protocol.valid:
            return protocol, None

        enforcement = self._build_enforcement_decision(context)

        return protocol, enforcement

    def execute(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
        *,
        executor: Any = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> CoordinationResult:
        """
        Coordinate exactly one execution attempt.

        No executor is discovered or invented here.

        The supplied executor is passed only to the controlled mutation
        boundary after all explicit safety conditions have passed.
        """

        action_id = self._safe_action_id(proposal)

        if action_id in self._coordinated_action_ids:
            protocol = validate_proposal(proposal)

            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action has already been coordinated by this instance.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                    "coordination_replay_blocked": True,
                },
            )

        protocol = validate_proposal(proposal)

        if not protocol.valid:
            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action proposal failed protocol validation.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                },
            )

        enforcement = self._build_enforcement_decision(context)

        if not enforcement.allowed:
            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Execution was blocked by enforcement preflight.",
                protocol=protocol,
                enforcement=enforcement,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                    "execution_attempted": False,
                },
            )

        request = MutationRequest(
            proposal=proposal,
            authorized=context.authorized,
            capability_available=context.capability_available,
            policy_allowed=context.policy_allowed,
            risk_allowed=context.risk_allowed,
            guard_allowed=context.guard_allowed,
            idempotency_clear=context.idempotency_clear,
            tripwires_clear=context.tripwires_clear,
            architecture_locked=context.architecture_locked,
            executor=executor,
            evidence=dict(context.evidence),
        )

        self._coordinated_action_ids.add(action_id)

        mutation = self._mutation_adapter.execute(request)

        if not mutation.executed:
            status = (
                CoordinationStatus.FAILED
                if mutation.decision.status.value == "FAILED"
                else CoordinationStatus.BLOCKED
            )

            return CoordinationResult(
                status=status,
                action_id=action_id,
                allowed=False,
                reason="Controlled mutation boundary did not complete execution.",
                protocol=protocol,
                enforcement=enforcement,
                mutation=mutation,
                evidence={
                    **dict(context.evidence),
                    **dict(mutation.evidence),
                    "coordination_attempted": True,
                    "execution_attempted": (
                        mutation.evidence.get("mutation_attempted") is True
                    ),
                },
            )

        postflight_data = dict(postflight or {})

        postflight_decision = self._postflight_decision(
            mutation=mutation,
            postflight=postflight_data,
        )

        if not postflight_decision.allowed:
            return CoordinationResult(
                status=CoordinationStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Mutation executed but postflight verification failed.",
                protocol=protocol,
                enforcement=postflight_decision,
                mutation=mutation,
                evidence={
                    **dict(context.evidence),
                    **dict(mutation.evidence),
                    "coordination_attempted": True,
                    "execution_attempted": True,
                    "execution_succeeded": True,
                    "postflight_passed": False,
                },
            )

        return CoordinationResult(
            status=CoordinationStatus.EXECUTED,
            action_id=action_id,
            allowed=True,
            reason="Execution completed and postflight verification passed.",
            protocol=protocol,
            enforcement=postflight_decision,
            mutation=mutation,
            evidence={
                **dict(context.evidence),
                **dict(mutation.evidence),
                "coordination_attempted": True,
                "execution_attempted": True,
                "execution_succeeded": True,
                "postflight_passed": True,
            },
        )

    @staticmethod
    def _safe_action_id(proposal: ActionProposal) -> str:
        """Extract an action id without allowing malformed input to escape."""

        try:
            action_id = proposal.action_id
        except Exception:
            return "<invalid-action-id>"

        return (
            action_id
            if isinstance(action_id, str) and action_id
            else "<invalid-action-id>"
        )

    @staticmethod
    def _build_enforcement_decision(
        context: ExecutionContext,
    ) -> EnforcementDecision:
        """
        Build the coordinator's deterministic enforcement decision.

        Enforcement remains default-deny. Every required condition must be
        explicitly true.
        """

        failures: list[str] = []

        checks = (
            ("authorization", context.authorized),
            ("capability", context.capability_available),
            ("policy", context.policy_allowed),
            ("risk", context.risk_allowed),
            ("guard", context.guard_allowed),
            ("idempotency", context.idempotency_clear),
            ("tripwires", context.tripwires_clear),
            ("architecture_lock", not context.architecture_locked),
        )

        for name, allowed in checks:
            if allowed is not True:
                failures.append(f"{name}:failed")

        return EnforcementDecision(
            allowed=not failures,
            stage="PREFLIGHT",
            reason=(
                "All coordinator enforcement checks passed."
                if not failures
                else "Coordinator enforcement rejected the operation."
            ),
            checks=tuple(name for name, _ in checks),
            failures=tuple(failures),
        )

    @staticmethod
    def _postflight_decision(
        *,
        mutation: MutationResult,
        postflight: Mapping[str, bool],
    ) -> EnforcementDecision:
        """Create deterministic postflight verification."""

        failures: list[str] = []

        if mutation.executed is not True:
            failures.append("execution_failed")

        if postflight.get("evidence_complete") is not True:
            failures.append("evidence_incomplete")

        if postflight.get("provenance_valid") is not True:
            failures.append("provenance_invalid")

        if postflight.get("state_consistent") is not True:
            failures.append("state_inconsistent")

        return EnforcementDecision(
            allowed=not failures,
            stage="POSTFLIGHT",
            reason=(
                "Postflight verification passed."
                if not failures
                else "Postflight verification rejected completion."
            ),
            checks=(
                "execution_result",
                "evidence",
                "provenance",
                "state_consistency",
            ),
            failures=tuple(failures),
            metadata={
                "mutation_status": mutation.decision.status.value,
                "mutation_executed": mutation.executed,
            },
        )

    def coordinated(self, action_id: str) -> bool:
        """Return whether this coordinator already coordinated an action."""

        return action_id in self._coordinated_action_ids

    def reset(self) -> None:
        """
        Clear only local coordination memory.

        This does not clear controller state or persistent idempotency state.
        """

        self._coordinated_action_ids.clear()

    @staticmethod
    def mutation_block_reason() -> tuple[MutationBlockReason, ...]:
        """
        Expose known mutation refusal classes without owning their policy.

        This is intentionally informational and performs no mutation.
        """

        return tuple(MutationBlockReason)