from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .truth_fingerprint import digest


class StateReadError(RuntimeError):
    pass


class CanonicalStateReader:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.path = self.root / "data" / "state.json"

    def read(self) -> dict[str, Any]:
        if not self.path.is_file():
            raise StateReadError(f"Canonical state missing: {self.path}")
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StateReadError(f"Canonical state invalid: {self.path}") from exc
        if not isinstance(data, dict):
            raise StateReadError("Canonical state root must be an object.")
        return data

    def digest(self, state: dict[str, Any]) -> str:
        return digest(state)

    def execution_projection(self, state: dict[str, Any]) -> dict[str, Any]:
        execution = state.get("execution")
        if not isinstance(execution, dict):
            raise StateReadError("Canonical state has no valid execution object.")
        return {
            "current_gate": execution.get("current_gate"),
            "current_task": execution.get("current_task"),
            "current_subtask": execution.get("current_subtask"),
            "status": execution.get("status"),
            "phase": state.get("phases", {}).get("current") if isinstance(state.get("phases"), dict) else None,
        }
