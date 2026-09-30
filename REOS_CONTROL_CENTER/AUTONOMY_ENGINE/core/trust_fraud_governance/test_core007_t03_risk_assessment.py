"""CORE-007 T03 regression suite - Risk Assessment."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from .fraud_detection import (
    FraudAssessment,
    FraudFinding,
    FraudFindingCode,
    FraudSeverity,
)
from .risk_assessment import (
    RiskAssessmentConflictError,
    RiskAssessmentInsufficientEvidenceError,
    RiskAssessmentScopeError,
    RiskAssessmentValidationError,
    RiskFactorSource,
    RiskLevel,
)
from .risk_assessment_engine import (
    RiskAssessmentEngine,
)
from .risk_assessment_policy import (
    RiskAssessmentPolicy,
)
from .trust_score import (
    TrustScoreEngine,
    TrustScoringModel,
    TrustSignal,
)


TENANT_ID = str(uuid4())
SUBJECT_ID = str(uuid4())


def utc_now() -> datetime:
    return datetime(
        2026,
        1,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )


def build_trust_score(
    *,
    score_value: int,
    tenant_id: str = TENANT_ID,
    subject_id: str = SUBJECT_ID,
):
    signal = TrustSignal(
        signal_id="trust-signal-001",
        tenant_id=tenant_id,
        subject_id=subject_id,
        category="identity",
        value=score_value,
        evidence_reference="evidence://trust/001",
        source_reference="source://identity/001",
        observed_at=utc_now(),
    )

    model = TrustScoringModel(
        model_version="1.0",
        category_weights_bps={
            "identity": 10000,
        },
    )

    return TrustScoreEngine.compute(
        tenant_id=tenant_id,
        subject_id=subject_id,
        signals=(signal,),
        model=model,
        computed_at=utc_now(),
    )


def build_fraud_assessment(
    *,
    severity: FraudSeverity | None = FraudSeverity.HIGH,
    tenant_id: UUID | None = None,
    subject_id: UUID | None = None,
):
    resolved_tenant = (
        tenant_id
        or UUID(TENANT_ID)
    )
    resolved_subject = (
        subject_id
        or UUID(SUBJECT_ID)
    )

    findings = ()

    if severity is not None:
        findings = (
            FraudFinding(
                finding_id=uuid4(),
                tenant_id=resolved_tenant,
                subject_id=resolved_subject,
                code=FraudFindingCode.GPS_PROXY_DETECTED,
                severity=severity,
                message="Synthetic T03 test finding.",
                evidence_references=(
                    "evidence://fraud/001",
                ),
                source_references=(
                    "source://fraud/001",
                ),
                observed_at=utc_now(),
            ),
        )

    return FraudAssessment(
        assessment_id=uuid4(),
        tenant_id=resolved_tenant,
        subject_id=resolved_subject,
        correlation_id="t03-test-correlation",
        model_version="1.0",
        policy_fingerprint="fraud-policy-test",
        findings=findings,
        tripwire_raised=(
            severity in {
                FraudSeverity.HIGH,
                FraudSeverity.CRITICAL,
            }
        ),
        generated_at=utc_now(),
    )


def test_baseline_policy_is_complete_and_stable():
    first = RiskAssessmentPolicy.baseline()
    second = RiskAssessmentPolicy.baseline()

    assert first.policy_id == "CORE-007-T03-RISK-BASELINE"
    assert first.policy_version == "1.0"
    assert first.fingerprint == second.fingerprint
    assert (
        first.trust_score_rule(85).risk_level
        == RiskLevel.INFORMATIONAL
    )
    assert (
        first.trust_score_rule(10).risk_level
        == RiskLevel.CRITICAL
    )


def test_trust_score_only_produces_deterministic_assessment():
    trust = build_trust_score(score_value=85)
    engine = RiskAssessmentEngine()
    policy = RiskAssessmentPolicy.baseline()

    first = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        policy=policy,
        assessment_id=UUID(int=1),
        evaluated_at=utc_now(),
    )

    second = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        policy=policy,
        assessment_id=UUID(int=2),
        evaluated_at=utc_now(),
    )

    assert first.risk_score == 0
    assert first.risk_level == RiskLevel.INFORMATIONAL
    assert first.determinism_key == second.determinism_key
    assert first.fingerprint == second.fingerprint
    assert len(first.factors) == 1
    assert (
        first.factors[0].source_type
        == RiskFactorSource.TRUST_SCORE
    )


def test_low_trust_score_maps_to_high_risk():
    trust = build_trust_score(score_value=20)

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        evaluated_at=utc_now(),
    )

    assert assessment.risk_score == 70
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.factors[0].code == "TRUST_20_39"


def test_high_fraud_finding_is_consumed_without_reimplementing_fraud():
    fraud = build_fraud_assessment(
        severity=FraudSeverity.HIGH,
    )

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        fraud_assessment=fraud,
        evaluated_at=utc_now(),
    )

    assert assessment.risk_score == 70
    assert assessment.risk_level == RiskLevel.HIGH
    assert any(
        factor.source_type
        == RiskFactorSource.FRAUD_FINDING
        for factor in assessment.factors
    )


def test_clear_fraud_assessment_is_valid_evidence():
    fraud = build_fraud_assessment(
        severity=None,
    )

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        fraud_assessment=fraud,
        evaluated_at=utc_now(),
    )

    assert assessment.risk_score == 0
    assert assessment.risk_level == RiskLevel.INFORMATIONAL
    assert assessment.factors[0].code == (
        "FRAUD_ASSESSMENT_CLEAR"
    )
    assert (
        assessment.factors[0].source_type
        == RiskFactorSource.FRAUD_ASSESSMENT
    )


def test_combined_sources_are_deterministic():
    trust = build_trust_score(score_value=55)
    fraud = build_fraud_assessment(
        severity=FraudSeverity.REVIEW,
    )

    engine = RiskAssessmentEngine()

    first = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        fraud_assessment=fraud,
        assessment_id=UUID(int=10),
        evaluated_at=utc_now(),
    )

    second = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        fraud_assessment=fraud,
        assessment_id=UUID(int=11),
        evaluated_at=utc_now(),
    )

    assert first.risk_score == 75
    assert first.risk_level == RiskLevel.HIGH
    assert first.determinism_key == second.determinism_key
    assert first.fingerprint == second.fingerprint


def test_risk_score_is_capped_at_100():
    trust = build_trust_score(score_value=0)
    fraud = build_fraud_assessment(
        severity=FraudSeverity.CRITICAL,
    )

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        fraud_assessment=fraud,
        evaluated_at=utc_now(),
    )

    assert assessment.risk_score == 100
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_trust_scope_violation_is_rejected():
    trust = build_trust_score(
        score_value=80,
        tenant_id="different-tenant",
        subject_id=SUBJECT_ID,
    )

    with pytest.raises(Exception):
        RiskAssessmentEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            trust_score=trust,
            evaluated_at=utc_now(),
        )


def test_fraud_scope_violation_is_rejected():
    fraud = build_fraud_assessment(
        severity=FraudSeverity.HIGH,
        tenant_id=UUID(str(uuid4())),
        subject_id=UUID(SUBJECT_ID),
    )

    with pytest.raises(RiskAssessmentScopeError):
        RiskAssessmentEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            fraud_assessment=fraud,
            evaluated_at=utc_now(),
        )


def test_no_source_evidence_is_rejected():
    with pytest.raises(
        RiskAssessmentInsufficientEvidenceError
    ):
        RiskAssessmentEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            evaluated_at=utc_now(),
        )


def test_conflicting_duplicate_fraud_finding_is_rejected():
    tenant = UUID(TENANT_ID)
    subject = UUID(SUBJECT_ID)
    finding_id = uuid4()

    first_finding = FraudFinding(
        finding_id=finding_id,
        tenant_id=tenant,
        subject_id=subject,
        code=FraudFindingCode.GPS_PROXY_DETECTED,
        severity=FraudSeverity.HIGH,
        message="first",
        evidence_references=("evidence://one",),
        source_references=("source://one",),
        observed_at=utc_now(),
    )

    conflicting_finding = FraudFinding(
        finding_id=finding_id,
        tenant_id=tenant,
        subject_id=subject,
        code=FraudFindingCode.GPS_PROXY_DETECTED,
        severity=FraudSeverity.CRITICAL,
        message="conflicting",
        evidence_references=("evidence://two",),
        source_references=("source://two",),
        observed_at=utc_now(),
    )

    fraud = FraudAssessment(
        assessment_id=uuid4(),
        tenant_id=tenant,
        subject_id=subject,
        correlation_id="conflict-test",
        model_version="1.0",
        policy_fingerprint="fraud-policy",
        findings=(
            first_finding,
            conflicting_finding,
        ),
        tripwire_raised=True,
        generated_at=utc_now(),
    )

    with pytest.raises(
        RiskAssessmentConflictError
    ):
        RiskAssessmentEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            fraud_assessment=fraud,
            evaluated_at=utc_now(),
        )


def test_evidence_and_trace_are_preserved():
    trust = build_trust_score(score_value=40)

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        evaluated_at=utc_now(),
    )

    assert assessment.input_fingerprints
    assert assessment.evaluation_trace
    assert (
        assessment.evaluation_trace[0].factor_id
        == assessment.factors[0].factor_id
    )
    assert assessment.evaluation_trace[0].explanation


def test_serialization_is_stable():
    trust = build_trust_score(score_value=60)

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        assessment_id=UUID(int=99),
        evaluated_at=utc_now(),
    )

    payload = assessment.to_dict()

    assert payload["source_of_truth"] == "risk_assessment"
    assert payload["risk_score"] == 20
    assert payload["risk_level"] == RiskLevel.LOW.value
    assert payload["determinism_key"] == assessment.determinism_key
    assert payload["fingerprint"] == assessment.fingerprint


def test_same_assessment_is_compatible():
    trust = build_trust_score(score_value=80)
    engine = RiskAssessmentEngine()

    first = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        assessment_id=UUID(int=123),
        evaluated_at=utc_now(),
    )

    second = engine.evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        assessment_id=UUID(int=456),
        evaluated_at=utc_now(),
    )

    first.assert_compatible(second)


def test_assessment_boundary_does_not_publish_governance_decisions():
    trust = build_trust_score(score_value=20)

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        evaluated_at=utc_now(),
    )

    payload = assessment.to_dict()
    serialized_keys = {
        str(key).lower()
        for key in payload
    }

    forbidden = {
        "authorization",
        "authorized",
        "approval",
        "approve",
        "deny",
        "allow",
        "sanction",
        "payment",
    }

    assert serialized_keys.isdisjoint(forbidden)


def test_policy_version_and_fingerprint_are_embedded():
    trust = build_trust_score(score_value=85)
    policy = RiskAssessmentPolicy.baseline()

    assessment = RiskAssessmentEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        trust_score=trust,
        policy=policy,
        evaluated_at=utc_now(),
    )

    assert assessment.policy_version == policy.policy_version
    assert (
        assessment.policy_fingerprint
        == policy.fingerprint
    )


def test_invalid_subject_scope_is_rejected():
    trust = build_trust_score(score_value=80)

    with pytest.raises(
        Exception
    ):
        RiskAssessmentEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id="different-subject",
            trust_score=trust,
            evaluated_at=utc_now(),
        )
