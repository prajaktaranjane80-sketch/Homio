"""ACRL T03 — reconstruction validation tests."""

from __future__ import annotations

from .reconstruction_validation import (
    ReconstructionStatus,
    validate_reconstructed_state,
)
from .state_reconstruction import ExecutionStateSnapshot


def _snapshot(
    *,
    current_status: str = "CURRENT",
    current_subtask: str = "CORE-005-T01",
    completed: tuple[str, ...] = (),
    pending: tuple[str, ...] = (
        "CORE-005-T01",
        "CORE-005-T02",
    ),
) -> ExecutionStateSnapshot:
    return ExecutionStateSnapshot(
        phase="PRE-CODING ARCHITECTURE",
        gate_id="CORE-005",
        gate_name="Search & Matching Core",
        gate_status="CURRENT",
        current_task="Implement search foundation",
        current_subtask=current_subtask,
        current_subtask_status=current_status,
        completed_subtasks=completed,
        pending_subtasks=pending,
        future_gates=("CORE-006",),
        state_schema_version=3,
        controller_version="7.0",
        canonical_source="data/state.json",
        source_state_sha256="a" * 64,
    )


def test_valid_snapshot_is_valid() -> None:
    report = validate_reconstructed_state(
        _snapshot()
    )

    assert report.status == ReconstructionStatus.VALID
    assert report.valid is True
    assert report.failures == ()


def test_current_subtask_completed_is_invalid() -> None:
    report = validate_reconstructed_state(
        _snapshot(
            completed=("CORE-005-T01",),
        )
    )

    assert report.valid is False


def test_non_done_subtask_must_be_pending() -> None:
    report = validate_reconstructed_state(
        _snapshot(
            pending=("CORE-005-T02",),
        )
    )

    assert report.valid is False


def test_done_subtask_may_be_outside_pending() -> None:
    report = validate_reconstructed_state(
        _snapshot(
            current_status="DONE",
            pending=("CORE-005-T02",),
        )
    )

    assert report.valid is True


def test_completed_and_pending_overlap_is_invalid() -> None:
    report = validate_reconstructed_state(
        _snapshot(
            completed=("CORE-005-T02",),
            pending=("CORE-005-T01", "CORE-005-T02"),
        )
    )

    assert report.valid is False
