from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitRegistry:
    layer: str = "T21"
    name: str = (
        "Git Repository Read/Write Coordination"
    )
    schema_version: str = "1.0"
    mode: str = "authorized-git-transaction"

    def validate(self) -> None:
        if self.layer != "T21":
            raise ValueError(
                "Invalid T21 layer."
            )

        if self.schema_version != "1.0":
            raise ValueError(
                "Unsupported T21 schema."
            )

        if self.mode != (
            "authorized-git-transaction"
        ):
            raise ValueError(
                "Invalid T21 mode."
            )
