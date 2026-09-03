"""ACRL T04 — Gate / Subtask Continuity tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.gate_subtask_continuity import (
    GateContinuityConflictError,
    GateContinuityIntegrityError,
    GateContinuitySourceError,
    GateSubtaskContinuityReader,
    ResumeDecision,
)


def _write_state(
    root: Path,
    *,
    current_subtask: str = "CORE-005-T02",
    current_status: str = "CURRENT",
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "current_gate": {
            "id": "CORE-005",
            "name": "Search & Matching Core",
            "status": "CURRENT",
            "subtasks": [
                "CORE-005-T01",
                "CORE-005-T02",
                "CORE-005-T03",
                "CORE-005-T04",
            ],
            "completed_subtasks": [
                "CORE-005-T01",
            ],
            "pending_subtasks": [
                "CORE-005-T02",
                "CORE-005-T03",
                "CORE-005-T04",
            ],
        },
        "current_subtask": {
            "id": current_subtask,
        },
        "subtask_status": {
            "status": current_status,
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_reconstructs_current_gate_and_subtask(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    continuity = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.gate_id == "CORE-005"
    assert continuity.current_subtask == "CORE-005-T02"
    assert continuity.current_subtask_status == "CURRENT"


def test_reconstructs_subtask_position(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    continuity = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.subtask_index == 2
    assert continuity.total_subtasks == 4


def test_completed_and_remaining_are_consistent(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    continuity = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.completed_subtasks == (
        "CORE-005-T01",
    )

    assert continuity.remaining_subtasks == (
        "CORE-005-T02",
        "CORE-005-T03",
        "CORE-005-T04",
    )


def test_resume_decision_is_resume(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    continuity = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
    )

    assert continuity.resume_decision == ResumeDecision.RESUME
    assert continuity.can_resume() is True


def test_projection_is_serializable(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    payload = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
        .to_dict()
    )

    assert payload["schema_version"] == "1.0"
    assert payload["gate"]["id"] == "CORE-005"
    assert payload["subtask"]["current"] == "CORE-005-T02"
    assert len(payload["continuity"]["fingerprint"]) == 64
    assert len(payload["authority"]["source_state_sha256"]) == 64


def test_duplicate_completed_subtasks_fail_closed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["current_gate"]["completed_subtasks"] = [
        "CORE-005-T01",
        "CORE-005-T01",
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(GateContinuityIntegrityError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_duplicate_pending_subtasks_fail_closed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["current_gate"]["pending_subtasks"] = [
        "CORE-005-T02",
        "CORE-005-T02",
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(GateContinuityIntegrityError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_completed_pending_overlap_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["current_gate"]["completed_subtasks"] = [
        "CORE-005-T01",
        "CORE-005-T02",
    ]

    state["current_gate"]["pending_subtasks"] = [
        "CORE-005-T02",
        "CORE-005-T03",
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_current_subtask_outside_gate_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T99",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_current_subtask_already_completed_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_missing_state_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(GateContinuitySourceError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()