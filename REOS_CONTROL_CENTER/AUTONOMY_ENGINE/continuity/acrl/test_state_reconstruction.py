"""ACRL T03 — Execution State Reconstruction tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.state_reconstruction import (
    ExecutionStateReconstructor,
    StateReconstructionIntegrityError,
    StateReconstructionSourceError,
)


def _write_state(
    root: Path,
    *,
    current_subtask: str = "CORE-005-T01",
    current_status: str = "CURRENT",
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "schema_version": 3,
            "control_center_version": "7.0",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
        "current_gate": {
            "id": "CORE-005",
            "name": "Search & Matching Core",
            "status": "CURRENT",
            "completed_subtasks": [],
            "pending_subtasks": [
                "CORE-005-T01",
                "CORE-005-T02",
                "CORE-005-T03",
            ],
        },
        "current_task": {
            "name": "Implement search foundation",
        },
        "current_subtask": {
            "id": current_subtask,
        },
        "subtask_status": {
            "status": current_status,
        },
        "roadmap": {
            "future_gates": [
                "CORE-006",
                "CORE-007",
                "CORE-008",
            ],
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_reconstructs_current_execution_state(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    snapshot = ExecutionStateReconstructor(tmp_path).reconstruct()

    assert snapshot.phase == "PRE-CODING ARCHITECTURE"
    assert snapshot.gate_id == "CORE-005"
    assert snapshot.gate_name == "Search & Matching Core"
    assert snapshot.current_subtask == "CORE-005-T01"
    assert snapshot.current_subtask_status == "CURRENT"


def test_completed_and_pending_subtasks_are_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["current_gate"]["completed_subtasks"] = [
        "CORE-005-T00",
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    snapshot = ExecutionStateReconstructor(tmp_path).reconstruct()

    assert snapshot.completed_subtasks == ("CORE-005-T00",)
    assert "CORE-005-T01" in snapshot.pending_subtasks


def test_future_gates_are_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    snapshot = ExecutionStateReconstructor(tmp_path).reconstruct()

    assert snapshot.future_gates == (
        "CORE-006",
        "CORE-007",
        "CORE-008",
    )


def test_projection_is_serializable(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    payload = (
        ExecutionStateReconstructor(tmp_path)
        .reconstruct()
        .to_dict()
    )

    assert payload["schema_version"] == "1.0"
    assert payload["gate"]["id"] == "CORE-005"
    assert payload["execution"]["current_subtask"] == "CORE-005-T01"
    assert len(payload["source_state_sha256"]) == 64


def test_resume_context_is_compact(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = (
        ExecutionStateReconstructor(tmp_path)
        .reconstruct()
        .resume_context()
    )

    assert "GATE=CORE-005" in context
    assert "CURRENT_SUBTASK=CORE-005-T01" in context
    assert "AUTHORITY=data/state.json" in context
    assert "STATE_SHA256=" in context


def test_current_subtask_cannot_be_completed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["current_gate"]["completed_subtasks"] = [
        "CORE-005-T01",
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(StateReconstructionIntegrityError):
        ExecutionStateReconstructor(tmp_path).reconstruct()


def test_invalid_current_subtask_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T99",
        current_status="CURRENT",
    )

    with pytest.raises(StateReconstructionIntegrityError):
        ExecutionStateReconstructor(tmp_path).reconstruct()


def test_missing_state_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(StateReconstructionSourceError):
        ExecutionStateReconstructor(tmp_path).reconstruct()


def test_state_fingerprint_changes_after_state_change(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ExecutionStateReconstructor(tmp_path)

    first = reader.reconstruct().source_state_sha256

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["current_gate"]["status"] = "VALIDATED"

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    second = reader.reconstruct().source_state_sha256

    assert first != second


def test_done_subtask_is_allowed_outside_pending(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
        current_status="DONE",
    )

    snapshot = ExecutionStateReconstructor(tmp_path).reconstruct()

    assert snapshot.current_subtask_status == "DONE"