from __future__ import annotations

from pathlib import Path

from .acrl_runtime import ACRLRuntime


PROJECT_ROOT = (
    Path(__file__).resolve().parents[5]
)


def test_stage1_integrates_all_acrl_tasks() -> None:
    runtime = ACRLRuntime(PROJECT_ROOT)

    snapshot = runtime.build_snapshot()

    assert len(snapshot.tasks) == 30
    assert [task.task_id for task in snapshot.tasks] == [
        f"T{number:02d}" for number in range(1, 31)
    ]
    assert snapshot.healthy is True


def test_stage1_preserves_authority_boundary() -> None:
    runtime = ACRLRuntime(PROJECT_ROOT)

    snapshot = runtime.build_snapshot()

    assert snapshot.architecture_authority == (
        "FROZEN_APPROVED_ARCHITECTURE"
    )
    assert snapshot.roadmap_authority == "REOS_CONTROL_CENTER"
    assert snapshot.execution_state_authority == (
        "REOS_CONTROL_CENTER/data/state.json"
    )
    assert snapshot.code_authority == "GIT_REPOSITORY"
    assert snapshot.continuity_authority == (
        "DERIVED_FROM_EXECUTION_STATE"
    )
    assert snapshot.chat_authority == "NONE"
