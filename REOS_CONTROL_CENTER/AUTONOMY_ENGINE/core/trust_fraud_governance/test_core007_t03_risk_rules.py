from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from .fraud_detection import (
    FraudDetectionEngine,
    FraudDetectionScopeError,
    FraudSeverity,
    VisitTelemetryObservation,
)

from .risk_rules import (
    RISK_RULE_ENGINE_VERSION,
    RiskRule,
    RiskRuleCondition,
    RiskRuleConflictError,
    RiskRuleEngine,
    RiskRuleOutcome,
    RiskRulePolicy,
    RiskRuleScopeError,
    RiskRuleValidationError,
    default_fraud_risk_policy,
)

from .trust_score import (
    TrustScoreEngine,
    TrustScoringModel,
    TrustSignal,
)


TENANT = "tenant-001"
OTHER_TENANT = "tenant-999"
SUBJECT = "subject-001"
OTHER_SUBJECT = "subject-999"

NOW = datetime(
    2026,
    9,
    30,
    10,
    0,
    tzinfo=timezone.utc,
)

EVALUATION_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def trust_model() -> TrustScoringModel:
    return TrustScoringModel(
        model_version="1.0",
        category_weights_bps={
            "EVIDENCE": 10000,
        },
    )


def trust_signal(
    *,
    value: int = 80,
    tenant_id: str = TENANT,
    subject_id: str = SUBJECT,
    signal_id: str = "signal-001",
) -> TrustSignal:
    return TrustSignal(
        signal_id=signal_id,
        tenant_id=tenant_id,
        subject_id=subject_id,
        category="EVIDENCE",
        value=value,
        evidence_reference="evidence://trust/001",
        source_reference="source://trust/001",
        observed_at=NOW,
    )


def trust_score(
    *,
    value: int = 80,
    tenant_id: str = TENANT,
    subject_id: str = SUBJECT,
) :
    return TrustScoreEngine.compute(
        tenant_id=tenant_id,
        subject_id=subject_id,
        signals=(
            trust_signal(
                value=value,
                tenant_id=tenant_id,
                subject_id=subject_id,
            ),
        ),
        model=trust_model(),
        computed_at=NOW,
    )


def fraud_assessment(
    *,
    tenant_id=TENANT,
    subject_id=SUBJECT,
    mock_location: bool = False,
):
    observations = ()

    if mock_location:
        observations = (
            VisitTelemetryObservation(
                observation_id=UUID(
                    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
                ),
                tenant_id=UUID(
                    "11111111-1111-1111-1111-111111111111"
                ),
                lead_id=UUID(
                    "33333333-3333-3333-3333-333333333333"
                ),
                observed_at=NOW,
                evidence_reference="evidence://fraud/001",
                source_reference="source://fraud/001",
                mock_location_provider=True,
            ),
        )

        return FraudDetectionEngine().detect(
            tenant_id=observations[0].tenant_id,
            subject_id=observations[0].lead_id,
            correlation_id="fraud-001",
            visit_observations=observations,
            generated_at=NOW,
        )

    return FraudDetectionEngine().detect(
        tenant_id=UUID(
            "11111111-1111-1111-1111-111111111111"
        ),
        subject_id=UUID(
            "33333333-3333-3333-3333-333333333333"
        ),
        correlation_id="fraud-clean-001",
        generated_at=NOW,
    )


def critical_fraud_assessment():
    return fraud_assessment(
        mock_location=True,
    )


def review_rule() -> RiskRule:
    return RiskRule(
        rule_id="RULE-REVIEW",
        version="1.0",
        priority=10,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=RiskRuleOutcome.REVIEW,
        description="Review when fraud is in review state.",
        fraud_severity=FraudSeverity.REVIEW,
    )


def critical_rule() -> RiskRule:
    return RiskRule(
        rule_id="RULE-CRITICAL",
        version="1.0",
        priority=20,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=RiskRuleOutcome.CRITICAL,
        description="Critical fraud requires critical risk classification.",
        fraud_severity=FraudSeverity.CRITICAL,
    )


