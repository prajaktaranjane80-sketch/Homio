from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BudgetProvenance:
    authority: str = (
        "REOS_CONTROL_CENTER"
    )

    layer: str = "T25"

    source: str = (
        "T25_Context_Token_Work_Budget_Manager"
    )

    upstream_layers: tuple[int, ...] = (
        23,
        24,
    )

    supporting_layers: tuple[int, ...] = (
        3,
        8,
        9,
        12,
        22,
    )

    mode: str = (
        "DETERMINISTIC_BUDGET_GOVERNANCE"
    )

    def validate(self) -> None:
        if self.authority != (
            "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Invalid T25 authority."
            )

        if 23 not in self.upstream_layers:
            raise ValueError(
                "T23 must be upstream."
            )

        if 24 not in self.upstream_layers:
            raise ValueError(
                "T24 must be upstream."
            )
