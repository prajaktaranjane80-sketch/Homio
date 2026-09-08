"""
ACRL T15 — Integration Tests.
"""

from .operator_autonomy import (
    OperatorAutonomyEngine,
    OperatorRequest,
)
from .operator_decision_boundary import (
    OperatorDecisionBoundary,
)
from .operator_integration import (
    OperatorIntegrationEngine,
)
from .operator_policy import (
    OperatorActionType,
    OperatorDecision,
)
from .operator_validation import (
    OperatorContext,
)


def make_context(**overrides):
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


def make_request(**overrides):
    values = {
        "context": make_context(),
        "requested_action": OperatorActionType.ANALYZE,
        "objective": "Analyze current validated evidence.",
        "evidence": ("validated_state",),
        "metadata": {},
    }

    values.update(overrides)
    return OperatorRequest(**values)


def test_safe_context_boundary_is_propose():
    assert (
        OperatorDecisionBoundary.classify(
            make_context()
        )
        is OperatorDecision.PROPOSE
    )


def test_missing_state_boundary_is_block():
    assert (
        OperatorDecisionBoundary.classify(
            make_context(
                state_available=False
            )
        )
        is OperatorDecision.BLOCK
    )


def test_invalid_integrity_boundary_is_fail_closed():
    assert (
        OperatorDecisionBoundary.classify(
            make_context(
                integrity_valid=False
            )
        )
        is OperatorDecision.FAIL_CLOSED
    )


def test_invalid_authority_boundary_is_fail_closed():
    assert (
        OperatorDecisionBoundary.classify(
            make_context(
                authority_valid=False
            )
        )
        is OperatorDecision.FAIL_CLOSED
    )


def test_safe_request_produces_external_handoff():
    report = OperatorAutonomyEngine.operate(
        make_request()
    )

    handoff = (
        OperatorIntegrationEngine.build_handoff(
            report
        )
    )

    assert handoff.decision == "PROPOSE"
    assert handoff.execution_authorized is False
    assert handoff.state_mutated is False
