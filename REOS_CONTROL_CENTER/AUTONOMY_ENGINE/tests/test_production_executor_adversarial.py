"""
Adversarial verification suite for the production execution boundary.
R3 — Live Production Executor Wiring

This suite verifies that ProductionExecutor remains a strict execution
boundary and cannot accidentally become an authority source.

Security / reliability invariants
----------------------------------
1. Default-deny execution.
2. No executor may be used before explicit binding.
3. Invalid proposals never reach the executor.
4. A bound executor must remain callable.
5. Execution is single-shot per action_id.
6. Executor failures are represented as deterministic failures.
7. Timeout configuration is rejected when invalid.
8. Successful execution produces deterministic evidence.
9. Reset only clears local attempt memory.
10. ProductionExecutor must not silently discover or invent an executor.
11. Malformed external values fail closed.
12. Executor identity/capability metadata cannot authorize execution by itself.
13. The proposal action_id remains the authoritative local replay key.
14. A failed execution must not become a successful execution result.
15. No second execution is permitted after a completed attempt.

These tests intentionally avoid depending on REOS_CONTROL_CENTER internals.
The controller remains the authoritative mutation owner.
"""

from __future__ import annotations

from typing import Any

import pytest

from execution.production_executor import (
    ExecutorCapability,
    ExecutorIdentity,
    ExecutionEnvelope,
    ProductionCallable,
    ProductionExecutionResult,
    ProductionExecutor,
    ProductionExecutorBlockReason,
    ProductionExecutorFailure,
    ProductionExecutorStatus,
)
from protocols.action_protocol import ActionProposal


def make_proposal(
    *,
    action_id: str = "action-001",
    action: str = "approve-gate",
    target: str = "REOS_CONTROL_CENTER",
    parameters: dict[str, Any] | None = None,
) -> ActionProposal:
    """Create a deterministic valid proposal for boundary tests."""

    return ActionProposal(
        action_id=action_id,
        action=action,
        target=target,
        parameters=dict(parameters or {}),
    )


def make_executor() -> ProductionExecutor:
    """Create an unbound production executor."""

    return ProductionExecutor(
        identity=ExecutorIdentity(
            name="test-controller-executor",
            version="1.0.0",
        ),
        capability=ExecutorCapability(
            name="controller-mutation",
        ),
    )


def bind_successful_executor(
    executor: ProductionExecutor,
    *,
    calls: list[str] | None = None,
) -> ProductionExecutor:
    """Bind a deterministic successful executor."""

    def run(proposal: ActionProposal) -> dict[str, Any]:
        if calls is not None:
            calls.append(proposal.action_id)

        return {
            "accepted": True,
            "action_id": proposal.action_id,
        }

    executor.bind(run)
    return executor


def test_unbound_executor_is_default_deny() -> None:
    """Execution must be blocked when no executor has been explicitly bound."""

    executor = make_executor()
    proposal = make_proposal()

    result = executor.execute(proposal)

    assert result.allowed is False
    assert result.status is ProductionExecutorStatus.BLOCKED
    assert result.block_reason is not None
    assert result.block_reason is ProductionExecutorBlockReason.EXECUTOR_MISSING


def test_preflight_never_executes_unbound_executor() -> None:
    """Preflight must remain observation-only."""

    executor = make_executor()
    proposal = make_proposal()

    result = executor.preflight(proposal)

    assert result.allowed is False
    assert result.status is ProductionExecutorStatus.BLOCKED
    assert executor.attempted(proposal.action_id) is False


