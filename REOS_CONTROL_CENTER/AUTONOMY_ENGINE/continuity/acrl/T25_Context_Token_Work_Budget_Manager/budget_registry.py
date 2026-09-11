from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BudgetRegistry:
    layer: str = "T25"
    name: str = (
        "Context / Token / Work-Budget Manager"
    )
    schema_version: str = "1.0"
    mode: str = (
        "deterministic-budget-governance"
    )

    upstream: tuple[str, ...] = (
        "T23_Reference_Evidence_Resolution_Engine",
        "T24_Cross_Chat_Continuity_Recovery_Engine",
    )

    downstream: tuple[str, ...] = (
        "T26_Dependency_Aware_Work_Scheduler",
        "T27_Conflict_Resolution_Reconciliation_Engine",
        "T28_Execution_Orchestration_Controlled_Execution",
    )

    def validate(self) -> None:
        if self.layer != "T25":
            raise ValueError(
                "Invalid T25 registry layer."
            )

        if self.schema_version != "1.0":
            raise ValueError(
                "Unsupported T25 schema version."
            )

        if self.mode != (
            "deterministic-budget-governance"
        ):
            raise ValueError(
                "Invalid T25 mode."
            )
