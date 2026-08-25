"""
Safe execution integration boundary for AUTONOMY_ENGINE.

This module is intentionally additive.

Authority model
---------------
- REOS_CONTROL_CENTER remains the authoritative controller.
- This module never mutates controller state directly.
- This module never discovers or invents an executor.
- ExecutionCoordinator remains responsible for orchestration.
- ControlledMutationAdapter remains responsible for the mutation boundary.
- All authorization, capability, policy, risk, guard, idempotency,
  tripwire, and architecture decisions must be explicit.

Safety model
------------
ActionProposal
    |
    v
SafeExecutionGateway
    |
    +--> proposal validation
    |
    +--> execution context validation
    |
    +--> ExecutionCoordinator
    |
    +--> ControlledMutationAdapter
    |
    +--> explicitly supplied authoritative executor
    |
    +--> postflight verification
    |
    v
Deterministic SafeExecutionResult

Design guarantees
-----------------
- Default deny.
- Fail closed.
- No implicit authorization.
- No implicit executor discovery.
- No retry loop.
- No direct state.json mutation.
- No controller command invention.
- No execution when preconditions are incomplete.
- No execution when the proposal is malformed.
- No execution when the executor is missing or invalid.
- One action_id is coordinated only once per gateway instance.
- Evidence is preserved.
- Exceptions are converted into deterministic failure results.
- Existing AUTONOMY_ENGINE modules remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from orchestration.execution_coordinator import (
    CoordinationResult,
    CoordinationStatus,
    ExecutionContext,
    ExecutionCoordinator,
)
from protocols.action_protocol import (
    ActionProposal,
    ProtocolDecision,
    validate_proposal,
)


class SafeExecutionStatus(str, Enum):
    """Deterministic lifecycle status of safe execution."""

    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class SafeExecutionBlockReason(str, Enum):
    """Machine-readable reasons for refusing safe execution."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    CONTEXT_INVALID = "CONTEXT_INVALID"
    ALREADY_EXECUTED = "ALREADY_EXECUTED"
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    EXECUTOR_INVALID = "EXECUTOR_INVALID"
    COORDINATION_BLOCKED = "COORDINATION_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    POSTFLIGHT_FAILED = "POSTFLIGHT_FAILED"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


@dataclass(frozen=True)
class SafeExecutionResult:
    """Immutable result returned by the safe execution boundary."""

    status: SafeExecutionStatus
    action_id: str
    allowed: bool
    reason: str
    protocol: ProtocolDecision
    coordination: CoordinationResult | None = None
    block_reason: SafeExecutionBlockReason | None = None
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
            "coordination": (
                self.coordination.to_dict()
                if self.coordination is not None
                else None
            ),
            "block_reason": (
                self.block_reason.value
                if self.block_reason is not None
                else None
            ),
            "evidence": dict(self.evidence),
        }


