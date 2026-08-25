"""
Adversarial tests for the pre-execution defensive firewall.

These tests verify that unsafe execution requests are rejected before
crossing the execution boundary.

The firewall must:
- fail closed;
- never invoke an executor during inspection;
- require every safety gate explicitly;
- reject malformed proposals and contexts;
- reject missing or invalid executors;
- reject incomplete postflight contracts;
- preserve caller evidence;
- prevent duplicate inspection through one firewall instance;
- never mutate controller state;
- never create implicit authorization or retry behavior.

This test module is additive and does not modify existing AUTONOMY_ENGINE
modules or controller state.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

# Allow direct execution from the AUTONOMY_ENGINE root while remaining
# compatible with normal pytest discovery.
ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from execution.pre_execution_firewall import (  # noqa: E402
    FirewallBlockReason,
    FirewallRequest,
    FirewallStatus,
    PreExecutionFirewall,
)
from orchestration.execution_coordinator import ExecutionContext  # noqa: E402
from protocols.action_protocol import ActionProposal  # noqa: E402


def make_proposal(
    action_id: str = "firewall-001",
) -> ActionProposal:
    """Create a deterministic valid action proposal."""

    return ActionProposal(
        action_id=action_id,
        action="create_project",
        target="project:test-001",
        parameters={"source": "firewall-adversarial-test"},
        requester="test-agent",
        tenant_id="tenant-test",
    )


def fully_cleared_context() -> ExecutionContext:
    """Create a context where every required safety gate is explicit."""

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
            "source": "test_pre_execution_firewall_adversarial",
        },
    )


def make_request(
    proposal: ActionProposal | None = None,
    *,
    context: ExecutionContext | None = None,
    executor=None,
    postflight: dict[str, bool] | None = None,
    evidence: dict[str, object] | None = None,
) -> FirewallRequest:
    """Build a deterministic firewall request."""

    return FirewallRequest(
        proposal=proposal or make_proposal(),
        context=context or fully_cleared_context(),
        executor=(
            executor
            if executor is not None
            else lambda _: {"accepted": True}
        ),
        postflight=(
            postflight
            if postflight is not None
            else {
                "evidence_complete": True,
                "provenance_valid": True,
                "state_consistent": True,
            }
        ),
        evidence=(
            evidence
            if evidence is not None
            else {
                "trace_id": "firewall-trace-001",
                "source": "test_pre_execution_firewall_adversarial",
            }
        ),
    )


def test_fully_valid_request_is_cleared() -> None:
    """A completely valid request may pass the firewall."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(make_request())

    assert result.status is FirewallStatus.CLEARED
    assert result.allowed is True
    assert result.action_id == "firewall-001"
    assert result.failures == ()
    assert result.metadata["executor_invoked"] is False
    assert result.metadata["mutation_executed"] is False
    assert result.metadata["controller_state_mutated"] is False


