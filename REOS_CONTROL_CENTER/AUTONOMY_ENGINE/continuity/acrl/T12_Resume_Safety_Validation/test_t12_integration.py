"""
T12 Resume Safety Validation — Integration Tests

Validates the T10 → T11 → T12 evidence boundary.

Safety boundary:
- T12 does not mutate authoritative state.
- T12 does not perform recovery.
- T12 does not execute business actions.
- T12 only produces resume-safety evidence.
"""

from dataclasses import FrozenInstanceError

import pytest

from .resume_safety_validation import (
    ResumeDecision,
    ResumeSafetyReason,
    ResumeSafetyRequest,
    ResumeSafetyValidator,
)
from .resume_policy import ResumePolicyEngine
from .resume_identity import ResumeIdentityEngine
from .resume_provenance import ResumeProvenanceEngine
from .resume_validation import ResumeValidationEngine
from .resume_compatibility import (
    ResumeCompatibilityEngine,
    ResumeCompatibilityStatus,
)
from .resume_metrics import ResumeMetricsEngine


def _safe_request(**overrides):
    data = {
        "checkpoint_available": True,
        "checkpoint_valid": True,
        "state_available": True,
        "state_valid": True,
        "gate_available": True,
        "gate_valid": True,
        "authority_valid": True,
        "integrity_valid": True,
        "architecture_stable": True,
        "recovery_safe": True,
        "state_ambiguous": False,
        "state_stale": False,
        "metadata": {},
    }
    data.update(overrides)
    return ResumeSafetyRequest(**data)


def test_t12_complete_safe_pipeline():
    request = _safe_request()

    policy = ResumePolicyEngine.default()

    assert policy.allow_state_mutation is False

    ResumeValidationEngine.validate_request_structure(request)
    ResumeValidationEngine.validate_policy(policy)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.SAFE_TO_RESUME
    assert report.reason is ResumeSafetyReason.VALID
    assert report.validated is True
    assert report.fail_closed is False

    identity = ResumeIdentityEngine.build(
        report.request_fingerprint,
        report.decision,
    )

    ResumeIdentityEngine.validate(identity)

    provenance = ResumeProvenanceEngine.build(
        source_layer="T11_RECOVERY_FAIL_CLOSED",
        source_identity="T11-RECOVERY-VALIDATED",
        source_fingerprint=report.request_fingerprint,
        policy_version=policy.version,
    )

    ResumeProvenanceEngine.validate(provenance)

    metrics = ResumeMetricsEngine.from_report(report)
    summary = ResumeMetricsEngine.summarize([report])

    assert metrics.decision == "SAFE_TO_RESUME"
    assert summary["total"] == 1
    assert summary["safe_to_resume"] == 1
    assert summary["block_resume"] == 0
    assert summary["fail_closed"] == 0


