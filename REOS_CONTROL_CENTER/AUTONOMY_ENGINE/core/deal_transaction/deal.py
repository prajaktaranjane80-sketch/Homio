from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Mapping
from uuid import uuid4

from .deal_contract import (
    DEAL_CONTRACT_SCHEMA_VERSION,
    DISPUTE_STATES,
    EXPIRY_STATES,
    NOMINAL_TRANSITIONS,
    REJECTION_STATES,
    TERMINAL_STATES,
    DealContract,
    DealHistoryEntry,
    DealStatus,
    utc_datetime,
)
from .deal_evidence_audit import (
    DealAuditConflictError,
    DealAuditEntry,
    DealEvidenceConflictError,
    DealEvidenceReference,
)
from .deal_offer_negotiation import (
    DealNegotiation,
    DealNegotiationStatus,
    DealOffer,
    DealOfferStatus,
)
from .deal_ownership_integration import (
    DealOwnershipBinding,
    DealOwnershipConflictError,
)
from .deal_parties import (
    DealPartyRelationship,
    DealPartyRole,
)
from .deal_transaction_milestones import (
    DealTransactionMilestone,
    TRANSACTION_STATUSES,
)


class DealDomainError(ValueError):
    pass


class DealTransitionError(DealDomainError):
    pass


class DealTenantError(DealDomainError):
    pass


class DealConcurrencyError(DealDomainError):
    pass


class DealReferenceConflictError(DealDomainError):
    pass


class DealValidationError(DealDomainError):
    pass


def _require_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealValidationError(
            f"{field_name} must be a non-empty string."
        )
    return value.strip()


