"""ACRL T14 regression policy."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RegressionPolicy:
    """Immutable safety boundary for T14."""

    schema_version: str = "1.0"
    allow_source_inspection: bool = True
    allow_pytest_plan: bool = True
    allow_test_execution: bool = False
    allow_repository_mutation: bool = False
    allow_controller_mutation: bool = False
    allow_state_mutation: bool = False
    allow_architecture_mutation: bool = False

    def validate(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("Unsupported T14 policy schema.")
        if not self.allow_source_inspection:
            raise ValueError("T14 requires source inspection.")
        if not self.allow_pytest_plan:
            raise ValueError("T14 requires pytest planning.")
        if any((self.allow_test_execution, self.allow_repository_mutation,
                self.allow_controller_mutation, self.allow_state_mutation,
                self.allow_architecture_mutation)):
            raise ValueError("T14 is read-only and cannot authorize execution or mutation.")
