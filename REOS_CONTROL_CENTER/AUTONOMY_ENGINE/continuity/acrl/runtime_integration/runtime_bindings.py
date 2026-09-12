from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeBinding:
    task_id: str
    module_path: str
    export_name: str

    def resolve(self) -> Any:
        module = import_module(self.module_path)
        component = getattr(module, self.export_name, None)

        if component is None:
            raise AttributeError(
                f"{self.task_id} export not found: "
                f"{self.module_path}.{self.export_name}"
            )

        return component


T21_TO_T30_BINDINGS: tuple[RuntimeBinding, ...] = (
    RuntimeBinding(
        "T21",
        "AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination",
        "GitReader",
    ),
    RuntimeBinding(
        "T22",
        "AUTONOMY_ENGINE.continuity.acrl.T22_Commit_Execution_Checkpoint_Coordination",
        "create_execution_checkpoint",
    ),
    RuntimeBinding(
        "T23",
        "AUTONOMY_ENGINE.continuity.acrl.T23_Reference_Evidence_Resolution_Engine",
        "resolve_evidence",
    ),
    RuntimeBinding(
        "T24",
        "AUTONOMY_ENGINE.continuity.acrl.T24_Cross_Chat_Continuity_Recovery_Engine",
        "recover_continuity",
    ),
    RuntimeBinding(
        "T25",
        "AUTONOMY_ENGINE.continuity.acrl.T25_Context_Token_Work_Budget_Manager",
        "allocate_work_budget",
    ),
    RuntimeBinding(
        "T26",
        "AUTONOMY_ENGINE.continuity.acrl.T26_Autonomous_Execution_Loop_Controller",
        "start_execution_loop",
    ),
    RuntimeBinding(
        "T27",
        "AUTONOMY_ENGINE.continuity.acrl.T27_Dependency_Aware_Work_Scheduler",
        "build_schedule",
    ),
    RuntimeBinding(
        "T28",
        "AUTONOMY_ENGINE.continuity.acrl.T28_Conflict_Resolution_Reconciliation_Engine",
        "reconcile",
    ),
    RuntimeBinding(
        "T29",
        "AUTONOMY_ENGINE.continuity.acrl.T29_Human_Decision_Boundary_Controller",
        "create_decision_boundary",
    ),
    RuntimeBinding(
        "T30",
        "AUTONOMY_ENGINE.continuity.acrl.T30_Autonomous_Completion_Handoff_Engine",
        "evaluate_completion",
    ),
)


def resolve_all_bindings() -> dict[str, Any]:
    resolved: dict[str, Any] = {}

    for binding in T21_TO_T30_BINDINGS:
        resolved[binding.task_id] = binding.resolve()

    return resolved
