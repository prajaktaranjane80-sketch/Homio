"""CORE-007 T09/T10 — policy conflict, tenant isolation and freeze regression."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from .exception_registry import (
    ExceptionRegistry,
    ExceptionScopeError,
)
from .governance_policy import (
    GovernanceActionClass,
    GovernanceDisposition,
    GovernancePolicy,
    GovernancePolicyConflictError,
    GovernanceRule,
)
from .governance_evidence import (
    EvidenceLink,
    GovernanceEvidenceEnvelope,
)
from .approval_workflow import (
    ApprovalDecision,
    ApprovalTransitionError,
    ApprovalWorkflow,
)
from .dispute_escalation import (
    EscalationHooks,
    EscalationLevel,
)


NOW = datetime(
    2026,
    9,
    30,
    12,
    0,
    tzinfo=timezone.utc,
)

TENANT = "tenant-t09"
SUBJECT = "subject-t09"


def policy() -> GovernancePolicy:
    return GovernancePolicy(
        policy_id="T09-POLICY",
        version="1.0",
        rules=(
            GovernanceRule(
                rule_id="CRITICAL-REVIEW",
                version="1.0",
                action_class=GovernanceActionClass.CRITICAL,
                disposition=GovernanceDisposition.ESCALATE,
                priority=100,
                reason="Critical governance escalation.",
            ),
        ),
    )


def test_policy_fingerprint_is_stable() -> None:
    first = policy()
    second = policy()

    assert first.fingerprint == second.fingerprint


def test_evidence_envelope_integrity_is_verifiable() -> None:
    link = EvidenceLink(
        reference="evidence://governance/t09",
        source_type="governance",
        fingerprint="abc123",
        tenant_id=TENANT,
        subject_id=SUBJECT,
        observed_at=NOW,
    )

    envelope = GovernanceEvidenceEnvelope.build(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="t09-evidence",
        policy_id="T09-POLICY",
        policy_version="1.0",
        links=(link,),
        created_at=NOW,
    )

    envelope.verify()


def test_exception_is_tenant_and_subject_scoped() -> None:
    exception = ExceptionRegistry.create(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        policy_id="T09-POLICY",
        policy_version="1.0",
        reason="Controlled test exception.",
        evidence_reference="evidence://exception/t09",
        granted_at=NOW,
        expires_at=NOW.replace(hour=13),
    )

    assert exception.is_active(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        at=NOW,
    )

    with pytest.raises(ExceptionScopeError):
        exception.is_active(
            tenant_id="other-tenant",
            subject_id=SUBJECT,
            at=NOW,
        )


def test_approval_cannot_transition_twice() -> None:
    request = ApprovalWorkflow.request(
        tenant_id=TENANT,
        subject_id=SUBJECT,
        correlation_id="t09-approval",
        governance_fingerprint=policy().fingerprint,
        policy_id="T09-POLICY",
        policy_version="1.0",
        requested_at=NOW,
        expires_at=NOW.replace(hour=13),
    )

    record = ApprovalWorkflow.transition(
        request=request,
        decision=ApprovalDecision.APPROVE,
        actor_reference="actor://t09",
        reason="Approved in test.",
        decision_at=NOW,
    )

    assert record.state.value == "APPROVED"

    with pytest.raises(ApprovalTransitionError):
        ApprovalWorkflow.transition(
            request=request.__class__(
                request_id=request.request_id,
                tenant_id=request.tenant_id,
                subject_id=request.subject_id,
                correlation_id=request.correlation_id,
                governance_fingerprint=request.governance_fingerprint,
                policy_id=request.policy_id,
                policy_version=request.policy_version,
                requested_at=request.requested_at,
                expires_at=request.expires_at,
                state=record.state,
            ),
            decision=ApprovalDecision.REJECT,
            actor_reference="actor://t09",
            reason="Second decision must fail.",
            decision_at=NOW,
        )


def test_escalation_hook_requires_evidence() -> None:
    with pytest.raises(Exception):
        EscalationHooks.create(
            tenant_id=TENANT,
            subject_id=SUBJECT,
            correlation_id="t09-escalation",
            level=EscalationLevel.CRITICAL,
            reason="Critical escalation.",
            evidence_references=(),
            created_at=NOW,
        )


def test_freeze_boundary_has_no_hidden_authorization_state() -> None:
    payload = policy().to_dict()

    forbidden = {
        "authorization",
        "authorized",
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
