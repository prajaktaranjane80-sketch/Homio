from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from ..T21_Git_Repository_Read_Write_Coordination.git_read import GitReader
from .authority_bridge import AuthorityBridge
from .task_registry import ACRLTaskRegistry


@dataclass(frozen=True, slots=True)
class UnifiedRuntimeContext:
    """Immutable runtime context shared across the integrated ACRL chain."""

    schema_version: str
    mission_id: str
    objective: str
    control_center_root: str

    architecture_authority: str
    roadmap_authority: str
    execution_state_authority: str
    code_authority: str
    continuity_authority: str
    chat_authority: str

    git_branch: str
    git_head_sha: str
    git_worktree_clean: bool
    git_fingerprint: str

    acrl_task_ids: tuple[str, ...]
    context_fingerprint: str

    @classmethod
    def build(
        cls,
        *,
        control_center_root: Path,
        mission_id: str,
        objective: str,
    ) -> "UnifiedRuntimeContext":
        root = Path(control_center_root).resolve()
        mission_id = mission_id.strip()
        objective = objective.strip()

        if not mission_id:
            raise ValueError("mission_id is required")

        if not objective:
            raise ValueError("objective is required")

        authority = AuthorityBridge(root)
        authority.validate()
        authority_data = authority.as_dict()

        acrl_root = (
            root
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl"
        )

        tasks = ACRLTaskRegistry(acrl_root).validate()
        task_ids = tuple(
            task.task_id for task in tasks
        )

        git_snapshot = GitReader(root).snapshot()

        payload = {
            "schema_version": "1.0",
            "mission_id": mission_id,
            "objective": objective,
            "control_center_root": str(root),
            "authority": authority_data,
            "git": {
                "branch": git_snapshot.branch,
                "head_sha": git_snapshot.head_sha,
                "working_tree_clean": (
                    git_snapshot.working_tree_clean
                ),
                "fingerprint": git_snapshot.fingerprint,
            },
            "acrl_task_ids": task_ids,
        }

        context_fingerprint = sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        return cls(
            schema_version="1.0",
            mission_id=mission_id,
            objective=objective,
            control_center_root=str(root),
            architecture_authority=(
                authority_data["architecture_authority"]
            ),
            roadmap_authority=(
                authority_data["roadmap_authority"]
            ),
            execution_state_authority=(
                authority_data[
                    "execution_state_authority"
                ]
            ),
            code_authority=(
                authority_data["code_authority"]
            ),
            continuity_authority=(
                authority_data[
                    "continuity_authority"
                ]
            ),
            chat_authority=(
                authority_data["chat_authority"]
            ),
            git_branch=git_snapshot.branch,
            git_head_sha=git_snapshot.head_sha,
            git_worktree_clean=(
                git_snapshot.working_tree_clean
            ),
            git_fingerprint=(
                git_snapshot.fingerprint
            ),
            acrl_task_ids=task_ids,
            context_fingerprint=(
                context_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "objective": self.objective,
            "control_center_root": (
                self.control_center_root
            ),
            "architecture_authority": (
                self.architecture_authority
            ),
            "roadmap_authority": (
                self.roadmap_authority
            ),
            "execution_state_authority": (
                self.execution_state_authority
            ),
            "code_authority": (
                self.code_authority
            ),
            "continuity_authority": (
                self.continuity_authority
            ),
            "chat_authority": (
                self.chat_authority
            ),
            "git_branch": self.git_branch,
            "git_head_sha": self.git_head_sha,
            "git_worktree_clean": (
                self.git_worktree_clean
            ),
            "git_fingerprint": (
                self.git_fingerprint
            ),
            "acrl_task_ids": list(
                self.acrl_task_ids
            ),
            "context_fingerprint": (
                self.context_fingerprint
            ),
        }