def test_invalid_proposal_is_rejected_before_execution() -> None:
    """Malformed proposals must never cross the production boundary."""

    executor = make_executor()

    calls: list[str] = []

    def run(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    executor.bind(run)

    invalid = ActionProposal(
        action_id="",
        action="approve-gate",
        target="REOS_CONTROL_CENTER",
    )

    result = executor.execute(invalid)

    assert result.allowed is False
    assert result.status is ProductionExecutorStatus.BLOCKED
    assert result.block_reason is ProductionExecutorBlockReason.INVALID_PROPOSAL
    assert calls == []


def test_non_action_proposal_fails_closed() -> None:
    """External malformed objects must not reach the bound executor."""

    executor = make_executor()

    calls: list[Any] = []

    def run(proposal: ActionProposal) -> None:
        calls.append(proposal)

    executor.bind(run)

    result = executor.execute(object())  # type: ignore[arg-type]

    assert result.allowed is False
    assert result.status in {
        ProductionExecutorStatus.BLOCKED,
        ProductionExecutorStatus.FAILED,
    }
    assert calls == []


def test_explicit_binding_is_required() -> None:
    """ProductionExecutor must not discover an executor implicitly."""

    executor = make_executor()
    proposal = make_proposal()

    assert executor.bound is False

    result = executor.execute(proposal)

    assert result.allowed is False
    assert result.block_reason is ProductionExecutorBlockReason.EXECUTOR_MISSING


def test_explicit_binding_enables_preflight() -> None:
    """A valid explicitly bound executor may pass the local executor boundary."""

    executor = bind_successful_executor(make_executor())
    proposal = make_proposal()

    result = executor.preflight(proposal)

    assert result.allowed is True
    assert result.status is ProductionExecutorStatus.READY


def test_successful_execution_calls_executor_exactly_once() -> None:
    """One action_id must cross the production executor boundary only once."""

    calls: list[str] = []

    executor = bind_successful_executor(
        make_executor(),
        calls=calls,
    )

    proposal = make_proposal()

    result = executor.execute(proposal)

    assert result.allowed is True
    assert result.status is ProductionExecutorStatus.EXECUTED
    assert result.executed is True
    assert calls == ["action-001"]
    assert executor.attempted("action-001") is True


def test_replay_is_blocked_after_success() -> None:
    """A completed action must not be silently replayed."""

    calls: list[str] = []

    executor = bind_successful_executor(
        make_executor(),
        calls=calls,
    )

    proposal = make_proposal()

    first = executor.execute(proposal)
    second = executor.execute(proposal)

    assert first.status is ProductionExecutorStatus.EXECUTED

    assert second.status is ProductionExecutorStatus.BLOCKED
    assert second.allowed is False
    assert second.block_reason is ProductionExecutorBlockReason.ALREADY_ATTEMPTED

    assert calls == ["action-001"]


def test_executor_failure_is_terminal_for_action() -> None:
    """Executor exceptions must produce failure and prevent automatic retry."""

    calls: list[str] = []

    executor = make_executor()

    def failing_executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)
        raise RuntimeError("controller unavailable")

    executor.bind(failing_executor)

    proposal = make_proposal()

    first = executor.execute(proposal)
    second = executor.execute(proposal)

    assert first.status is ProductionExecutorStatus.FAILED
    assert first.allowed is False
    assert first.executed is False

    assert second.status is ProductionExecutorStatus.BLOCKED
    assert second.allowed is False

    assert calls == ["action-001"]


def test_executor_exception_is_not_reported_as_success() -> None:
    """An executor exception can never become an EXECUTED result."""

    executor = make_executor()

    def failing_executor(proposal: ActionProposal) -> None:
        raise PermissionError("mutation denied")

    executor.bind(failing_executor)

    result = executor.execute(make_proposal())

    assert result.status is ProductionExecutorStatus.FAILED
    assert result.allowed is False
    assert result.executed is False
    assert result.error


def test_executor_result_preserves_action_identity() -> None:
    """Execution results must preserve the proposal action_id."""

    executor = bind_successful_executor(make_executor())

    proposal = make_proposal(action_id="immutable-action-42")

    result = executor.execute(proposal)

    assert result.action_id == "immutable-action-42"


def test_executor_does_not_rewrite_action_id() -> None:
    """The executor boundary must not replace the caller's action identity."""

    executor = bind_successful_executor(make_executor())

    proposal = make_proposal(action_id="caller-owned-id")

    result = executor.execute(proposal)

    assert result.action_id == proposal.action_id


def test_bound_property_reflects_explicit_binding() -> None:
    """Binding state must be observable and deterministic."""

    executor = make_executor()

    assert executor.bound is False

    executor.bind(
        lambda proposal: {
            "action_id": proposal.action_id,
        }
    )

    assert executor.bound is True


def test_bind_rejects_non_callable_executor() -> None:
    """A non-callable executor must never become the execution mechanism."""

    executor = make_executor()

    with pytest.raises((TypeError, ValueError)):
        executor.bind(None)  # type: ignore[arg-type]


