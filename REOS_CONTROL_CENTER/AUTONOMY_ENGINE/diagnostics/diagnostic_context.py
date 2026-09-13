from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class DiagnosticContext:
    """
    Bounded diagnostic context.

    This is an observational snapshot only.
    It is NOT a replacement for ACRL context reconstruction.
    """

    project_root: Path
    control_center_root: Path
    state_file: Path
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    architecture_authority: str
    execution_authority: str
    continuity_authority: str
    evidence_budget: int = 32

    def position(self) -> tuple[str | None, str | None, str | None]:
        return (
            self.current_gate,
            self.current_task,
            self.current_subtask,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "control_center_root": str(self.control_center_root),
            "state_file": str(self.state_file),
            "current_gate": self.current_gate,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "architecture_authority": self.architecture_authority,
            "execution_authority": self.execution_authority,
            "continuity_authority": self.continuity_authority,
            "evidence_budget": self.evidence_budget,
        }

    @classmethod
    def from_state(
        cls,
        *,
        project_root: Path,
        control_center_root: Path,
        state_file: Path,
        state: Mapping[str, Any],
    ) -> "DiagnosticContext":
        gate = (
            state.get("current_gate")
            or state.get("gate")
            or state.get("active_gate")
        )

        task = (
            state.get("current_task")
            or state.get("task")
            or state.get("active_task")
        )

        subtask = (
            state.get("current_subtask")
            or state.get("subtask")
            or state.get("active_subtask")
        )

        return cls(
            project_root=project_root,
            control_center_root=control_center_root,
            state_file=state_file,
            current_gate=str(gate) if gate is not None else None,
            current_task=str(task) if task is not None else None,
            current_subtask=str(subtask) if subtask is not None else None,
            architecture_authority="FROZEN_APPROVED_ARCHITECTURE",
            execution_authority="REOS_CONTROL_CENTER",
            continuity_authority="ACRL",
        )
