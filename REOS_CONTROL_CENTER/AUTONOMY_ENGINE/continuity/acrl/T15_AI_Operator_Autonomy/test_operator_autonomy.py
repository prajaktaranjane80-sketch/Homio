"""
ACRL T15 — Operator Autonomy Tests.

Tests the first bounded T15 operator implementation.

T15 test rules:
    - No direct execution.
    - No authoritative state mutation.
    - No self-approval.
    - Unsafe context must block or fail closed.
    - Valid context may produce only a bounded proposal.
"""

import pytest

from .operator_autonomy import (
    OperatorAutonomyBoundaryError,
    OperatorAutonomyEngine,
    OperatorAutonomyInputError,
    OperatorDecision,
    OperatorRequest,
)
from .operator_policy import (
    OperatorActionType,
    OperatorPolicy,
    OperatorRisk,
)
from .operator_validation import (
    OperatorContext,
    OperatorProposal,
    OperatorValidationEngine,
    OperatorValidationError,
)


def valid_context(**overrides):
    """Return a valid baseline T15 context."""

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


def valid_request(**overrides):
    """Return a valid baseline T15 request."""

    values = {
        "context": valid_context(),
        "requested_action": OperatorActionType.ANALYZE,
        "objective": "Analyze the current implementation evidence.",
        "evidence": (
            "validated_state",
            "validated_architecture",
        ),
        "metadata": {},
    }

    values.update(overrides)
    return OperatorRequest(**values)


def test_valid_context_is_accepted():
    context = valid_context()

    assert OperatorValidationEngine.validate_context(context) is True


def test_safe_analysis_produces_bounded_proposal():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.ANALYZE
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.proposal is not None
    assert report.execution_authorized is False
    assert report.state_mutated is False
    assert report.proposal.requires_authorization is True


def test_observe_action_is_low_risk():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.OBSERVE
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.risk is OperatorRisk.LOW
    assert report.proposal is not None
    assert report.proposal.risk is OperatorRisk.LOW


def test_verify_action_is_low_risk():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.VERIFY
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.risk is OperatorRisk.LOW


def test_test_action_is_low_risk():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.TEST
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.risk is OperatorRisk.LOW


def test_propose_change_is_bounded():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.PROPOSE_CHANGE,
            objective="Propose a minimal change for review.",
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.proposal is not None
    assert report.proposal.reversible is True
    assert report.proposal.requires_authorization is True
    assert report.execution_authorized is False


def test_human_decision_request_is_medium_risk():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            requested_action=OperatorActionType.REQUEST_HUMAN_DECISION,
            objective="Request a human decision for an unresolved ambiguity.",
        )
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.risk is OperatorRisk.MEDIUM
    assert report.proposal is not None
    assert report.execution_authorized is False


def test_invalid_authority_fails_closed():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                authority_valid=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False
    assert report.state_mutated is False
    assert report.proposal is None


def test_invalid_integrity_fails_closed():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                integrity_valid=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False
    assert report.state_mutated is False
    assert report.proposal is None


def test_architecture_instability_fails_closed():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                architecture_stable=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False
    assert report.proposal is None


def test_invalid_state_fails_closed():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                state_valid=False
            )
        )
    )

    assert report.decision is OperatorDecision.FAIL_CLOSED
    assert report.execution_authorized is False
    assert report.state_mutated is False


def test_missing_state_blocks_operator():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                state_available=False
            )
        )
    )

    assert report.decision is OperatorDecision.BLOCK
    assert report.execution_authorized is False
    assert report.proposal is None


def test_missing_evidence_blocks_operator():
    report = OperatorAutonomyEngine.operate(
        valid_request(
            context=valid_context(
                evidence_available=False
            )
        )
    )

    assert report.decision is OperatorDecision.BLOCK
    assert report.execution_authorized is False
    assert report.proposal is None


def test_empty_objective_is_rejected():
    with pytest.raises(OperatorAutonomyInputError):
        OperatorAutonomyEngine.operate(
            valid_request(
                objective=""
            )
        )


def test_invalid_request_type_is_rejected():
    with pytest.raises(OperatorAutonomyInputError):
        OperatorAutonomyEngine.operate(
            object()
        )


def test_invalid_context_type_is_rejected():
    with pytest.raises(OperatorAutonomyInputError):
        OperatorAutonomyEngine.operate(
            valid_request(
                context=object()
            )
        )


def test_invalid_evidence_type_is_rejected():
    with pytest.raises(OperatorAutonomyInputError):
        OperatorAutonomyEngine.operate(
            valid_request(
                evidence="invalid"
            )
        )


def test_t15_never_authorizes_execution():
    actions = (
        OperatorActionType.OBSERVE,
        OperatorActionType.VERIFY,
        OperatorActionType.ANALYZE,
        OperatorActionType.TEST,
        OperatorActionType.PROPOSE_CHANGE,
        OperatorActionType.REQUEST_HUMAN_DECISION,
    )

    for action in actions:
        report = OperatorAutonomyEngine.operate(
            valid_request(
                requested_action=action
            )
        )

        assert report.execution_authorized is False


