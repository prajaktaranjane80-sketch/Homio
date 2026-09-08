"""
ACRL T15 — Adversarial / Red-Team Tests.
"""

import pytest

from .operator_autonomy import (
    OperatorAutonomyEngine,
    OperatorRequest,
)
from .operator_integration import (
    OperatorIntegrationEngine,
    OperatorIntegrationError,
)
from .operator_policy import (
    OperatorActionType,
    OperatorDecision,
    OperatorPolicy,
    OperatorRisk,
)
from .operator_validation import (
    OperatorContext,
    OperatorProposal,
    OperatorValidationEngine,
    OperatorValidationError,
)


def context(**overrides):
    values = {
        "gate": "CORE-004",
        "subtask": "CORE-004-T01",
        "task": "Implement project domain",
        "state_available": True,
        "state_valid": True,
        "architecture_stable": True,
        "authority_valid": True,
        "integrity_valid": True,
        "evidence_available": True,
        "metadata": {},
    }

    values.update(overrides)
    return OperatorContext(**values)


def request(**overrides):
    values = {
        "context": context(),
        "requested_action": OperatorActionType.ANALYZE,
        "objective": "Analyze evidence.",
        "evidence": ("validated_state",),
        "metadata": {},
    }

    values.update(overrides)
    return OperatorRequest(**values)


def test_authority_attack_fails_closed():
    report = OperatorAutonomyEngine.operate(
        request(
            context=context(
                authority_valid=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False
    assert report.state_mutated is False


def test_integrity_attack_fails_closed():
    report = OperatorAutonomyEngine.operate(
        request(
            context=context(
                integrity_valid=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False


def test_architecture_bypass_fails_closed():
    report = OperatorAutonomyEngine.operate(
        request(
            context=context(
                architecture_stable=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.proposal is None


def test_state_bypass_is_blocked():
    report = OperatorAutonomyEngine.operate(
        request(
            context=context(
                state_available=False
            )
        )
    )

    assert report.decision is OperatorDecision.BLOCK
    assert report.execution_authorized is False


def test_evidence_bypass_is_blocked():
    report = OperatorAutonomyEngine.operate(
        request(
            context=context(
                evidence_available=False
            )
        )
    )

    assert report.decision is OperatorDecision.BLOCK
    assert report.execution_authorized is False


def test_t15_cannot_self_authorize():
    report = OperatorAutonomyEngine.operate(
        request()
    )

    assert report.execution_authorized is False

    handoff = OperatorIntegrationEngine.build_handoff(
        report
    )

    assert handoff.execution_authorized is False


def test_t15_cannot_mutate_state():
    report = OperatorAutonomyEngine.operate(
        request()
    )

    assert report.state_mutated is False


def test_execution_authorized_report_is_rejected():
    safe_report = OperatorAutonomyEngine.operate(
        request()
    )

    object.__setattr__(
        safe_report,
        "execution_authorized",
        True,
    )

    with pytest.raises(
        OperatorIntegrationError
    ):
        OperatorIntegrationEngine.build_handoff(
            safe_report
        )


def test_state_mutation_report_is_rejected():
    safe_report = OperatorAutonomyEngine.operate(
        request()
    )

    object.__setattr__(
        safe_report,
        "state_mutated",
        True,
    )

    with pytest.raises(
        OperatorIntegrationError
    ):
        OperatorIntegrationEngine.build_handoff(
            safe_report
        )


def test_unsafe_policy_cannot_enable_execution():
    with pytest.raises(ValueError):
        OperatorPolicy(
            allow_execution=True
        ).validate()


def test_unsafe_policy_cannot_enable_mutation():
    with pytest.raises(ValueError):
        OperatorPolicy(
            allow_state_mutation=True
        ).validate()


def test_proposal_without_authorization_is_rejected():
    proposal = OperatorProposal(
        action_type=OperatorActionType.ANALYZE,
        description="Analyze evidence.",
        risk=OperatorRisk.LOW,
        reversible=True,
        requires_authorization=False,
        evidence_basis=("evidence",),
        context_fingerprint="a" * 64,
    )

    with pytest.raises(
        OperatorValidationError
    ):
        OperatorValidationEngine.validate_proposal(
            proposal
        )
