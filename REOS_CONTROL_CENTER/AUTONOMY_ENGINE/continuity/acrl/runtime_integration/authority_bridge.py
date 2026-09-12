from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.canonical_truth.STAGE0_Canonical_Truth_Sync_Engine.authority_registry import (
    AuthorityRegistry,
)


class AuthorityBridge:
    """Read-only bridge from Stage 0 canonical authority into ACRL runtime."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.registry = AuthorityRegistry()
        self.registry.validate()

    def validate(self) -> None:
        if self.registry.architecture_authority != "FROZEN_APPROVED_ARCHITECTURE":
            raise ValueError("Architecture authority mismatch.")

        if self.registry.roadmap_authority != "REOS_CONTROL_CENTER":
            raise ValueError("Roadmap authority mismatch.")

        expected_state = "REOS_CONTROL_CENTER/data/state.json"
        if self.registry.execution_state_authority != expected_state:
            raise ValueError("Execution-state authority mismatch.")

        if self.registry.code_authority != "GIT_REPOSITORY":
            raise ValueError("Code authority mismatch.")

        if self.registry.continuity_authority != "DERIVED_FROM_EXECUTION_STATE":
            raise ValueError("Continuity authority mismatch.")

        if self.registry.chat_authority != "NONE":
            raise ValueError("Chat cannot be an authority source.")

    def as_dict(self) -> dict[str, str]:
        return self.registry.as_dict()
