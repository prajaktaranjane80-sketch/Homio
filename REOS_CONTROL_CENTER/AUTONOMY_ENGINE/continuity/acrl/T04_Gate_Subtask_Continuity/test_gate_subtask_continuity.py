"""ACRL T04 — Gate / Subtask Continuity acceptance tests."""

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
    current_subtask_status: str = "CURRENT",
    gate_status: str = "CURRENT",
    statuses: tuple[str, ...] = (
        "DONE",
        "CURRENT",
        "PENDING",
        "PENDING",
    ),
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    subtasks = [
        {
            "id": "CORE-005-T01",
            "status": statuses[0],
        },
        {
            "id": "CORE-005-T02",
            "status": statuses[1],
        },
        {
            "id": "CORE-005-T03",
            "status": statuses[2],
        },
        {
            "id": "CORE-005-T04",
            "status": statuses[3],
        },
    ]

    state = {
        "meta": {
            "schema_version": 3,
            "control_center_version": "6.0",
        },
        "constitution": {
            "canonical_source": "data/state.json",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
        "execution": {
            "current_gate": "CORE-005",
            "current_task": "CORE-005-T01",
        },
        "gate_plans": {
            "CORE-005": {
                "name": "Search & Matching Core",
                "status": gate_status,
                "current_subtask": current_subtask,
                "subtasks": subtasks,
            }
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "gate": "CORE-005",
                    "status": "CURRENT",
                },
                {
                    "gate": "CORE-006",
                    "status": "PENDING",
                },
            ]
        },
    }

    state_path = data / "state.json"
    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_reconstructs_gate_and_subtask(tmp_path: Path) -> None:
    _write_state(tmp_path)

    continuity = GateSubtaskContinuityReader(tmp_path).reconstruct()

    assert continuity.gate_id == "CORE-005"
    assert continuity.gate_name == "Search & Matching Core"
    assert continuity.current_task == "CORE-005-T01"
    assert continuity.current_subtask == "CORE-005-T02"
    assert continuity.current_subtask_status == "CURRENT"


def test_completed_work_is_preserved_and_not_resumed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    continuity = GateSubtaskContinuityReader(tmp_path).reconstruct()

    assert continuity.completed_subtasks == (
        "CORE-005-T01",
    )

    assert continuity.pending_subtasks == (
        "CORE-005-T02",
        "CORE-005-T03",
        "CORE-005-T04",
    )

    assert continuity.first_incomplete_authoritative_unit == "CORE-005-T02"


def test_first_incomplete_is_authoritative_resume_point(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T03",
        current_subtask_status="PENDING",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_completed_subtask_cannot_be_current(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
        current_subtask_status="DONE",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_current_subtask_must_exist_in_gate(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T99",
        current_subtask_status="CURRENT",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_duplicate_subtask_ids_fail_closed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["gate_plans"]["CORE-005"]["subtasks"][2]["id"] = (
        "CORE-005-T02"
    )

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(GateContinuityIntegrityError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_invalid_subtask_status_fails_closed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    state["gate_plans"]["CORE-005"]["subtasks"][2]["status"] = (
        "STARTED"
    )

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(GateContinuityIntegrityError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_completed_gate_with_incomplete_subtask_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        gate_status="COMPLETE",
    )

    with pytest.raises(GateContinuityConflictError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()


def test_resume_is_allowed_for_first_incomplete_unit(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    continuity = GateSubtaskContinuityReader(tmp_path).reconstruct()

    assert continuity.resume_decision == ResumeDecision.RESUME
    assert continuity.can_resume() is True


def test_subtask_position_is_reconstructed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    continuity = GateSubtaskContinuityReader(tmp_path).reconstruct()

    assert continuity.subtask_index == 2
    assert continuity.total_subtasks == 4


def test_projection_is_serializable(tmp_path: Path) -> None:
    _write_state(tmp_path)

    payload = (
        GateSubtaskContinuityReader(tmp_path)
        .reconstruct()
        .to_dict()
    )

    assert payload["schema_version"] == "2.0"
    assert payload["gate"]["id"] == "CORE-005"
    assert (
        payload["subtask"]["first_incomplete_authoritative_unit"]
        == "CORE-005-T02"
    )
    assert payload["continuity"]["resume_decision"] == "RESUME"
    assert len(payload["continuity"]["fingerprint"]) == 64
    assert len(payload["authority"]["source_state_sha256"]) == 64


def test_missing_state_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(GateContinuitySourceError):
        GateSubtaskContinuityReader(tmp_path).reconstruct()
