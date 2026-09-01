"""ACRL T04 — Gate / Subtask Continuity.

Provides a deterministic, read-only continuity projection for the
current REOS gate and subtask.

The authoritative execution state remains:
    REOS_CONTROL_CENTER/data/state.json

This module does not:
    - modify state.json
    - complete subtasks
    - advance gates
    - approve gates
    - freeze gates
    - create a second execution state
    - replace REOS_CONTROL_CENTER

It determines whether the current execution position is structurally
safe to resume.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class GateContinuityError(RuntimeError):
    """Base error for gate/subtask continuity failures."""


class GateContinuitySourceError(GateContinuityError):
    """Raised when authoritative state cannot be loaded."""


class GateContinuityIntegrityError(GateContinuityError):
    """Raised when continuity data is structurally invalid."""


class GateContinuityConflictError(GateContinuityError):
    """Raised when gate/subtask state contains a conflict."""


class ResumeDecision(str, Enum):
    RESUME = "RESUME"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class GateSubtaskContinuity:
    """Immutable gate/subtask continuity projection."""

    gate_id: str
    gate_name: str
    gate_status: str

    current_subtask: str
    current_subtask_status: str

    subtask_index: int
    total_subtasks: int

    completed_subtasks: tuple[str, ...]
    remaining_subtasks: tuple[str, ...]

    resume_decision: ResumeDecision
    continuity_fingerprint: str
    source_state_sha256: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable projection."""

        return {
            "schema_version": "1.0",
            "gate": {
                "id": self.gate_id,
                "name": self.gate_name,
                "status": self.gate_status,
            },
            "subtask": {
                "current": self.current_subtask,
                "status": self.current_subtask_status,
                "index": self.subtask_index,
                "total": self.total_subtasks,
            },
            "continuity": {
                "completed_subtasks": list(self.completed_subtasks),
                "remaining_subtasks": list(self.remaining_subtasks),
                "resume_decision": self.resume_decision.value,
                "fingerprint": self.continuity_fingerprint,
            },
            "authority": {
                "canonical_source": "data/state.json",
                "source_state_sha256": self.source_state_sha256,
            },
        }

    def can_resume(self) -> bool:
        """Return whether execution may safely continue."""

        return self.resume_decision == ResumeDecision.RESUME


