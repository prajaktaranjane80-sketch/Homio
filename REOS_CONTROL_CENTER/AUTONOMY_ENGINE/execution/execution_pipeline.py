"""
Deterministic execution pipeline for AUTONOMY_ENGINE.

This module is an additive orchestration boundary.

Authority model
---------------
- REOS_CONTROL_CENTER remains the authoritative controller.
- This pipeline never becomes a controller.
- This pipeline never mutates controller state directly.
- This pipeline never discovers or invents an executor.
- All mutation execution remains dependency-injected.
- Existing AUTONOMY_ENGINE modules remain unchanged.

Execution model
---------------
ActionProposal
    -> protocol validation
    -> explicit execution context
    -> ExecutionCoordinator
    -> ControlledMutationAdapter
    -> authoritative executor
    -> postflight verification
    -> deterministic pipeline result

Safety principles
-----------------
- Fail closed.
- Default deny.
- No implicit authorization.
- No implicit capability grant.
- No implicit retry.
- No executor discovery.
- No controller command invention.
- No direct state.json mutation.
- No mutation before every required gate is positive.
- Preserve evidence across every boundary.
- One action may be processed only once per pipeline instance.
- Failed execution is terminal for this pipeline instance.
- Pipeline orchestration does not create authority.

This module intentionally delegates mutation coordination to
orchestration.execution_coordinator.ExecutionCoordinator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

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


class PipelineStatus(str, Enum):
    """Deterministic lifecycle status of one pipeline attempt."""

    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class PipelineBlockReason(str, Enum):
    """Machine-readable pipeline refusal reasons."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    ALREADY_PROCESSED = "ALREADY_PROCESSED"
    COORDINATION_BLOCKED = "COORDINATION_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    POSTFLIGHT_BLOCKED = "POSTFLIGHT_BLOCKED"


@dataclass(frozen=True)
class PipelineResult:
    """Immutable final result of one execution pipeline attempt."""

    status: PipelineStatus
    action_id: str
    allowed: bool
    reason: str
    protocol: ProtocolDecision
    coordination: CoordinationResult | None = None
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
            "evidence": dict(self.evidence),
        }


class ExecutionPipeline:
    """
    Deterministic top-level execution pipeline.

    This class is orchestration-only. It does not own controller authority,
    policy authority, mutation authority, or executor discovery.
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
        self._processed_action_ids: set[str] = set()

    def execute(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
        *,
        executor: Any = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> PipelineResult:
        """
        Execute exactly one controlled pipeline attempt.

        No executor is discovered or invented here.
        """

        action_id = self._safe_action_id(proposal)

        if action_id in self._processed_action_ids:
            protocol = validate_proposal(proposal)

            return PipelineResult(
                status=PipelineStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action has already been processed by this pipeline instance.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "pipeline_attempted": True,
                    "pipeline_replay_blocked": True,
                },
            )

        protocol = validate_proposal(proposal)

        if not protocol.valid:
            self._processed_action_ids.add(action_id)

            return PipelineResult(
                status=PipelineStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action proposal failed protocol validation.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "pipeline_attempted": True,
                    "execution_attempted": False,
                },
            )

        self._processed_action_ids.add(action_id)

        coordination = self._coordinator.execute(
            proposal,
            context,
            executor=executor,
            postflight=postflight,
        )

        evidence = {
            **dict(context.evidence),
            **dict(coordination.evidence),
            "pipeline_attempted": True,
        }

        if coordination.status is CoordinationStatus.EXECUTED:
            evidence["pipeline_succeeded"] = True

            return PipelineResult(
                status=PipelineStatus.EXECUTED,
                action_id=action_id,
                allowed=True,
                reason="Execution pipeline completed successfully.",
                protocol=protocol,
                coordination=coordination,
                evidence=evidence,
            )

        if coordination.status is CoordinationStatus.FAILED:
            evidence["pipeline_succeeded"] = False

            return PipelineResult(
                status=PipelineStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Execution pipeline failed at a downstream safety boundary.",
                protocol=protocol,
                coordination=coordination,
                evidence=evidence,
            )

        evidence["pipeline_succeeded"] = False

        return PipelineResult(
            status=PipelineStatus.BLOCKED,
            action_id=action_id,
            allowed=False,
            reason="Execution pipeline was blocked by a downstream safety boundary.",
            protocol=protocol,
            coordination=coordination,
            evidence=evidence,
        )

    def preflight(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
    ) -> tuple[ProtocolDecision, Any | None]:
        """
        Perform pipeline preflight without executing a mutation.

        The coordinator owns the actual enforcement decision.
        """

        if self._safe_action_id(proposal) in self._processed_action_ids:
            protocol = validate_proposal(proposal)
            return protocol, None

        return self._coordinator.preflight(proposal, context)

    def processed(self, action_id: str) -> bool:
        """Return whether this pipeline already processed an action."""

        return action_id in self._processed_action_ids

    def reset(self) -> None:
        """
        Clear only local pipeline memory.

        This does not clear controller state or persistent idempotency records.
        """

        self._processed_action_ids.clear()

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
