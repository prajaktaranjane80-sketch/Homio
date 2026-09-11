from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoopProvenance:
    authority: str = (
        "REOS_CONTROL_CENTER"
    )

    layer: str = "T26"

    source: str = (
        "T26_Autonomous_Execution_Loop_Controller"
    )

    upstream_layers: tuple[int, ...] = (
        22,
        23,
        24,
        25,
    )

    mode: str = (
        "BOUNDED_AUTONOMOUS_LOOP_CONTROL"
    )

    def validate(self) -> None:
        if self.authority != (
            "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Invalid T26 authority."
            )

        for required in (
            22,
            23,
            24,
            25,
        ):
            if required not in self.upstream_layers:
                raise ValueError(
                    f"T{required} must be upstream."
                )

        if self.mode != (
            "BOUNDED_AUTONOMOUS_LOOP_CONTROL"
        ):
            raise ValueError(
                "Invalid T26 mode."
            )
