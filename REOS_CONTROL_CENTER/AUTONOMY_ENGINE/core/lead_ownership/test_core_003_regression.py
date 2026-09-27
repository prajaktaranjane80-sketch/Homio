"""
CORE-003 T13 — Full Regression + Cross-Core Verification

End-to-end domain contract verification for CORE-003.

Verifies:
- Lead
- Contract
- Attribution
- Ownership
- Ownership transfer
- Communication evidence hook
- Fraud handoff
- Concurrency
- Security
- ACRL boundary
- CORE-002 event integration
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .lead import (
    Lead,
    LeadPriority,
    LeadSource,
    LeadSourceType,
    LeadStatus,
)
from .lead_contract import DEFAULT_LEAD_CONTRACT
from .lead_attribution import LeadAttribution
from .lead_ownership import (
    LeadOwnerRole,
    LeadOwnership,
)
from .ownership_transfer import (
    OwnershipTransfer,
    TransferReason,
)
from .lead_communication import (
    CommunicationChannel,
    CommunicationDirection,
    LeadCommunicationEvidenceHook,
)
from .lead_fraud_handoff import (
    FraudHandoffPriority,
    FraudHandoffReason,
    LeadFraudHandoff,
)
from .lead_consistency import (
    LeadConsistencySnapshot,
    LeadMutationPrecondition,
)
from .lead_security import (
    LeadCapability,
    LeadSecurityContext,
)
from .lead_acrl_contract import (
    LeadAcrlIntegrationContract,
    ReosLeadOperation,
)
from .lead_event_integration import (
    LeadDomainEvent,
    LeadDomainEventType,
)


def test_core_003_complete_business_flow():
    tenant_id = uuid4()
    customer_id = uuid4()

    lead = Lead.create(
        tenant_id=tenant_id,
        customer_id=customer_id,
        source=LeadSource(
            source_type=LeadSourceType.BUILDER,
            source_id="builder-source-001",
            campaign_id="campaign-001",
            channel="partner",
        ),
        priority=LeadPriority.HIGH,
        metadata={
            "market": "international",
            "origin": "builder",
        },
    )

    DEFAULT_LEAD_CONTRACT.validate_mapping(
        lead.to_dict()
        | {
            "lead_id": lead.lead_id,
            "tenant_id": lead.tenant_id,
            "customer_id": lead.customer_id,
            "status": lead.status,
            "priority": lead.priority,
            "source": lead.source,
            "metadata": lead.metadata,
            "revision": lead.revision,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
        }
    )

    attribution = LeadAttribution(
        lead_id=lead.lead_id,
        tenant_id=tenant_id,
        source_type="BUILDER",
        source_reference="builder-source-001",
        attributed_at=datetime.now(timezone.utc),
        campaign_reference="campaign-001",
        channel="partner",
    )

    attribution.ensure_tenant(tenant_id)

    lead = lead.transition(
        LeadStatus.QUALIFYING
    )

    owner_a = uuid4()

    ownership = LeadOwnership.create(
        lead_id=lead.lead_id,
        tenant_id=tenant_id,
        owner_id=owner_a,
        owner_role=LeadOwnerRole.BROKER,
        assignment_reference="assignment-001",
    )

    consistency_before_transfer = (
        LeadConsistencySnapshot.capture(
            lead,
            ownership,
        )
    )

    owner_b = uuid4()

    transfer = OwnershipTransfer.create(
        lead_id=lead.lead_id,
        tenant_id=tenant_id,
        previous_owner_id=ownership.owner_id,
        new_owner_id=owner_b,
        previous_revision=ownership.revision,
        reason=TransferReason.REASSIGNMENT,
        transfer_reference="transfer-001",
    )

    transfer.ensure_tenant(tenant_id)

    ownership = ownership.rebind(
        owner_id=owner_b,
        owner_role=LeadOwnerRole.AGENT,
        expected_revision=ownership.revision,
        assignment_reference="transfer-001",
    )

    communication = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=tenant_id,
        communication_id=uuid4(),
        evidence_reference="evidence-communication-001",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.WHATSAPP,
        occurred_at=datetime.now(timezone.utc),
        actor_id=owner_b,
    )

    communication.ensure_tenant(tenant_id)

    handoff = LeadFraudHandoff.create(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        reason=FraudHandoffReason.OWNERSHIP_CONFLICT,
        priority=FraudHandoffPriority.REVIEW,
        idempotency_key="fraud-handoff-001",
        evidence_references=(
            communication.evidence_reference,
        ),
        source_reference="CORE-003",
        observed_lead_revision=lead.revision,
        observed_ownership_revision=ownership.revision,
    )

    handoff.ensure_tenant(tenant_id)

    snapshot_after_transfer = (
        LeadConsistencySnapshot.capture(
            lead,
            ownership,
        )
    )

    assert (
        snapshot_after_transfer.lead_revision
        == consistency_before_transfer.lead_revision
    )

    assert (
        snapshot_after_transfer.ownership_revision
        == 1
    )

    security = LeadSecurityContext(
        tenant_id=tenant_id,
        actor_id=owner_b,
        capabilities=frozenset(
            {
                LeadCapability.READ_LEAD,
                LeadCapability.TRANSFER_LEAD,
                LeadCapability.ATTACH_COMMUNICATION_EVIDENCE,
                LeadCapability.CREATE_FRAUD_HANDOFF,
            }
        ),
        authorization_reference="core001-auth-001",
        issued_at=datetime.now(timezone.utc),
    )

    security.ensure_lead(lead)
    security.ensure_ownership(ownership)
    security.require(
        LeadCapability.TRANSFER_LEAD
    )

    precondition = LeadMutationPrecondition(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        expected_lead_revision=lead.revision,
        expected_ownership_revision=ownership.revision,
        idempotency_key="op-transfer-001",
    )

    acrl_contract = LeadAcrlIntegrationContract.create(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.TRANSFER_OWNER,
        correlation_id=uuid4(),
        idempotency_key="op-transfer-001",
        precondition=precondition,
        evidence_references=(
            communication.evidence_reference,
            handoff.fingerprint,
        ),
        expected_post_lead_revision=lead.revision,
        expected_post_ownership_revision=ownership.revision,
        handoff_reference=handoff.idempotency_key,
    )

    acrl_contract.validate_current_domain(
        lead,
        ownership,
    )

    domain_event = LeadDomainEvent.create(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        event_type=(
            LeadDomainEventType.LEAD_OWNER_TRANSFERRED
        ),
        correlation_id=acrl_contract.correlation_id,
        idempotency_key="event-transfer-001",
        payload={
            "previous_owner_id": str(owner_a),
            "new_owner_id": str(owner_b),
            "ownership_revision": ownership.revision,
            "transfer_id": str(transfer.transfer_id),
        },
        causation_id=acrl_contract.operation_id,
    )

    event_payload = (
        domain_event.to_core002_payload()
    )

    assert (
        event_payload["event_type"]
        == "LEAD_OWNER_TRANSFERRED"
    )

    assert (
        event_payload["tenant_id"]
        == str(tenant_id)
    )

    assert (
        event_payload["idempotency_key"]
        == "event-transfer-001"
    )


def test_core_002_boundary_is_transport_free():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-boundary-001",
        payload={
            "status": "NEW",
        },
    )

    payload = event.to_core002_payload()

    assert "event_type" in payload
    assert "schema_version" in payload
    assert "tenant_id" in payload
    assert "correlation_id" in payload
    assert "idempotency_key" in payload
    assert "payload" in payload

    assert "kafka" not in str(
        payload
    ).lower()

    assert "outbox" not in str(
        payload
    ).lower()


def test_tenant_identity_is_preserved_across_all_boundaries():
    tenant_id = uuid4()
    lead = Lead.create(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        source=LeadSource(
            source_type=LeadSourceType.DIRECT
        ),
    )

    ownership = LeadOwnership.create(
        lead_id=lead.lead_id,
        tenant_id=tenant_id,
        owner_id=uuid4(),
        owner_role=LeadOwnerRole.BROKER,
    )

    snapshot = LeadConsistencySnapshot.capture(
        lead,
        ownership,
    )

    precondition = LeadMutationPrecondition(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        expected_lead_revision=lead.revision,
        expected_ownership_revision=ownership.revision,
        idempotency_key="tenant-check-001",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="tenant-check-001",
        precondition=precondition,
    )

    assert lead.tenant_id == tenant_id
    assert ownership.tenant_id == tenant_id
    assert snapshot.tenant_id == tenant_id
    assert contract.tenant_id == tenant_id
