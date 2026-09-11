from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckpointRegistry:
    layer: str = "T22"
    name: str = (
        "Commit & Execution Checkpoint Coordination"
    )
    schema_version: str = "1.0"
    mode: str = "immutable-execution-checkpoint"

    upstream: tuple[str, ...] = (
        "T03_State_Reconstruction",
        "T12_Resume_Safety",
        "T14_Full_Regression",
        "T17_Change_Impact_Dependency_Analysis",
        "T18_Safe_Execution_Authorization_Guard",
        "T19_Intelligent_Test_Selection_Failure_Diagnosis",
        "T20_Autonomous_Repair_Patch_Verification",
        "T21_Git_Repository_Read_Write_Coordination",
    )

    downstream: tuple[str, ...] = (
        "future_execution_orchestration_layer",
        "future_deployment_layer",
        "future_release_layer",
        "future_audit_layer",
    )

    def validate(self) -> None:
        if self.layer != "T22":
            raise ValueError(
                "Invalid T22 registry layer."
            )

        if self.schema_version != "1.0":
            raise ValueError(
                "Unsupported T22 schema version."
            )

        if self.mode != "immutable-execution-checkpoint":
            raise ValueError(
                "Invalid T22 operating mode."
            )
