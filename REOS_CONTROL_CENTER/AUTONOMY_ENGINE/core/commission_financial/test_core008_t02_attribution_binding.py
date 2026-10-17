from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from ..deal_transaction.deal import Deal
from ..lead_ownership.lead_attribution import LeadAttribution
from .commission_attribution import (
    CommissionAttributionBinding,
    CommissionAttributionValidationError,
)
from .commission_contract import (
    CommissionBasis,
    CommissionBasisType,
    CommissionContract,
    CommissionContractState,
    CommissionEligibilityRule,
    CommissionEntitlementReference,
    CommissionPartyReference,
    CommissionPartyType,
    CommissionProvenance,
    CommissionRate,
    CommissionRateType,
    EligibilityOperator,
)


UTC = timezone.utc
TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
LEAD_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_LEAD_ID = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def build_contract(
    *,
    tenant_id: UUID = TENANT_ID,
    deal_reference: str = "deal-001",
    ownership_reference: str = "ownership-001",
    provenance_reference: str = "deal-proof-001",
    party_type: CommissionPartyType = CommissionPartyType.BROKER,
    party_id: str = "broker-001",
) -> CommissionContract:
    tenant = str(tenant_id)
    return CommissionContract(
        commission_id="commission-001",
        tenant_id=tenant,
        entitlement=CommissionEntitlementReference(
            entitlement_id="entitlement-001",
            tenant_id=tenant,
            entitled_party=CommissionPartyReference(
                party_type=party_type,
                party_id=party_id,
            ),
            deal_reference=deal_reference,
            ownership_reference=ownership_reference,
            provenance_reference=provenance_reference,
        ),
        basis=CommissionBasis(
            basis_type=CommissionBasisType.GROSS_TRANSACTION_VALUE,
            source_reference="deal.gross_value",
        ),
        rate=CommissionRate(
            rate_type=CommissionRateType.PERCENTAGE,
            value="2.5",
        ),
        eligibility_rules=(
            CommissionEligibilityRule(
                rule_code="DEAL_ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="YES",
            ),
        ),
        effective_from=NOW,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-001",
            captured_at=NOW - timedelta(days=1),
            evidence_reference="mou-proof-001",
        ),
        state=CommissionContractState.ACTIVE,
    )


def build_sources(
    *,
    lead_id: UUID = LEAD_ID,
    lead_tenant_id: UUID = TENANT_ID,
    binding_lead_id: UUID | None = None,
    deal_tenant_id: UUID = TENANT_ID,
    contract_tenant_id: UUID = TENANT_ID,
    deal_reference: str = "deal-001",
    ownership_reference: str = "ownership-001",
    provenance_reference: str = "deal-proof-001",
    lead_evidence_reference: str | None = "lead-proof-001",
    include_ownership: bool = True,
    include_deal_evidence: bool = True,
    party_type: CommissionPartyType = CommissionPartyType.BROKER,
    party_id: str = "broker-001",
):
    lead = LeadAttribution(
        lead_id=lead_id,
        tenant_id=lead_tenant_id,
        source_type="ENQUIRY",
        source_reference="enquiry-001",
        attributed_at=NOW - timedelta(hours=1),
        evidence_reference=lead_evidence_reference,
        campaign_reference="campaign-001",
        channel="WEB",
    )

    deal_tenant = str(deal_tenant_id)
    deal = Deal.create(
        tenant_id=deal_tenant,
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        deal_id="deal-001",
        at=NOW,
    )

    linked_lead_id = binding_lead_id or LEAD_ID
    if include_ownership:
        deal = deal.bind_ownership(
            binding_id="binding-001",
            lead_id=str(linked_lead_id),
            ownership_record_id="ownership-001",
            owner_id="owner-001",
            tenant_id=deal_tenant,
            expected_version=1,
            at=NOW + timedelta(seconds=1),
        )
        if include_deal_evidence:
            deal = deal.attach_evidence(
                evidence_id="evidence-001",
                tenant_id=deal_tenant,
                expected_version=2,
                evidence_type="COMMISSION_ATTRIBUTION",
                reference="deal-proof-001",
                actor_id="broker-001",
                at=NOW + timedelta(seconds=2),
            )

    contract = build_contract(
        tenant_id=contract_tenant_id,
        deal_reference=deal_reference,
        ownership_reference=ownership_reference,
        provenance_reference=provenance_reference,
        party_type=party_type,
        party_id=party_id,
    )
    return contract, lead, deal


