"""
Adversarial tests for the controlled mutation boundary.

These tests verify that AUTONOMY_ENGINE cannot cross the mutation boundary
unless every required safety condition is explicitly satisfied.

This test module is additive. It does not modify controller state, existing
architecture files, or existing AUTONOMY_ENGINE tests.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

# Allow the test file to run directly from the AUTONOMY_ENGINE root while
# remaining compatible with normal pytest package discovery.
ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from execution.mutation_adapter import (  # noqa: E402
    ControlledMutationAdapter,
    MutationBlockReason,
    MutationRequest,
    MutationStatus,
)
from protocols.action_protocol import ActionProposal  # noqa: E402


def make_proposal(
    action_id: str = "mutation-001",
) -> ActionProposal:
    """Create a valid deterministic proposal for testing."""
    return ActionProposal(
        action_id=action_id,
        action="create_project",
        target="project:test-001",
        parameters={"source": "adversarial-test"},
        requester="test-agent",
        tenant_id="tenant-test",
    )


def fully_authorized_request(
    proposal: ActionProposal | None = None,
    *,
    executor=None,
    architecture_locked: bool = False,
) -> MutationRequest:
    """Build an explicitly authorized request."""
    return MutationRequest(
        proposal=proposal or make_proposal(),
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=architecture_locked,
        executor=executor,
        evidence={
            "test": True,
            "source": "test_mutation_adapter_adversarial",
        },
    )


def test_invalid_proposal_is_blocked() -> None:
    """Malformed proposals must never reach the executor."""
    adapter = ControlledMutationAdapter()
    executor_calls: list[str] = []

    proposal = ActionProposal(
        action_id="invalid-001",
        action="",
        target=None,  # type: ignore[arg-type]
    )

    request = fully_authorized_request(
        proposal,
        executor=lambda _: executor_calls.append("called"),
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.BLOCKED
    assert (
        result.decision.block_reason
        is MutationBlockReason.INVALID_PROPOSAL
    )
    assert executor_calls == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authorized", MutationBlockReason.NOT_AUTHORIZED),
        ("capability_available", MutationBlockReason.CAPABILITY_DENIED),
        ("policy_allowed", MutationBlockReason.POLICY_DENIED),
        ("risk_allowed", MutationBlockReason.RISK_DENIED),
        ("guard_allowed", MutationBlockReason.GUARD_DENIED),
        ("idempotency_clear", MutationBlockReason.IDEMPOTENCY_BLOCKED),
        ("tripwires_clear", MutationBlockReason.TRIPWIRE_BLOCKED),
    ],
)
def test_each_safety_gate_defaults_to_deny(
    field: str,
    reason: MutationBlockReason,
) -> None:
    """Every individual safety gate must independently block execution."""
    adapter = ControlledMutationAdapter()
    executor_calls: list[str] = []

    kwargs = {
        "executor": lambda _: executor_calls.append("called"),
    }

    request = fully_authorized_request(**kwargs)

    # MutationRequest is frozen, so construct a modified request rather than
    # mutating the existing request object.
    values = {
        "proposal": request.proposal,
        "authorized": request.authorized,
        "capability_available": request.capability_available,
        "policy_allowed": request.policy_allowed,
        "risk_allowed": request.risk_allowed,
        "guard_allowed": request.guard_allowed,
        "idempotency_clear": request.idempotency_clear,
        "tripwires_clear": request.tripwires_clear,
        "architecture_locked": request.architecture_locked,
        "executor": request.executor,
        "evidence": request.evidence,
    }

    values[field] = False

    blocked_request = MutationRequest(**values)
    result = adapter.execute(blocked_request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.BLOCKED
    assert result.decision.block_reason is reason
    assert executor_calls == []


def test_frozen_architecture_is_blocked() -> None:
    """Frozen architecture must remain immutable through this adapter."""
    adapter = ControlledMutationAdapter()
    executor_calls: list[str] = []

    request = fully_authorized_request(
        executor=lambda _: executor_calls.append("called"),
        architecture_locked=True,
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.BLOCKED
    assert (
        result.decision.block_reason
        is MutationBlockReason.ARCHITECTURE_LOCKED
    )
    assert executor_calls == []


def test_missing_executor_is_fail_closed() -> None:
    """No mutation executor means no mutation."""
    adapter = ControlledMutationAdapter()

    request = fully_authorized_request(executor=None)

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.BLOCKED
    assert (
        result.decision.block_reason
        is MutationBlockReason.EXECUTOR_MISSING
    )


def test_non_callable_executor_is_blocked() -> None:
    """An invalid executor object must never cross the boundary."""
    adapter = ControlledMutationAdapter()

    request = fully_authorized_request(
        executor="not-callable",  # type: ignore[arg-type]
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.BLOCKED
    assert (
        result.decision.block_reason
        is MutationBlockReason.EXECUTOR_INVALID
    )


def test_executor_failure_is_not_reported_as_success() -> None:
    """Executor exceptions must fail closed and preserve evidence."""
    adapter = ControlledMutationAdapter()

    def failing_executor(_: ActionProposal) -> None:
        raise RuntimeError("simulated controller failure")

    request = fully_authorized_request(executor=failing_executor)

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status is MutationStatus.FAILED
    assert result.decision.allowed is False
    assert result.error == "simulated controller failure"
    assert result.evidence["mutation_attempted"] is True
    assert result.evidence["mutation_succeeded"] is False
    assert result.evidence["failure_type"] == "RuntimeError"


def test_successful_mutation_executes_once() -> None:
    """A fully authorized mutation may execute exactly once."""
    adapter = ControlledMutationAdapter()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> dict[str, str]:
        calls.append(proposal.action_id)
        return {"result": "accepted"}

    request = fully_authorized_request(executor=executor)

    result = adapter.execute(request)

    assert result.executed is True
    assert result.decision.status is MutationStatus.EXECUTED
    assert result.decision.allowed is True
    assert result.result == {"result": "accepted"}
    assert calls == ["mutation-001"]
    assert adapter.attempted("mutation-001") is True


def test_replay_of_same_action_id_is_blocked() -> None:
    """The same action_id must not execute twice through one adapter."""
    adapter = ControlledMutationAdapter()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    request = fully_authorized_request(executor=executor)

    first = adapter.execute(request)
    second = adapter.execute(request)

    assert first.executed is True
    assert second.executed is False
    assert second.decision.status is MutationStatus.BLOCKED
    assert (
        second.decision.block_reason
        is MutationBlockReason.ALREADY_ATTEMPTED
    )
    assert calls == ["mutation-001"]


def test_failed_mutation_is_not_automatically_retried() -> None:
    """
    A failed executor call remains terminal for this adapter instance.

    Autonomous retry policy belongs above this boundary and must be explicitly
    governed; the mutation adapter must never create an implicit retry loop.
    """
    adapter = ControlledMutationAdapter()
    calls: list[str] = []

    def failing_executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)
        raise RuntimeError("failure")

    request = fully_authorized_request(executor=failing_executor)

    first = adapter.execute(request)
    second = adapter.execute(request)

    assert first.executed is False
    assert first.decision.status is MutationStatus.FAILED

    assert second.executed is False
    assert second.decision.status is MutationStatus.BLOCKED
    assert (
        second.decision.block_reason
        is MutationBlockReason.ALREADY_ATTEMPTED
    )

    assert calls == ["mutation-001"]


def test_evidence_is_preserved() -> None:
    """Caller-supplied evidence must survive the mutation boundary."""
    adapter = ControlledMutationAdapter()

    request = fully_authorized_request(
        executor=lambda _: "ok",
    )

    result = adapter.execute(request)

    assert result.evidence["test"] is True
    assert (
        result.evidence["source"]
        == "test_mutation_adapter_adversarial"
    )
    assert result.evidence["mutation_attempted"] is True
    assert result.evidence["mutation_succeeded"] is True


def test_blocked_mutation_preserves_evidence() -> None:
    """Even blocked decisions must retain their evidence context."""
    adapter = ControlledMutationAdapter()

    request = fully_authorized_request(
        executor=lambda _: "must-not-run",
    )

    request = MutationRequest(
        proposal=request.proposal,
        authorized=False,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=request.executor,
        evidence={"trace_id": "trace-001"},
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.evidence["trace_id"] == "trace-001"


def test_adapter_does_not_execute_without_all_positive_conditions() -> None:
    """The boundary must require every safety condition simultaneously."""
    adapter = ControlledMutationAdapter()
    calls: list[str] = []

    request = MutationRequest(
        proposal=make_proposal(),
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=lambda proposal: calls.append(proposal.action_id),
    )

    result = adapter.execute(request)

    assert result.executed is True
    assert calls == ["mutation-001"]


def test_reset_only_clears_local_attempt_memory() -> None:
    """
    reset() may clear only local adapter memory.

    It must not imply that persistent controller idempotency state has been
    cleared.
    """
    adapter = ControlledMutationAdapter()

    request = fully_authorized_request(
        executor=lambda _: "ok",
    )

    first = adapter.execute(request)

    assert first.executed is True
    assert adapter.attempted("mutation-001") is True

    adapter.reset()

    assert adapter.attempted("mutation-001") is False


def test_preflight_has_no_execution_side_effect() -> None:
    """Preflight must never invoke the supplied executor."""
    adapter = ControlledMutationAdapter()
    calls: list[str] = []

    request = fully_authorized_request(
        executor=lambda proposal: calls.append(proposal.action_id),
    )

    decision = adapter.preflight(request)

    assert decision.allowed is True
    assert decision.status is MutationStatus.READY
    assert calls == []
    assert adapter.attempted("mutation-001") is False