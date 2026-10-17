"""Read-only binding of CORE-008 commission entitlement to canonical REOS sources."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from ..deal_transaction.deal import Deal
from ..deal_transaction.deal_evidence_audit import DealEvidenceReference
from ..deal_transaction.deal_ownership_integration import DealOwnershipBinding
from ..deal_transaction.deal_parties import DealPartyLifecycle, DealPartyRole
from ..lead_ownership.lead_attribution import LeadAttribution
from .commission_contract import CommissionContract, CommissionPartyType


CORE008_COMMISSION_ATTRIBUTION_SCHEMA_VERSION = 1


class CommissionAttributionError(ValueError):
    """Base CORE-008 attribution-binding error."""


class CommissionAttributionValidationError(CommissionAttributionError):
    """Commission references do not resolve to consistent authorities."""


@dataclass(frozen=True, slots=True)
class CommissionAttributionBinding:
    """Immutable derived reference; never a replacement source of truth."""

    tenant_id: str
    commission_id: str
    contract_version: int
    entitlement_id: str
    deal_id: str
    deal_version: int
    deal_updated_at: str
    lead_id: str
    lead_source_type: str
    lead_source_reference: str
    lead_attributed_at: str
    lead_attribution_fingerprint: str
    lead_evidence_reference: str
    ownership_binding_id: str
    ownership_record_id: str
    ownership_reference: str
    owner_id: str
    ownership_reference_key: str
    ownership_authority: str
    ownership_authority_version: str
    ownership_bound_at: str
    entitled_party_type: str
    entitled_party_id: str
    commission_contract_fingerprint: str
    provenance_reference: str
    provenance_authority: str

    def __post_init__(self) -> None:
        required_text = (
            "tenant_id", "commission_id", "entitlement_id", "deal_id",
            "deal_updated_at", "lead_id", "lead_source_type",
            "lead_source_reference", "lead_attributed_at",
            "lead_attribution_fingerprint", "lead_evidence_reference",
            "ownership_binding_id", "ownership_record_id",
            "ownership_reference", "owner_id", "ownership_reference_key",
            "ownership_authority", "ownership_authority_version",
            "ownership_bound_at", "entitled_party_type", "entitled_party_id",
            "commission_contract_fingerprint", "provenance_reference",
            "provenance_authority",
        )
        for name in required_text:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise CommissionAttributionValidationError(
                    f"{name} must be non-empty text."
                )
            object.__setattr__(self, name, value.strip())

        for name in ("contract_version", "deal_version"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise CommissionAttributionValidationError(
                    f"{name} must be a positive integer."
                )

    @classmethod
    def from_authoritative_sources(
        cls,
        contract: CommissionContract,
        lead_attribution: LeadAttribution,
        deal: Deal,
    ) -> "CommissionAttributionBinding":
        """Validate already-resolved CORE-003, CORE-006 and ARCH-011 objects."""
        if not isinstance(contract, CommissionContract):
            raise CommissionAttributionValidationError(
                "contract must be CommissionContract."
            )
        if not isinstance(lead_attribution, LeadAttribution):
            raise CommissionAttributionValidationError(
                "lead_attribution must be LeadAttribution."
            )
        if not isinstance(deal, Deal):
            raise CommissionAttributionValidationError("deal must be Deal.")

        entitlement = contract.entitlement
        tenant_id = contract.tenant_id

        if entitlement.tenant_id != tenant_id:
            raise CommissionAttributionValidationError(
                "Entitlement and commission contract tenant scopes differ."
            )
        if deal.tenant_id != tenant_id:
            raise CommissionAttributionValidationError(
                "Deal and commission contract tenant scopes differ."
            )
        if str(lead_attribution.tenant_id) != tenant_id:
            raise CommissionAttributionValidationError(
                "Lead attribution and commission contract tenant scopes differ."
            )
        if entitlement.deal_reference != deal.deal_id:
            raise CommissionAttributionValidationError(
                "Commission deal_reference does not resolve to the supplied Deal."
            )

        ownership = deal.ownership_binding
        if not isinstance(ownership, DealOwnershipBinding):
            raise CommissionAttributionValidationError(
                "Deal has no authoritative ARCH-011 ownership binding."
            )
        try:
            ownership.assert_scope(deal_id=deal.deal_id, tenant_id=deal.tenant_id)
        except (TypeError, ValueError) as exc:
            raise CommissionAttributionValidationError(
                "Ownership binding crosses Deal or tenant scope."
            ) from exc

        if ownership.lead_id != str(lead_attribution.lead_id):
            raise CommissionAttributionValidationError(
                "Lead attribution does not match the Deal ownership binding."
            )
        if (
            not isinstance(lead_attribution.evidence_reference, str)
            or not lead_attribution.evidence_reference.strip()
        ):
            raise CommissionAttributionValidationError(
                "Lead attribution requires an evidence reference."
            )

        allowed_ownership_references = {
            ownership.ownership_record_id,
            ownership.binding_id,
            ownership.reference_key,
        }
        if entitlement.ownership_reference not in allowed_ownership_references:
            raise CommissionAttributionValidationError(
                "Commission ownership_reference does not resolve to ARCH-011 binding."
            )

        role_map = {
            CommissionPartyType.BROKER: {DealPartyRole.BROKER},
            CommissionPartyType.BROKERAGE: {DealPartyRole.BROKER},
            CommissionPartyType.AGENT: {DealPartyRole.REPRESENTATIVE},
            CommissionPartyType.REFERRAL_PARTY: {DealPartyRole.REPRESENTATIVE},
            CommissionPartyType.PARTNER: {
                DealPartyRole.BUILDER,
                DealPartyRole.SELLER,
                DealPartyRole.REPRESENTATIVE,
            },
        }
        party = entitlement.entitled_party
        allowed_roles = role_map.get(party.party_type)
        if not allowed_roles:
            raise CommissionAttributionValidationError(
                "Commission party type has no compatible Deal role."
            )

        party_found = False
        for participant in deal.participants:
            try:
                participant.assert_scope(
                    deal_id=deal.deal_id,
                    tenant_id=deal.tenant_id,
                )
            except (TypeError, ValueError) as exc:
                raise CommissionAttributionValidationError(
                    "Deal participant crosses Deal or tenant scope."
                ) from exc

            if (
                participant.party_id == party.party_id
                and participant.lifecycle is DealPartyLifecycle.ACTIVE
                and participant.role in allowed_roles
            ):
                party_found = True
                break

        if not party_found:
            raise CommissionAttributionValidationError(
                "Entitled party is not an active Deal participant with a compatible role."
            )

        provenance_reference = entitlement.provenance_reference
        provenance_authority: str | None = None

        for evidence in deal.evidence:
            if not isinstance(evidence, DealEvidenceReference):
                raise CommissionAttributionValidationError(
                    "Deal evidence contains an invalid reference type."
                )
            try:
                evidence.assert_scope(
                    deal_id=deal.deal_id,
                    tenant_id=deal.tenant_id,
                )
            except (TypeError, ValueError) as exc:
                raise CommissionAttributionValidationError(
                    "Deal evidence crosses Deal or tenant scope."
                ) from exc

            if provenance_reference in (evidence.evidence_id, evidence.reference):
                provenance_authority = evidence.source_of_truth
                break

        if provenance_authority is None:
            if provenance_reference == lead_attribution.evidence_reference:
                provenance_authority = "CORE-003"

        if provenance_authority is None:
            raise CommissionAttributionValidationError(
                "Commission provenance does not resolve to CORE-003 attribution or Deal evidence."
            )

        return cls(
            tenant_id=tenant_id,
            commission_id=contract.commission_id,
            contract_version=contract.contract_version,
            entitlement_id=entitlement.entitlement_id,
            deal_id=deal.deal_id,
            deal_version=deal.version,
            deal_updated_at=deal.updated_at.isoformat(),
            lead_id=str(lead_attribution.lead_id),
            lead_source_type=lead_attribution.source_type,
            lead_source_reference=lead_attribution.source_reference,
            lead_attributed_at=lead_attribution.attributed_at.isoformat(),
            lead_attribution_fingerprint=lead_attribution.fingerprint,
            lead_evidence_reference=lead_attribution.evidence_reference,
            ownership_binding_id=ownership.binding_id,
            ownership_record_id=ownership.ownership_record_id,
            ownership_reference=entitlement.ownership_reference,
            owner_id=ownership.owner_id,
            ownership_reference_key=ownership.reference_key,
            ownership_authority=ownership.authority,
            ownership_authority_version=ownership.authority_version,
            ownership_bound_at=ownership.bound_at.isoformat(),
            entitled_party_type=party.party_type.value,
            entitled_party_id=party.party_id,
            commission_contract_fingerprint=contract.immutable_terms_fingerprint,
            provenance_reference=provenance_reference,
            provenance_authority=provenance_authority,
        )

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(self.to_dict(include_fingerprint=False))

    def to_dict(self, *, include_fingerprint: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "binding_type": "CORE-008.COMMISSION_ATTRIBUTION_BINDING",
            "schema_version": CORE008_COMMISSION_ATTRIBUTION_SCHEMA_VERSION,
            "authorities": {
                "commission_contract": "CORE-008",
                "lead_attribution": "CORE-003",
                "deal": "CORE-006",
                "ownership": self.ownership_authority,
                "evidence": self.provenance_authority,
            },
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "contract_version": self.contract_version,
            "commission_contract_fingerprint": self.commission_contract_fingerprint,
            "entitlement_reference": {
                "entitlement_id": self.entitlement_id,
                "deal_reference": self.deal_id,
                "ownership_reference": self.ownership_reference,
                "provenance_reference": self.provenance_reference,
                "entitled_party": {
                    "party_type": self.entitled_party_type,
                    "party_id": self.entitled_party_id,
                },
            },
            "lead_attribution": {
                "lead_id": self.lead_id,
                "source_type": self.lead_source_type,
                "source_reference": self.lead_source_reference,
                "attributed_at": self.lead_attributed_at,
                "evidence_reference": self.lead_evidence_reference,
                "fingerprint": self.lead_attribution_fingerprint,
            },
            "deal": {
                "deal_id": self.deal_id,
                "deal_version": self.deal_version,
                "updated_at": self.deal_updated_at,
                "authority": "CORE-006",
            },
            "ownership_binding": {
                "binding_id": self.ownership_binding_id,
                "ownership_record_id": self.ownership_record_id,
                "reference_key": self.ownership_reference_key,
                "owner_id": self.owner_id,
                "authority": self.ownership_authority,
                "authority_version": self.ownership_authority_version,
                "bound_at": self.ownership_bound_at,
            },
            "provenance": {
                "reference": self.provenance_reference,
                "authority": self.provenance_authority,
            },
        }
        if include_fingerprint:
            result["immutable_fingerprint"] = self.immutable_fingerprint
        return result


__all__ = [
    "CORE008_COMMISSION_ATTRIBUTION_SCHEMA_VERSION",
    "CommissionAttributionError",
    "CommissionAttributionValidationError",
    "CommissionAttributionBinding",
]