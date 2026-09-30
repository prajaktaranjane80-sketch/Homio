from __future__ import annotations

from pathlib import Path


class AuthorityBridge:
    """Read-only ACRL authority bridge.

    ACRL is bound directly to the canonical REOS Control Center state.
    No secondary canonical-truth or synchronization engine is consulted.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()

        self._authority = {
            "project": "HOMIO / REOS",
            "architecture_authority": "FROZEN_APPROVED_ARCHITECTURE",
            "roadmap_authority": "REOS_CONTROL_CENTER",
            "execution_state_authority": "REOS_CONTROL_CENTER/data/state.json",
            "code_authority": "GIT_REPOSITORY",
            "continuity_authority": "DERIVED_FROM_EXECUTION_STATE",
            "chat_authority": "NONE",
            "schema_version": "1.0",
        }

    def validate(self) -> None:
        state_path = self.project_root / "data" / "state.json"

        if not state_path.is_file():
            raise ValueError(
                "Canonical REOS state.json is missing."
            )

        if (
            self._authority["architecture_authority"]
            != "FROZEN_APPROVED_ARCHITECTURE"
        ):
            raise ValueError(
                "Architecture authority mismatch."
            )

        if (
            self._authority["roadmap_authority"]
            != "REOS_CONTROL_CENTER"
        ):
            raise ValueError(
                "Roadmap authority mismatch."
            )

        if (
            self._authority["execution_state_authority"]
            != "REOS_CONTROL_CENTER/data/state.json"
        ):
            raise ValueError(
                "Execution-state authority mismatch."
            )

        if (
            self._authority["code_authority"]
            != "GIT_REPOSITORY"
        ):
            raise ValueError(
                "Code authority mismatch."
            )

        if (
            self._authority["continuity_authority"]
            != "DERIVED_FROM_EXECUTION_STATE"
        ):
            raise ValueError(
                "Continuity authority mismatch."
            )

        if self._authority["chat_authority"] != "NONE":
            raise ValueError(
                "Chat cannot be an authority source."
            )

    def as_dict(self) -> dict[str, str]:
        return dict(self._authority)