class SafeExecutionGateway:
    """
    Final integration boundary for controlled autonomous execution.

    This class is intentionally not an authority source.

    It accepts already-decided execution context and an explicitly supplied
    executor. It then delegates orchestration to ExecutionCoordinator.

    The gateway never:
    - discovers an executor,
    - creates authorization,
    - changes policy,
    - changes risk decisions,
    - changes controller state,
    - retries a failed mutation.
    """

    def __init__(
        self,
        coordinator: ExecutionCoordinator | None = None,
    ) -> None:
        self._coordinator = (
            coordinator
            if coordinator is not None
            else ExecutionCoordinator()
        )

        self._completed_action_ids: set[str] = set()

    def preflight(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
    ) -> SafeExecutionResult:
        """
        Perform validation without executing anything.

        This method is side-effect free with respect to mutation execution.
        """

        action_id = self._safe_action_id(proposal)

        try:
            protocol = validate_proposal(proposal)
        except Exception as exc:
            return SafeExecutionResult(
                status=SafeExecutionStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Proposal validation raised an exception.",
                protocol=self._invalid_protocol(),
                block_reason=SafeExecutionBlockReason.INTERNAL_FAILURE,
                evidence={
                    **self._context_evidence(context),
                    "preflight_exception": type(exc).__name__,
                },
            )

        if not protocol.valid:
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Safe execution rejected the action proposal.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.INVALID_PROPOSAL,
                evidence={
                    **self._context_evidence(context),
                    "preflight_passed": False,
                },
            )

        if action_id in self._completed_action_ids:
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action has already completed through this gateway.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.ALREADY_EXECUTED,
                evidence={
                    **self._context_evidence(context),
                    "replay_blocked": True,
                },
            )

        if not isinstance(context, ExecutionContext):
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Execution context is invalid.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.CONTEXT_INVALID,
                evidence={
                    "preflight_passed": False,
                },
            )

        return SafeExecutionResult(
            status=SafeExecutionStatus.EXECUTED
            if False
            else SafeExecutionStatus.BLOCKED,
            action_id=action_id,
            allowed=True,
            reason="Safe execution preflight passed.",
            protocol=protocol,
            evidence={
                **self._context_evidence(context),
                "preflight_passed": True,
                "execution_started": False,
            },
        )

    def execute(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
        *,
        executor: Callable[[ActionProposal], Any] | None = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> SafeExecutionResult:
        """
        Execute exactly one controlled action.

        The executor must be explicitly supplied by the caller.

        No executor discovery or retry occurs here.
        """

        action_id = self._safe_action_id(proposal)

        protocol = self._validate_safely(proposal)

        if not protocol.valid:
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action proposal failed protocol validation.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.INVALID_PROPOSAL,
                evidence={
                    **self._context_evidence(context),
                    "execution_attempted": False,
                },
            )

        if not isinstance(context, ExecutionContext):
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Execution context is invalid.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.CONTEXT_INVALID,
                evidence={
                    "execution_attempted": False,
                },
            )

        if action_id in self._completed_action_ids:
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action has already completed through this gateway.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.ALREADY_EXECUTED,
                evidence={
                    **self._context_evidence(context),
                    "replay_blocked": True,
                },
            )

        if executor is None:
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="No explicit authoritative executor was supplied.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.EXECUTOR_MISSING,
                evidence={
                    **self._context_evidence(context),
                    "execution_attempted": False,
                },
            )

        if not callable(executor):
            return SafeExecutionResult(
                status=SafeExecutionStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Supplied executor is not callable.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.EXECUTOR_INVALID,
                evidence={
                    **self._context_evidence(context),
                    "execution_attempted": False,
                },
            )

        try:
            coordination = self._coordinator.execute(
                proposal,
                context,
                executor=executor,
                postflight=postflight,
            )
        except Exception as exc:
            return SafeExecutionResult(
                status=SafeExecutionStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Execution coordinator raised an exception.",
                protocol=protocol,
                block_reason=SafeExecutionBlockReason.INTERNAL_FAILURE,
                evidence={
                    **self._context_evidence(context),
                    "execution_attempted": True,
                    "execution_succeeded": False,
                    "coordinator_exception": type(exc).__name__,
                },
            )

        if coordination.status is CoordinationStatus.EXECUTED:
            self._completed_action_ids.add(action_id)

            return SafeExecutionResult(
                status=SafeExecutionStatus.EXECUTED,
                action_id=action_id,
                allowed=True,
                reason="Safe execution completed successfully.",
                protocol=protocol,
                coordination=coordination,
                evidence={
                    **self._context_evidence(context),
                    **dict(coordination.evidence),
                    "safe_execution_completed": True,
                    "execution_attempted": True,
                    "execution_succeeded": True,
                },
            )

        if coordination.status is CoordinationStatus.FAILED:
            return SafeExecutionResult(
                status=SafeExecutionStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Execution failed or postflight verification failed.",
                protocol=protocol,
                coordination=coordination,
                block_reason=(
                    SafeExecutionBlockReason.POSTFLIGHT_FAILED
                    if coordination.evidence.get("postflight_passed") is False
                    else SafeExecutionBlockReason.EXECUTION_FAILED
                ),
                evidence={
                    **self._context_evidence(context),
                    **dict(coordination.evidence),
                    "safe_execution_completed": False,
                },
            )

        return SafeExecutionResult(
            status=SafeExecutionStatus.BLOCKED,
            action_id=action_id,
            allowed=False,
            reason="Safe execution was blocked by an upstream safety boundary.",
            protocol=protocol,
            coordination=coordination,
            block_reason=SafeExecutionBlockReason.COORDINATION_BLOCKED,
            evidence={
                **self._context_evidence(context),
                **dict(coordination.evidence),
                "safe_execution_completed": False,
            },
        )

    def completed(self, action_id: str) -> bool:
        """Return whether an action completed through this gateway."""

        return action_id in self._completed_action_ids

    def reset(self) -> None:
        """
        Clear only local gateway completion memory.

        This does not clear controller state or persistent idempotency state.
        """

        self._completed_action_ids.clear()

    @staticmethod
    def _safe_action_id(proposal: Any) -> str:
        """Extract a safe action identifier from possibly malformed input."""

        try:
            action_id = proposal.action_id
        except Exception:
            return "<invalid-action-id>"

        if isinstance(action_id, str) and action_id:
            return action_id

        return "<invalid-action-id>"

    @staticmethod
    def _validate_safely(proposal: Any) -> ProtocolDecision:
        """Validate a proposal without allowing validator exceptions to escape."""

        try:
            return validate_proposal(proposal)
        except Exception:
            return SafeExecutionGateway._invalid_protocol()

    @staticmethod
    def _invalid_protocol() -> ProtocolDecision:
        """
        Construct a deterministic invalid protocol decision.

        This fallback exists only for defensive exception handling.
        """

        return ProtocolDecision(
            valid=False,
            errors=("proposal_validation_exception",),
        )

    @staticmethod
    def _context_evidence(
        context: Any,
    ) -> dict[str, Any]:
        """Extract caller-supplied evidence without trusting its shape."""

        try:
            evidence = context.evidence
        except Exception:
            return {}

        if isinstance(evidence, Mapping):
            return dict(evidence)

        return {}


# Explicit functional alias for callers that prefer a shorter integration API.
SafeExecution = SafeExecutionGateway


__all__ = [
    "SafeExecutionStatus",
    "SafeExecutionBlockReason",
    "SafeExecutionResult",
    "SafeExecutionGateway",
    "SafeExecution",
]