def test_rule_is_immutable_and_fingerprinted() -> None:
    rule = review_rule()

    assert rule.fingerprint

    with pytest.raises(AttributeError):
        rule.priority = 99  # type: ignore[misc]


def test_rule_requires_valid_priority() -> None:
    with pytest.raises(RiskRuleValidationError):
        RiskRule(
            rule_id="RULE-1",
            version="1.0",
            priority=0,
            condition=RiskRuleCondition.FRAUD_TRIPWIRE,
            outcome=RiskRuleOutcome.HIGH,
            description="Invalid priority.",
        )


def test_rule_rejects_invalid_trust_range() -> None:
    with pytest.raises(RiskRuleValidationError):
        RiskRule(
            rule_id="RULE-TRUST",
            version="1.0",
            priority=10,
            condition=RiskRuleCondition.TRUST_SCORE_RANGE,
            outcome=RiskRuleOutcome.REVIEW,
            description="Invalid range.",
            min_trust_score=90,
            max_trust_score=20,
        )


def test_trust_rule_requires_at_least_one_bound() -> None:
    with pytest.raises(RiskRuleValidationError):
        RiskRule(
            rule_id="RULE-TRUST",
            version="1.0",
            priority=10,
            condition=RiskRuleCondition.TRUST_SCORE_RANGE,
            outcome=RiskRuleOutcome.REVIEW,
            description="Missing range bounds.",
        )


def test_fraud_severity_rule_requires_severity() -> None:
    with pytest.raises(RiskRuleValidationError):
        RiskRule(
            rule_id="RULE-FRAUD",
            version="1.0",
            priority=10,
            condition=RiskRuleCondition.FRAUD_SEVERITY,
            outcome=RiskRuleOutcome.REVIEW,
            description="Missing severity.",
        )


def test_policy_rejects_duplicate_rule_identity() -> None:
    rule = review_rule()

    with pytest.raises(RiskRuleConflictError):
        RiskRulePolicy(
            policy_id="POLICY-001",
            version="1.0",
            rules=(rule, rule),
        )


def test_policy_is_order_independent() -> None:
    policy_one = RiskRulePolicy(
        policy_id="POLICY-001",
        version="1.0",
        rules=(
            review_rule(),
            critical_rule(),
        ),
    )

    policy_two = RiskRulePolicy(
        policy_id="POLICY-001",
        version="1.0",
        rules=(
            critical_rule(),
            review_rule(),
        ),
    )

    assert policy_one.fingerprint == policy_two.fingerprint


def test_policy_conflicting_same_identity_is_rejected() -> None:
    first = RiskRulePolicy(
        policy_id="POLICY-001",
        version="1.0",
        rules=(review_rule(),),
    )

    conflicting_rule = RiskRule(
        rule_id="RULE-REVIEW",
        version="1.0",
        priority=10,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=RiskRuleOutcome.HIGH,
        description="Conflicting result.",
        fraud_severity=FraudSeverity.REVIEW,
    )

    second = RiskRulePolicy(
        policy_id="POLICY-001",
        version="1.0",
        rules=(conflicting_rule,),
    )

    with pytest.raises(RiskRuleConflictError):
        first.assert_compatible(second)


def test_default_policy_has_explicit_version() -> None:
    policy = default_fraud_risk_policy()

    assert policy.policy_id == "CORE-007-FRAUD-BASELINE"
    assert policy.version == "1.0"
    assert policy.fingerprint


def test_default_policy_without_evidence_is_informational() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-001",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.INFORMATIONAL
    assert result.matched_rule_ids == ()


def test_critical_fraud_maps_to_critical() -> None:
    assessment = critical_fraud_assessment()

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-critical",
        policy=default_fraud_risk_policy(),
        fraud_assessment=assessment,
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.CRITICAL
    assert "FRAUD-SEVERITY-CRITICAL" in result.matched_rule_ids


