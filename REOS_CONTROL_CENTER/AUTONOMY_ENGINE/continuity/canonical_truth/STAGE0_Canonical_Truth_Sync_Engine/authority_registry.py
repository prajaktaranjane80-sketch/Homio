from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityRegistry:
    project: str = "HOMIO / REOS"
    architecture_authority: str = "FROZEN_APPROVED_ARCHITECTURE"
    execution_state_authority: str = "REOS_CONTROL_CENTER/data/state.json"
    code_authority: str = "GIT_REPOSITORY"
    continuity_authority: str = "DERIVED_FROM_EXECUTION_STATE"
    roadmap_authority: str = "REOS_CONTROL_CENTER"
    chat_authority: str = "NONE"
    schema_version: str = "1.0"

    def as_dict(self) -> dict[str, str]:
        return {
            "project": self.project,
            "architecture_authority": self.architecture_authority,
            "execution_state_authority": self.execution_state_authority,
            "code_authority": self.code_authority,
            "continuity_authority": self.continuity_authority,
            "roadmap_authority": self.roadmap_authority,
            "chat_authority": self.chat_authority,
            "schema_version": self.schema_version,
        }

    def validate(self) -> None:
        if self.chat_authority != "NONE":
            raise ValueError("Chat must never be an authority source.")
        if "state/state.json" in self.execution_state_authority:
            raise ValueError("Invalid canonical state path.")
