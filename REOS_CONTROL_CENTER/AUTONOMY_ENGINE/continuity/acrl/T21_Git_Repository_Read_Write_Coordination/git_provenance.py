from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitProvenance:
    authority: str = "REOS_CONTROL_CENTER"
    source: str = (
        "T21_Git_Repository_Read_Write_Coordination"
    )
    upstream_layers: tuple[int, ...] = (
        3,
        14,
        16,
        17,
        18,
        19,
        20,
    )
    evidence_mode: str = (
        "AUTHORIZED_GIT_TRANSACTION"
    )

    def validate(self) -> None:
        if self.authority != "REOS_CONTROL_CENTER":
            raise ValueError(
                "Invalid T21 provenance authority."
            )

        if self.source != (
            "T21_Git_Repository_Read_Write_Coordination"
        ):
            raise ValueError(
                "Invalid T21 provenance source."
            )

        if self.upstream_layers != (
            3,
            14,
            16,
            17,
            18,
            19,
            20,
        ):
            raise ValueError(
                "Invalid T21 upstream provenance."
            )
