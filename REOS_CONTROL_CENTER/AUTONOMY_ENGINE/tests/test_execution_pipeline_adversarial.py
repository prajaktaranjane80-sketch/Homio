"""
Adversarial tests for the deterministic execution pipeline.

These tests verify that the top-level execution pipeline:
- remains fail-closed,
- never invents an executor,
- never bypasses the coordinator,
- never retries implicitly,
- preserves evidence,
- blocks replay,
- and never reports incomplete postflight as success.

This test module is additive and does not modify existing architecture,
controller state, or existing AUTONOMY_ENGINE modules.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from orchestration.execution_coordinator import (  # noqa: E402
    ExecutionContext,
)
from execution.execution_pipeline import (  # noqa: E402
    ExecutionPipeline,
    PipelineStatus,
)
from protocols.action_protocol import ActionProposal  # noqa: E402


def make_proposal(
    action_id: str = "pipeline-001",
) -> ActionProposal:
    """Create a valid deterministic proposal."""

    return ActionProposal(
        action_id=action_id,
        action="create_project",
        target="project:pipeline-test",
        parameters={"source": "pipeline-adversarial-test"},
        requester="test-agent",
        tenant_id="tenant-test",
    )


def fully_authorized_context() -> ExecutionContext:
    """Create an explicitly authorized execution context."""

    return ExecutionContext(
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        evidence={
            "test": True,
            "source": "test_execution_pipeline_adversarial",
        },
    )


def successful_postflight() -> dict[str, bool]:
    """Return complete successful postflight evidence."""

    return {
        "evidence_complete": True,
        "provenance_valid": True,
        "state_consistent": True,
    }


def test_invalid_proposal_is_blocked() -> None:
    """Malformed proposals must never reach execution."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    proposal = ActionProposal(
        action_id="invalid-pipeline-001",
        action="",
        target=None,  # type: ignore[arg-type]
    )

    result = pipeline.execute(
        proposal,
        fully_authorized_context(),
        executor=lambda _: calls.append("called"),
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.BLOCKED
    assert result.allowed is False
    assert result.coordination is None
    assert calls == []


@pytest.mark.parametrize(
    "field",
    [
        "authorized",
        "capability_available",
        "policy_allowed",
        "risk_allowed",
        "idempotency_clear",
        "tripwires_clear",
    ],
)
def test_each_safety_condition_blocks_pipeline(field: str) -> None:
    """Every required safety condition must independently deny execution."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    base = fully_authorized_context()

    values = {
        "authorized": base.authorized,
        "capability_available": base.capability_available,
        "policy_allowed": base.policy_allowed,
        "risk_allowed": base.risk_allowed,
        "guard_allowed": base.guard_allowed,
        "idempotency_clear": base.idempotency_clear,
        "tripwires_clear": base.tripwires_clear,
        "architecture_locked": base.architecture_locked,
        "evidence": base.evidence,
    }

    values[field] = False

    context = ExecutionContext(**values)

    result = pipeline.execute(
        make_proposal(),
        context,
        executor=lambda _: calls.append("called"),
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.BLOCKED
    assert result.allowed is False
    assert calls == []


def test_frozen_architecture_blocks_pipeline() -> None:
    """Frozen architecture must remain immutable."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    base = fully_authorized_context()

    context = ExecutionContext(
        authorized=base.authorized,
        capability_available=base.capability_available,
        policy_allowed=base.policy_allowed,
        risk_allowed=base.risk_allowed,
        guard_allowed=base.guard_allowed,
        idempotency_clear=base.idempotency_clear,
        tripwires_clear=base.tripwires_clear,
        architecture_locked=True,
        evidence=base.evidence,
    )

    result = pipeline.execute(
        make_proposal(),
        context,
        executor=lambda _: calls.append("called"),
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.BLOCKED
    assert result.allowed is False
    assert calls == []


def test_missing_executor_is_blocked() -> None:
    """The pipeline must never invent or discover an executor."""

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=None,
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.BLOCKED
    assert result.allowed is False
    assert result.coordination is not None
    assert result.coordination.mutation is not None
    assert result.coordination.mutation.executed is False


def test_non_callable_executor_is_blocked() -> None:
    """A non-callable executor must never cross the mutation boundary."""

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor="not-callable",
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.BLOCKED
    assert result.allowed is False


def test_executor_failure_is_terminal() -> None:
    """Executor failure must never be converted into success or retry."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    def failing_executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)
        raise RuntimeError("pipeline failure")

    first = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=failing_executor,
        postflight=successful_postflight(),
    )

    second = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=failing_executor,
        postflight=successful_postflight(),
    )

    assert first.status is PipelineStatus.FAILED
    assert first.allowed is False

    assert second.status is PipelineStatus.BLOCKED
    assert second.allowed is False

    assert calls == ["pipeline-001"]


def test_successful_execution_completes_once() -> None:
    """A fully authorized pipeline may execute exactly once."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> dict[str, str]:
        calls.append(proposal.action_id)
        return {"result": "accepted"}

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=executor,
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.EXECUTED
    assert result.allowed is True
    assert result.coordination is not None
    assert result.coordination.mutation is not None
    assert result.coordination.mutation.executed is True
    assert calls == ["pipeline-001"]


def test_replay_is_blocked() -> None:
    """The same action must not execute twice through one pipeline."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    first = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=executor,
        postflight=successful_postflight(),
    )

    second = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=executor,
        postflight=successful_postflight(),
    )

    assert first.status is PipelineStatus.EXECUTED
    assert second.status is PipelineStatus.BLOCKED
    assert second.allowed is False
    assert second.coordination is None
    assert calls == ["pipeline-001"]


@pytest.mark.parametrize(
    "postflight",
    [
        {"evidence_complete": False, "provenance_valid": True, "state_consistent": True},
        {"evidence_complete": True, "provenance_valid": False, "state_consistent": True},
        {"evidence_complete": True, "provenance_valid": True, "state_consistent": False},
        {},
    ],
)
def test_incomplete_postflight_is_not_success(
    postflight: dict[str, bool],
) -> None:
    """Execution without complete postflight verification must fail."""

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: {"result": "accepted"},
        postflight=postflight,
    )

    assert result.status is PipelineStatus.FAILED
    assert result.allowed is False
    assert result.evidence["postflight_passed"] is False


def test_evidence_is_preserved() -> None:
    """Caller evidence must survive the entire pipeline."""

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: "ok",
        postflight=successful_postflight(),
    )

    assert result.evidence["test"] is True
    assert (
        result.evidence["source"]
        == "test_execution_pipeline_adversarial"
    )
    assert result.evidence["pipeline_attempted"] is True
    assert result.evidence["pipeline_succeeded"] is True


def test_preflight_has_no_execution_side_effect() -> None:
    """Pipeline preflight must never invoke an executor."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    protocol, enforcement = pipeline.preflight(
        make_proposal(),
        fully_authorized_context(),
    )

    assert protocol.valid is True
    assert enforcement is not None
    assert enforcement.allowed is True
    assert calls == []
    assert pipeline.processed("pipeline-001") is False


def test_reset_clears_only_local_pipeline_memory() -> None:
    """Reset must only clear local processed-action memory."""

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: "ok",
        postflight=successful_postflight(),
    )

    assert result.status is PipelineStatus.EXECUTED
    assert pipeline.processed("pipeline-001") is True

    pipeline.reset()

    assert pipeline.processed("pipeline-001") is False


def test_different_action_ids_are_independent() -> None:
    """Different actions must not collide in local replay protection."""

    pipeline = ExecutionPipeline()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    first = pipeline.execute(
        make_proposal("pipeline-001"),
        fully_authorized_context(),
        executor=executor,
        postflight=successful_postflight(),
    )

    second = pipeline.execute(
        make_proposal("pipeline-002"),
        fully_authorized_context(),
        executor=executor,
        postflight=successful_postflight(),
    )

    assert first.status is PipelineStatus.EXECUTED
    assert second.status is PipelineStatus.EXECUTED
    assert calls == ["pipeline-001", "pipeline-002"]