def test_t12_unsafe_pipeline_blocks_resume():
    request = _safe_request(recovery_safe=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.BLOCK_RESUME
    assert report.fail_closed is False
    assert report.validated is True

    summary = ResumeMetricsEngine.summarize([report])

    assert summary["total"] == 1
    assert summary["block_resume"] == 1
    assert summary["safe_to_resume"] == 0


def test_t12_architecture_drift_fail_closes():
    request = _safe_request(architecture_stable=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.FAIL_CLOSED
    assert report.fail_closed is True
    assert report.reason is ResumeSafetyReason.ARCHITECTURE_DRIFT


def test_t12_ambiguous_state_fail_closes():
    request = _safe_request(state_ambiguous=True)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.FAIL_CLOSED
    assert report.fail_closed is True
    assert report.reason is ResumeSafetyReason.AMBIGUOUS_STATE


def test_t12_stale_state_blocks_resume():
    request = _safe_request(state_stale=True)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.BLOCK_RESUME
    assert report.fail_closed is False
    assert report.reason is ResumeSafetyReason.STALE_STATE


def test_t12_missing_checkpoint_blocks_resume():
    request = _safe_request(checkpoint_available=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.BLOCK_RESUME
    assert report.reason is ResumeSafetyReason.MISSING_CHECKPOINT


def test_t12_invalid_checkpoint_fail_closes():
    request = _safe_request(checkpoint_valid=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.FAIL_CLOSED
    assert report.fail_closed is True
    assert report.reason is ResumeSafetyReason.CHECKPOINT_INVALID


def test_t12_invalid_state_fail_closes():
    request = _safe_request(state_valid=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.FAIL_CLOSED
    assert report.fail_closed is True
    assert report.reason is ResumeSafetyReason.STATE_INVALID


def test_t12_invalid_gate_fail_closes():
    request = _safe_request(gate_valid=False)

    report = ResumeSafetyValidator.validate(request)

    assert report.decision is ResumeDecision.FAIL_CLOSED
    assert report.fail_closed is True
    assert report.reason is ResumeSafetyReason.GATE_INVALID


def test_t12_provenance_requires_authoritative_source_evidence():
    with pytest.raises(Exception):
        ResumeProvenanceEngine.build(
            source_layer="UNKNOWN_LAYER",
            source_identity="UNKNOWN",
            source_fingerprint="a" * 64,
            policy_version="T12-POLICY-1.0",
        )


def test_t12_compatibility_current_schema_is_supported():
    status = ResumeCompatibilityEngine.schema_status("1.0")

    assert status is ResumeCompatibilityStatus.SUPPORTED


def test_t12_compatibility_current_policy_is_supported():
    status = ResumeCompatibilityEngine.policy_status(
        "T12-POLICY-1.0"
    )

    assert status is ResumeCompatibilityStatus.SUPPORTED


def test_t12_compatibility_current_identity_is_supported():
    status = ResumeCompatibilityEngine.identity_status(
        "T12-IDENTITY-1.0"
    )

    assert status is ResumeCompatibilityStatus.SUPPORTED


def test_t12_compatibility_current_provenance_is_supported():
    status = ResumeCompatibilityEngine.provenance_status(
        "T12-PROVENANCE-1.0"
    )

    assert status is ResumeCompatibilityStatus.SUPPORTED


def test_t12_compatibility_unknown_schema_does_not_pass():
    status = ResumeCompatibilityEngine.schema_status("")

    assert status is ResumeCompatibilityStatus.UNKNOWN


def test_t12_compatibility_incompatible_schema_does_not_pass():
    status = ResumeCompatibilityEngine.schema_status("9.9")

    assert status is ResumeCompatibilityStatus.INCOMPATIBLE


def test_t12_identity_is_deterministic():
    request = _safe_request()
    report = ResumeSafetyValidator.validate(request)

    first = ResumeIdentityEngine.build(
        report.request_fingerprint,
        report.decision,
    )

    second = ResumeIdentityEngine.build(
        report.request_fingerprint,
        report.decision,
    )

    assert first.identity_fingerprint == second.identity_fingerprint


def test_t12_request_is_immutable():
    request = _safe_request()

    with pytest.raises(FrozenInstanceError):
        request.state_valid = False


def test_t12_report_is_immutable():
    report = ResumeSafetyValidator.validate(_safe_request())

    with pytest.raises(FrozenInstanceError):
        report.validated = False


def test_t12_no_safe_resume_from_invalid_integrity():
    request = _safe_request(integrity_valid=False)

    with pytest.raises(Exception):
        ResumeSafetyValidator.validate(request)


def test_t12_no_safe_resume_from_invalid_authority():
    request = _safe_request(authority_valid=False)

    with pytest.raises(Exception):
        ResumeSafetyValidator.validate(request)


def test_t12_metrics_are_observational_only():
    safe_report = ResumeSafetyValidator.validate(
        _safe_request()
    )

    blocked_report = ResumeSafetyValidator.validate(
        _safe_request(recovery_safe=False)
    )

    summary = ResumeMetricsEngine.summarize(
        [safe_report, blocked_report]
    )

    assert summary["total"] == 2
    assert summary["safe_to_resume"] == 1
    assert summary["block_resume"] == 1
    assert summary["fail_closed"] == 0


def test_t12_contract_report_machine_readable():
    report = ResumeSafetyValidator.validate(_safe_request())

    data = report.to_dict()

    required = {
        "schema_version",
        "authority",
        "decision",
        "reason",
        "request_fingerprint",
        "validated",
        "fail_closed",
        "explanation",
    }

    assert required.issubset(data.keys())


def test_t12_resume_or_raise_accepts_only_safe_resume():
    request = _safe_request()

    report = ResumeSafetyValidator.validate_or_raise(request)

    assert report.decision is ResumeDecision.SAFE_TO_RESUME


def test_t12_resume_or_raise_rejects_blocked_resume():
    request = _safe_request(recovery_safe=False)

    with pytest.raises(Exception):
        ResumeSafetyValidator.validate_or_raise(request)


def test_t12_full_decision_matrix_never_allows_unsafe_resume():
    cases = [
        {"checkpoint_available": False},
        {"checkpoint_valid": False},
        {"state_available": False},
        {"state_valid": False},
        {"gate_available": False},
        {"gate_valid": False},
        {"architecture_stable": False},
        {"recovery_safe": False},
        {"state_ambiguous": True},
        {"state_stale": True},
    ]

    for mutation in cases:
        request = _safe_request(**mutation)

        try:
            report = ResumeSafetyValidator.validate(request)
        except Exception:
            continue

        assert report.decision is not ResumeDecision.SAFE_TO_RESUME


def test_t12_safe_resume_requires_complete_evidence_chain():
    request = _safe_request()

    report = ResumeSafetyValidator.validate(request)

    assert report.validated is True
    assert report.fail_closed is False
    assert report.decision is ResumeDecision.SAFE_TO_RESUME

    identity = ResumeIdentityEngine.build(
        report.request_fingerprint,
        report.decision,
    )

    assert identity.request_fingerprint == report.request_fingerprint
    assert identity.decision is ResumeDecision.SAFE_TO_RESUME

    ResumeIdentityEngine.validate(identity)


def test_t12_provenance_identity_is_deterministic():
    fingerprint = "b" * 64

    first = ResumeProvenanceEngine.build(
        source_layer="T11_RECOVERY_FAIL_CLOSED",
        source_identity="T11-RECOVERY-VALIDATED",
        source_fingerprint=fingerprint,
        policy_version="T12-POLICY-1.0",
    )

    second = ResumeProvenanceEngine.build(
        source_layer="T11_RECOVERY_FAIL_CLOSED",
        source_identity="T11-RECOVERY-VALIDATED",
        source_fingerprint=fingerprint,
        policy_version="T12-POLICY-1.0",
    )

    assert first.to_dict() == second.to_dict()


def test_t12_policy_is_fail_safe():
    policy = ResumePolicyEngine.default()

    assert policy.require_authority is True
    assert policy.require_integrity is True
    assert policy.architecture_drift_fails_closed is True
    assert policy.allow_state_mutation is False


def test_t12_layer_does_not_promote_derived_data_to_authority():
    policy = ResumePolicyEngine.default()

    assert policy.authority == "REOS_CONTROL_CENTER"
    assert policy.allow_state_mutation is False


def test_t12_compatibility_fail_closed_boundary():
    status = ResumeCompatibilityEngine.schema_status("9.9")

    assert status is ResumeCompatibilityStatus.INCOMPATIBLE
