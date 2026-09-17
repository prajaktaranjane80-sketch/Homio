from types import SimpleNamespace

import pytest

from .continuity_controller import (
    ContinuityControlDecision,
    control_continuity,
)
from .unified_runtime_context import UnifiedRuntimeContext


def context() -> UnifiedRuntimeContext:
    return UnifiedRuntimeContext(
        schema_version="1.0",
        mission_id="PART23-001",
        objective="Autonomous continuity control",
        control_center_root="D:/HOMIO/REOS_CONTROL_CENTER",
        architecture_authority="FROZEN_APPROVED_ARCHITECTURE",
        roadmap_authority="REOS_CONTROL_CENTER",
        execution_state_authority=(
            "REOS_CONTROL_CENTER/data/state.json"
        ),
        code_authority="GIT_REPOSITORY",
        continuity_authority=(
            "DERIVED_FROM_EXECUTION_STATE"
        ),
        chat_authority="NONE",
        git_branch="reos-development",
        git_head_sha="abc123",
        git_worktree_clean=False,
        git_fingerprint="git-fp",
        acrl_task_ids=tuple(
            f"T{i:02d}"
            for i in range(1, 31)
        ),
        context_fingerprint="context-fp",
    )


def result(decision: str) -> SimpleNamespace:
    return SimpleNamespace(
        decision=SimpleNamespace(
            value=decision
        )
    )


def base_inputs():
    return {
        "context": context(),
        "continuity_result": result(
            "RECOVERED"
        ),
        "evidence_result": result(
            "RESOLVED"
        ),
        "loop_result": result(
            "STARTED"
        ),
        "scheduler_result": result(
            "SCHEDULED"
        ),
        "reconciliation_result": result(
            "RECONCILED"
        ),
        "decision_result": result(
            "AUTONOMY_ALLOWED"
        ),
    }


def test_full_flow_continues():
    outcome = control_continuity(
        **base_inputs()
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.CONTINUE
    )

    assert outcome.blocking_stage is None

    assert outcome.stages == (
        "RECONSTRUCT",
        "VERIFY",
        "DEPENDENCY_CHECK",
        "CONFLICT_CHECK",
        "HUMAN_BOUNDARY",
    )


def test_invalid_reconstruction_fails_closed():
    values = base_inputs()

    values["context"] = context()
    object.__setattr__(
        values["context"],
        "context_fingerprint",
        "",
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.FAIL_CLOSED
    )

    assert outcome.blocking_stage == "VERIFY"


def test_continuity_failure_blocks():
    values = base_inputs()
    values["continuity_result"] = result(
        "BLOCKED"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.BLOCKED
    )

    assert outcome.blocking_stage == "VERIFY"


def test_dependency_failure_blocks():
    values = base_inputs()
    values["scheduler_result"] = result(
        "WAITING"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.BLOCKED
    )

    assert (
        outcome.blocking_stage
        == "DEPENDENCY_CHECK"
    )


def test_dependency_resource_boundary_waits_for_human():
    values = base_inputs()

    values["scheduler_result"] = result(
        "RESOURCE_BLOCKED"
    )

    values["decision_result"] = result(
        "WAITING_FOR_HUMAN"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision
        .WAITING_FOR_HUMAN
    )

    assert (
        outcome.blocking_stage
        == "HUMAN_BOUNDARY"
    )


@pytest.mark.parametrize(
    "decision",
    [
        "NO_SAFE_RESOLUTION",
        "FAIL_CLOSED",
        "BLOCKED",
        "CONFLICT_UNRESOLVED",
    ],
)
def test_conflict_failure_blocks(
    decision: str,
):
    values = base_inputs()
    values["reconciliation_result"] = result(
        decision
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.BLOCKED
    )

    assert (
        outcome.blocking_stage
        == "CONFLICT_CHECK"
    )


def test_human_boundary_waits():
    values = base_inputs()
    values["decision_result"] = result(
        "WAITING_FOR_HUMAN"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision
        .WAITING_FOR_HUMAN
    )


def test_human_rejection_blocks():
    values = base_inputs()
    values["decision_result"] = result(
        "HUMAN_REJECTED"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.BLOCKED
    )


def test_human_approval_continues():
    values = base_inputs()
    values["decision_result"] = result(
        "HUMAN_APPROVED"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.CONTINUE
    )


def test_unknown_human_boundary_fails_closed():
    values = base_inputs()
    values["decision_result"] = result(
        "UNKNOWN"
    )

    outcome = control_continuity(
        **values
    )

    assert (
        outcome.decision
        == ContinuityControlDecision.FAIL_CLOSED
    )


def test_control_result_is_deterministic():
    first = control_continuity(
        **base_inputs()
    )

    second = control_continuity(
        **base_inputs()
    )

    assert (
        first.control_fingerprint
        == second.control_fingerprint
    )