class GateSubtaskContinuityReader:
    """Read-only gate/subtask continuity evaluator."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[3]
        else:
            self.root = Path(control_center_root)

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise GateContinuitySourceError(
                f"Authoritative state not found: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GateContinuitySourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(state, dict):
            raise GateContinuitySourceError(
                "Authoritative state must contain a JSON object."
            )

        return state

    @staticmethod
    def _required_string(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> str:
        value = mapping.get(key)

        if not isinstance(value, str) or not value.strip():
            raise GateContinuityIntegrityError(
                f"{section}.{key} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _string_list(
        value: Any,
        field_name: str,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise GateContinuityIntegrityError(
                f"{field_name} must be a list."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise GateContinuityIntegrityError(
                    f"{field_name} contains an invalid entry."
                )

            result.append(item.strip())

        return tuple(result)

    @staticmethod
    def _fingerprint(
        gate_id: str,
        gate_status: str,
        current_subtask: str,
        current_subtask_status: str,
        completed: tuple[str, ...],
        remaining: tuple[str, ...],
    ) -> str:
        payload = {
            "gate_id": gate_id,
            "gate_status": gate_status,
            "current_subtask": current_subtask,
            "current_subtask_status": current_subtask_status,
            "completed": completed,
            "remaining": remaining,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _state_sha256(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise GateContinuitySourceError(
                f"Unable to fingerprint state: {path}"
            ) from exc

    def reconstruct(self) -> GateSubtaskContinuity:
        """Evaluate gate/subtask continuity from authoritative state."""

        state = self._read_state(self.state_path)

        current_gate = state.get("current_gate")
        current_subtask = state.get("current_subtask")
        subtask_status = state.get("subtask_status")

        if not isinstance(current_gate, Mapping):
            raise GateContinuityIntegrityError(
                "state.current_gate must be an object."
            )

        if not isinstance(current_subtask, Mapping):
            raise GateContinuityIntegrityError(
                "state.current_subtask must be an object."
            )

        if not isinstance(subtask_status, Mapping):
            raise GateContinuityIntegrityError(
                "state.subtask_status must be an object."
            )

        gate_id = self._required_string(
            current_gate,
            "id",
            "current_gate",
        )

        gate_name = self._required_string(
            current_gate,
            "name",
            "current_gate",
        )

        gate_status = self._required_string(
            current_gate,
            "status",
            "current_gate",
        )

        subtask_id = self._required_string(
            current_subtask,
            "id",
            "current_subtask",
        )

        status = self._required_string(
            subtask_status,
            "status",
            "subtask_status",
        )

        all_subtasks = self._string_list(
            current_gate.get("subtasks"),
            "current_gate.subtasks",
        )

        completed = self._string_list(
            current_gate.get("completed_subtasks"),
            "current_gate.completed_subtasks",
        )

        pending = self._string_list(
            current_gate.get("pending_subtasks"),
            "current_gate.pending_subtasks",
        )

        # If the authoritative state does not expose an explicit
        # subtasks list, derive the ordered set from completed + pending.
        if not all_subtasks:
            ordered: list[str] = []

            for item in (*completed, *pending):
                if item not in ordered:
                    ordered.append(item)

            all_subtasks = tuple(ordered)

        if not all_subtasks:
            raise GateContinuityIntegrityError(
                "No gate subtasks are available for continuity."
            )

        if subtask_id in completed:
            raise GateContinuityConflictError(
                "Current subtask is already marked completed."
            )

        if subtask_id not in all_subtasks:
            raise GateContinuityConflictError(
                "Current subtask does not belong to the current gate."
            )

        if pending and subtask_id not in pending and status != "DONE":
            raise GateContinuityConflictError(
                "Current subtask is neither pending nor completed."
            )

        duplicate_completed = len(completed) != len(set(completed))

        if duplicate_completed:
            raise GateContinuityIntegrityError(
                "Completed subtasks contain duplicates."
            )

        duplicate_pending = len(pending) != len(set(pending))

        if duplicate_pending:
            raise GateContinuityIntegrityError(
                "Pending subtasks contain duplicates."
            )

        overlap = set(completed).intersection(pending)

        if overlap:
            raise GateContinuityConflictError(
                "A subtask cannot be both completed and pending."
            )

        try:
            subtask_index = all_subtasks.index(subtask_id) + 1
        except ValueError as exc:
            raise GateContinuityConflictError(
                "Current subtask position cannot be reconstructed."
            ) from exc

        remaining = tuple(
            item
            for item in all_subtasks
            if item not in completed
        )

        fingerprint = self._fingerprint(
            gate_id,
            gate_status,
            subtask_id,
            status,
            completed,
            remaining,
        )

        return GateSubtaskContinuity(
            gate_id=gate_id,
            gate_name=gate_name,
            gate_status=gate_status,
            current_subtask=subtask_id,
            current_subtask_status=status,
            subtask_index=subtask_index,
            total_subtasks=len(all_subtasks),
            completed_subtasks=completed,
            remaining_subtasks=remaining,
            resume_decision=ResumeDecision.RESUME,
            continuity_fingerprint=fingerprint,
            source_state_sha256=self._state_sha256(
                self.state_path
            ),
        )


def reconstruct_gate_subtask_continuity(
    control_center_root: Path | str | None = None,
) -> GateSubtaskContinuity:
    """Convenience API for gate/subtask continuity."""

    return GateSubtaskContinuityReader(
        control_center_root
    ).reconstruct()


__all__ = [
    "GateContinuityConflictError",
    "GateContinuityError",
    "GateContinuityIntegrityError",
    "GateContinuitySourceError",
    "GateSubtaskContinuity",
    "GateSubtaskContinuityReader",
    "ResumeDecision",
    "reconstruct_gate_subtask_continuity",
]