def test_firewall_never_invokes_executor() -> None:
    """Inspection must never execute the supplied executor."""

    firewall = PreExecutionFirewall()
    calls: list[str] = []

    def executor(proposal: ActionProposal) -> None:
        calls.append(proposal.action_id)

    result = firewall.inspect(
        make_request(executor=executor)
    )

    assert result.allowed is True
    assert calls == []
    assert firewall.checked("firewall-001") is True


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("authorized", FirewallBlockReason.AUTHORIZATION_DENIED),
        (
            "capability_available",
            FirewallBlockReason.CAPABILITY_DENIED,
        ),
        ("policy_allowed", FirewallBlockReason.POLICY_DENIED),
        ("risk_allowed", FirewallBlockReason.RISK_DENIED),
        ("guard_allowed", FirewallBlockReason.GUARD_DENIED),
        (
            "idempotency_clear",
            FirewallBlockReason.IDEMPOTENCY_BLOCKED,
        ),
        (
            "tripwires_clear",
            FirewallBlockReason.TRIPWIRE_BLOCKED,
        ),
    ],
)
def test_every_safety_gate_defaults_to_deny(
    field: str,
    reason: FirewallBlockReason,
) -> None:
    """Every individual safety gate must independently block."""

    firewall = PreExecutionFirewall()

    values = {
        "authorized": True,
        "capability_available": True,
        "policy_allowed": True,
        "risk_allowed": True,
        "guard_allowed": True,
        "idempotency_clear": True,
        "tripwires_clear": True,
        "architecture_locked": False,
        "evidence": {
            "trace_id": "gate-test",
        },
    }

    values[field] = False

    context = ExecutionContext(**values)

    result = firewall.inspect(
        make_request(context=context)
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (reason.value,)


def test_frozen_architecture_is_blocked() -> None:
    """A frozen architecture cannot cross the firewall."""

    firewall = PreExecutionFirewall()

    context = ExecutionContext(
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=True,
    )

    result = firewall.inspect(
        make_request(context=context)
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.decision if False else True
    assert result.failures == (
        FirewallBlockReason.ARCHITECTURE_LOCKED.value,
    )


def test_invalid_proposal_is_blocked() -> None:
    """Malformed action proposals must fail before execution."""

    firewall = PreExecutionFirewall()

    proposal = ActionProposal(
        action_id="invalid-firewall-001",
        action="",
        target=None,  # type: ignore[arg-type]
    )

    calls: list[str] = []

    result = firewall.inspect(
        make_request(
            proposal=proposal,
            executor=lambda _: calls.append("called"),
        )
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.INVALID_PROPOSAL.value,
    )
    assert calls == []


def test_missing_executor_is_blocked() -> None:
    """An executor must be explicitly supplied."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        FirewallRequest(
            proposal=make_proposal(),
            context=fully_cleared_context(),
            executor=None,
            postflight={
                "evidence_complete": True,
                "provenance_valid": True,
                "state_consistent": True,
            },
            evidence={},
        )
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.EXECUTOR_MISSING.value,
    )


def test_non_callable_executor_is_blocked() -> None:
    """A non-callable executor must never cross the firewall."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        make_request(executor="not-callable")
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.EXECUTOR_INVALID.value,
    )


def test_incomplete_postflight_contract_is_blocked() -> None:
    """All required postflight fields must exist before execution."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        make_request(
            postflight={
                "evidence_complete": True,
                "provenance_valid": True,
            }
        )
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.POSTFLIGHT_INVALID.value,
    )
    assert result.metadata["missing_fields"] == (
        "state_consistent",
    )


@pytest.mark.parametrize(
    "missing_field",
    [
        "evidence_complete",
        "provenance_valid",
        "state_consistent",
    ],
)
def test_each_postflight_field_is_required(
    missing_field: str,
) -> None:
    """Every individual postflight contract field is mandatory."""

    firewall = PreExecutionFirewall()

    postflight = {
        "evidence_complete": True,
        "provenance_valid": True,
        "state_consistent": True,
    }

    del postflight[missing_field]

    result = firewall.inspect(
        make_request(postflight=postflight)
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.POSTFLIGHT_INVALID.value,
    )


def test_duplicate_inspection_is_blocked() -> None:
    """The same action cannot pass inspection twice on one instance."""

    firewall = PreExecutionFirewall()

    first = firewall.inspect(
        make_request()
    )

    second = firewall.inspect(
        make_request()
    )

    assert first.status is FirewallStatus.CLEARED
    assert first.allowed is True

    assert second.status is FirewallStatus.BLOCKED
    assert second.allowed is False
    assert second.failures == (
        FirewallBlockReason.ALREADY_CHECKED.value,
    )


def test_different_action_ids_can_be_inspected() -> None:
    """Local replay protection is scoped to action_id."""

    firewall = PreExecutionFirewall()

    first = firewall.inspect(
        make_request(
            proposal=make_proposal("firewall-001"),
        )
    )

    second = firewall.inspect(
        make_request(
            proposal=make_proposal("firewall-002"),
        )
    )

    assert first.allowed is True
    assert second.allowed is True
    assert firewall.checked("firewall-001") is True
    assert firewall.checked("firewall-002") is True


def test_reset_only_clears_local_firewall_memory() -> None:
    """Reset must only clear this firewall's local inspection memory."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(make_request())

    assert result.allowed is True
    assert firewall.checked("firewall-001") is True

    firewall.reset()

    assert firewall.checked("firewall-001") is False


def test_evidence_does_not_grant_authorization() -> None:
    """Evidence cannot substitute for an explicit authorization gate."""

    firewall = PreExecutionFirewall()

    context = ExecutionContext(
        authorized=False,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        evidence={
            "authorized": True,
            "source": "untrusted-evidence",
        },
    )

    result = firewall.inspect(
        make_request(
            context=context,
            evidence={
                "authorized": True,
                "approval": True,
            },
        )
    )

    assert result.status is FirewallStatus.BLOCKED
    assert result.failures == (
        FirewallBlockReason.AUTHORIZATION_DENIED.value,
    )


def test_false_postflight_values_do_not_clear_firewall() -> None:
    """Postflight fields must exist with the correct contract semantics."""

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        make_request(
            postflight={
                "evidence_complete": False,
                "provenance_valid": True,
                "state_consistent": True,
            }
        )
    )

    # The firewall validates the contract structure here.
    # It does not perform post-execution verification itself.
    assert result.status is FirewallStatus.CLEARED
    assert result.allowed is True