def test_t15_never_mutates_state():
    actions = (
        OperatorActionType.OBSERVE,
        OperatorActionType.VERIFY,
        OperatorActionType.ANALYZE,
        OperatorActionType.TEST,
        OperatorActionType.PROPOSE_CHANGE,
        OperatorActionType.REQUEST_HUMAN_DECISION,
    )

    for action in actions:
        report = OperatorAutonomyEngine.operate(
            valid_request(
                requested_action=action
            )
        )

        assert report.state_mutated is False


def test_every_proposal_requires_external_authorization():
    actions = (
        OperatorActionType.OBSERVE,
        OperatorActionType.VERIFY,
        OperatorActionType.ANALYZE,
        OperatorActionType.TEST,
        OperatorActionType.PROPOSE_CHANGE,
        OperatorActionType.REQUEST_HUMAN_DECISION,
    )

    for action in actions:
        report = OperatorAutonomyEngine.operate(
            valid_request(
                requested_action=action
            )
        )

        assert report.proposal is not None
        assert report.proposal.requires_authorization is True


def test_context_fingerprint_is_deterministic():
    first = OperatorAutonomyEngine.fingerprint(
        valid_context().to_dict()
    )
    second = OperatorAutonomyEngine.fingerprint(
        valid_context().to_dict()
    )

    assert first == second
    assert len(first) == 64


def test_request_fingerprint_changes_when_objective_changes():
    first = OperatorAutonomyEngine.fingerprint(
        valid_request(
            objective="Objective A"
        ).to_dict()
    )
    second = OperatorAutonomyEngine.fingerprint(
        valid_request(
            objective="Objective B"
        ).to_dict()
    )

    assert first != second


def test_report_serialization_is_stable():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    data = report.to_dict()

    assert data["schema_version"] == "1.0"
    assert data["authority"] == "REOS_CONTROL_CENTER"
    assert data["decision"] == "PROPOSE"
    assert data["execution_authorized"] is False
    assert data["state_mutated"] is False
    assert data["proposal"] is not None


def test_policy_defaults_are_safe():
    policy = OperatorPolicy()

    assert policy.allow_state_mutation is False
    assert policy.allow_execution is False
    assert policy.allow_authority_promotion is False
    assert policy.allow_architecture_change is False
    assert policy.allow_self_approval is False
    assert policy.allow_unbounded_actions is False
    assert policy.validate() is True


def test_unsafe_policy_is_rejected():
    policy = OperatorPolicy(
        allow_execution=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_policy_rejects_authority_promotion():
    policy = OperatorPolicy(
        allow_authority_promotion=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_policy_rejects_state_mutation():
    policy = OperatorPolicy(
        allow_state_mutation=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_policy_rejects_architecture_change():
    policy = OperatorPolicy(
        allow_architecture_change=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_policy_rejects_self_approval():
    policy = OperatorPolicy(
        allow_self_approval=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_policy_rejects_unbounded_actions():
    policy = OperatorPolicy(
        allow_unbounded_actions=True
    )

    with pytest.raises(ValueError):
        policy.validate()


def test_proposal_requires_valid_fingerprint():
    proposal = OperatorProposal(
        action_type=OperatorActionType.ANALYZE,
        description="Analyze evidence.",
        risk=OperatorRisk.LOW,
        reversible=True,
        requires_authorization=True,
        evidence_basis=("evidence",),
        context_fingerprint="invalid",
    )

    with pytest.raises(OperatorValidationError):
        OperatorValidationEngine.validate_proposal(
            proposal
        )


def test_proposal_requires_authorization():
    proposal = OperatorProposal(
        action_type=OperatorActionType.ANALYZE,
        description="Analyze evidence.",
        risk=OperatorRisk.LOW,
        reversible=True,
        requires_authorization=False,
        evidence_basis=("evidence",),
        context_fingerprint="a" * 64,
    )

    with pytest.raises(OperatorValidationError):
        OperatorValidationEngine.validate_proposal(
            proposal
        )


def test_non_reversible_change_is_rejected():
    proposal = OperatorProposal(
        action_type=OperatorActionType.PROPOSE_CHANGE,
        description="Propose change.",
        risk=OperatorRisk.MEDIUM,
        reversible=False,
        requires_authorization=True,
        evidence_basis=("evidence",),
        context_fingerprint="a" * 64,
    )

    with pytest.raises(OperatorValidationError):
        OperatorValidationEngine.validate_proposal(
            proposal
        )


def test_invalid_risk_type_is_rejected():
    proposal = OperatorProposal(
        action_type=OperatorActionType.ANALYZE,
        description="Analyze evidence.",
        risk="LOW",
        reversible=True,
        requires_authorization=True,
        evidence_basis=("evidence",),
        context_fingerprint="a" * 64,
    )

    with pytest.raises(OperatorValidationError):
        OperatorValidationEngine.validate_proposal(
            proposal
        )


def test_boundary_error_is_an_engine_error():
    assert issubclass(
        OperatorAutonomyBoundaryError,
        RuntimeError,
    )


def test_input_error_is_an_engine_error():
    assert issubclass(
        OperatorAutonomyInputError,
        RuntimeError,
    )
