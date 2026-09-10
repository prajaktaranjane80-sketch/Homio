from __future__ import annotations

from dataclasses import dataclass

from .impact_errors import (
    ChangeImpactCompatibilityError,
    ChangeImpactValidationError,
)


@dataclass(frozen=True, slots=True)
class ImpactPolicy:
    schema_version: str = "1.0"
    allow_state_mutation: bool = False
    allow_execution: bool = False
    allow_authority_change: bool = False
    allow_architecture_change: bool = False
    allow_self_approval: bool = False
    allow_unbounded_analysis: bool = False

    def validate(self) -> None:
        if self.schema_version != "1.0":
            raise ChangeImpactCompatibilityError(
                self.schema_version
            )

        if any(
            (
                self.allow_state_mutation,
                self.allow_execution,
                self.allow_authority_change,
                self.allow_architecture_change,
                self.allow_self_approval,
                self.allow_unbounded_analysis,
            )
        ):
            raise ChangeImpactValidationError(
                "T17 is read-only, non-executing, bounded, and non-authoritative."
            )


__all__ = [
    "ImpactPolicy",
]
