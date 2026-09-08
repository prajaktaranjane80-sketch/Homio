"""
ACRL T15 — Contract Tests.
"""

from .operator_autonomy import (
    OperatorAutonomyEngine,
    OperatorRequest,
)
from .operator_compatibility import (
    OperatorCompatibilityEngine,
    OperatorCompatibilityStatus,
)
from .operator_identity import (
    OperatorIdentityEngine,
)
from .operator_integration import (
    OperatorIntegrationEngine,
)
from .operator_metrics import (
    OperatorMetricsEngine,
)
from .operator_policy import (
    OperatorActionType,
    OperatorDecision,
)
from .operator_validation import (
    OperatorContext,
)
from .operator_registry import (
    OperatorCapabilityRegistry,
)


def valid_context():
    return OperatorContext(
        gate="CORE-004",
        subtask="CORE-004-T01",
        task="Implement project domain",
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
        metadata={},
    )


def valid_request():
    return OperatorRequest(
        context=valid_context(),
        requested_action=OperatorActionType.ANALYZE,
        objective="Analyze validated implementation evidence.",
        evidence=("validated_state",),
        metadata={},
    )


def test_t15_authority_is_reos_control_center():
    assert (
        OperatorAutonomyEngine.AUTHORITY
        == "REOS_CONTROL_CENTER"
    )


def test_t15_safe_request_produces_proposal():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    assert report.decision is OperatorDecision.PROPOSE
    assert report.proposal is not None


def test_t15_proposal_never_authorizes_execution():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    assert report.execution_authorized is False


def test_t15_proposal_never_mutates_state():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    assert report.state_mutated is False


def test_t15_handoff_never_authorizes_execution():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    handoff = OperatorIntegrationEngine.build_handoff(
        report
    )

    assert handoff.execution_authorized is False
    assert handoff.state_mutated is False


def test_t15_identity_is_deterministic():
    identity = OperatorIdentityEngine.build(
        valid_request()
    )

    assert OperatorIdentityEngine.validate(identity)
    assert len(identity.identity_fingerprint) == 64


def test_t15_schema_is_supported():
    status = (
        OperatorCompatibilityEngine.schema_status("1.0")
    )

    assert status is OperatorCompatibilityStatus.SUPPORTED


def test_t15_registry_is_bounded():
    for capability in OperatorCapabilityRegistry.all():
        assert capability.execution_allowed is False
        assert capability.state_mutation_allowed is False
        assert capability.external_authorization_required is True


def test_t15_metrics_report_zero_execution():
    report = OperatorAutonomyEngine.operate(
        valid_request()
    )

    metrics = OperatorMetricsEngine.from_report(
        report
    )

    assert metrics.proposals == 1
    assert metrics.execution_authorized == 0
    assert metrics.state_mutations == 0
