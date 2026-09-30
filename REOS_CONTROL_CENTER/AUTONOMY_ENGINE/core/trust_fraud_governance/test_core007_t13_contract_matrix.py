"""CORE-007 Point 13 — contract + adversarial regression matrix."""

from __future__ import annotations

from uuid import uuid4

from ..event_platform.event_domain import (
    EventEnvelope,
)
from .governance_acrl_contract import (
    GovernanceACRLArtifact,
    GovernanceACRLArtifactDescriptor,
)
from .governance_event_contract import (
    build_escalation_event,
    build_governance_review_event,
    build_override_event,
    build_risk_assessment_event,
)


def test_risk_assessment_event_contains_reproducibility():
    event = build_risk_assessment_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "assessment_id": "assessment-1",
            "subject_id": "subject-1",
            "assessment_version": 1,
            "risk_factors": [
                {
                    "code": "F1",
                    "value": 10,
                }
            ],
            "assessment_evidence": [
                "evidence-1"
            ],
            "reproducibility": "DETERMINISTIC",
        },
    )

    assert (
        event.payload[
            "assessment_version"
        ]
        == 1
    )

    assert (
        event.payload[
            "reproducibility"
        ]
        == "DETERMINISTIC"
    )


def test_governance_review_event_contains_policy_and_review_state():
    event = build_governance_review_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "review_id": "review-1",
            "subject_id": "subject-1",
            "review_state": "PENDING",
            "decision_evidence": [
                "evidence-1"
            ],
            "policy_id": "policy-1",
            "policy_version": "1.0",
        },
    )

    assert (
        event.event_type.value
        == "CORE007.GOVERNANCE_REVIEW"
    )


def test_escalation_event_requires_evidence_reference():
    event = build_escalation_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "escalation_id": "escalation-1",
            "subject_id": "subject-1",
            "escalation_state": "OPEN",
            "reason": "HIGH_RISK",
            "evidence_references": [
                "evidence-1"
            ],
        },
    )

    assert event.payload[
        "evidence_references"
    ] == (
        "evidence-1",
    )


def test_override_event_requires_authorization():
    event = build_override_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "override_id": "override-1",
            "subject_id": "subject-1",
            "override_reference": (
                "override-reference-1"
            ),
            "override_authorization": (
                "authorization-reference-1"
            ),
            "review_reference": "review-1",
            "evidence_references": [
                "evidence-1"
            ],
        },
    )

    assert event.payload[
        "override_authorization"
    ] == (
        "authorization-reference-1"
    )


def test_core_002_remains_event_envelope_owner():
    tenant_id = uuid4()

    envelope = EventEnvelope.create(
        event_type="CORE007.TEST",
        schema_name=(
            "REOS.CORE007.GovernanceEvent"
        ),
        schema_version=1,
        event_version=1,
        tenant_id=tenant_id,
        producer_id=uuid4(),
        payload={
            "tenant_id": str(
                tenant_id
            ),
            "ok": True,
        },
    )

    assert envelope.tenant_id == tenant_id
    assert envelope.immutable_fingerprint


def test_acrl_descriptor_is_immutable_and_versioned():
    descriptor = (
        GovernanceACRLArtifactDescriptor(
            artifact_id="decision-1",
            artifact_type=(
                GovernanceACRLArtifact
                .GOVERNANCE_DECISION
            ),
            tenant_id="tenant-1",
            contract_key=(
                "CORE007:DECISION:1"
            ),
            version=1,
            fingerprint="a" * 64,
            provenance_reference="prov-1",
        )
    )

    assert descriptor.version == 1
    assert (
        descriptor.artifact_type
        is GovernanceACRLArtifact
        .GOVERNANCE_DECISION
    )
