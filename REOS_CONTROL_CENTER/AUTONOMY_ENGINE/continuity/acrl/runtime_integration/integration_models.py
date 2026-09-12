from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ACRLTaskDescriptor:
    task_id: str
    directory_name: str
    path: str
    exists: bool
    has_init: bool
    contract_files: tuple[str, ...]
    test_files: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return self.exists and bool(self.test_files)


@dataclass(frozen=True)
class ACRLIntegrationSnapshot:
    architecture_authority: str
    roadmap_authority: str
    execution_state_authority: str
    code_authority: str
    continuity_authority: str
    chat_authority: str
    tasks: tuple[ACRLTaskDescriptor, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "architecture_authority": self.architecture_authority,
            "roadmap_authority": self.roadmap_authority,
            "execution_state_authority": self.execution_state_authority,
            "code_authority": self.code_authority,
            "continuity_authority": self.continuity_authority,
            "chat_authority": self.chat_authority,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "directory_name": task.directory_name,
                    "path": task.path,
                    "exists": task.exists,
                    "has_init": task.has_init,
                    "contract_files": list(task.contract_files),
                    "test_files": list(task.test_files),
                    "healthy": task.healthy,
                }
                for task in self.tasks
            ],
        }

    @property
    def healthy(self) -> bool:
        return (
            self.architecture_authority == "FROZEN_APPROVED_ARCHITECTURE"
            and self.roadmap_authority == "REOS_CONTROL_CENTER"
            and self.execution_state_authority
            == "REOS_CONTROL_CENTER/data/state.json"
            and self.code_authority == "GIT_REPOSITORY"
            and self.continuity_authority == "DERIVED_FROM_EXECUTION_STATE"
            and self.chat_authority == "NONE"
            and len(self.tasks) == 30
            and all(task.healthy for task in self.tasks)
        )

