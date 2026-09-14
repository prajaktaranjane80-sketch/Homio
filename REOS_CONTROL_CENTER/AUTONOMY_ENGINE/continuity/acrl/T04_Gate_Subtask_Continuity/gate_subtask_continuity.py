"""ACRL T04 — Gate / Subtask Continuity.

Read-only continuity projection built on the canonical T03 execution-state
reconstruction. The authoritative source remains:

    REOS_CONTROL_CENTER/data/state.json

T04 answers one narrow continuity question:

    Within the authoritative current gate, what work is complete,
    what is current, and what is the first incomplete unit that
    may be resumed?

This module never mutates state, advances gates, completes subtasks,
or creates a second execution-state authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from AUTONOMY_ENGINE.continuity.acrl.T03_State_Reconstruction.state_reconstruction import (
    ExecutionStateReconstructor,
    StateReconstructionError,
)


class GateContinuityError(RuntimeError):
    """Base error for gate/subtask continuity failures."""


class GateContinuitySourceError(GateContinuityError):
    """Raised when authoritative execution state cannot be reconstructed."""


class GateContinuityIntegrityError(GateContinuityError):
    """Raised when authoritative gate/subtask data is structurally invalid."""


class GateContinuityConflictError(GateContinuityError):
    """Raised when current work disagrees with the authoritative order."""


class ResumeDecision(str, Enum):
    RESUME = "RESUME"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class GateSubtaskContinuity:
    """Immutable gate/subtask continuity projection."""

    gate_id: str
    gate_name: str
    gate_status: str

    current_task: str
    current_subtask: str
    current_subtask_status: str

    subtask_index: int
    total_subtasks: int

    completed_subtasks: tuple[str, ...]
    pending_subtasks: tuple[str, ...]
    first_incomplete_authoritative_unit: str

    resume_decision: ResumeDecision
    continuity_fingerprint: str
    source_state_sha256: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable continuity projection."""

        return {
            "schema_version": "2.0",
            "gate": {
                "id": self.gate_id,
                "name": self.gate_name,
                "status": self.gate_status,
            },
            "execution": {
                "current_task": self.current_task,
                "current_subtask": self.current_subtask,
                "current_subtask_status": self.current_subtask_status,
            },
            "subtask": {
                "index": self.subtask_index,
                "total": self.total_subtasks,
                "first_incomplete_authoritative_unit": (
                    self.first_incomplete_authoritative_unit
                ),
            },
            "continuity": {
                "completed_subtasks": list(self.completed_subtasks),
                "pending_subtasks": list(self.pending_subtasks),
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

        return self.resume_decision is ResumeDecision.RESUME


class GateSubtaskContinuityReader:
    """Reconstruct T04 continuity from the authoritative T03 projection."""

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
    def _load_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise GateContinuitySourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise GateContinuitySourceError(
                f"Authoritative state is not a file: {path}"
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
    def _string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise GateContinuityIntegrityError(
                f"{field_name} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _continuity_fingerprint(
        gate_id: str,
        gate_status: str,
        current_task: str,
        current_subtask: str,
        current_subtask_status: str,
        ordered_subtasks: tuple[str, ...],
        completed_subtasks: tuple[str, ...],
        pending_subtasks: tuple[str, ...],
        first_incomplete: str,
    ) -> str:
        payload = {
            "gate_id": gate_id,
            "gate_status": gate_status,
            "current_task": current_task,
            "current_subtask": current_subtask,
            "current_subtask_status": current_subtask_status,
            "ordered_subtasks": ordered_subtasks,
            "completed_subtasks": completed_subtasks,
            "pending_subtasks": pending_subtasks,
            "first_incomplete": first_incomplete,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def reconstruct(self) -> GateSubtaskContinuity:
        """Reconstruct authoritative gate/subtask continuity."""

        try:
            execution_snapshot = ExecutionStateReconstructor(
                self.root
            ).reconstruct()
        except StateReconstructionError as exc:
            raise GateContinuitySourceError(
                "T04 requires a valid T03 execution-state reconstruction."
            ) from exc

        state = self._load_state(self.state_path)

        gate_plans = state.get("gate_plans")

        if not isinstance(gate_plans, Mapping):
            raise GateContinuityIntegrityError(
                "state.gate_plans must be an object."
            )

        gate = gate_plans.get(execution_snapshot.gate_id)

        if not isinstance(gate, Mapping):
            raise GateContinuityIntegrityError(
                "Current gate is missing from gate_plans: "
                f"{execution_snapshot.gate_id}"
            )

        gate_name = self._string(
            gate.get("name"),
            f"gate_plans[{execution_snapshot.gate_id}].name",
        )

        gate_status = self._string(
            gate.get("status"),
            f"gate_plans[{execution_snapshot.gate_id}].status",
        ).upper()

        subtasks_raw = gate.get("subtasks")

        if not isinstance(subtasks_raw, list) or not subtasks_raw:
            raise GateContinuityIntegrityError(
                f"gate_plans[{execution_snapshot.gate_id}].subtasks "
                "must be a non-empty list."
            )

        ordered: list[str] = []
        statuses: dict[str, str] = {}

        for item in subtasks_raw:
            if not isinstance(item, Mapping):
                raise GateContinuityIntegrityError(
                    f"gate_plans[{execution_snapshot.gate_id}].subtasks "
                    "contains an invalid entry."
                )

            subtask_id = self._string(
                item.get("id"),
                "subtask.id",
            )

            status = self._string(
                item.get("status"),
                f"subtask[{subtask_id}].status",
            ).upper()

            if subtask_id in statuses:
                raise GateContinuityIntegrityError(
                    f"Duplicate subtask id: {subtask_id}"
                )

            if status not in {"PENDING", "CURRENT", "DONE"}:
                raise GateContinuityIntegrityError(
                    f"Invalid status for {subtask_id}: {status}"
                )

            ordered.append(subtask_id)
            statuses[subtask_id] = status

        completed = tuple(
            subtask_id
            for subtask_id in ordered
            if statuses[subtask_id] == "DONE"
        )

        pending = tuple(
            subtask_id
            for subtask_id in ordered
            if statuses[subtask_id] != "DONE"
        )

        if not pending:
            raise GateContinuityConflictError(
                "Current gate contains no incomplete authoritative subtask."
            )

        first_incomplete = pending[0]
        current_subtask = execution_snapshot.current_subtask
        current_status = statuses.get(current_subtask)

        if current_status is None:
            raise GateContinuityConflictError(
                "Current subtask is not present in the current gate plan: "
                f"{current_subtask}"
            )

        if current_status == "DONE":
            raise GateContinuityConflictError(
                "Current subtask is already completed; "
                "authoritative position is stale."
            )

        if current_subtask != first_incomplete:
            raise GateContinuityConflictError(
                "Current subtask is stale: the first incomplete "
                f"authoritative unit is {first_incomplete}, "
                f"not {current_subtask}."
            )

        if execution_snapshot.current_subtask_status != current_status:
            raise GateContinuityConflictError(
                "T03 and gate plan disagree on current subtask status."
            )

        if gate_status in {"COMPLETE", "COMPLETED", "DONE"}:
            raise GateContinuityConflictError(
                "Current gate is completed but still has an incomplete subtask."
            )

        ordered_tuple = tuple(ordered)

        fingerprint = self._continuity_fingerprint(
            execution_snapshot.gate_id,
            gate_status,
            execution_snapshot.current_task,
            current_subtask,
            current_status,
            ordered_tuple,
            completed,
            pending,
            first_incomplete,
        )

        return GateSubtaskContinuity(
            gate_id=execution_snapshot.gate_id,
            gate_name=gate_name,
            gate_status=gate_status,
            current_task=execution_snapshot.current_task,
            current_subtask=current_subtask,
            current_subtask_status=current_status,
            subtask_index=ordered.index(current_subtask) + 1,
            total_subtasks=len(ordered),
            completed_subtasks=completed,
            pending_subtasks=pending,
            first_incomplete_authoritative_unit=first_incomplete,
            resume_decision=ResumeDecision.RESUME,
            continuity_fingerprint=fingerprint,
            source_state_sha256=execution_snapshot.source_state_sha256,
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
