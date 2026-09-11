from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoopRegistry:
    layer: str = "T26"

    name: str = (
        "Autonomous Execution Loop Controller"
    )

    schema_version: str = "1.0"

    mode: str = (
        "bounded-autonomous-loop-control"
    )

    upstream: tuple[str, ...] = (
        "T22_Commit_Execution_Checkpoint_Coordination",
        "T23_Reference_Evidence_Resolution_Engine",
        "T24_Cross_Chat_Continuity_Recovery_Engine",
        "T25_Context_Token_Work_Budget_Manager",
    )

    downstream: tuple[str, ...] = (
        "T27_Dependency_Aware_Work_Scheduler",
        "T28_Conflict_Resolution_Reconciliation_Engine",
        "T29_Human_Decision_Boundary_Controller",
        "T30_Autonomous_Completion_Handoff_Engine",
    )

    def validate(self) -> None:
        if self.layer != "T26":
            raise ValueError(
                "Invalid T26 registry layer."
            )

        if self.schema_version != "1.0":
            raise ValueError(
                "Unsupported T26 schema version."
            )
