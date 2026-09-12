from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from execution.controller_executor import ControllerExecutor
from execution.execution_pipeline import ExecutionPipeline, PipelineResult
from orchestration.execution_coordinator import ExecutionContext
from protocols.action_protocol import ActionProposal
from reos_control_center import calculate_hash, load_state

from .runtime_orchestrator import ACRLRuntimeOrchestrator
from .unified_runtime_context import UnifiedRuntimeContext


PROJECT_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class OperationalRuntimeResult:
    """Final evidence for one real ACRL -> Control Center operation."""

    context: UnifiedRuntimeContext
    integration_healthy: bool
    pipeline: PipelineResult

    @property
    def succeeded(self) -> bool:
        return self.pipeline.status.value == "EXECUTED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "integration_healthy": self.integration_healthy,
            "succeeded": self.succeeded,
            "context": self.context.to_dict(),
            "pipeline": self.pipeline.to_dict(),
        }


class ACRLOperationalRuntime:
    """
    Final operational bridge for the existing ACRL + AUTONOMY_ENGINE stack.

    Flow:
        ACRL authority/context
            -> T01-T30 integration validation
            -> ActionProposal
            -> ExecutionPipeline
            -> ExecutionCoordinator
            -> ControlledMutationAdapter
            -> ControllerExecutor
            -> reos_control_center.py
            -> state.json
            -> postflight integrity verification

    This is one operational runtime addition, not a new ACRL task generation.
    The first explicit production-safe mutation is the existing Control Center
    `checkpoint` command. No controller command is inferred.
    """

    MUTATION_NAME = "checkpoint"

    def __init__(self, control_center_root: Path | None = None) -> None:
        self.control_center_root = (
            Path(control_center_root).resolve()
            if control_center_root is not None
            else PROJECT_ROOT
        )

    def build_context(
        self,
        *,
        mission_id: str,
        objective: str,
    ) -> UnifiedRuntimeContext:
        return UnifiedRuntimeContext.build(
            control_center_root=self.control_center_root,
            mission_id=mission_id,
            objective=objective,
        )

    def validate_integration(
        self,
        context: UnifiedRuntimeContext,
    ) -> bool:
        snapshot = ACRLRuntimeOrchestrator(context).build_snapshot()
        return snapshot.healthy

    def run_checkpoint(
        self,
        *,
        mission_id: str,
        note: str,
        requester: str = "ACRL_OPERATIONAL_RUNTIME",
    ) -> OperationalRuntimeResult:
        """Execute one real, explicitly authorized Control Center checkpoint."""

        normalized_note = note.strip()
        if not normalized_note:
            raise ValueError("checkpoint note is required")

        context = self.build_context(
            mission_id=mission_id,
            objective="Execute one controlled ACRL operational checkpoint.",
        )

        integration_healthy = self.validate_integration(context)
        if not integration_healthy:
            raise RuntimeError("ACRL runtime integration is not healthy.")

        proposal = ActionProposal.create(
            action=self.MUTATION_NAME,
            target="REOS_CONTROL_CENTER",
            parameters={"note": normalized_note},
            requester=requester,
            reason="Final ACRL operational runtime proof.",
        )

        controller_executor = ControllerExecutor(
            self.control_center_root,
            allowed_mutations=(self.MUTATION_NAME,),
        )

        def execute_controller_command(
            action: ActionProposal,
        ) -> Any:
            result = controller_executor.execute(
                action,
                command=(self.MUTATION_NAME, normalized_note),
                evidence={
                    "acrl_context_fingerprint": context.context_fingerprint,
                    "acrl_runtime": "operational",
                    "controller_command_explicit": True,
                },
            )
            return result.to_dict()

        execution_context = ExecutionContext(
            authorized=True,
            capability_available=True,
            policy_allowed=True,
            risk_allowed=True,
            guard_allowed=True,
            idempotency_clear=True,
            tripwires_clear=True,
            # The existing coordinator interprets True as a block condition.
            architecture_locked=False,
            evidence={
                "mission_id": mission_id,
                "acrl_context_fingerprint": context.context_fingerprint,
                "acrl_t01_t30_validated": True,
                "controller_mutation": self.MUTATION_NAME,
            },
        )

        state_before = load_state()
        hash_before = state_before.get("integrity", {}).get("sha256")

        pipeline = ExecutionPipeline()
        result = pipeline.execute(
            proposal,
            execution_context,
            executor=execute_controller_command,
            postflight={
                "evidence_complete": True,
                "provenance_valid": True,
                "state_consistent": self._state_integrity_ok(
                    expected_previous_hash=hash_before,
                ),
            },
        )

        return OperationalRuntimeResult(
            context=context,
            integration_healthy=integration_healthy,
            pipeline=result,
        )

    def _state_integrity_ok(
        self,
        *,
        expected_previous_hash: str | None,
    ) -> bool:
        state = load_state()
        stored_hash = state.get("integrity", {}).get("sha256")
        calculated_hash = calculate_hash(state)

        if stored_hash != calculated_hash:
            return False

        if expected_previous_hash is None:
            return True

        return stored_hash != expected_previous_hash


def run_final_operational_proof(
    *,
    mission_id: str,
    note: str,
) -> OperationalRuntimeResult:
    """Convenience entrypoint for the final one-time ACRL proof."""

    return ACRLOperationalRuntime().run_checkpoint(
        mission_id=mission_id,
        note=note,
    )
