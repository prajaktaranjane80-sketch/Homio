"""CORE-006 Deal & Transaction bounded context."""

from .deal import (
    Deal,
    DealConcurrencyError,
    DealDomainError,
    DealHistoryEntry,
    DealPartyRelationship,
    DealPartyRole,
    DealReferenceConflictError,
    DealStatus,
    DealTenantError,
    DealTransitionError,
    DealValidationError,
)
from .deal_evidence_audit import (
    DealAuditConflictError,
    DealAuditEntry,
    DealAuditScopeError,
    DealEvidenceAuditError,
    DealEvidenceConflictError,
    DealEvidenceReference,
    DealEvidenceScopeError,
)
from .deal_offer_negotiation import (
    DealNegotiation,
    DealNegotiationStatus,
    DealOffer,
    DealOfferNegotiationError,
    DealOfferStatus,
)
from .deal_ownership_integration import (
    DealOwnershipBinding,
    DealOwnershipError,
    DealOwnershipTenantError,
    DealOwnershipValidationError,
)
from .deal_transaction_milestones import (
    DealTransactionMilestone,
    DealTransactionMilestoneError,
)
from .deal_external_contracts import (
    DealExternalAuthority,
    DealExternalContractError,
    DealExternalReference,
)

__all__ = [
    "Deal",
    "DealConcurrencyError",
    "DealDomainError",
    "DealHistoryEntry",
    "DealPartyRelationship",
    "DealPartyRole",
    "DealReferenceConflictError",
    "DealStatus",
    "DealTenantError",
    "DealTransitionError",
    "DealValidationError",
    "DealAuditConflictError",
    "DealAuditEntry",
    "DealAuditScopeError",
    "DealEvidenceAuditError",
    "DealEvidenceConflictError",
    "DealEvidenceReference",
    "DealEvidenceScopeError",
    "DealNegotiation",
    "DealNegotiationStatus",
    "DealOffer",
    "DealOfferNegotiationError",
    "DealOfferStatus",
    "DealOwnershipBinding",
    "DealOwnershipError",
    "DealOwnershipTenantError",
    "DealOwnershipValidationError",
    "DealTransactionMilestone",
    "DealTransactionMilestoneError",
    "DealExternalAuthority",
    "DealExternalContractError",
    "DealExternalReference",
]
