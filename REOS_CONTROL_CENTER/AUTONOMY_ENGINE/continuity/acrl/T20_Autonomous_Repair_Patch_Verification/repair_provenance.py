from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepairProvenance:
    authority: str = "REOS_CONTROL_CENTER"
    source: str = "T20_Autonomous_Repair_Patch_Verification"
    upstream_layers: tuple[int, ...] = (
        3,
        12,
        14,
        17,
        18,
        19,
    )
    evidence_mode: str = (
        "AUTHORIZED_ISOLATED_REPAIR_AND_EXTERNAL_VERIFICATION"
    )

    def validate(self) -> None:
        if self.authority != "REOS_CONTROL_CENTER":
            raise ValueError(
                "Invalid T20 provenance authority."
            )

        if self.source != (
            "T20_Autonomous_Repair_Patch_Verification"
        ):
            raise ValueError(
                "Invalid T20 provenance source."
            )