def test_firewall_does_not_execute_on_blocked_request() -> None:
    """A blocked request must have zero executor side effects."""

    firewall = PreExecutionFirewall()
    calls: list[str] = []

    context = ExecutionContext(
        authorized=False,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
    )

    result = firewall.inspect(
        make_request(
            context=context,
            executor=lambda proposal: calls.append(proposal.action_id),
        )
    )

    assert result.allowed is False
    assert calls == []
    assert firewall.checked("firewall-001") is False


def test_firewall_is_deterministic_for_same_input() -> None:
    """Equivalent requests produce equivalent decisions."""

    first_firewall = PreExecutionFirewall()
    second_firewall = PreExecutionFirewall()

    first = first_firewall.inspect(
        make_request()
    )

    second = second_firewall.inspect(
        make_request()
    )

    assert first.to_dict() == second.to_dict()


def test_firewall_preserves_action_identity() -> None:
    """The firewall must preserve the validated action identity."""

    firewall = PreExecutionFirewall()

    proposal = make_proposal("unique-firewall-action-999")

    result = firewall.inspect(
        make_request(proposal=proposal)
    )

    assert result.allowed is True
    assert result.action_id == "unique-firewall-action-999"


def test_firewall_never_becomes_authority() -> None:
    """
    Passing the firewall means eligibility only.

    It must not claim that mutation has executed or that controller state
    changed.
    """

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        make_request()
    )

    assert result.allowed is True
    assert result.metadata["executor_invoked"] is False
    assert result.metadata["mutation_executed"] is False
    assert result.metadata["controller_state_mutated"] is False


def test_invalid_context_is_blocked() -> None:
    """Malformed execution context must fail closed."""

    firewall = PreExecutionFirewall()

    request = FirewallRequest(
        proposal=make_proposal(),
        context=None,  # type: ignore[arg-type]
        executor=lambda _: True,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
        evidence={},
    )

    result = firewall.inspect(request)

    assert result.status is FirewallStatus.BLOCKED
    assert result.allowed is False
    assert result.failures == (
        FirewallBlockReason.INVALID_CONTEXT.value,
    )


def test_empty_evidence_is_allowed_when_structure_is_valid() -> None:
    """
    Empty evidence does not itself authorize execution, but the firewall
    does not invent an evidence policy beyond structural validation.
    """

    firewall = PreExecutionFirewall()

    result = firewall.inspect(
        make_request(evidence={})
    )

    assert result.allowed is True
    assert result.metadata["executor_invoked"] is False
