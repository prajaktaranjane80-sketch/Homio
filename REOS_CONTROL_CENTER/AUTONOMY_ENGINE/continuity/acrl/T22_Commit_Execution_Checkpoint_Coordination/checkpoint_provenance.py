from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckpointProvenance:
    authority: str = (
        "REOS_CONTROL_CENTER"
    )

    source: str = (
        "T22_Commit_Execution_Checkpoint_Coordination"
    )

    upstream_layers: tuple[int, ...] = (
        3,
        12,
        14,
        17,
        18,
        19,
        20,
        21,
    )

    evidence_mode: str = (
        "IMMUTABLE_EXECUTION_CHECKPOINT"
    )

    def validate(self) -> None:
        if self.authority != "REOS_CONTROL_CENTER":
            raise ValueError(
                "T22 authority is invalid."
            )

        if 21 not in self.upstream_layers:
            raise ValueError(
                "T21 must be an upstream dependency."
            )

        if 18 not in self.upstream_layers:
            raise ValueError(
                "T18 must be an upstream dependency."
            )

        if 20 not in self.upstream_layers:
            raise ValueError(
                "T20 must be an upstream dependency."
            )
