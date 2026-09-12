from __future__ import annotations

from pathlib import Path

from .authority_bridge import AuthorityBridge
from .integration_models import ACRLIntegrationSnapshot
from .task_registry import ACRLTaskRegistry


class ACRLRuntime:
    """
    Final ACRL integration boundary.

    Responsibilities:
    - consume canonical Stage 0 authority
    - discover T01–T30
    - validate their presence/package/contracts
    - expose one deterministic integration snapshot

    It does NOT:
    - mutate state.json
    - approve gates
    - execute shell commands
    - skip ACRL tasks
    - invent new T31+ tasks
    """

    def __init__(self, control_center_root: Path) -> None:
        self.control_center_root = Path(control_center_root)
        self.acrl_root = (
            self.control_center_root
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl"
        )

        self.authority = AuthorityBridge(self.control_center_root)
        self.tasks = ACRLTaskRegistry(self.acrl_root)

    def build_snapshot(self) -> ACRLIntegrationSnapshot:
        self.authority.validate()

        task_descriptors = self.tasks.validate()
        authority = self.authority.as_dict()

        return ACRLIntegrationSnapshot(
            architecture_authority=authority["architecture_authority"],
            roadmap_authority=authority["roadmap_authority"],
            execution_state_authority=authority[
                "execution_state_authority"
            ],
            code_authority=authority["code_authority"],
            continuity_authority=authority[
                "continuity_authority"
            ],
            chat_authority=authority["chat_authority"],
            tasks=task_descriptors,
        )

    def validate(self) -> bool:
        return self.build_snapshot().healthy