@dataclass(frozen=True)
class Deal:
    deal_id: str
    tenant_id: str
    customer_id: str
    broker_id: str

    builder_id: str | None
    project_id: str | None
    unit_id: str | None

    status: DealStatus
    version: int

    created_at: datetime
    updated_at: datetime

    history: tuple[DealHistoryEntry, ...] = ()

    source_of_truth: str = "deal"
    offers: tuple[DealOffer, ...] = ()
    negotiation: DealNegotiation | None = None
    milestones: tuple[DealTransactionMilestone, ...] = ()
    ownership_binding: DealOwnershipBinding | None = None
    evidence: tuple[DealEvidenceReference, ...] = ()
    audit_log: tuple[DealAuditEntry, ...] = ()
    participants: tuple[DealPartyRelationship, ...] = ()

    contract_schema_version: str = (
        DEAL_CONTRACT_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "customer_id",
            "broker_id",
        ):
            _require_id(getattr(self, name), name)

        for name in (
            "builder_id",
            "project_id",
            "unit_id",
        ):
            value = getattr(self, name)

            if value is not None:
                _require_id(value, name)

        if self.version < 1:
            raise DealValidationError(
                "version must be >= 1."
            )

        if self.source_of_truth != "deal":
            raise DealValidationError(
                "Deal source_of_truth must remain 'deal'."
            )

        object.__setattr__(
            self,
            "status",
            DealStatus(self.status),
        )

        previous_version = 0

        if self.history and self.history[0].version != 1:
            raise DealValidationError(
                "Lifecycle history must start at version 1."
            )

        for entry in self.history:
            if entry.version < 1 or entry.version > self.version:
                raise DealValidationError(
                    "Deal history versions must be ordered and cannot exceed Deal version."
                )

            if entry.version <= previous_version:
                raise DealValidationError(
                    "Deal history versions must be strictly increasing."
                )

            previous_version = entry.version

        relationship_keys = set()

        for participant in self.participants:
            participant.assert_scope(
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
            )

            if participant.relationship_key in relationship_keys:
                raise DealValidationError(
                    "Duplicate participant relationship."
                )

            relationship_keys.add(
                participant.relationship_key
            )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        customer_id: str,
        broker_id: str,
        builder_id: str | None = None,
        project_id: str | None = None,
        unit_id: str | None = None,
        deal_id: str | None = None,
        at: Any = None,
    ) -> "Deal":
        timestamp = utc_datetime(at)
        identifier = deal_id or str(uuid4())

        tenant_id = _require_id(
            tenant_id,
            "tenant_id",
        )

        customer_id = _require_id(
            customer_id,
            "customer_id",
        )

        broker_id = _require_id(
            broker_id,
            "broker_id",
        )

        builder_id = (
            _require_id(builder_id, "builder_id")
            if builder_id is not None
            else None
        )

        project_id = (
            _require_id(project_id, "project_id")
            if project_id is not None
            else None
        )

        unit_id = (
            _require_id(unit_id, "unit_id")
            if unit_id is not None
            else None
        )

        history = (
            DealHistoryEntry(
                history_id=str(uuid4()),
                from_status=None,
                to_status=DealStatus.QUALIFIED,
                version=1,
                changed_at=timestamp,
                reason="DEAL_CREATED",
            ),
        )

        participants = (
            DealPartyRelationship(
                deal_id=identifier,
                tenant_id=tenant_id,
                role=DealPartyRole.BUYER,
                party_id=customer_id,
            ),
            DealPartyRelationship(
                deal_id=identifier,
                tenant_id=tenant_id,
                role=DealPartyRole.BROKER,
                party_id=broker_id,
            ),
        )

        if builder_id is not None:
            participants += (
                DealPartyRelationship(
                    deal_id=identifier,
                    tenant_id=tenant_id,
                    role=DealPartyRole.BUILDER,
                    party_id=builder_id,
                ),
            )

        return cls(
            deal_id=identifier,
            tenant_id=tenant_id,
            customer_id=customer_id,
            broker_id=broker_id,
            builder_id=builder_id,
            project_id=project_id,
            unit_id=unit_id,
            status=DealStatus.QUALIFIED,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
            history=history,
            participants=participants,
        )

    @property
    def identity_key(self) -> str:
        return f"{self.tenant_id}:{self.deal_id}"

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATES

    @property
    def opportunity_bound(self) -> bool:
        return all(
            value is not None
            for value in (
                self.builder_id,
                self.project_id,
                self.unit_id,
            )
        )

    @property
    def current_offer(self) -> DealOffer | None:
        return (
            self.offers[-1]
            if self.offers
            else None
        )

    @property
    def last_transaction_milestone(
        self,
    ) -> DealTransactionMilestone | None:
        return (
            self.milestones[-1]
            if self.milestones
            else None
        )

    def party_for(
        self,
        role: DealPartyRole,
    ) -> str | None:
        role = DealPartyRole(role)

        for relationship in self.participants:
            if relationship.role is role:
                return relationship.party_id

        return None

    def _assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        if tenant_id != self.tenant_id:
            raise DealTenantError(
                "Deal tenant mismatch."
            )

    def _assert_version(
        self,
        expected_version: int,
    ) -> None:
        if (
            isinstance(expected_version, bool)
            or not isinstance(expected_version, int)
            or expected_version < 1
        ):
            raise DealConcurrencyError(
                "expected_version must be an integer >= 1."
            )

        if expected_version != self.version:
            raise DealConcurrencyError(
                "Deal version is stale."
            )

    def bind_opportunity(
        self,
        *,
        builder_id: str,
        project_id: str,
        unit_id: str,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        builder_id = _require_id(
            builder_id,
            "builder_id",
        )
        project_id = _require_id(
            project_id,
            "project_id",
        )
        unit_id = _require_id(
            unit_id,
            "unit_id",
        )

        if self.opportunity_bound:
            existing = (
                self.builder_id,
                self.project_id,
                self.unit_id,
            )

            requested = (
                builder_id,
                project_id,
                unit_id,
            )

            if existing == requested:
                return self

            raise DealReferenceConflictError(
                "Opportunity substitution is forbidden."
            )

        timestamp = utc_datetime(at)

        participants = tuple(
            p
            for p in self.participants
            if p.role is not DealPartyRole.BUILDER
        )

        participants += (
            DealPartyRelationship(
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
                role=DealPartyRole.BUILDER,
                party_id=builder_id,
            ),
        )

        return replace(
            self,
            builder_id=builder_id,
            project_id=project_id,
            unit_id=unit_id,
            version=self.version + 1,
            updated_at=timestamp,
            participants=participants,
        )

    def bind_party(
        self,
        *,
        role: DealPartyRole,
        party_id: str,
        tenant_id: str,
        expected_version: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        role = DealPartyRole(role)
        party_id = _require_id(
            party_id,
            "party_id",
        )

        existing = next(
            (
                item
                for item in self.participants
                if item.role is role
            ),
            None,
        )

        if existing:
            if existing.party_id == party_id:
                return self

            raise DealReferenceConflictError(
                "Existing party cannot be silently replaced."
            )

        relationship = DealPartyRelationship(
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            role=role,
            party_id=party_id,
            metadata=dict(metadata or {}),
        )

        return replace(
            self,
            participants=(
                self.participants + (relationship,)
            ),
            version=self.version + 1,
        )

    def transition(
        self,
        target: DealStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        reason: str | None = None,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        target = DealStatus(target)

        if self.is_terminal:
            raise DealTransitionError(
                "Terminal Deal cannot transition."
            )

        if target is self.status:
            raise DealTransitionError(
                "Deal cannot transition to its current status."
            )

        allowed = set(
            NOMINAL_TRANSITIONS.get(
                self.status,
                frozenset(),
            )
        )

        if target is DealStatus.CANCELLED:
            allowed.add(target)

        if (
            target is DealStatus.EXPIRED
            and self.status in EXPIRY_STATES
        ):
            allowed.add(target)

        if (
            target is DealStatus.REJECTED
            and self.status in REJECTION_STATES
        ):
            allowed.add(target)

        if (
            target is DealStatus.DISPUTED
            and self.status in DISPUTE_STATES
        ):
            allowed.add(target)

        if target is DealStatus.FRAUD_BLOCKED:
            allowed.add(target)

        if target not in allowed:
            raise DealTransitionError(
                f"Invalid Deal transition: "
                f"{self.status.value} -> "
                f"{target.value}"
            )

        if (
            target is DealStatus.MATCHED
            and not self.opportunity_bound
        ):
            raise DealTransitionError(
                "Deal must have a bound opportunity before MATCHED."
            )

        timestamp = utc_datetime(at)
        new_version = self.version + 1

        history = self.history + (
            DealHistoryEntry(
                history_id=str(uuid4()),
                from_status=self.status,
                to_status=target,
                version=new_version,
                changed_at=timestamp,
                reason=reason,
            ),
        )

        return replace(
            self,
            status=target,
            version=new_version,
            updated_at=timestamp,
            history=history,
        )

    def create_offer(
        self,
        offer_id: str | None = None,
        *,
        tenant_id: str,
        expected_version: int,
        terms: Mapping[str, Any] | None = None,
        supersedes_offer_id: str | None = None,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal Deal cannot create an offer."
            )

        if not self.opportunity_bound:
            raise DealReferenceConflictError(
                "Offer requires a bound opportunity."
            )

        if self.status not in {
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        }:
            raise DealTransitionError(
                "Offer requires VISITED, OFFERED or NEGOTIATING."
            )

        if supersedes_offer_id is not None:
            if not any(
                item.offer_id == supersedes_offer_id
                for item in self.offers
            ):
                raise DealReferenceConflictError(
                    "supersedes_offer_id must reference an existing offer."
                )

        if offer_id is not None:
            existing = next(
                (
                    item
                    for item in self.offers
                    if item.offer_id == offer_id
                ),
                None,
            )

            if existing is not None:
                return self

        offer = DealOffer.create(
            offer_id=offer_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            at=at,
            terms=terms,
            supersedes_offer_id=supersedes_offer_id,
        )

        return replace(
            self,
            offers=self.offers + (offer,),
            version=self.version + 1,
            updated_at=utc_datetime(at),
        )

    def submit_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        index = next(
            (
                i
                for i, offer in enumerate(self.offers)
                if offer.offer_id == offer_id
            ),
            None,
        )

        if index is None:
            raise DealReferenceConflictError(
                "Offer does not belong to this Deal."
            )

        offer = self.offers[index]

        if offer.status is DealOfferStatus.SUBMITTED:
            return self

        updated_offer = offer.transition(
            DealOfferStatus.SUBMITTED,
            tenant_id=tenant_id,
            expected_version=offer.version,
            at=at,
        )

        offers = list(self.offers)
        offers[index] = updated_offer

        target_status = self.status
        history = self.history
        new_version = self.version + 1

        if self.status is DealStatus.VISITED:
            target_status = DealStatus.OFFERED
            history += (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=target_status,
                    version=new_version,
                    changed_at=utc_datetime(at),
                    reason="OFFER_SUBMITTED",
                ),
            )

        return replace(
            self,
            status=target_status,
            offers=tuple(offers),
            version=new_version,
            updated_at=utc_datetime(at),
            history=history,
        )

    def start_negotiation(
        self,
        negotiation_id: str | None = None,
        *,
        tenant_id: str,
        expected_version: int,
        offer_id: str | None = None,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.status is not DealStatus.OFFERED:
            raise DealTransitionError(
                "Negotiation can only start from OFFERED."
            )

        if self.negotiation is not None:
            if (
                negotiation_id is not None
                and self.negotiation.negotiation_id
                == negotiation_id
            ):
                return self

            raise DealReferenceConflictError(
                "Deal already has a negotiation."
            )

        active_offer = (
            self.current_offer
            if offer_id is None
            else next(
                (
                    offer
                    for offer in self.offers
                    if offer.offer_id == offer_id
                ),
                None,
            )
        )

        if active_offer is None:
            raise DealReferenceConflictError(
                "Negotiation requires an existing offer."
            )

        if active_offer.status not in {
            DealOfferStatus.SUBMITTED,
            DealOfferStatus.COUNTERED,
        }:
            raise DealTransitionError(
                "Negotiation requires a submitted/countered offer."
            )

        negotiation = DealNegotiation.create(
            negotiation_id=negotiation_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            active_offer_id=active_offer.offer_id,
            at=at,
        )

        timestamp = utc_datetime(at)
        new_version = self.version + 1

        history = self.history + (
            DealHistoryEntry(
                history_id=str(uuid4()),
                from_status=self.status,
                to_status=DealStatus.NEGOTIATING,
                version=new_version,
                changed_at=timestamp,
                reason="NEGOTIATION_STARTED",
            ),
        )

        return replace(
            self,
            status=DealStatus.NEGOTIATING,
            negotiation=negotiation,
            version=new_version,
            updated_at=timestamp,
            history=history,
        )

    def transition_negotiation(
        self,
        target: DealNegotiationStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.negotiation is None:
            raise DealReferenceConflictError(
                "Deal has no negotiation."
            )

        negotiation = self.negotiation.transition(
            target,
            tenant_id=tenant_id,
            expected_version=self.negotiation.version,
            at=at,
        )

        timestamp = utc_datetime(at)
        new_status = self.status

        if target is DealNegotiationStatus.AGREED:
            new_status = DealStatus.OFFERED

        elif target is DealNegotiationStatus.REJECTED:
            new_status = DealStatus.REJECTED

        history = self.history

        if new_status is not self.status:
            history += (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=new_status,
                    version=self.version + 1,
                    changed_at=timestamp,
                    reason=(
                        f"NEGOTIATION_{target.value}"
                    ),
                ),
            )

        return replace(
            self,
            negotiation=negotiation,
            status=new_status,
            version=self.version + 1,
            updated_at=timestamp,
            history=history,
        )

    def advance_transaction_milestone(
        self,
        target: DealStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        reference_id: str | None = None,
        evidence_required: bool = True,
        at: Any = None,
    ) -> "Deal":
        target = DealStatus(target)

        if target not in TRANSACTION_STATUSES:
            raise DealTransitionError(
                "Target is not a transaction milestone status."
            )

        updated = self.transition(
            target,
            tenant_id=tenant_id,
            expected_version=expected_version,
            reason="TRANSACTION_MILESTONE",
            at=at,
        )

        milestone = DealTransactionMilestone.create(
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            from_status=self.status,
            to_status=target,
            sequence=len(self.milestones) + 1,
            deal_version=updated.version,
            reference_id=reference_id,
            evidence_required=evidence_required,
            occurred_at=updated.updated_at,
        )

        return replace(
            updated,
            milestones=self.milestones + (
                milestone,
            ),
        )

    def bind_ownership(
        self,
        binding_id: str,
        *,
        lead_id: str,
        ownership_record_id: str,
        owner_id: str,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal Deal cannot change ownership."
            )

        binding = DealOwnershipBinding(
            binding_id=binding_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            ownership_record_id=ownership_record_id,
            owner_id=owner_id,
            bound_at=utc_datetime(at),
        )

        if self.ownership_binding is not None:
            current = self.ownership_binding

            if current.to_dict() == binding.to_dict():
                return self

            raise DealOwnershipConflictError(
                "Ownership substitution is forbidden."
            )

        return replace(
            self,
            ownership_binding=binding,
            version=self.version + 1,
            updated_at=utc_datetime(at),
        )

    def attach_evidence(
        self,
        evidence_id: str | None = None,
        *,
        tenant_id: str,
        expected_version: int,
        evidence_type: str,
        reference: str,
        actor_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        candidate = DealEvidenceReference.create(
            evidence_id=evidence_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            deal_version=self.version + 1,
            actor_id=actor_id,
            metadata=metadata,
            at=at,
        )

        if evidence_id is not None:
            for existing in self.evidence:
                if existing.evidence_id != evidence_id:
                    continue

                if existing.semantic_key() == candidate.semantic_key():
                    return self

                raise DealEvidenceConflictError(
                    "Evidence identity already exists with different data."
                )

        return replace(
            self,
            evidence=self.evidence + (
                candidate,
            ),
            version=self.version + 1,
            updated_at=utc_datetime(at),
        )

    def record_audit(
        self,
        *,
        tenant_id: str,
        expected_version: int,
        action: str,
        actor_id: str,
        audit_id: str | None = None,
        outcome: str = "RECORDED",
        metadata: Mapping[str, Any] | None = None,
        at: Any = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        candidate = DealAuditEntry.create(
            audit_id=audit_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            action=action,
            actor_id=actor_id,
            deal_version=self.version + 1,
            outcome=outcome,
            metadata=metadata,
            at=at,
        )

        for existing in self.audit_log:
            if existing.audit_id != candidate.audit_id:
                continue

            if existing.semantic_key() == candidate.semantic_key():
                return self

            raise DealAuditConflictError(
                "Audit identity already exists with different data."
            )

        return replace(
            self,
            audit_log=self.audit_log + (
                candidate,
            ),
            version=self.version + 1,
            updated_at=utc_datetime(at),
        )

    def to_dict(
        self,
        *,
        include_contract: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "deal_id": self.deal_id,
            "identity_key": self.identity_key,
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "broker_id": self.broker_id,
            "builder_id": self.builder_id,
            "project_id": self.project_id,
            "unit_id": self.unit_id,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_of_truth": self.source_of_truth,
            "contract_schema_version": (
                self.contract_schema_version
            ),
            "history": [
                entry.to_dict()
                for entry in self.history
            ],
            "participants": [
                participant.to_dict()
                for participant in self.participants
            ],
            "offers": [
                offer.to_dict()
                for offer in self.offers
            ],
            "negotiation": (
                self.negotiation.to_dict()
                if self.negotiation is not None
                else None
            ),
            "milestones": [
                milestone.to_dict()
                for milestone in self.milestones
            ],
            "ownership_binding": (
                self.ownership_binding.to_dict()
                if self.ownership_binding is not None
                else None
            ),
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "audit_log": [
                item.to_dict()
                for item in self.audit_log
            ],
        }

        if include_contract:
            payload["contract"] = (
                DealContract.from_deal(self).to_dict()
            )

        return payload
