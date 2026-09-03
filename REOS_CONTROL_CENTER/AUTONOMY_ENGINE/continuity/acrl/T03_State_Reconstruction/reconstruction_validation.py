"""ACRL T03 — reconstruction consistency validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .state_reconstruction import ExecutionStateSnapshot


class ReconstructionStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ReconstructionValidationReport:
    """Immutable reconstruction validation result."""

    status: ReconstructionStatus
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.status == ReconstructionStatus.VALID

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checks": list(self.checks),
            "failures": list(self.failures),
            "valid": self.valid,
        }


def validate_reconstructed_state(
    snapshot: ExecutionStateSnapshot,
) -> ReconstructionValidationReport:
    """Validate semantic consistency of a reconstructed snapshot."""

    if not isinstance(
        snapshot,
        ExecutionStateSnapshot,
    ):
        raise TypeError(
            "snapshot must be ExecutionStateSnapshot."
        )

    checks: list[str] = []
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        reason: str,
    ) -> None:
        checks.append(name)

        if not condition:
            failures.append(reason)

    check(
        "gate_identity",
        bool(snapshot.gate_id.strip()),
        "Gate ID is empty.",
    )

    check(
        "subtask_identity",
        bool(snapshot.current_subtask.strip()),
        "Current subtask is empty.",
    )

    check(
        "controller_version",
        bool(snapshot.controller_version.strip()),
        "Controller version is empty.",
    )

    check(
        "canonical_source",
        snapshot.canonical_source == "data/state.json",
        "Canonical source is not data/state.json.",
    )

    check(
        "state_sha256",
        len(snapshot.source_state_sha256) == 64,
        "Invalid state SHA-256 length.",
    )

    check(
        "current_subtask_not_completed",
        snapshot.current_subtask
        not in snapshot.completed_subtasks,
        "Current subtask is also marked completed.",
    )

    if snapshot.current_subtask_status != "DONE":
        check(
            "current_subtask_is_pending",
            snapshot.current_subtask
            in snapshot.pending_subtasks,
            "Current subtask is neither pending nor DONE.",
        )

    check(
        "completed_pending_disjoint",
        not (
            set(snapshot.completed_subtasks)
            & set(snapshot.pending_subtasks)
        ),
        "Completed and pending subtasks overlap.",
    )

    return ReconstructionValidationReport(
        status=(
            ReconstructionStatus.VALID
            if not failures
            else ReconstructionStatus.INVALID
        ),
        checks=tuple(checks),
        failures=tuple(failures),
    )


__all__ = [
    "ReconstructionStatus",
    "ReconstructionValidationReport",
    "validate_reconstructed_state",
]
