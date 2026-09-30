"""CORE-007 T03 — adversarial risk-rule evaluation regression.

This suite protects the T03 risk-rule boundary against:
- cross-tenant input leakage
- cross-subject input leakage
- disabled and expired rules
- malformed rule contracts
- duplicate rule identities
- conflicting policy versions
- deterministic evaluation drift
- authorization/governance leakage
- mutable result state
- evidence loss

The suite deliberately does not create another risk engine.
It validates the existing risk_rules authority only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from .fraud_detection import (
    FraudAssessment,
    FraudFinding,
    FraudFindingCode,
    FraudSeverity,
)
from .risk_rules import (
    RiskRule,
    RiskRuleCondition,
    RiskRuleConflictError,
    RiskRuleEngine,
    RiskRuleEvaluation,
    RiskRuleOutcome,
    RiskRulePolicy,
    RiskRuleScopeError,
    RiskRuleValidationError,
)
from .trust_score import (
    TrustScoreEngine,
    TrustScoringModel,
    TrustSignal,
)


TENANT_ID = str(uuid4())
OTHER_TENANT_ID = str(uuid4())

SUBJECT_ID = str(uuid4())
OTHER_SUBJECT_ID = str(uuid4())

NOW = datetime(
    2026,
    9,
    30,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_trust_score(
    *,
    score: int,
    tenant_id: str = TENANT_ID,
    subject_id: str = SUBJECT_ID,
):
    signal = TrustSignal(
        signal_id="t03-adversarial-trust-signal",
        tenant_id=tenant_id,
        subject_id=subject_id,
        category="identity",
        value=score,
        evidence_reference="evidence://trust/t03",
        source_reference="source://trust/t03",
        observed_at=NOW,
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
        computed_at=NOW,
    )


def build_fraud_assessment(
    *,
    severity: FraudSeverity = FraudSeverity.HIGH,
    tenant_id: UUID | None = None,
    subject_id: UUID | None = None,
):
    resolved_tenant = (
        tenant_id
        if tenant_id is not None
        else UUID(TENANT_ID)
    )

    resolved_subject = (
        subject_id
        if subject_id is not None
        else UUID(SUBJECT_ID)
    )

    finding = FraudFinding(
        finding_id=uuid4(),
        tenant_id=resolved_tenant,
        subject_id=resolved_subject,
        code=FraudFindingCode.GPS_PROXY_DETECTED,
        severity=severity,
        message="T03 adversarial fraud finding.",
        evidence_references=(
            "evidence://fraud/t03",
        ),
        source_references=(
            "source://fraud/t03",
        ),
        observed_at=NOW,
    )

    return FraudAssessment(
        assessment_id=uuid4(),
        tenant_id=resolved_tenant,
        subject_id=resolved_subject,
        correlation_id="t03-adversarial",
        model_version="1.0",
        policy_fingerprint="fraud-policy-t03",
        findings=(finding,),
        tripwire_raised=(
            severity
            in {
                FraudSeverity.HIGH,
                FraudSeverity.CRITICAL,
            }
        ),
        generated_at=NOW,
    )


def trust_rule(
    *,
    rule_id: str = "TRUST-LOW",
    version: str = "1.0",
    minimum: int | None = None,
    maximum: int | None = 39,
    outcome: RiskRuleOutcome = RiskRuleOutcome.HIGH,
    enabled: bool = True,
    effective_at: datetime | None = None,
    expires_at: datetime | None = None,
):
    return RiskRule(
        rule_id=rule_id,
        version=version,
        priority=100,
        condition=RiskRuleCondition.TRUST_SCORE_RANGE,
        outcome=outcome,
        description="Low trust score adversarial test rule.",
        min_trust_score=minimum,
        max_trust_score=maximum,
        enabled=enabled,
        effective_at=effective_at,
        expires_at=expires_at,
    )


def fraud_rule(
    *,
    rule_id: str = "FRAUD-HIGH",
    version: str = "1.0",
    severity: FraudSeverity = FraudSeverity.HIGH,
    outcome: RiskRuleOutcome = RiskRuleOutcome.CRITICAL,
):
    return RiskRule(
        rule_id=rule_id,
        version=version,
        priority=200,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=outcome,
        description="Fraud severity adversarial test rule.",
        fraud_severity=severity,
    )


def test_disabled_rule_never_matches() -> None:
    rule = trust_rule(enabled=False)

    assert not rule.is_active(NOW)

    assert not rule.matches(
        trust_score=build_trust_score(score=20),
        fraud_assessment=None,
    )


def test_not_yet_effective_rule_is_inactive() -> None:
    rule = trust_rule(
        effective_at=NOW + timedelta(hours=1),
    )

    assert not rule.is_active(NOW)


def test_expired_rule_is_inactive() -> None:
    rule = trust_rule(
        effective_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
    )

    assert not rule.is_active(NOW)


def test_active_window_is_respected() -> None:
    rule = trust_rule(
        effective_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=1),
    )

    assert rule.is_active(NOW)


def test_duplicate_rule_identity_is_rejected() -> None:
    rule = trust_rule()

    with pytest.raises(RiskRuleConflictError):
        RiskRulePolicy(
            policy_id="T03-DUPLICATE",
            version="1.0",
            rules=(
                rule,
                rule,
            ),
        )


def test_invalid_trust_range_is_rejected() -> None:
    with pytest.raises(RiskRuleValidationError):
        trust_rule(
            minimum=90,
            maximum=10,
        )


def test_invalid_fraud_rule_shape_is_rejected() -> None:
    with pytest.raises(RiskRuleValidationError):
        RiskRule(
            rule_id="INVALID-FRAUD",
            version="1.0",
            priority=10,
            condition=RiskRuleCondition.FRAUD_TRIPWIRE,
            outcome=RiskRuleOutcome.HIGH,
            description="Invalid mixed rule.",
            fraud_severity=FraudSeverity.HIGH,
        )


def test_cross_tenant_trust_input_is_rejected() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-SCOPE",
        version="1.0",
        rules=(
            trust_rule(),
        ),
    )

    trust = build_trust_score(
        score=20,
        tenant_id=OTHER_TENANT_ID,
    )

    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            correlation_id="cross-tenant-trust",
            policy=policy,
            trust_score=trust,
            evaluated_at=NOW,
        )


def test_cross_subject_trust_input_is_rejected() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-SUBJECT",
        version="1.0",
        rules=(
            trust_rule(),
        ),
    )

    trust = build_trust_score(
        score=20,
        subject_id=OTHER_SUBJECT_ID,
    )

    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            correlation_id="cross-subject-trust",
            policy=policy,
            trust_score=trust,
            evaluated_at=NOW,
        )


def test_cross_tenant_fraud_input_is_rejected() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-FRAUD-SCOPE",
        version="1.0",
        rules=(
            fraud_rule(),
        ),
    )

    fraud = build_fraud_assessment(
        tenant_id=UUID(OTHER_TENANT_ID),
        subject_id=UUID(SUBJECT_ID),
    )

    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            correlation_id="cross-tenant-fraud",
            policy=policy,
            fraud_assessment=fraud,
            evaluated_at=NOW,
        )


def test_cross_subject_fraud_input_is_rejected() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-FRAUD-SUBJECT",
        version="1.0",
        rules=(
            fraud_rule(),
        ),
    )

    fraud = build_fraud_assessment(
        tenant_id=UUID(TENANT_ID),
        subject_id=UUID(OTHER_SUBJECT_ID),
    )

    with pytest.raises(RiskRuleScopeError):
        RiskRuleEngine().evaluate(
            tenant_id=TENANT_ID,
            subject_id=SUBJECT_ID,
            correlation_id="cross-subject-fraud",
            policy=policy,
            fraud_assessment=fraud,
            evaluated_at=NOW,
        )


def test_higher_priority_rule_controls_precedence() -> None:
    low_rule = RiskRule(
        rule_id="LOW-PRIORITY",
        version="1.0",
        priority=10,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=RiskRuleOutcome.REVIEW,
        description="Lower priority rule.",
        fraud_severity=FraudSeverity.HIGH,
    )

    critical_rule = RiskRule(
        rule_id="HIGH-PRIORITY",
        version="1.0",
        priority=100,
        condition=RiskRuleCondition.FRAUD_SEVERITY,
        outcome=RiskRuleOutcome.CRITICAL,
        description="Higher priority rule.",
        fraud_severity=FraudSeverity.HIGH,
    )

    policy = RiskRulePolicy(
        policy_id="T03-PRECEDENCE",
        version="1.0",
        rules=(
            low_rule,
            critical_rule,
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="precedence",
        policy=policy,
        fraud_assessment=build_fraud_assessment(
            severity=FraudSeverity.HIGH,
        ),
        evaluated_at=NOW,
    )

    assert result.outcome is RiskRuleOutcome.CRITICAL
    assert result.matched_rule_ids[0] == "HIGH-PRIORITY"


def test_evaluation_identity_is_deterministic() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-DETERMINISM",
        version="1.0",
        rules=(
            trust_rule(),
        ),
    )

    first = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="determinism",
        policy=policy,
        trust_score=build_trust_score(score=20),
        evaluated_at=NOW,
        evaluation_id=UUID(int=101),
    )

    second = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="determinism",
        policy=policy,
        trust_score=build_trust_score(score=20),
        evaluated_at=NOW,
        evaluation_id=UUID(int=202),
    )

    assert first.determinism_key == second.determinism_key
    assert first.fingerprint == second.fingerprint


def test_evaluation_is_immutable() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-IMMUTABLE",
        version="1.0",
        rules=(
            trust_rule(),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="immutable",
        policy=policy,
        trust_score=build_trust_score(score=20),
        evaluated_at=NOW,
    )

    assert isinstance(result, RiskRuleEvaluation)

    with pytest.raises(AttributeError):
        result.outcome = RiskRuleOutcome.CRITICAL  # type: ignore[misc]


def test_policy_fingerprint_changes_when_rule_changes() -> None:
    first = RiskRulePolicy(
        policy_id="T03-FINGERPRINT",
        version="1.0",
        rules=(
            trust_rule(
                outcome=RiskRuleOutcome.HIGH,
            ),
        ),
    )

    second = RiskRulePolicy(
        policy_id="T03-FINGERPRINT",
        version="1.0",
        rules=(
            trust_rule(
                outcome=RiskRuleOutcome.CRITICAL,
            ),
        ),
    )

    assert first.fingerprint != second.fingerprint


def test_same_policy_identity_rejects_changed_definition() -> None:
    first = RiskRulePolicy(
        policy_id="T03-CONFLICT",
        version="1.0",
        rules=(
            trust_rule(
                outcome=RiskRuleOutcome.HIGH,
            ),
        ),
    )

    second = RiskRulePolicy(
        policy_id="T03-CONFLICT",
        version="1.0",
        rules=(
            trust_rule(
                outcome=RiskRuleOutcome.CRITICAL,
            ),
        ),
    )

    with pytest.raises(RiskRuleConflictError):
        first.assert_compatible(second)


def test_evaluation_does_not_become_authorization_engine() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-BOUNDARY",
        version="1.0",
        rules=(
            trust_rule(),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="boundary",
        policy=policy,
        trust_score=build_trust_score(score=20),
        evaluated_at=NOW,
    )

    payload = result.to_dict()

    forbidden = {
        "authorization",
        "authorized",
        "approval",
        "approved",
        "allow",
        "allowed",
        "deny",
        "denied",
        "payment",
        "execute",
    }

    assert {
        str(key).lower()
        for key in payload
    }.isdisjoint(forbidden)


def test_evidence_references_are_preserved() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-EVIDENCE",
        version="1.0",
        rules=(
            fraud_rule(),
        ),
    )

    fraud = build_fraud_assessment()

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="evidence",
        policy=policy,
        fraud_assessment=fraud,
        evaluated_at=NOW,
    )

    assert (
        fraud.fingerprint
        in result.evidence_references
    )

    assert (
        "evidence://fraud/t03"
        in result.evidence_references
    )


def test_serialized_result_contains_rule_and_policy_identity() -> None:
    policy = RiskRulePolicy(
        policy_id="T03-SERIALIZATION",
        version="7.0",
        rules=(
            trust_rule(
                rule_id="SERIAL-RULE",
                version="3.0",
            ),
        ),
    )

    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT_ID,
        subject_id=SUBJECT_ID,
        correlation_id="serialization",
        policy=policy,
        trust_score=build_trust_score(score=20),
        evaluated_at=NOW,
    )

    payload = result.to_dict()

    assert payload["policy_id"] == "T03-SERIALIZATION"
    assert payload["policy_version"] == "7.0"
    assert "SERIAL-RULE" in payload["matched_rule_ids"]
    assert "fingerprint" in payload
