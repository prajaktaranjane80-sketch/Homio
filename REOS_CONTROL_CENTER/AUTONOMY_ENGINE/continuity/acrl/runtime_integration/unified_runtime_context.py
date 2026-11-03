from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from ..T21_Git_Repository_Read_Write_Coordination.git_read import (
    GitReader,
)
from .authority_bridge import AuthorityBridge
from .operational_runtime import load_execution_projection
from .task_registry import ACRLTaskRegistry


@dataclass(frozen=True, slots=True)
class UnifiedRuntimeContext:
    """Immutable runtime context shared across the integrated ACRL chain.

    The original authority, Git and T01-T30 fields remain compatible.

    The additive execution projection makes the current Control Center
    position available to downstream ACRL layers without requiring each
    consumer to load and interpret state.json independently.
    """

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

    # Additive fields preserve older direct constructors.
    state_integrity_sha256: str = ""

    current_gate: str = ""
    current_gate_status: str = ""

    current_task: str = ""
    current_subtask: str = ""
    current_subtask_status: str = ""

    execution_status: str = ""
    current_acceptance_criteria: tuple[str, ...] = ()

    @classmethod
    def build(
        cls,
        *,
        control_center_root: Path,
        mission_id: str,
        objective: str,
    ) -> "UnifiedRuntimeContext":
        root = Path(control_center_root).resolve()

        if not isinstance(mission_id, str) or not mission_id.strip():
            raise ValueError("mission_id is required")

        if not isinstance(objective, str) or not objective.strip():
            raise ValueError("objective is required")

        mission_id = mission_id.strip()
        objective = objective.strip()

        # Capture repository identity before reconstructing the context.
        git_reader = GitReader(root)
        git_before = git_reader.snapshot()

        # Keep the existing authority boundary.
        authority = AuthorityBridge(root)
        authority.validate()
        authority_data = authority.as_dict()

        # Use the one canonical state reader and integrity implementation.
        execution = load_execution_projection(
            root / "data" / "state.json"
        )

        # Keep the existing canonical T01-T30 registry.
        acrl_root = (
            root
            / "AUTONOMY_ENGINE"
            / "continuity"
            / "acrl"
        )

        tasks = ACRLTaskRegistry(
            acrl_root
        ).validate()

        task_ids = tuple(
            task.task_id
            for task in tasks
        )

        # Capture repository identity again to reject a moving snapshot.
        git_after = git_reader.snapshot()

        stable_repository = (
            git_before.branch == git_after.branch
            and git_before.head_sha == git_after.head_sha
            and git_before.fingerprint == git_after.fingerprint
            and (
                git_before.working_tree_clean
                == git_after.working_tree_clean
            )
        )

        if not stable_repository:
            raise RuntimeError(
                "Repository changed while UnifiedRuntimeContext was "
                "being reconstructed. Retry from a fresh repository view."
            )

        git_snapshot = git_after
        execution_data = execution.to_dict()

        payload = {
            "schema_version": "1.0",
            "mission_id": mission_id,
            "objective": objective,
            "control_center_root": str(root),
            "authority": authority_data,
            "execution": execution_data,
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
                ensure_ascii=False,
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
                authority_data["execution_state_authority"]
            ),
            code_authority=(
                authority_data["code_authority"]
            ),
            continuity_authority=(
                authority_data["continuity_authority"]
            ),
            chat_authority=(
                authority_data["chat_authority"]
            ),

            git_branch=git_snapshot.branch,
            git_head_sha=git_snapshot.head_sha,
            git_worktree_clean=(
                git_snapshot.working_tree_clean
            ),
            git_fingerprint=git_snapshot.fingerprint,

            acrl_task_ids=task_ids,
            context_fingerprint=context_fingerprint,

            state_integrity_sha256=(
                execution.state_integrity_sha256
            ),

            current_gate=execution.current_gate,
            current_gate_status=execution.current_gate_status,

            current_task=execution.current_task,
            current_subtask=execution.current_subtask,
            current_subtask_status=execution.current_subtask_status,

            execution_status=execution.execution_status,
            current_acceptance_criteria=(
                execution.current_acceptance_criteria
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible compact runtime context."""

        return {
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "objective": self.objective,
            "control_center_root": self.control_center_root,

            "architecture_authority": (
                self.architecture_authority
            ),
            "roadmap_authority": (
                self.roadmap_authority
            ),
            "execution_state_authority": (
                self.execution_state_authority
            ),
            "code_authority": self.code_authority,
            "continuity_authority": (
                self.continuity_authority
            ),
            "chat_authority": self.chat_authority,

            "git_branch": self.git_branch,
            "git_head_sha": self.git_head_sha,
            "git_worktree_clean": (
                self.git_worktree_clean
            ),
            "git_fingerprint": self.git_fingerprint,

            "acrl_task_ids": list(self.acrl_task_ids),

            "state_integrity_sha256": (
                self.state_integrity_sha256
            ),

            "current_gate": self.current_gate,
            "current_gate_status": self.current_gate_status,

            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "current_subtask_status": (
                self.current_subtask_status
            ),

            "execution_status": self.execution_status,
            "current_acceptance_criteria": list(
                self.current_acceptance_criteria
            ),

            "context_fingerprint": self.context_fingerprint,
        }


__all__ = [
    "UnifiedRuntimeContext",
]
