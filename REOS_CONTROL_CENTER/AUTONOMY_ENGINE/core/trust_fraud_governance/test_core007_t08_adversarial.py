"""CORE-007 T08 — adversarial and false-positive regression tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from .governance_policy import (
    GovernanceActionClass,
    GovernanceDisposition,
    GovernancePolicy,
    GovernancePolicyConflictError,
    GovernanceRule,
)
from .governance_engine import (
    GovernanceEngine,
    GovernanceScopeError,
)
from .risk_rules import (
    RiskRule,
    RiskRuleCondition,
    RiskRuleEngine,
    RiskRuleOutcome,
    RiskRulePolicy,
)
from .trust_score import (
    TrustScoreEngine,
    TrustScoringModel,
    TrustSignal,
)


NOW = datetime(
    2026,
    9,
    30,
    12,
    0,
    tzinfo=timezone.utc,
)

TENANT = "tenant-t03"
SUBJECT = "subject-t03"


def trust_score(value: int):
    signal = TrustSignal(
        signal_id="adversarial-signal",
        tenant_id=TENANT,
        subject_id=SUBJECT,
        category="identity",
        value=value,
        evidence_reference="evidence://trust/adversarial",
        source_reference="source://trust/adversarial",
        observed_at=NOW,
    )

    return TrustScoreEngine.compute(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        signals=(signal,),
        model=TrustScoringModel(
            model_version="1.0",
            category_weights_bps={"identity": 10000},
        ),
        computed_at=NOW,
    )


def risk_policy():
    return RiskRulePolicy(
        policy_id="T03-ADV",
        version="1.0",
        rules=(
            RiskRule(
                rule_id="LOW-TRUST",
                version="1.0",
                priority=100,
                condition=RiskRuleCondition.TRUST_SCORE_RANGE,
                outcome=RiskRuleOutcome.HIGH,
                description="Low trust.",
                max_trust_score=39,
            ),
        ),
    )


def governance_policy():
    return GovernancePolicy(
        policy_id="T04-ADV",
        version="1.0",
        rules=(
            GovernanceRule(
                rule_id="HIGH-RISK-REVIEW",
                version="1.0",
                action_class=GovernanceActionClass.HIGH_RISK,
                disposition=GovernanceDisposition.APPROVAL_REQUIRED,
                priority=100,
                reason="High risk requires approval.",
            ),
        ),
    )


def test_false_positive_information_is_not_promoted() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="false-positive",
        policy=risk_policy(),
        trust_score=trust_score(90),
        evaluated_at=NOW,
    )

    assert result.outcome is RiskRuleOutcome.INFORMATIONAL


def test_high_risk_requires_governance_review_boundary() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="high-risk",
        policy=risk_policy(),
        trust_score=trust_score(20),
        evaluated_at=NOW,
    )

    governance = GovernanceEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="high-risk",
        policy=governance_policy(),
        risk_evaluation=result,
        evaluated_at=NOW,
    )

    assert governance.disposition is (
        GovernanceDisposition.APPROVAL_REQUIRED
    )


def test_cross_tenant_governance_input_is_rejected() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="tenant-boundary",
        policy=risk_policy(),
        trust_score=trust_score(20),
        evaluated_at=NOW,
    )

    with pytest.raises(GovernanceScopeError):
        GovernanceEngine().evaluate(
            tenant_id="another-tenant",
            subject_id=SUBJECT,
            correlation_id="tenant-boundary",
            policy=governance_policy(),
            risk_evaluation=result,
            evaluated_at=NOW,
        )


def test_expired_governance_policy_is_rejected() -> None:
    policy = GovernancePolicy(
        policy_id="EXPIRED",
        version="1.0",
        rules=(),
        effective_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
    )

    with pytest.raises(Exception):
        GovernanceEngine().evaluate(
            tenant_id=TENANT,
            subject_id=SUBJECT,
            correlation_id="expired",
            policy=policy,
            evaluated_at=NOW,
        )


def test_same_policy_identity_rejects_conflicting_definition() -> None:
    first = governance_policy()

    second = GovernancePolicy(
        policy_id="T04-ADV",
        version="1.0",
        rules=(
            GovernanceRule(
                rule_id="HIGH-RISK-REVIEW",
                version="1.0",
                action_class=GovernanceActionClass.CRITICAL,
                disposition=GovernanceDisposition.ESCALATE,
                priority=100,
                reason="Conflicting definition.",
            ),
        ),
    )

    with pytest.raises(
        GovernancePolicyConflictError
    ):
        first.assert_compatible(second)


def test_governance_evaluation_is_not_authorization() -> None:
    result = RiskRuleEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="boundary",
        policy=risk_policy(),
        trust_score=trust_score(20),
        evaluated_at=NOW,
    )

    governance = GovernanceEngine().evaluate(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="boundary",
        policy=governance_policy(),
        risk_evaluation=result,
        evaluated_at=NOW,
    )

    payload = governance.to_dict()

    forbidden = {
        "authorization",
        "authorized",
        "allow",
        "allowed",
        "deny",
        "denied",
        "execute",
        "payment",
    }

    assert {
        str(key).lower()
        for key in payload
    }.isdisjoint(forbidden)
