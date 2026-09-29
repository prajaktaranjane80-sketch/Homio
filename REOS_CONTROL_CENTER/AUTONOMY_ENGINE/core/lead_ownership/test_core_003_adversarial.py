"""
CORE-003 T12 — Adversarial / Contract Regression

These tests protect the actual domain contracts.
They must not be weakened merely to obtain PASS.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from .lead import (
    Lead,
    LeadLifecycleError,
    LeadPriority,
    LeadSource,
    LeadSourceType,
    LeadStatus,
    LeadTenantViolation,
)
from .lead_contract import (
    DEFAULT_LEAD_CONTRACT,
    LeadSchemaError,
)
from .lead_attribution import (
    AttributionValidationError,
    LeadAttribution,
)
from .lead_ownership import (
    LeadOwnerRole,
    LeadOwnership,
    OwnershipConflictError,
    OwnershipTenantViolation,
)
from .ownership_transfer import (
    OwnershipTransfer,
    OwnershipTransferValidationError,
    TransferReason,
)
from .lead_communication import (
    CommunicationChannel,
    CommunicationDirection,
    CommunicationEvidenceConflictError,
    LeadCommunicationEvidenceHook,
)
from .lead_fraud_handoff import (
    FraudHandoffPriority,
    FraudHandoffReason,
    LeadFraudHandoff,
    FraudHandoffConflictError,
)
from .lead_consistency import (
    LeadConcurrencyConflict,
    LeadConsistencySnapshot,
    LeadMutationPrecondition,
)
from .lead_security import (
    LeadCapability,
    LeadCapabilityViolation,
    LeadSecurityContext,
    LeadTenantBoundaryViolation,
)
from .lead_acrl_contract import (
    LeadAcrlIntegrationContract,
    LeadAcrlPreconditionConflict,
    ReosLeadOperation,
)
from .lead_event_integration import (
    LeadDomainEvent,
    LeadDomainEventType,
)


def make_lead() -> Lead:
    return Lead.create(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        source=LeadSource(
            source_type=LeadSourceType.WEBSITE,
            source_id="website-001",
            channel="organic",
        ),
    )


def make_ownership(
    lead: Lead,
    owner_id=None,
    revision: int = 0,
) -> LeadOwnership:
    return LeadOwnership(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        owner_id=owner_id or uuid4(),
        owner_role=LeadOwnerRole.AGENT,
        assigned_at=datetime.now(timezone.utc),
        revision=revision,
    )


def test_lead_is_immutable():
    lead = make_lead()

    with pytest.raises(FrozenInstanceError):
        lead.status = LeadStatus.QUALIFIED


def test_archived_lead_cannot_transition():
    lead = make_lead().transition(
        LeadStatus.ARCHIVED
    )

    with pytest.raises(LeadLifecycleError):
        lead.transition(LeadStatus.NEW)


def test_cross_tenant_lead_access_is_blocked():
    lead = make_lead()

    with pytest.raises(LeadTenantViolation):
        lead.ensure_tenant(uuid4())


def test_contract_rejects_unknown_fields():
    lead = make_lead()
    payload = lead.to_dict()
    payload["unexpected"] = "attack"

    with pytest.raises(LeadSchemaError):
        DEFAULT_LEAD_CONTRACT.validate_mapping(payload)


def test_attribution_cross_tenant_is_blocked():
    lead = make_lead()

    attribution = LeadAttribution(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        source_type="WEBSITE",
        source_reference="source-1",
        attributed_at=datetime.now(timezone.utc),
    )

    with pytest.raises(AttributionValidationError):
        attribution.ensure_tenant(uuid4())


def test_ownership_stale_revision_is_blocked():
    lead = make_lead()
    ownership = make_ownership(lead)

    with pytest.raises(OwnershipConflictError):
        ownership.rebind(
            owner_id=uuid4(),
            owner_role=LeadOwnerRole.AGENT,
            expected_revision=99,
        )


def test_ownership_cross_tenant_is_blocked():
    lead = make_lead()
    ownership = make_ownership(lead)

    with pytest.raises(OwnershipTenantViolation):
        ownership.ensure_tenant(uuid4())


def test_transfer_cannot_keep_same_owner():
    lead = make_lead()
    owner = uuid4()

    with pytest.raises(
        OwnershipTransferValidationError
    ):
        OwnershipTransfer.create(
            lead_id=lead.lead_id,
            tenant_id=lead.tenant_id,
            previous_owner_id=owner,
            new_owner_id=owner,
            previous_revision=0,
            reason=TransferReason.MANUAL,
        )


def test_communication_duplicate_identity_conflict():
    lead = make_lead()

    communication_id = uuid4()
    timestamp = datetime.now(timezone.utc)

    first = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        communication_id=communication_id,
        evidence_reference="evidence-1",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.EMAIL,
        occurred_at=timestamp,
    )

    second = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        communication_id=communication_id,
        evidence_reference="different-evidence",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.EMAIL,
        occurred_at=timestamp,
    )

    with pytest.raises(
        CommunicationEvidenceConflictError
    ):
        first.assert_compatible(second)


def test_fraud_handoff_same_idempotency_conflict():
    lead = make_lead()

    first = LeadFraudHandoff.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        reason=FraudHandoffReason.DUPLICATE_LEAD,
        priority=FraudHandoffPriority.REVIEW,
        idempotency_key="handoff-1",
        evidence_references=("evidence-1",),
        source_reference="CORE-003",
    )

    second = LeadFraudHandoff.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        reason=FraudHandoffReason.EVIDENCE_CONFLICT,
        priority=FraudHandoffPriority.HIGH,
        idempotency_key="handoff-1",
        evidence_references=("evidence-2",),
        source_reference="CORE-003",
    )

    with pytest.raises(FraudHandoffConflictError):
        first.assert_compatible(second)


def test_consistency_snapshot_blocks_changed_revision():
    lead = make_lead()

    snapshot = LeadConsistencySnapshot.capture(
        lead,
        None,
    )

    changed = lead.with_priority(
        LeadPriority.HIGH
    )

    with pytest.raises(LeadConcurrencyConflict):
        snapshot.assert_current(
            changed,
            None,
        )


def test_security_context_fails_without_capability():
    context = LeadSecurityContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        capabilities=frozenset(),
        authorization_reference="auth-001",
        issued_at=datetime.now(timezone.utc),
    )

    with pytest.raises(LeadCapabilityViolation):
        context.require(
            LeadCapability.TRANSFER_LEAD
        )


def test_security_context_blocks_cross_tenant():
    context = LeadSecurityContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        capabilities=frozenset(
            {LeadCapability.READ_LEAD}
        ),
        authorization_reference="auth-001",
        issued_at=datetime.now(timezone.utc),
    )

    with pytest.raises(LeadTenantBoundaryViolation):
        context.ensure_tenant(uuid4())


def test_security_context_expiration_is_enforced():
    issued = datetime.now(timezone.utc)

    context = LeadSecurityContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        capabilities=frozenset(
            {LeadCapability.READ_LEAD}
        ),
        authorization_reference="auth-001",
        issued_at=issued,
        expires_at=issued + timedelta(seconds=1),
    )

    with pytest.raises(Exception):
        context.assert_active(
            now=issued + timedelta(seconds=2)
        )


def test_acrl_contract_rejects_wrong_tenant_snapshot():
    lead = make_lead()

    precondition = LeadMutationPrecondition(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        expected_lead_revision=lead.revision,
        expected_ownership_revision=None,
        idempotency_key="op-001",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="op-001",
        precondition=precondition,
    )

    foreign_lead = Lead.create(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        source=LeadSource(
            source_type=LeadSourceType.DIRECT
        ),
    )

    with pytest.raises(LeadAcrlPreconditionConflict):
        contract.validate_current_domain(
            foreign_lead,
            None,
        )


def test_event_payload_is_immutable():
    lead = make_lead()

    event = LeadDomainEvent.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-001",
        payload={"status": "NEW"},
    )

    with pytest.raises(TypeError):
        event.payload["status"] = "HACKED"


def test_event_identity_conflict_is_detected():
    lead = make_lead()

    first = LeadDomainEvent.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-001",
        payload={"status": "NEW"},
    )

    second = LeadDomainEvent.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        event_type=LeadDomainEventType.LEAD_STATUS_CHANGED,
        correlation_id=uuid4(),
        idempotency_key="event-001",
        payload={"status": "QUALIFYING"},
    )

    with pytest.raises(Exception):
        first.assert_compatible(second)