def test_valid_binding_keeps_canonical_authorities_and_references() -> None:
    contract, lead, deal = build_sources()
    binding = CommissionAttributionBinding.from_authoritative_sources(
        contract, lead, deal
    )
    payload = binding.to_dict()

    assert binding.tenant_id == str(TENANT_ID)
    assert binding.deal_id == deal.deal_id
    assert binding.deal_version == deal.version
    assert binding.lead_id == str(LEAD_ID)
    assert binding.ownership_record_id == "ownership-001"
    assert binding.provenance_authority == "ARCH-014"
    assert payload["authorities"]["lead_attribution"] == "CORE-003"
    assert payload["authorities"]["deal"] == "CORE-006"
    assert payload["ownership_binding"]["authority"] == "ARCH-011"
    assert "source_of_truth" not in payload


def test_cross_tenant_lead_attribution_is_rejected() -> None:
    contract, lead, deal = build_sources(lead_tenant_id=OTHER_TENANT_ID)
    with pytest.raises(CommissionAttributionValidationError, match="tenant"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_lead_must_match_ownership_binding() -> None:
    contract, lead, deal = build_sources(binding_lead_id=OTHER_LEAD_ID)
    with pytest.raises(CommissionAttributionValidationError, match="Lead attribution"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_deal_reference_must_resolve_exactly() -> None:
    contract, lead, deal = build_sources(deal_reference="another-deal")
    with pytest.raises(CommissionAttributionValidationError, match="deal_reference"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_ownership_reference_must_resolve_to_authoritative_binding() -> None:
    contract, lead, deal = build_sources(ownership_reference="another-ownership")
    with pytest.raises(CommissionAttributionValidationError, match="ownership_reference"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_missing_ownership_binding_is_rejected() -> None:
    contract, lead, deal = build_sources(include_ownership=False)
    with pytest.raises(CommissionAttributionValidationError, match="ownership binding"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_missing_lead_evidence_reference_is_rejected() -> None:
    contract, lead, deal = build_sources(lead_evidence_reference=None)
    with pytest.raises(CommissionAttributionValidationError, match="evidence reference"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_unresolved_provenance_is_rejected() -> None:
    contract, lead, deal = build_sources(
        provenance_reference="orphan-proof",
        include_deal_evidence=False,
    )
    with pytest.raises(CommissionAttributionValidationError, match="provenance"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_party_must_be_an_active_participant_with_a_compatible_role() -> None:
    contract, lead, deal = build_sources(
        party_type=CommissionPartyType.AGENT,
        party_id="broker-001",
    )
    with pytest.raises(CommissionAttributionValidationError, match="active Deal participant"):
        CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)


def test_provenance_can_resolve_to_core003_lead_evidence() -> None:
    contract, lead, deal = build_sources(provenance_reference="lead-proof-001")
    binding = CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)
    assert binding.provenance_authority == "CORE-003"


def test_ownership_reference_key_is_supported() -> None:
    reference_key = f"{TENANT_ID}:deal-001:ownership-001"
    contract, lead, deal = build_sources(ownership_reference=reference_key)
    binding = CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)
    assert binding.ownership_reference_key == reference_key


def test_binding_is_deterministic_and_immutable() -> None:
    contract, lead, deal = build_sources()
    first = CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)
    second = CommissionAttributionBinding.from_authoritative_sources(contract, lead, deal)
    assert first.immutable_fingerprint == second.immutable_fingerprint
    with pytest.raises(FrozenInstanceError):
        first.deal_id = "substituted-deal"


def test_binding_public_api_is_exported() -> None:
    from . import CommissionAttributionBinding as PublicBinding
    assert PublicBinding is CommissionAttributionBinding