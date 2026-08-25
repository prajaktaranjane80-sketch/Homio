"""
Adversarial tests for the additive execution coordinator.

These tests verify that the coordinator:

- remains fail-closed;
- never invents authority;
- never executes without explicit safety conditions;
- never silently retries;
- preserves replay protection;
- requires complete postflight evidence;
- delegates mutation only through the controlled mutation boundary;
- does not mutate REOS_CONTROL_CENTER state directly.

These tests are additive and must not modify existing controller files.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from orchestration.execution_coordinator import (  # noqa: E402
    CoordinationStatus,
    ExecutionContext,
    ExecutionCoordinator,
)
from protocols.action_protocol import ActionProposal  # noqa: E402


def make_proposal(
    action_id: str = "coord-001",
) -> ActionProposal:
    """Create a deterministic valid action proposal."""

    return ActionProposal(
        action_id=action_id,
        action="create_project",
        target="project:test-001",
        parameters={"source": "coordinator-test"},
        requester="test-agent",
        tenant_id="tenant-test",
    )


def fully_authorized_context() -> ExecutionContext:
    """Create a fully positive execution context."""

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
            "source": "test_execution_coordinator_adversarial",
        },
    )


def test_invalid_proposal_is_blocked() -> None:
    """Malformed proposals must never reach the executor."""

    coordinator = ExecutionCoordinator()
    calls: list[str] = []

    proposal = ActionProposal(
        action_id="invalid-001",
        action="",
        target=None,  # type: ignore[arg-type]
    )

    result = coordinator.execute(
        proposal,
        fully_authorized_context(),
        executor=lambda _: calls.append("called"),
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert calls == []


@pytest.mark.parametrize(
    "field",
    [
        "authorized",
        "capability_available",
        "policy_allowed",
        "risk_allowed",
        "guard_allowed",
        "idempotency_clear",
        "tripwires_clear",
    ],
)
def test_each_required_safety_condition_defaults_to_block(
    field: str,
) -> None:
    """Every required safety condition must independently block execution."""

    coordinator = ExecutionCoordinator()
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

    result = coordinator.execute(
        make_proposal(),
        context,
        executor=lambda _: calls.append("called"),
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert calls == []


def test_architecture_lock_blocks_execution() -> None:
    """Frozen architecture must prevent mutation."""

    coordinator = ExecutionCoordinator()
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

    result = coordinator.execute(
        make_proposal(),
        context,
        executor=lambda _: calls.append("called"),
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert calls == []


def test_missing_executor_is_blocked() -> None:
    """The coordinator must never invent an executor."""

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=None,
    )

    assert result.status is CoordinationStatus.BLOCKED
    assert result.allowed is False
    assert result.mutation is not None
    assert result.mutation.executed is False


def test_preflight_never_executes_executor() -> None:
    """Preflight must have zero execution side effects."""

    coordinator = ExecutionCoordinator()
    calls: list[str] = []

    proposal = make_proposal()
    context = fully_authorized_context()

    protocol, enforcement = coordinator.preflight(
        proposal,
        context,
    )

    assert protocol.valid is True
    assert enforcement is not None
    assert enforcement.allowed is True
    assert calls == []


def test_executor_failure_is_terminal() -> None:
    """Executor failure must not become success or trigger retry."""

    coordinator = ExecutionCoordinator()
    calls: list[str] = []

    def failing_executor(_: ActionProposal) -> None:
        calls.append("called")
        raise RuntimeError("simulated failure")

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=failing_executor,
    )

    assert result.status is CoordinationStatus.FAILED
    assert result.allowed is False
    assert calls == ["called"]


def test_failed_execution_cannot_be_replayed() -> None:
    """A failed action must not be silently retried by the coordinator."""

    coordinator = ExecutionCoordinator()
    calls: list[str] = []

    def failing_executor(_: ActionProposal) -> None:
        calls.append("called")
        raise RuntimeError("failure")

    proposal = make_proposal()

    first = coordinator.execute(
        proposal,
        fully_authorized_context(),
        executor=failing_executor,
    )

    second = coordinator.execute(
        proposal,
        fully_authorized_context(),
        executor=failing_executor,
    )

    assert first.status is CoordinationStatus.FAILED
    assert second.status is CoordinationStatus.BLOCKED
    assert calls == ["called"]


def test_success_without_postflight_evidence_is_not_success() -> None:
    """
    Mutation execution alone is insufficient.

    Complete postflight evidence is mandatory before final success.
    """

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: {"accepted": True},
        postflight={},
    )

    assert result.status is CoordinationStatus.FAILED
    assert result.allowed is False
    assert result.mutation is not None
    assert result.mutation.executed is True


def test_incomplete_postflight_evidence_is_blocked() -> None:
    """Partial postflight evidence must fail closed."""

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: {"accepted": True},
        postflight={
            "evidence_complete": True,
            "provenance_valid": False,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.FAILED
    assert result.allowed is False


def test_complete_postflight_produces_executed_result() -> None:
    """Only complete execution and verification may produce success."""

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: {"accepted": True},
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.status is CoordinationStatus.EXECUTED
    assert result.allowed is True
    assert result.mutation is not None
    assert result.mutation.executed is True
    assert result.evidence["execution_succeeded"] is True
    assert result.evidence["postflight_passed"] is True


def test_successful_action_cannot_be_replayed() -> None:
    """A successful action must execute only once."""

    coordinator = ExecutionCoordinator()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    proposal = make_proposal()

    first = coordinator.execute(
        proposal,
        fully_authorized_context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    second = coordinator.execute(
        proposal,
        fully_authorized_context(),
        executor=executor,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert first.status is CoordinationStatus.EXECUTED
    assert second.status is CoordinationStatus.BLOCKED
    assert calls == ["coord-001"]


def test_coordinated_state_is_local_only() -> None:
    """Coordinator replay memory must remain local to the instance."""

    coordinator = ExecutionCoordinator()

    assert coordinator.coordinated("coord-001") is False

    coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: "ok",
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert coordinator.coordinated("coord-001") is True


def test_reset_clears_only_local_coordination_memory() -> None:
    """Reset must not imply persistent controller-state deletion."""

    coordinator = ExecutionCoordinator()

    coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: "ok",
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert coordinator.coordinated("coord-001") is True

    coordinator.reset()

    assert coordinator.coordinated("coord-001") is False


def test_evidence_is_preserved() -> None:
    """Caller-provided evidence must survive coordination."""

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: "ok",
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.evidence["test"] is True
    assert (
        result.evidence["source"]
        == "test_execution_coordinator_adversarial"
    )


def test_to_dict_is_deterministic_and_serializable() -> None:
    """Final coordination result must expose a serializable structure."""

    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        make_proposal(),
        fully_authorized_context(),
        executor=lambda _: {"accepted": True},
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    payload = result.to_dict()

    assert isinstance(payload, dict)
    assert payload["status"] == "EXECUTED"
    assert payload["action_id"] == "coord-001"
    assert payload["allowed"] is True
    assert isinstance(payload["evidence"], dict)