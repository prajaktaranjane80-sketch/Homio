"""ACRL T03 â€” Execution State Reconstruction.

Read-only reconstruction of the current REOS execution state.

Authoritative source:
    REOS_CONTROL_CENTER/data/state.json

This module does not:
    - create another state store
    - modify controller state
    - advance gates
    - complete subtasks
    - approve gates
    - use chat history as authority

Its sole responsibility is to reconstruct a deterministic,
compact execution snapshot for autonomous continuation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class StateReconstructionError(RuntimeError):
    """Base error for state reconstruction failures."""


class StateReconstructionSourceError(StateReconstructionError):
    """Raised when authoritative state cannot be loaded."""


class StateReconstructionIntegrityError(StateReconstructionError):
    """Raised when authoritative state is structurally invalid."""


@dataclass(frozen=True)
class ExecutionStateSnapshot:
    """Immutable current execution-state projection."""

    phase: str
    gate_id: str
    gate_name: str
    gate_status: str

    current_task: str
    current_subtask: str
    current_subtask_status: str

    completed_subtasks: tuple[str, ...]
    pending_subtasks: tuple[str, ...]
    future_gates: tuple[str, ...]

    state_schema_version: int
    controller_version: str

    canonical_source: str
    source_state_sha256: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable state snapshot."""

        return {
            "schema_version": "1.0",
            "phase": self.phase,
            "gate": {
                "id": self.gate_id,
                "name": self.gate_name,
                "status": self.gate_status,
            },
            "execution": {
                "current_task": self.current_task,
                "current_subtask": self.current_subtask,
                "current_subtask_status": (
                    self.current_subtask_status
                ),
                "completed_subtasks": list(self.completed_subtasks),
                "pending_subtasks": list(self.pending_subtasks),
            },
            "future_gates": list(self.future_gates),
            "authority": {
                "canonical_source": self.canonical_source,
                "state_schema_version": self.state_schema_version,
                "controller_version": self.controller_version,
            },
            "source_state_sha256": self.source_state_sha256,
        }

    def resume_context(self) -> str:
        """Return compact context sufficient to resume execution."""

        return "\n".join(
            (
                "REOS EXECUTION STATE SNAPSHOT v1.0",
                "=" * 58,
                f"PHASE={self.phase}",
                f"GATE={self.gate_id}",
                f"GATE_NAME={self.gate_name}",
                f"GATE_STATUS={self.gate_status}",
                f"CURRENT_TASK={self.current_task}",
                f"CURRENT_SUBTASK={self.current_subtask}",
                f"SUBTASK_STATUS={self.current_subtask_status}",
                (
                    "COMPLETED_SUBTASKS="
                    + ",".join(self.completed_subtasks)
                ),
                (
                    "PENDING_SUBTASKS="
                    + ",".join(self.pending_subtasks)
                ),
                "AUTHORITY=data/state.json",
                f"STATE_SHA256={self.source_state_sha256}",
            )
        )


class ExecutionStateReconstructor:
    """Reconstruct current execution state from controller state."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[4]
        else:
            self.root = Path(control_center_root)

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise StateReconstructionSourceError(
                f"Authoritative state not found: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateReconstructionSourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(state, dict):
            raise StateReconstructionSourceError(
                "Authoritative state must contain a JSON object."
            )

        return state

    @staticmethod
    def _string(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> str:
        value = mapping.get(key)

        if not isinstance(value, str) or not value.strip():
            raise StateReconstructionIntegrityError(
                f"{section}.{key} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _int(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> int:
        value = mapping.get(key)

        if isinstance(value, bool) or not isinstance(value, int):
            raise StateReconstructionIntegrityError(
                f"{section}.{key} must be an integer."
            )

        return value

    @staticmethod
    def _string_tuple(
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise StateReconstructionIntegrityError(
                f"{field_name} must be a list."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise StateReconstructionIntegrityError(
                    f"{field_name} contains an invalid entry."
                )

            result.append(item.strip())

        return tuple(result)

    @staticmethod
    def _sha256(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise StateReconstructionSourceError(
                f"Unable to fingerprint state: {path}"
            ) from exc

    def reconstruct(self) -> ExecutionStateSnapshot:
        """Build an immutable snapshot of the current execution state."""

        state = self._read_state(self.state_path)

        meta = state.get("meta")
        phases = state.get("phases")
        roadmap = state.get("roadmap")
        current_gate = state.get("current_gate")
        current_task = state.get("current_task")
        current_subtask = state.get("current_subtask")
        subtask_status = state.get("subtask_status")

        if not isinstance(meta, Mapping):
            raise StateReconstructionIntegrityError(
                "state.meta must be an object."
            )

        if not isinstance(phases, Mapping):
            raise StateReconstructionIntegrityError(
                "state.phases must be an object."
            )

        if not isinstance(roadmap, Mapping):
            raise StateReconstructionIntegrityError(
                "state.roadmap must be an object."
            )

        phase = self._string(phases, "current", "phases")

        gate_id = self._string(
            current_gate,
            "id",
            "current_gate",
        )

        gate_name = self._string(
            current_gate,
            "name",
            "current_gate",
        )

        gate_status = self._string(
            current_gate,
            "status",
            "current_gate",
        )

        task = self._string(
            current_task,
            "name",
            "current_task",
        )

        subtask = self._string(
            current_subtask,
            "id",
            "current_subtask",
        )

        status = self._string(
            subtask_status,
            "status",
            "subtask_status",
        )

        completed = self._string_tuple(
            current_gate.get("completed_subtasks"),
            "current_gate.completed_subtasks",
        )

        pending = self._string_tuple(
            current_gate.get("pending_subtasks"),
            "current_gate.pending_subtasks",
        )

        future = self._string_tuple(
            roadmap.get("future_gates"),
            "roadmap.future_gates",
        )

        if subtask in completed:
            raise StateReconstructionIntegrityError(
                "Current subtask cannot also be completed."
            )

        if subtask not in pending and status != "DONE":
            raise StateReconstructionIntegrityError(
                "Current subtask must be pending unless marked DONE."
            )

        return ExecutionStateSnapshot(
            phase=phase,
            gate_id=gate_id,
            gate_name=gate_name,
            gate_status=gate_status,
            current_task=task,
            current_subtask=subtask,
            current_subtask_status=status,
            completed_subtasks=completed,
            pending_subtasks=pending,
            future_gates=future,
            state_schema_version=self._int(
                meta,
                "schema_version",
                "meta",
            ),
            controller_version=self._string(
                meta,
                "control_center_version",
                "meta",
            ),
            canonical_source="data/state.json",
            source_state_sha256=self._sha256(self.state_path),
        )


def reconstruct_execution_state(
    control_center_root: Path | str | None = None,
) -> ExecutionStateSnapshot:
    """Convenience API for execution-state reconstruction."""

    return ExecutionStateReconstructor(control_center_root).reconstruct()


__all__ = [
    "ExecutionStateReconstructor",
    "ExecutionStateSnapshot",
    "StateReconstructionError",
    "StateReconstructionIntegrityError",
    "StateReconstructionSourceError",
    "reconstruct_execution_state",
]
