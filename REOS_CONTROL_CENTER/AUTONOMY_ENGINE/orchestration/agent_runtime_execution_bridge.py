"""
Agent Runtime -> Execution Coordinator bridge for AUTONOMY_ENGINE.

Purpose
-------
Connect the existing AgentRuntime lifecycle to the existing
ExecutionCoordinator safety/execution boundary.

This module does NOT:
- become a controller
- mutate state.json directly
- discover an executor
- bypass policy/guard/authorization
- create a second execution engine
- create a second runtime

Execution flow
--------------
AgentRuntime
    -> start
    -> ExecutionCoordinator
    -> existing ControlledMutationAdapter
    -> supplied authoritative executor
    -> result
    -> AgentRuntime terminal state

Safety
------
All execution authority remains dependency-injected through the existing
ExecutionCoordinator boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from orchestration.agent_runtime import AgentRuntime
from orchestration.execution_coordinator import (
    CoordinationResult,
    CoordinationStatus,
    ExecutionContext,
    ExecutionCoordinator,
)
from protocols.action_protocol import ActionProposal


@dataclass(frozen=True, slots=True)
class RuntimeExecutionResult:
    """Combined runtime and execution result."""

    runtime_status: str
    coordination_status: str
    allowed: bool
    action_id: str
    reason: str
    evidence: Mapping[str, Any]


class AgentRuntimeExecutionBridge:
    """
    Bind one AgentRuntime to the existing ExecutionCoordinator.

    The bridge is orchestration only. It does not own execution authority.
    """

    def __init__(
        self,
        runtime: AgentRuntime,
        coordinator: ExecutionCoordinator | None = None,
    ) -> None:
        self.runtime = runtime
        self.coordinator = coordinator or ExecutionCoordinator()

    def execute(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
        *,
        executor: Any = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> RuntimeExecutionResult:
        """
        Run one bounded runtime execution attempt.

        Runtime lifecycle:
            PLANNED -> RUNNING -> COMPLETED/BLOCKED/FAILED

        Execution lifecycle is delegated completely to the existing
        ExecutionCoordinator.
        """

        if self.runtime.status != "PLANNED":
            raise RuntimeError(
                f"runtime must be PLANNED before execution; "
                f"current={self.runtime.status}"
            )

        self.runtime.start()

        try:
            result = self.coordinator.execute(
                proposal,
                context,
                executor=executor,
                postflight=postflight,
            )

        except Exception as exc:
            runtime_result = self.runtime.fail(
                f"{type(exc).__name__}: {exc}"
            )

            return RuntimeExecutionResult(
                runtime_status=runtime_result.status,
                coordination_status=CoordinationStatus.FAILED.value,
                allowed=False,
                action_id=proposal.action_id,
                reason=str(exc),
                evidence={
                    "runtime_execution_attempted": True,
                    "runtime_terminal": True,
                    "coordination_exception": type(exc).__name__,
                },
            )

        if result.status == CoordinationStatus.EXECUTED:
            runtime_result = self.runtime.complete(
                output={
                    "coordination_status": result.status.value,
                    "action_id": result.action_id,
                    "allowed": result.allowed,
                    "reason": result.reason,
                }
            )

        elif result.status == CoordinationStatus.BLOCKED:
            runtime_result = self.runtime.block(
                result.reason or "Execution coordinator blocked execution."
            )

        else:
            runtime_result = self.runtime.fail(
                result.reason or "Execution coordinator reported failure."
            )

        return self._combined_result(
            runtime_result.status,
            result,
        )

    @staticmethod
    def _combined_result(
        runtime_status: str,
        result: CoordinationResult,
    ) -> RuntimeExecutionResult:
        evidence = {
            **dict(result.evidence),
            "runtime_execution_attempted": True,
            "runtime_terminal": runtime_status
            in {"COMPLETED", "BLOCKED", "FAILED"},
        }

        if result.mutation is not None:
            evidence["mutation_executed"] = result.mutation.executed
            evidence["mutation_status"] = (
                result.mutation.decision.status.value
            )

        return RuntimeExecutionResult(
            runtime_status=runtime_status,
            coordination_status=result.status.value,
            allowed=result.allowed,
            action_id=result.action_id,
            reason=result.reason,
            evidence=evidence,
        )
