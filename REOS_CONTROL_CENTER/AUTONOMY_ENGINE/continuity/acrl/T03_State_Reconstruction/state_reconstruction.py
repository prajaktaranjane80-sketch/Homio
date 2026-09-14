"""ACRL T03 - Execution State Reconstruction.

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
                "current_subtask_status": self.current_subtask_status,
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
                "COMPLETED_SUBTASKS=" + ",".join(
                    self.completed_subtasks
                ),
                "PENDING_SUBTASKS=" + ",".join(
                    self.pending_subtasks
                ),
                "AUTHORITY=data/state.json",
                f"STATE_SHA256={self.source_state_sha256}",
            )
        )


class ExecutionStateReconstructor:
    """Reconstruct current execution state from canonical controller state."""

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

        if not path.is_file():
            raise StateReconstructionSourceError(
                f"Authoritative state is not a file: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
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
    def _sha256(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise StateReconstructionSourceError(
                f"Unable to fingerprint state: {path}"
            ) from exc

    @staticmethod
    def _future_gates(
        execution_plan: Mapping[str, Any],
        current_gate_id: str,
    ) -> tuple[str, ...]:
        sequence = execution_plan.get(
            "authoritative_sequence",
            [],
        )

        if sequence is None:
            return ()

        if not isinstance(sequence, list):
            raise StateReconstructionIntegrityError(
                "execution_plan.authoritative_sequence "
                "must be a list."
            )

        current_index: int | None = None

        for index, item in enumerate(sequence):
            if not isinstance(item, Mapping):
                raise StateReconstructionIntegrityError(
                    "execution_plan.authoritative_sequence "
                    "contains an invalid entry."
                )

            gate = item.get("gate")

            if (
                isinstance(gate, str)
                and gate.strip() == current_gate_id
            ):
                current_index = index
                break

        if current_index is None:
            return ()

        future: list[str] = []

        for item in sequence[current_index + 1 :]:
            gate = item.get("gate")
            status = item.get("status")

            if not isinstance(gate, str) or not gate.strip():
                continue

            if (
                isinstance(status, str)
                and status.strip().upper() == "COMPLETE"
            ):
                continue

            future.append(gate.strip())

        return tuple(future)

    def reconstruct(self) -> ExecutionStateSnapshot:
        """Build an immutable snapshot from canonical state.json only."""

        state = self._read_state(self.state_path)

        meta = state.get("meta")
        phases = state.get("phases")
        execution = state.get("execution")
        gate_plans = state.get("gate_plans")
        execution_plan = state.get("execution_plan", {})
        constitution = state.get("constitution")

        if not isinstance(meta, Mapping):
            raise StateReconstructionIntegrityError(
                "state.meta must be an object."
            )

        if not isinstance(phases, Mapping):
            raise StateReconstructionIntegrityError(
                "state.phases must be an object."
            )

        if not isinstance(execution, Mapping):
            raise StateReconstructionIntegrityError(
                "state.execution must be an object."
            )

        if not isinstance(gate_plans, Mapping):
            raise StateReconstructionIntegrityError(
                "state.gate_plans must be an object."
            )

        if not isinstance(execution_plan, Mapping):
            raise StateReconstructionIntegrityError(
                "state.execution_plan must be an object."
            )

        phase = self._string(
            phases,
            "current",
            "phases",
        )

        gate_id = self._string(
            execution,
            "current_gate",
            "execution",
        )

        current_task = self._string(
            execution,
            "current_task",
            "execution",
        )

        gate = gate_plans.get(gate_id)

        if not isinstance(gate, Mapping):
            raise StateReconstructionIntegrityError(
                f"gate_plans is missing current gate: {gate_id}"
            )

        gate_name = self._string(
            gate,
            "name",
            f"gate_plans[{gate_id}]",
        )

        gate_status = self._string(
            gate,
            "status",
            f"gate_plans[{gate_id}]",
        )

        current_subtask = self._string(
            gate,
            "current_subtask",
            f"gate_plans[{gate_id}]",
        )

        subtasks = gate.get("subtasks")

        if not isinstance(subtasks, list):
            raise StateReconstructionIntegrityError(
                f"gate_plans[{gate_id}].subtasks must be a list."
            )

        completed: list[str] = []
        pending: list[str] = []
        current_subtask_status: str | None = None

        for item in subtasks:
            if not isinstance(item, Mapping):
                raise StateReconstructionIntegrityError(
                    f"gate_plans[{gate_id}].subtasks "
                    "contains an invalid entry."
                )

            subtask_id = self._string(
                item,
                "id",
                f"gate_plans[{gate_id}].subtasks",
            )

            status = self._string(
                item,
                "status",
                f"gate_plans[{gate_id}].subtasks[{subtask_id}]",
            ).upper()

            if subtask_id == current_subtask:
                current_subtask_status = status

            if status == "DONE":
                completed.append(subtask_id)
            else:
                pending.append(subtask_id)

        if current_subtask_status is None:
            raise StateReconstructionIntegrityError(
                "Current subtask is not present in gate plan: "
                f"{current_subtask}"
            )

        if current_subtask in completed:
            raise StateReconstructionIntegrityError(
                "Current subtask cannot also be completed."
            )

        if (
            current_subtask_status != "DONE"
            and current_subtask not in pending
        ):
            raise StateReconstructionIntegrityError(
                "Current subtask must be pending unless marked DONE."
            )

        canonical_source = "data/state.json"

        if isinstance(constitution, Mapping):
            declared = constitution.get("canonical_source")

            if declared != canonical_source:
                raise StateReconstructionIntegrityError(
                    "Canonical source is not data/state.json."
                )

        return ExecutionStateSnapshot(
            phase=phase,
            gate_id=gate_id,
            gate_name=gate_name,
            gate_status=gate_status,
            current_task=current_task,
            current_subtask=current_subtask,
            current_subtask_status=current_subtask_status,
            completed_subtasks=tuple(completed),
            pending_subtasks=tuple(pending),
            future_gates=self._future_gates(
                execution_plan,
                gate_id,
            ),
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
            canonical_source=canonical_source,
            source_state_sha256=self._sha256(
                self.state_path
            ),
        )


def reconstruct_execution_state(
    control_center_root: Path | str | None = None,
) -> ExecutionStateSnapshot:
    """Convenience API for execution-state reconstruction."""

    return ExecutionStateReconstructor(
        control_center_root
    ).reconstruct()


__all__ = [
    "ExecutionStateReconstructor",
    "ExecutionStateSnapshot",
    "StateReconstructionError",
    "StateReconstructionIntegrityError",
    "StateReconstructionSourceError",
    "reconstruct_execution_state",
]
