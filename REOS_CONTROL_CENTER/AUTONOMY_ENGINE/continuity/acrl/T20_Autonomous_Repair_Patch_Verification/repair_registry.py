from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RepairRegistry:
    schema_version: str = "1.0"
    layer: str = "T20"
    name: str = (
        "Autonomous Repair & Patch Verification"
    )
    mode: str = (
        "bounded-repair-and-verification"
    )

    def validate(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError(
                "Unsupported T20 registry schema."
            )

        if self.layer != "T20":
            raise ValueError(
                "Invalid T20 registry layer."
            )

        if self.mode != (
            "bounded-repair-and-verification"
        ):
            raise ValueError(
                "Invalid T20 registry mode."
            )
