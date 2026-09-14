"""ACRL T05 — Task Dependency Reconstruction tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T05_Dependency_Authority_Map.task_dependency_reconstruction import (
    DependencyResolutionStatus,
    TaskDependencyConflictError,
    TaskDependencyReconstructor,
    reconstruct_task_dependencies,
)


def _write_state(
    root: Path,
    *,
    current_subtask: str = "CORE-005-T01",
    subtask_statuses: tuple[str, ...] = (
        "CURRENT",
        "PENDING",
        "PENDING",
    ),
    core004_status: str = "APPROVED",
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

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
            "CORE-004": {
                "id": "CORE-004",
                "name": "Inventory Core",
                "status": core004_status,
                "current_subtask": "CORE-004-T03",
                "subtasks": [
                    {
                        "id": "CORE-004-T01",
                        "status": "DONE",
                    },
                    {
                        "id": "CORE-004-T02",
                        "status": "DONE",
                    },
                    {
                        "id": "CORE-004-T03",
                        "status": "DONE",
                    },
                ],
            },
            "CORE-005": {
                "id": "CORE-005",
                "name": "Search & Matching Core",
                "status": "CURRENT",
                "current_subtask": current_subtask,
                "subtasks": [
                    {
                        "id": "CORE-005-T01",
                        "status": subtask_statuses[0],
                    },
                    {
                        "id": "CORE-005-T02",
                        "status": subtask_statuses[1],
                    },
                    {
                        "id": "CORE-005-T03",
                        "status": subtask_statuses[2],
                    },
                ],
            },
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "gate": "CORE-004",
                    "status": "COMPLETE",
                },
                {
                    "gate": "CORE-005",
                    "status": "CURRENT",
                },
                {
                    "gate": "CORE-006",
                    "status": "PENDING",
                },
            ],
        },
        "dependencies": {
            "nodes": [
                {
                    "id": "CORE-004",
                    "status": "APPROVED",
                },
                {
                    "id": "CORE-005",
                    "status": "CURRENT",
                },
            ],
            "edges": [
                [
                    "CORE-004",
                    "CORE-005",
                ],
            ],
            "rules": [
                "A gate cannot start before its dependencies are complete.",
                "A subtask cannot start before prior required subtasks are complete.",
            ],
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_current_work_unit_is_reconstructed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    result = reconstruct_task_dependencies(tmp_path)

    assert result.current_gate == "CORE-005"
    assert result.current_task == "CORE-005-T01"
    assert result.current_subtask == "CORE-005-T01"
    assert result.first_valid_work_unit == "CORE-005:CORE-005-T01"


def test_prerequisite_gate_is_reconstructed(tmp_path: Path) -> None:
    _write_state(tmp_path)

    result = reconstruct_task_dependencies(tmp_path)

    assert result.prerequisite_gates == ("CORE-004",)


def test_completed_prerequisite_gate_does_not_block(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    result = reconstruct_task_dependencies(tmp_path)

    assert result.blocked_by == ()


def test_prior_subtasks_are_dependencies(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T03",
        subtask_statuses=(
            "DONE",
            "DONE",
            "CURRENT",
        ),
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert result.prerequisite_subtasks == (
        "CORE-005-T01",
        "CORE-005-T02",
    )
    assert result.status == DependencyResolutionStatus.VALID


def test_incomplete_prior_subtask_blocks(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T03",
        subtask_statuses=(
            "DONE",
            "PENDING",
            "CURRENT",
        ),
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert result.status == DependencyResolutionStatus.BLOCKED
    assert any(
        blocker.dependency_id == "CORE-005-T02"
        for blocker in result.blocked_by
    )


def test_current_completed_subtask_is_invalid(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        current_subtask="CORE-005-T01",
        subtask_statuses=(
            "DONE",
            "PENDING",
            "PENDING",
        ),
    )

    with pytest.raises(TaskDependencyConflictError):
        TaskDependencyReconstructor(tmp_path).reconstruct()


def test_prerequisite_gate_blocks_when_incomplete(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        core004_status="CURRENT",
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert result.status == DependencyResolutionStatus.BLOCKED
    assert any(
        blocker.kind == "GATE"
        and blocker.dependency_id == "CORE-004"
        for blocker in result.blocked_by
    )


def test_stale_dependency_node_status_is_detected(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )

    state["dependencies"]["nodes"] = [
        {
            "id": "CORE-004",
            "status": "FUTURE",
        },
        {
            "id": "CORE-005",
            "status": "FUTURE",
        },
    ]

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert any(
        "stale/conflicting" in conflict
        for conflict in result.conflicts
    )


def test_missing_dependency_edge_is_not_invented(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )

    state["dependencies"]["edges"] = []

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert result.prerequisite_gates == ()
    assert not any(
        blocker.kind == "GATE"
        for blocker in result.blocked_by
    )


def test_module_dependencies_are_never_invented(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    result = reconstruct_task_dependencies(tmp_path)

    assert result.prerequisite_modules == ()


def test_declared_module_owner_is_reconstructed(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )

    state["gate_plans"]["CORE-005"]["prerequisite_modules"] = [
        "SEARCH_SCHEMA",
    ]
    state["gate_plans"]["CORE-005"]["module_owners"] = {
        "SEARCH_SCHEMA": "SEARCH_DOMAIN",
    }

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    result = reconstruct_task_dependencies(tmp_path)

    assert result.prerequisite_modules == (
        "SEARCH_SCHEMA",
    )
    assert (
        "SEARCH_SCHEMA",
        "SEARCH_DOMAIN",
    ) in result.dependency_owners


def test_fingerprint_is_deterministic(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    first = reconstruct_task_dependencies(tmp_path)
    second = reconstruct_task_dependencies(tmp_path)

    assert first.dependency_fingerprint == (
        second.dependency_fingerprint
    )
    assert len(first.dependency_fingerprint) == 64


def test_serializable_projection_contains_resolution(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    payload = reconstruct_task_dependencies(
        tmp_path
    ).to_dict()

    assert payload["schema_version"] == "1.0"
    assert (
        payload["current"]["gate"] == "CORE-005"
    )
    assert (
        payload["resolution"]["first_valid_work_unit"]
        == "CORE-005:CORE-005-T01"
    )
    assert len(payload["fingerprint"]) == 64
