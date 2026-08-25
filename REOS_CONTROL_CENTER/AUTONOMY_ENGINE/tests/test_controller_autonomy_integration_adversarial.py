"""
Adversarial integration tests for:

REOS_CONTROL_CENTER <-> AUTONOMY_ENGINE

This test layer verifies the integration boundary without replacing
the authoritative controller or creating a second controller authority.

Guarantees under test:
- Controller remains authoritative.
- AUTONOMY_ENGINE remains an execution/orchestration layer.
- Read-only observation cannot become mutation.
- Mutation requires explicit authorization inputs.
- No executor discovery is permitted.
- Architecture lock fails closed.
- Missing safety conditions fail closed.
- Replay protection remains active.
- Postflight failure cannot become success.
- Controller integration does not silently mutate state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bridge.readonly_controller_bridge import ReadOnlyControllerBridge
from integration.preflight import run_preflight
from integration.safe_next import next_safe_action
from orchestration.execution_coordinator import (
    ExecutionContext,
    ExecutionCoordinator,
)
from protocols.action_protocol import ActionProposal
from execution.mutation_adapter import (
    ControlledMutationAdapter,
    MutationRequest,
    MutationBlockReason,
)


def make_root(tmp_path: Path) -> Path:
    """
    Create a minimal controller root for boundary tests.

    The integration tests intentionally do not create or mutate a real
    REOS_CONTROL_CENTER state file.
    """
    return tmp_path


def make_proposal() -> ActionProposal:
    return ActionProposal.create(
        action="TEST_ACTION",
        target="TEST_TARGET",
        parameters={"source": "integration-test"},
        requester="integration-test",
    )


def fully_authorized_context(
    *,
    architecture_locked: bool = False,
) -> ExecutionContext:
    return ExecutionContext(
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=architecture_locked,
        evidence={
            "integration_test": True,
            "controller_authority": "REOS_CONTROL_CENTER",
        },
    )


def test_readonly_bridge_never_exposes_mutation_commands() -> None:
    bridge = ReadOnlyControllerBridge(Path("."))

    for command in (
        "complete-subtask",
        "verify-criterion",
        "validate-gate",
        "approve-gate",
        "transition",
        "repair",
        "reset",
    ):
        with pytest.raises(PermissionError):
            bridge.run(command)


def test_readonly_bridge_rejects_unknown_commands() -> None:
    bridge = ReadOnlyControllerBridge(Path("."))

    with pytest.raises(PermissionError):
        bridge.run("invented-controller-command")


def test_readonly_bridge_safe_commands_are_explicitly_allowlisted() -> None:
    bridge = ReadOnlyControllerBridge(Path("."))

    assert bridge.SAFE_COMMANDS == (
        "verify-state",
        "status",
        "plan",
        "gate",
        "verify-all",
    )


def test_autonomy_engine_cannot_execute_without_explicit_executor() -> None:
    coordinator = ExecutionCoordinator()
    proposal = make_proposal()
    context = fully_authorized_context()

    result = coordinator.execute(
        proposal,
        context,
        executor=None,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.allowed is False
    assert result.mutation is not None
    assert result.mutation.executed is False
    assert result.mutation.decision.block_reason is (
        MutationBlockReason.EXECUTOR_MISSING
    )


def test_executor_discovery_is_never_attempted() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=None,
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.EXECUTOR_MISSING


def test_architecture_lock_blocks_mutation_even_when_other_conditions_pass() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=True,
        executor=lambda _: "MUST_NOT_RUN",
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.ARCHITECTURE_LOCKED


def test_missing_authorization_fails_closed() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=False,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=lambda _: "MUST_NOT_RUN",
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.NOT_AUTHORIZED


def test_missing_policy_fails_closed() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=False,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=lambda _: "MUST_NOT_RUN",
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.POLICY_DENIED


def test_missing_risk_clearance_fails_closed() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=False,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=lambda _: "MUST_NOT_RUN",
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.RISK_DENIED


def test_tripwire_failure_blocks_controller_execution() -> None:
    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=False,
        architecture_locked=False,
        executor=lambda _: "MUST_NOT_RUN",
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.TRIPWIRE_BLOCKED


def test_idempotency_failure_blocks_before_executor() -> None:
    called = False

    def executor(_: ActionProposal) -> str:
        nonlocal called
        called = True
        return "MUST_NOT_RUN"

    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=False,
        tripwires_clear=True,
        architecture_locked=False,
        executor=executor,
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.block_reason is MutationBlockReason.IDEMPOTENCY_BLOCKED
    assert called is False


def test_successful_executor_is_single_shot() -> None:
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> str:
        calls.append(proposal.action_id)
        return "controller-result"

    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=executor,
    )

    first = adapter.execute(request)
    second = adapter.execute(request)

    assert first.executed is True
    assert second.executed is False
    assert len(calls) == 1
    assert adapter.attempted(proposal.action_id) is True


def test_executor_failure_is_not_reported_as_success() -> None:
    def executor(_: ActionProposal) -> str:
        raise RuntimeError("controller execution failure")

    adapter = ControlledMutationAdapter()
    proposal = make_proposal()

    request = MutationRequest(
        proposal=proposal,
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        executor=executor,
    )

    result = adapter.execute(request)

    assert result.executed is False
    assert result.decision.status.value == "FAILED"
    assert result.evidence["mutation_attempted"] is True
    assert result.evidence["mutation_succeeded"] is False


def test_coordinator_rejects_invalid_context_before_mutation() -> None:
    coordinator = ExecutionCoordinator()
    proposal = make_proposal()

    context = ExecutionContext(
        authorized=False,
        capability_available=False,
        policy_allowed=False,
        risk_allowed=False,
        guard_allowed=False,
        idempotency_clear=False,
        tripwires_clear=False,
        architecture_locked=True,
    )

    called = False

    def executor(_: ActionProposal) -> str:
        nonlocal called
        called = True
        return "MUST_NOT_RUN"

    result = coordinator.execute(
        proposal,
        context,
        executor=executor,
    )

    assert result.allowed is False
    assert called is False
    assert result.evidence["execution_attempted"] is False


def test_postflight_failure_cannot_become_success() -> None:
    coordinator = ExecutionCoordinator()
    proposal = make_proposal()
    context = fully_authorized_context()

    result = coordinator.execute(
        proposal,
        context,
        executor=lambda _: "controller-result",
        postflight={
            "evidence_complete": True,
            "provenance_valid": False,
            "state_consistent": True,
        },
    )

    assert result.status.value == "FAILED"
    assert result.allowed is False
    assert result.evidence["execution_succeeded"] is True
    assert result.evidence["postflight_passed"] is False


def test_preflight_does_not_execute_executor() -> None:
    coordinator = ExecutionCoordinator()
    proposal = make_proposal()
    context = fully_authorized_context()

    called = False

    def executor(_: ActionProposal) -> str:
        nonlocal called
        called = True
        return "MUST_NOT_RUN"

    protocol, enforcement = coordinator.preflight(
        proposal,
        context,
    )

    assert protocol.valid is True
    assert enforcement is not None
    assert called is False


def test_controller_integration_preflight_fails_closed_when_entrypoint_missing(
    tmp_path: Path,
) -> None:
    result = run_preflight(make_root(tmp_path))

    assert result.safe is False
    assert "CONTROL_CENTER_ENTRYPOINT_MISSING" in result.blockers


def test_safe_next_action_stops_when_controller_integration_is_unavailable(
    tmp_path: Path,
) -> None:
    result = next_safe_action(make_root(tmp_path))

    assert result.status == "BLOCKED"
    assert result.action == "STOP_AND_DIAGNOSE"
    assert result.reason


def test_integration_boundary_does_not_modify_controller_root(
    tmp_path: Path,
) -> None:
    root = make_root(tmp_path)

    before = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
    )

    run_preflight(root)
    next_safe_action(root)

    after = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
    )

    assert before == after


def test_controller_authority_is_explicit_in_execution_evidence() -> None:
    context = fully_authorized_context()

    assert context.evidence["controller_authority"] == "REOS_CONTROL_CENTER"


def test_integration_boundary_preserves_fail_closed_default() -> None:
    coordinator = ExecutionCoordinator()
    proposal = make_proposal()

    result = coordinator.execute(
        proposal,
        ExecutionContext(),
        executor=lambda _: "MUST_NOT_RUN",
    )

    assert result.allowed is False
    assert result.status.value == "BLOCKED"


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
def test_every_positive_execution_gate_is_required(field: str) -> None:
    values = {
        "authorized": True,
        "capability_available": True,
        "policy_allowed": True,
        "risk_allowed": True,
        "guard_allowed": True,
        "idempotency_clear": True,
        "tripwires_clear": True,
        "architecture_locked": False,
    }

    values[field] = False

    coordinator = ExecutionCoordinator()
    proposal = make_proposal()

    called = False

    def executor(_: ActionProposal) -> str:
        nonlocal called
        called = True
        return "MUST_NOT_RUN"

    context = ExecutionContext(**values)

    result = coordinator.execute(
        proposal,
        context,
        executor=executor,
    )

    assert result.allowed is False
    assert called is False