def test_fraud_tripwire_maps_to_high() -> None:
    assessment = critical_fraud_assessment()

    policy = RiskRulePolicy(
        policy_id="TRIPWIRE-POLICY",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="TRIPWIRE-HIGH",
                version="1.0",
                priority=20,
                condition=RiskRuleCondition.FRAUD_TRIPWIRE,
                outcome=RiskRuleOutcome.HIGH,
                description="Tripwire creates high risk classification.",
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=str(assessment.tenant_id),
        subject_id=str(assessment.subject_id),
        correlation_id="eval-tripwire",
        policy=policy,
        fraud_assessment=assessment,
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.HIGH
    assert result.matched_rule_ids == (
        "TRIPWIRE-HIGH",
    )


def test_trust_score_range_rule_matches() -> None:
    policy = RiskRulePolicy(
        policy_id="TRUST-POLICY",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="TRUST-HIGH",
                version="1.0",
                priority=50,
                condition=RiskRuleCondition.TRUST_SCORE_RANGE,
                outcome=RiskRuleOutcome.REVIEW,
                description="Review within configured trust range.",
                min_trust_score=70,
                max_trust_score=90,
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-trust",
        policy=policy,
        trust_score=trust_score(value=80),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.REVIEW
    assert result.trust_score == 80


@pytest.mark.parametrize(
    "value",
    (69, 91),
)
def test_trust_score_range_rule_rejects_outside_values(
    value: int,
) -> None:
    policy = RiskRulePolicy(
        policy_id="TRUST-POLICY",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="TRUST-BOUNDARY",
                version="1.0",
                priority=50,
                condition=RiskRuleCondition.TRUST_SCORE_RANGE,
                outcome=RiskRuleOutcome.REVIEW,
                description="Bounded trust rule.",
                min_trust_score=70,
                max_trust_score=90,
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id=f"eval-trust-{value}",
        policy=policy,
        trust_score=trust_score(value=value),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.INFORMATIONAL
    assert result.matched_rule_ids == ()


def test_disabled_rule_does_not_match() -> None:
    policy = RiskRulePolicy(
        policy_id="DISABLED-POLICY",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="DISABLED-RULE",
                version="1.0",
                priority=100,
                condition=RiskRuleCondition.FRAUD_SEVERITY,
                outcome=RiskRuleOutcome.CRITICAL,
                description="Disabled rule.",
                fraud_severity=FraudSeverity.CRITICAL,
                enabled=False,
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-disabled",
        policy=policy,
        fraud_assessment=critical_fraud_assessment(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.INFORMATIONAL


def test_expired_rule_does_not_match() -> None:
    policy = RiskRulePolicy(
        policy_id="EXPIRY-POLICY",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="EXPIRED-RULE",
                version="1.0",
                priority=100,
                condition=RiskRuleCondition.FRAUD_TRIPWIRE,
                outcome=RiskRuleOutcome.CRITICAL,
                description="Expired rule.",
                expires_at=NOW - timedelta(seconds=1),
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-expired",
        policy=policy,
        fraud_assessment=critical_fraud_assessment(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.INFORMATIONAL


def test_future_policy_is_rejected() -> None:
    policy = RiskRulePolicy(
        policy_id="FUTURE-POLICY",
        version="1.0",
        effective_at=NOW + timedelta(minutes=1),
        rules=(),
    )

    with pytest.raises(RiskRuleValidationError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT,
            subject_id=SUBJECT,
            correlation_id="eval-future",
            policy=policy,
            evaluated_at=NOW,
            evaluation_id=EVALUATION_ID,
        )


def test_highest_outcome_wins_over_lower_priority() -> None:
    policy = RiskRulePolicy(
        policy_id="PRECEDENCE-POLICY",
        version="1.0",
        rules=(
            review_rule(),
            critical_rule(),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-precedence",
        policy=policy,
        fraud_assessment=critical_fraud_assessment(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.outcome is RiskRuleOutcome.CRITICAL
    assert result.matched_rule_ids[0] == (
        "RULE-CRITICAL"
    )


def test_cross_tenant_trust_score_is_rejected() -> None:
    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT,
            subject_id=SUBJECT,
            correlation_id="eval-scope-trust",
            policy=RiskRulePolicy(
                policy_id="SCOPE-POLICY",
                version="1.0",
                rules=(),
            ),
            trust_score=trust_score(
                tenant_id=OTHER_TENANT,
                subject_id=SUBJECT,
            ),
            evaluated_at=NOW,
            evaluation_id=EVALUATION_ID,
        )


def test_cross_subject_trust_score_is_rejected() -> None:
    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT,
            subject_id=SUBJECT,
            correlation_id="eval-scope-subject",
            policy=RiskRulePolicy(
                policy_id="SCOPE-POLICY",
                version="1.0",
                rules=(),
            ),
            trust_score=trust_score(
                tenant_id=TENANT,
                subject_id=OTHER_SUBJECT,
            ),
            evaluated_at=NOW,
            evaluation_id=EVALUATION_ID,
        )


def test_cross_tenant_fraud_assessment_is_rejected() -> None:
    assessment = critical_fraud_assessment()

    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=OTHER_TENANT,
            subject_id=str(
                assessment.subject_id
            ),
            correlation_id="eval-scope-fraud",
            policy=default_fraud_risk_policy(),
            fraud_assessment=assessment,
            evaluated_at=NOW,
            evaluation_id=EVALUATION_ID,
        )


def test_evaluation_is_immutable() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-immutable",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    with pytest.raises(AttributeError):
        result.outcome = RiskRuleOutcome.CRITICAL  # type: ignore[misc]


def test_evaluation_fingerprint_is_deterministic() -> None:
    first = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-deterministic",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    second = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-deterministic",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert first.fingerprint == second.fingerprint
    assert first.to_dict() == second.to_dict()


def test_evaluation_serializes() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-json",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    payload = result.to_dict()

    assert payload["source_of_truth"] == "risk_rules"
    assert payload["engine_version"] == (
        RISK_RULE_ENGINE_VERSION
    )
    assert "fingerprint" in payload


def test_evaluation_does_not_contain_authorization_verdict() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-boundary",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    payload = result.to_dict()

    assert "authorization" not in payload
    assert "allowed" not in payload
    assert "approved" not in payload
    assert "deny" not in payload
    assert "approval_required" not in payload


def test_evaluation_preserves_evidence_from_fraud_and_trust() -> None:
    assessment = critical_fraud_assessment()
    score = trust_score(value=85)

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-evidence",
        policy=default_fraud_risk_policy(),
        trust_score=score,
        fraud_assessment=assessment,
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    assert result.fraud_assessment_fingerprint == (
        assessment.fingerprint
    )

    assert score.model_fingerprint in (
        result.evidence_references
    )

    assert (
        "evidence://fraud/001"
        in result.evidence_references
    )


def test_same_evaluation_identity_accepts_compatible_result() -> None:
    first = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-compatible",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    second = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-compatible",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    first.assert_compatible(second)


def test_same_evaluation_identity_rejects_conflicting_result() -> None:
    first = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-conflict",
        policy=default_fraud_risk_policy(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    conflicting_policy = RiskRulePolicy(
        policy_id="CONFLICTING-POLICY",
        version="1.0",
        rules=(
            critical_rule(),
        ),
    )

    second = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="eval-conflict",
        policy=conflicting_policy,
        fraud_assessment=critical_fraud_assessment(),
        evaluated_at=NOW,
        evaluation_id=EVALUATION_ID,
    )

    with pytest.raises(RiskRuleConflictError):
        first.assert_compatible(second)
