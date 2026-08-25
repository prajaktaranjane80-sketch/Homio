"""Adversarial tests for AUTONOMY_ENGINE enforcement boundary."""

from __future__ import annotations

from protocols.action_protocol import ActionProposal
from execution.enforcement import EnforcementEngine


def valid_proposal() -> ActionProposal:
    return ActionProposal(
        action_id="test-action-001",
        action="read_state",
        target="controller_state",
    )


def test_preflight_accepts_valid_proposal() -> None:
    engine = EnforcementEngine()

    decision = engine.preflight(
        valid_proposal(),
        checks={
            "integrity": lambda: True,
            "authorization": lambda: True,
            "capability": lambda: True,
            "policy": lambda: True,
        },
    )

    assert decision.allowed is True
    assert decision.failures == ()


def test_preflight_rejects_invalid_proposal() -> None:
    engine = EnforcementEngine()

    proposal = ActionProposal(
        action_id="test-action-002",
        action="",
        target=None,
    )

    decision = engine.preflight(proposal)

    assert decision.allowed is False
    assert "action_protocol:action is required." in decision.failures
    assert any(
        failure.startswith("action_protocol:")
        for failure in decision.failures
    )


def test_failed_preflight_blocks_mutation() -> None:
    engine = EnforcementEngine()
    called = False

    def mutation(_: ActionProposal) -> bool:
        nonlocal called
        called = True
        return True

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: False,
        },
        mutation_adapter=mutation,
    )

    assert result.preflight.allowed is False
    assert result.execution_attempted is False
    assert called is False


def test_missing_mutation_adapter_fails_closed() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
    )

    assert result.preflight.allowed is True
    assert result.execution_attempted is False
    assert result.execution_succeeded is False
    assert result.postflight.allowed is False
    assert "mutation_adapter_missing" in result.postflight.failures


def test_non_callable_mutation_adapter_fails_closed() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter="not-callable",
    )

    assert result.execution_attempted is False
    assert result.execution_succeeded is False
    assert "mutation_adapter_invalid" in result.postflight.failures


def test_mutation_exception_is_not_success() -> None:
    engine = EnforcementEngine()

    def mutation(_: ActionProposal) -> bool:
        raise RuntimeError("simulated mutation failure")

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter=mutation,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.execution_attempted is True
    assert result.execution_succeeded is False
    assert result.postflight.allowed is False
    assert "execution_failed" in result.postflight.failures


def test_false_mutation_result_is_not_success() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter=lambda _: False,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.execution_attempted is True
    assert result.execution_succeeded is False
    assert result.postflight.allowed is False


def test_incomplete_evidence_blocks_completion() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter=lambda _: True,
        postflight={
            "evidence_complete": False,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.execution_succeeded is True
    assert result.postflight.allowed is False
    assert "evidence_incomplete" in result.postflight.failures


def test_invalid_provenance_blocks_completion() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter=lambda _: True,
        postflight={
            "evidence_complete": True,
            "provenance_valid": False,
            "state_consistent": True,
        },
    )

    assert result.postflight.allowed is False
    assert "provenance_invalid" in result.postflight.failures


def test_inconsistent_state_blocks_completion() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "security": lambda: True,
        },
        mutation_adapter=lambda _: True,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": False,
        },
    )

    assert result.postflight.allowed is False
    assert "state_inconsistent" in result.postflight.failures


def test_complete_success_requires_all_postflight_conditions() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "integrity": lambda: True,
            "authorization": lambda: True,
            "capability": lambda: True,
            "policy": lambda: True,
        },
        mutation_adapter=lambda _: True,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    assert result.preflight.allowed is True
    assert result.execution_attempted is True
    assert result.execution_succeeded is True
    assert result.postflight.allowed is True
    assert result.allowed is True


def test_preflight_check_exception_fails_closed() -> None:
    engine = EnforcementEngine()

    def broken_check() -> bool:
        raise RuntimeError("tripwire failure")

    decision = engine.preflight(
        valid_proposal(),
        checks={
            "tripwire": broken_check,
        },
    )

    assert decision.allowed is False
    assert "tripwire:exception:RuntimeError" in decision.failures


def test_non_boolean_preflight_result_fails_closed() -> None:
    engine = EnforcementEngine()

    decision = engine.preflight(
        valid_proposal(),
        checks={
            "security": lambda: 1,
        },
    )

    assert decision.allowed is False
    assert "security:failed" in decision.failures


def test_postflight_requires_explicit_true_values() -> None:
    engine = EnforcementEngine()

    decision = engine.postflight(
        execution_succeeded=1,
        evidence_complete=1,
        provenance_valid=1,
        state_consistent=1,
    )

    assert decision.allowed is False
    assert "execution_failed" in decision.failures
    assert "evidence_incomplete" in decision.failures
    assert "provenance_invalid" in decision.failures
    assert "state_inconsistent" in decision.failures


def test_failed_preflight_skips_postflight_as_success() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={
            "architecture_lock": lambda: False,
        },
        mutation_adapter=lambda _: True,
    )

    assert result.execution_attempted is False
    assert result.postflight.allowed is False
    assert "preflight_failed" in result.postflight.failures


def test_result_serialization_is_deterministic() -> None:
    engine = EnforcementEngine()

    result = engine.enforce(
        valid_proposal(),
        preflight_checks={"security": lambda: True},
        mutation_adapter=lambda _: True,
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
    )

    payload = result.to_dict()

    assert payload["allowed"] is True
    assert payload["execution_attempted"] is True
    assert payload["execution_succeeded"] is True
    assert payload["preflight"]["allowed"] is True
    assert payload["postflight"]["allowed"] is True