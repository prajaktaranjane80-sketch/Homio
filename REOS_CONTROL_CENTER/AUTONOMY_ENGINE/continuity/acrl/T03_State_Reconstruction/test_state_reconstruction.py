"""ACRL T03 - Execution State Reconstruction tests."""

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
    data.mkdir(parents=True, exist_ok=True)

    subtasks = [
        {
            "id": "CORE-005-T01",
            "title": "Implement search foundation",
            "priority": "CRITICAL",
            "status": (
                current_status
                if current_subtask == "CORE-005-T01"
                else "PENDING"
            ),
        },
        {
            "id": "CORE-005-T02",
            "title": "Define search contracts",
            "priority": "HIGH",
            "status": (
                current_status
                if current_subtask == "CORE-005-T02"
                else "PENDING"
            ),
        },
        {
            "id": "CORE-005-T03",
            "title": "Validate search behavior",
            "priority": "HIGH",
            "status": (
                current_status
                if current_subtask == "CORE-005-T03"
                else "PENDING"
            ),
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
            "current_task": "Implement search foundation",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "gate_plans": {
            "CORE-005": {
                "id": "CORE-005",
                "name": "Search & Matching Core",
                "status": "CURRENT",
                "current_subtask": current_subtask,
                "subtasks": subtasks,
            },
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "id": "CORE-005",
                    "gate": "CORE-005",
                    "name": "Search & Matching Core",
                    "status": "CURRENT",
                },
                {
                    "id": "CORE-006",
                    "gate": "CORE-006",
                    "name": "Deal & Transaction Core",
                    "status": "PENDING",
                },
                {
                    "id": "CORE-007",
                    "gate": "CORE-007",
                    "name": "Trust, Fraud & Governance",
                    "status": "PENDING",
                },
                {
                    "id": "CORE-008",
                    "gate": "CORE-008",
                    "name": "Commission & Financial Core",
                    "status": "PENDING",
                },
            ],
        },
    }

    (data / "state.json").write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_reconstructs_current_execution_state(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    snapshot = ExecutionStateReconstructor(
        tmp_path
    ).reconstruct()

    assert snapshot.phase == "PRE-CODING ARCHITECTURE"
    assert snapshot.gate_id == "CORE-005"
    assert snapshot.gate_name == "Search & Matching Core"
    assert snapshot.gate_status == "CURRENT"
    assert snapshot.current_task == "Implement search foundation"
    assert snapshot.current_subtask == "CORE-005-T01"
    assert snapshot.current_subtask_status == "CURRENT"


def test_completed_and_pending_subtasks_are_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["gate_plans"]["CORE-005"]["subtasks"][1]["status"] = "DONE"

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    snapshot = ExecutionStateReconstructor(
        tmp_path
    ).reconstruct()

    assert snapshot.completed_subtasks == (
        "CORE-005-T02",
    )
    assert snapshot.pending_subtasks == (
        "CORE-005-T01",
        "CORE-005-T03",
    )


def test_current_subtask_cannot_be_completed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["gate_plans"]["CORE-005"]["subtasks"][0]["status"] = "DONE"

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        StateReconstructionIntegrityError
    ):
        ExecutionStateReconstructor(
            tmp_path
        ).reconstruct()


def test_completed_subtask_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
        current_status="CURRENT",
    )

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["gate_plans"]["CORE-005"]["subtasks"][1]["status"] = "DONE"

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    snapshot = ExecutionStateReconstructor(
        tmp_path
    ).reconstruct()

    assert snapshot.current_subtask == "CORE-005-T01"
    assert snapshot.current_subtask_status == "CURRENT"
    assert snapshot.completed_subtasks == (
        "CORE-005-T02",
    )
    assert snapshot.pending_subtasks == (
        "CORE-005-T01",
        "CORE-005-T03",
    )


def test_future_gates_are_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    snapshot = ExecutionStateReconstructor(
        tmp_path
    ).reconstruct()

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
    assert payload["phase"] == (
        "PRE-CODING ARCHITECTURE"
    )
    assert payload["gate"]["id"] == "CORE-005"
    assert payload["gate"]["status"] == "CURRENT"
    assert (
        payload["execution"]["current_task"]
        == "Implement search foundation"
    )
    assert (
        payload["execution"]["current_subtask"]
        == "CORE-005-T01"
    )
    assert len(
        payload["source_state_sha256"]
    ) == 64


def test_resume_context_contains_exact_position(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = (
        ExecutionStateReconstructor(tmp_path)
        .reconstruct()
        .resume_context()
    )

    assert "PHASE=PRE-CODING ARCHITECTURE" in context
    assert "GATE=CORE-005" in context
    assert "GATE_NAME=Search & Matching Core" in context
    assert "GATE_STATUS=CURRENT" in context
    assert (
        "CURRENT_TASK=Implement search foundation"
        in context
    )
    assert (
        "CURRENT_SUBTASK=CORE-005-T01"
        in context
    )
    assert "SUBTASK_STATUS=CURRENT" in context
    assert "AUTHORITY=data/state.json" in context
    assert "STATE_SHA256=" in context


def test_invalid_current_subtask_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T99",
        current_status="CURRENT",
    )

    with pytest.raises(
        StateReconstructionIntegrityError
    ):
        ExecutionStateReconstructor(
            tmp_path
        ).reconstruct()


def test_missing_state_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        StateReconstructionSourceError
    ):
        ExecutionStateReconstructor(
            tmp_path
        ).reconstruct()


def test_invalid_canonical_source_fails_closed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["constitution"]["canonical_source"] = (
        "another_state.json"
    )

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        StateReconstructionIntegrityError
    ):
        ExecutionStateReconstructor(
            tmp_path
        ).reconstruct()


def test_state_fingerprint_changes_after_state_change(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ExecutionStateReconstructor(
        tmp_path
    )

    first = reader.reconstruct().source_state_sha256

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["gate_plans"]["CORE-005"]["status"] = (
        "VALIDATED"
    )

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    second = reader.reconstruct().source_state_sha256

    assert first != second


def test_l4_part03_exact_position_contract(
    tmp_path: Path,
) -> None:
    """Verify the complete L4 Part 03 reconstruction contract."""

    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
        current_status="CURRENT",
    )

    snapshot = ExecutionStateReconstructor(
        tmp_path
    ).reconstruct()

    # Current phase.
    assert snapshot.phase == (
        "PRE-CODING ARCHITECTURE"
    )

    # Current gate.
    assert snapshot.gate_id == "CORE-005"
    assert snapshot.gate_name == (
        "Search & Matching Core"
    )

    # Current gate status.
    assert snapshot.gate_status == "CURRENT"

    # Current task.
    assert snapshot.current_task == (
        "Implement search foundation"
    )

    # Current subtask.
    assert snapshot.current_subtask == (
        "CORE-005-T01"
    )

    # Current subtask status.
    assert snapshot.current_subtask_status == (
        "CURRENT"
    )

    # Completed / pending position.
    assert snapshot.completed_subtasks == ()
    assert snapshot.pending_subtasks == (
        "CORE-005-T01",
        "CORE-005-T02",
        "CORE-005-T03",
    )

    # Authoritative future sequence.
    assert snapshot.future_gates == (
        "CORE-006",
        "CORE-007",
        "CORE-008",
    )

    # State fingerprint.
    assert (
        isinstance(
            snapshot.source_state_sha256,
            str,
        )
    )
    assert len(
        snapshot.source_state_sha256
    ) == 64

    # Canonical authority.
    assert snapshot.canonical_source == (
        "data/state.json"
    )