def test_invalid_timeout_is_rejected() -> None:
    """Timeout values must fail closed rather than being silently normalized."""

    executor = make_executor()

    invalid_values = (
        -1,
        0,
        float("nan"),
        float("inf"),
        float("-inf"),
    )

    for timeout in invalid_values:
        with pytest.raises((TypeError, ValueError)):
            executor._validate_timeout(timeout)


def test_valid_timeout_is_accepted() -> None:
    """Positive finite timeout values are valid configuration."""

    executor = make_executor()

    for timeout in (0.1, 1.0, 5.0, 30.0):
        assert executor._validate_timeout(timeout) == timeout


def test_none_timeout_remains_unset() -> None:
    """An omitted timeout must remain explicitly unset."""

    executor = make_executor()

    assert executor._validate_timeout(None) is None


def test_attempted_uses_action_id_as_replay_boundary() -> None:
    """Replay tracking must be deterministic and action-specific."""

    executor = bind_successful_executor(make_executor())

    proposal = make_proposal(action_id="tracked-action")

    assert executor.attempted("tracked-action") is False

    result = executor.execute(proposal)

    assert result.status is ProductionExecutorStatus.EXECUTED
    assert executor.attempted("tracked-action") is True
    assert executor.attempted("different-action") is False


def test_reset_only_clears_local_attempt_memory() -> None:
    """Reset must only clear local replay state."""

    executor = bind_successful_executor(make_executor())

    proposal = make_proposal(action_id="reset-action")

    result = executor.execute(proposal)

    assert result.status is ProductionExecutorStatus.EXECUTED
    assert executor.attempted("reset-action") is True

    executor.reset()

    assert executor.attempted("reset-action") is False


def test_reset_does_not_unbind_executor() -> None:
    """Reset must not silently destroy production executor binding."""

    executor = bind_successful_executor(make_executor())

    assert executor.bound is True

    executor.reset()

    assert executor.bound is True


def test_success_result_contains_execution_evidence() -> None:
    """Successful execution must retain deterministic evidence."""

    executor = bind_successful_executor(make_executor())

    result = executor.execute(make_proposal())

    assert isinstance(result.evidence, dict)

    assert (
        result.evidence.get("production_execution_completed") is True
        or result.evidence.get("execution_succeeded") is True
        or result.evidence.get("mutation_succeeded") is True
    )


def test_failure_result_contains_failure_evidence() -> None:
    """Failure must retain enough evidence to diagnose the boundary."""

    executor = make_executor()

    def failing_executor(proposal: ActionProposal) -> None:
        raise RuntimeError("controlled failure")

    executor.bind(failing_executor)

    result = executor.execute(make_proposal())

    assert result.status is ProductionExecutorStatus.FAILED
    assert isinstance(result.evidence, dict)


def test_identity_is_descriptive_not_authoritative() -> None:
    """
    Executor identity metadata must not itself authorize execution.

    A named/versioned executor without an explicitly bound callable remains
    blocked.
    """

    executor = make_executor()

    assert executor.identity is not None
    assert executor.identity.name
    assert executor.identity.version

    result = executor.execute(make_proposal())

    assert result.allowed is False
    assert result.block_reason is ProductionExecutorBlockReason.EXECUTOR_MISSING


def test_capability_is_descriptive_not_authoritative() -> None:
    """
    Capability metadata alone must not grant mutation authority.
    """

    executor = make_executor()

    assert executor.capability is not None
    assert executor.capability.name

    result = executor.execute(make_proposal())

    assert result.allowed is False
    assert result.block_reason is ProductionExecutorBlockReason.EXECUTOR_MISSING


def test_describe_is_observation_only() -> None:
    """describe() must not execute or mark an action as attempted."""

    executor = make_executor()
    proposal = make_proposal()

    description = executor.describe()

    assert description is not None
    assert executor.attempted(proposal.action_id) is False


def test_preflight_does_not_mark_action_as_attempted() -> None:
    """Preflight must never consume the action replay slot."""

    executor = bind_successful_executor(make_executor())
    proposal = make_proposal()

    result = executor.preflight(proposal)

    assert result.allowed is True
    assert executor.attempted(proposal.action_id) is False


