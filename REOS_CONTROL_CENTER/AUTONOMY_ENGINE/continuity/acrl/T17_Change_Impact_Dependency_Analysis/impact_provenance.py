from __future__ import annotations

from dataclasses import dataclass

from .impact_errors import (
    ChangeImpactValidationError,
)


@dataclass(frozen=True, slots=True)
class T17Provenance:
    source: str = "T16_REPOSITORY_INTELLIGENCE"
    authority: str = "REOS_CONTROL_CENTER"
    read_only: bool = True

    def validate(self) -> None:
        if self.source != "T16_REPOSITORY_INTELLIGENCE":
            raise ChangeImpactValidationError(
                "Invalid provenance source."
            )

        if self.authority != "REOS_CONTROL_CENTER":
            raise ChangeImpactValidationError(
                "Invalid authority."
            )

        if self.read_only is not True:
            raise ChangeImpactValidationError(
                "T17 must remain read-only."
            )


__all__ = [
    "T17Provenance",
]