def test_multiple_action_ids_are_independently_executable() -> None:
    """Replay protection must not incorrectly block unrelated actions."""

    calls: list[str] = []

    executor = bind_successful_executor(
        make_executor(),
        calls=calls,
    )

    first = executor.execute(
        make_proposal(action_id="action-A")
    )
    second = executor.execute(
        make_proposal(action_id="action-B")
    )

    assert first.status is ProductionExecutorStatus.EXECUTED
    assert second.status is ProductionExecutorStatus.EXECUTED
    assert calls == ["action-A", "action-B"]


def test_same_action_id_with_different_payload_is_still_replay_blocked() -> None:
    """
    action_id remains the replay boundary.

    Changing parameters must not create a second execution opportunity for the
    same action identity.
    """

    calls: list[str] = []

    executor = bind_successful_executor(
        make_executor(),
        calls=calls,
    )

    first = executor.execute(
        make_proposal(
            action_id="same-id",
            parameters={"value": 1},
        )
    )

    second = executor.execute(
        make_proposal(
            action_id="same-id",
            parameters={"value": 999},
        )
    )

    assert first.status is ProductionExecutorStatus.EXECUTED
    assert second.status is ProductionExecutorStatus.BLOCKED
    assert second.block_reason is ProductionExecutorBlockReason.ALREADY_ATTEMPTED
    assert calls == ["same-id"]


def test_production_result_is_serializable() -> None:
    """Result serialization must remain deterministic."""

    executor = bind_successful_executor(make_executor())

    result = executor.execute(make_proposal())

    payload = result.to_dict()

    assert isinstance(payload, dict)
    assert payload["action_id"] == "action-001"
    assert payload["status"] == ProductionExecutorStatus.EXECUTED.value
    assert payload["allowed"] is True


def test_failure_result_is_serializable() -> None:
    """Failure results must also have a stable machine representation."""

    executor = make_executor()

    def failing_executor(proposal: ActionProposal) -> None:
        raise RuntimeError("failure")

    executor.bind(failing_executor)

    result = executor.execute(make_proposal())

    payload = result.to_dict()

    assert isinstance(payload, dict)
    assert payload["status"] == ProductionExecutorStatus.FAILED.value
    assert payload["allowed"] is False


def test_production_executor_never_invents_controller_commands() -> None:
    """
    The production boundary accepts a callable; it must not synthesize a
    controller command when one is absent.
    """

    executor = make_executor()

    result = executor.execute(
        make_proposal(
            action="some-controller-operation",
            target="REOS_CONTROL_CENTER",
        )
    )

    assert result.allowed is False
    assert result.block_reason is ProductionExecutorBlockReason.EXECUTOR_MISSING


def test_execution_envelope_is_data_only() -> None:
    """
    ExecutionEnvelope must remain a data contract and must not implicitly
    execute anything.
    """

    proposal = make_proposal()

    envelope = ExecutionEnvelope(
        proposal=proposal,
    )

    assert envelope.proposal.action_id == proposal.action_id


def test_failure_types_are_machine_distinguishable() -> None:
    """Production failure classes must remain explicit and distinguishable."""

    assert issubclass(ProductionExecutorFailure, Exception)


def test_status_values_are_closed() -> None:
    """Executor lifecycle states must remain explicit."""

    assert {
        member.value
        for member in ProductionExecutorStatus
    } == {
        "BLOCKED",
        "READY",
        "EXECUTED",
        "FAILED",
    }


def test_block_reasons_are_machine_readable() -> None:
    """Critical refusal reasons must remain stable enum values."""

    required = {
        ProductionExecutorBlockReason.INVALID_PROPOSAL,
        ProductionExecutorBlockReason.EXECUTOR_MISSING,
        ProductionExecutorBlockReason.EXECUTOR_INVALID,
        ProductionExecutorBlockReason.ALREADY_ATTEMPTED,
    }

    assert required.issubset(
        set(ProductionExecutorBlockReason)
    )


def test_bound_executor_is_the_only_execution_path() -> None:
    """
    The only successful execution path must be an explicitly bound callable.
    """

    calls: list[str] = []

    executor = make_executor()

    result_before_binding = executor.execute(
        make_proposal(action_id="before-bind")
    )

    assert result_before_binding.allowed is False
    assert calls == []

    executor.bind(
        lambda proposal: calls.append(proposal.action_id)
    )

    result_after_binding = executor.execute(
        make_proposal(action_id="after-bind")
    )

    assert result_after_binding.allowed is True
    assert calls == ["after-bind"]