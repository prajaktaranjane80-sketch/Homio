from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

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
from .deal_ownership_integration import DealOwnershipBinding
from .deal_transaction_milestones import DealTransactionMilestone


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


class DealPartyRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    BROKER = "BROKER"
    BUILDER = "BUILDER"


class DealStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    MATCHED = "MATCHED"
    VISIT_PENDING = "VISIT_PENDING"
    VISITED = "VISITED"
    OFFERED = "OFFERED"
    NEGOTIATING = "NEGOTIATING"
    BOOKING_PENDING = "BOOKING_PENDING"
    BOOKED = "BOOKED"
    AGREEMENT_PENDING = "AGREEMENT_PENDING"
    AGREED = "AGREED"
    REGISTRATION_PENDING = "REGISTRATION_PENDING"
    REGISTERED = "REGISTERED"
    COMPLETION_PENDING = "COMPLETION_PENDING"
    COMPLETED = "COMPLETED"

    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    FRAUD_BLOCKED = "FRAUD_BLOCKED"


_NOMINAL: dict[
    DealStatus,
    frozenset[DealStatus],
] = {
    DealStatus.QUALIFIED: frozenset({DealStatus.MATCHED}),
    DealStatus.MATCHED: frozenset({DealStatus.VISIT_PENDING}),
    DealStatus.VISIT_PENDING: frozenset({DealStatus.VISITED}),
    DealStatus.VISITED: frozenset({DealStatus.OFFERED}),
    DealStatus.OFFERED: frozenset({
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
    }),
    DealStatus.NEGOTIATING: frozenset({
        DealStatus.OFFERED,
        DealStatus.BOOKING_PENDING,
    }),
    DealStatus.BOOKING_PENDING: frozenset({
        DealStatus.BOOKED,
    }),
    DealStatus.BOOKED: frozenset({
        DealStatus.AGREEMENT_PENDING,
    }),
    DealStatus.AGREEMENT_PENDING: frozenset({
        DealStatus.AGREED,
    }),
    DealStatus.AGREED: frozenset({
        DealStatus.REGISTRATION_PENDING,
    }),
    DealStatus.REGISTRATION_PENDING: frozenset({
        DealStatus.REGISTERED,
    }),
    DealStatus.REGISTERED: frozenset({
        DealStatus.COMPLETION_PENDING,
    }),
    DealStatus.COMPLETION_PENDING: frozenset({
        DealStatus.COMPLETED,
    }),
    DealStatus.COMPLETED: frozenset(),
    DealStatus.CANCELLED: frozenset(),
    DealStatus.EXPIRED: frozenset(),
    DealStatus.REJECTED: frozenset(),
    DealStatus.DISPUTED: frozenset(),
    DealStatus.FRAUD_BLOCKED: frozenset(),
}


_PREBOOK = frozenset({
    DealStatus.QUALIFIED,
    DealStatus.MATCHED,
    DealStatus.VISIT_PENDING,
    DealStatus.VISITED,
    DealStatus.OFFERED,
    DealStatus.NEGOTIATING,
    DealStatus.BOOKING_PENDING,
    DealStatus.AGREEMENT_PENDING,
})


_DISPUTE = frozenset({
    DealStatus.BOOKED,
    DealStatus.AGREEMENT_PENDING,
    DealStatus.AGREED,
    DealStatus.REGISTRATION_PENDING,
    DealStatus.REGISTERED,
    DealStatus.COMPLETION_PENDING,
})


_ACTIVE = frozenset(_NOMINAL.keys()) - frozenset({
    DealStatus.COMPLETED,
    DealStatus.CANCELLED,
    DealStatus.EXPIRED,
    DealStatus.REJECTED,
    DealStatus.DISPUTED,
    DealStatus.FRAUD_BLOCKED,
})


def _id(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealValidationError(
            f"{name} must be a non-empty string."
        )
    return value.strip()


def _dt(
    value: datetime | str | None,
) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise DealValidationError(
                "Invalid ISO-8601 datetime."
            ) from exc

    if not isinstance(value, datetime):
        raise DealValidationError(
            "Timestamp must be datetime, ISO-8601 string, or None."
        )

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class DealHistoryEntry:
    history_id: str
    from_status: DealStatus | None
    to_status: DealStatus
    version: int
    changed_at: datetime
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "from_status": (
                self.from_status.value
                if self.from_status
                else None
            ),
            "to_status": self.to_status.value,
            "version": self.version,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DealPartyRelationship:
    deal_id: str
    tenant_id: str
    role: DealPartyRole
    party_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "role": self.role.value,
            "party_id": self.party_id,
        }


@dataclass(frozen=True)
class Deal:
    """
    Canonical CORE-006 Deal aggregate.

    Owns:
      - Deal lifecycle
      - Deal identity
      - transaction version
      - immutable history
      - offer/negotiation state
      - transaction milestone references

    References:
      - Lead ownership authority
      - Evidence authority
      - Inventory references
      - Identity/tenant context

    Does NOT implement:
      - search engine
      - event transport
      - fraud engine
      - governance engine
      - commission engine
      - AI decision engine
    """

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

    history: tuple[DealHistoryEntry, ...]

    source_of_truth: str = "deal"

    offers: tuple[DealOffer, ...] = field(
        default_factory=tuple
    )

    negotiation: DealNegotiation | None = None

    milestones: tuple[
        DealTransactionMilestone,
        ...
    ] = field(default_factory=tuple)

    ownership_binding: DealOwnershipBinding | None = None

    evidence: tuple[
        DealEvidenceReference,
        ...
    ] = field(default_factory=tuple)

    audit_log: tuple[
        DealAuditEntry,
        ...
    ] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "customer_id",
            "broker_id",
        ):
            _id(getattr(self, name), name)

        for name in (
            "builder_id",
            "project_id",
            "unit_id",
        ):
            value = getattr(self, name)

            if value is not None:
                _id(value, name)

        if self.version < 1:
            raise DealValidationError(
                "version must be >= 1."
            )

        object.__setattr__(
            self,
            "status",
            DealStatus(self.status),
        )

        if self.source_of_truth != "deal":
            raise DealValidationError(
                "Deal source_of_truth must remain 'deal'."
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
        at: datetime | str | None = None,
    ) -> "Deal":
        stamp = _dt(at)
        canonical_deal_id = deal_id or str(uuid4())

        history = DealHistoryEntry(
            history_id=str(uuid4()),
            from_status=None,
            to_status=DealStatus.QUALIFIED,
            version=1,
            changed_at=stamp,
            reason="DEAL_CREATED",
        )

        return cls(
            deal_id=_id(
                canonical_deal_id,
                "deal_id",
            ),
            tenant_id=_id(
                tenant_id,
                "tenant_id",
            ),
            customer_id=_id(
                customer_id,
                "customer_id",
            ),
            broker_id=_id(
                broker_id,
                "broker_id",
            ),
            builder_id=(
                _id(builder_id, "builder_id")
                if builder_id is not None
                else None
            ),
            project_id=(
                _id(project_id, "project_id")
                if project_id is not None
                else None
            ),
            unit_id=(
                _id(unit_id, "unit_id")
                if unit_id is not None
                else None
            ),
            status=DealStatus.QUALIFIED,
            version=1,
            created_at=stamp,
            updated_at=stamp,
            history=(history,),
        )

    @property
    def identity_key(self) -> str:
        return f"{self.tenant_id}:{self.deal_id}"

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
    def is_terminal(self) -> bool:
        return self.status not in _ACTIVE

    @property
    def current_offer(self) -> DealOffer | None:
        if not self.offers:
            return None

        return self.offers[-1]

    @property
    def party_relationships(
        self,
    ) -> tuple[DealPartyRelationship, ...]:
        pairs = (
            (
                DealPartyRole.CUSTOMER,
                self.customer_id,
            ),
            (
                DealPartyRole.BROKER,
                self.broker_id,
            ),
            (
                DealPartyRole.BUILDER,
                self.builder_id,
            ),
        )

        return tuple(
            DealPartyRelationship(
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
                role=role,
                party_id=party_id,
            )
            for role, party_id in pairs
            if party_id is not None
        )

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise DealTenantError(
                "Deal operation belongs to a different tenant."
            )

    def _version(
        self,
        expected_version: int | None,
    ) -> None:
        if expected_version is None:
            return

        if (
            not isinstance(expected_version, int)
            or isinstance(expected_version, bool)
            or expected_version < 1
        ):
            raise DealConcurrencyError(
                "expected_version must be an integer >= 1."
            )

        if expected_version != self.version:
            raise DealConcurrencyError(
                "Deal version is stale; refresh before mutating."
            )

    def bind_opportunity(
        self,
        *,
        builder_id: str,
        project_id: str,
        unit_id: str,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        values = (
            _id(builder_id, "builder_id"),
            _id(project_id, "project_id"),
            _id(unit_id, "unit_id"),
        )

        if self.opportunity_bound:
            if (
                self.builder_id,
                self.project_id,
                self.unit_id,
            ) == values:
                return self

            raise DealReferenceConflictError(
                "Opportunity substitution is forbidden."
            )

        stamp = _dt(at)

        return replace(
            self,
            builder_id=values[0],
            project_id=values[1],
            unit_id=values[2],
            version=self.version + 1,
            updated_at=stamp,
        )

    def transition(
        self,
        target: DealStatus | str,
        *,
        tenant_id: str,
        expected_version: int | None = None,
        reason: str | None = None,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        target = DealStatus(target)

        if self.is_terminal:
            raise DealTransitionError(
                "Terminal Deal cannot transition."
            )

        if target == self.status:
            raise DealTransitionError(
                "Deal cannot transition to its current status."
            )

        if (
            target is DealStatus.MATCHED
            and not self.opportunity_bound
        ):
            raise DealTransitionError(
                "Deal must be bound to builder/project/unit "
                "before MATCHED."
            )

        allowed = set(
            _NOMINAL[self.status]
        )

        if target is DealStatus.CANCELLED:
            allowed.add(target)

        if (
            target is DealStatus.EXPIRED
            and self.status in _PREBOOK
        ):
            allowed.add(target)

        if (
            target is DealStatus.REJECTED
            and self.status in _PREBOOK
        ):
            allowed.add(target)

        if target is DealStatus.FRAUD_BLOCKED:
            allowed.add(target)

        if (
            target is DealStatus.DISPUTED
            and self.status in _DISPUTE
        ):
            allowed.add(target)

        if target not in allowed:
            raise DealTransitionError(
                f"Invalid Deal transition: "
                f"{self.status.value} -> {target.value}."
            )

        stamp = _dt(at)
        version = self.version + 1

        history = self.history + (
            DealHistoryEntry(
                history_id=str(uuid4()),
                from_status=self.status,
                to_status=target,
                version=version,
                changed_at=stamp,
                reason=reason,
            ),
        )

        return replace(
            self,
            status=target,
            version=version,
            updated_at=stamp,
            history=history,
        )

    def create_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        supersedes_offer_id: str | None = None,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal Deal cannot create offers."
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
                "Offers require VISITED, OFFERED or NEGOTIATING."
            )

        if any(
            item.offer_id == offer_id
            for item in self.offers
        ):
            return self

        if (
            supersedes_offer_id is not None
            and not any(
                item.offer_id == supersedes_offer_id
                for item in self.offers
            )
        ):
            raise DealReferenceConflictError(
                "supersedes_offer_id must reference this Deal."
            )

        offer = DealOffer.create(
            offer_id=offer_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            at=at,
            supersedes_offer_id=supersedes_offer_id,
        )

        return replace(
            self,
            offers=self.offers + (offer,),
            version=self.version + 1,
            updated_at=_dt(at),
        )

    def submit_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        index = next(
            (
                index
                for index, item in enumerate(self.offers)
                if item.offer_id == offer_id
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

        status = (
            DealStatus.OFFERED
            if self.status is DealStatus.VISITED
            else self.status
        )

        if status not in {
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        }:
            raise DealTransitionError(
                "Offer submission is invalid from current Deal state."
            )

        stamp = _dt(at)
        version = self.version + 1
        history = self.history

        if status is not self.status:
            history = history + (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=status,
                    version=version,
                    changed_at=stamp,
                    reason="OFFER_SUBMITTED",
                ),
            )

        return replace(
            self,
            status=status,
            offers=tuple(offers),
            version=version,
            updated_at=stamp,
            history=history,
        )

    def start_negotiation(
        self,
        negotiation_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        offer_id: str | None = None,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.status is not DealStatus.OFFERED:
            raise DealTransitionError(
                "Negotiation can only start from OFFERED."
            )

        if self.negotiation is not None:
            if (
                self.negotiation.negotiation_id
                == negotiation_id
            ):
                return self

            raise DealReferenceConflictError(
                "Deal already has a negotiation."
            )

        offer = (
            self.current_offer
            if offer_id is None
            else next(
                (
                    item
                    for item in self.offers
                    if item.offer_id == offer_id
                ),
                None,
            )
        )

        if (
            offer is None
            or offer.status is not DealOfferStatus.SUBMITTED
        ):
            raise DealTransitionError(
                "Negotiation requires a SUBMITTED offer."
            )

        negotiation = DealNegotiation.create(
            negotiation_id=negotiation_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            active_offer_id=offer.offer_id,
            at=at,
        )

        updated = self.transition(
            DealStatus.NEGOTIATING,
            tenant_id=tenant_id,
            expected_version=self.version,
            reason="NEGOTIATION_STARTED",
            at=at,
        )

        return replace(
            updated,
            negotiation=negotiation,
        )

    def close_negotiation(
        self,
        *,
        tenant_id: str,
        expected_version: int,
        accepted: bool,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.negotiation is None:
            raise DealReferenceConflictError(
                "No active negotiation exists."
            )

        target = (
            DealNegotiationStatus.AGREED
            if accepted
            else DealNegotiationStatus.CLOSED
        )

        negotiation = self.negotiation.transition(
            target,
            tenant_id=tenant_id,
            expected_version=self.negotiation.version,
            at=at,
        )

        updated = replace(
            self,
            negotiation=negotiation,
            version=self.version + 1,
            updated_at=_dt(at),
        )

        if accepted:
            updated = updated.transition(
                DealStatus.BOOKING_PENDING,
                tenant_id=tenant_id,
                expected_version=updated.version,
                reason="NEGOTIATION_AGREED",
                at=at,
            )

        return updated

    def advance_transaction_milestone(
        self,
        target: DealStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        reference_id: str | None = None,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        updated = self.transition(
            target,
            tenant_id=tenant_id,
            expected_version=self.version,
            at=at,
        )

        milestone = DealTransactionMilestone.create(
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            from_status=self.status,
            to_status=updated.status,
            sequence=len(self.milestones) + 1,
            deal_version=updated.version,
            occurred_at=at,
            reference_id=reference_id,
        )

        return replace(
            updated,
            milestones=self.milestones + (milestone,),
        )

    def bind_ownership(
        self,
        *,
        binding_id: str,
        lead_id: str,
        ownership_record_id: str,
        owner_id: str,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal Deal cannot change ownership binding."
            )

        if self.ownership_binding is not None:
            current = self.ownership_binding

            if (
                current.ownership_record_id,
                current.lead_id,
                current.owner_id,
            ) == (
                ownership_record_id,
                lead_id,
                owner_id,
            ):
                return self

            raise DealReferenceConflictError(
                "Ownership substitution is forbidden."
            )

        stamp = _dt(at)

        binding = DealOwnershipBinding(
            binding_id=binding_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            ownership_record_id=ownership_record_id,
            owner_id=owner_id,
            bound_at=stamp,
        )

        return replace(
            self,
            ownership_binding=binding,
            version=self.version + 1,
            updated_at=stamp,
        )

    def attach_evidence(
        self,
        evidence_id: str,
        *,
        evidence_type: str,
        reference: str,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        probe = (
            evidence_id,
            self.deal_id,
            tenant_id,
            evidence_type,
            reference,
            dict(metadata or {}),
        )

        for existing in self.evidence:
            if existing.evidence_id == evidence_id:
                if existing.semantic_key() == probe:
                    return self

                raise DealEvidenceConflictError(
                    "Evidence identity is already bound "
                    "to different data."
                )

        version = self.version + 1

        evidence = DealEvidenceReference.create(
            evidence_id=evidence_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            deal_version=version,
            at=at,
            metadata=metadata,
        )

        return replace(
            self,
            evidence=self.evidence + (evidence,),
            version=version,
            updated_at=_dt(at),
        )

    def record_audit(
        self,
        *,
        action: str,
        actor_id: str,
        tenant_id: str,
        expected_version: int,
        audit_id: str | None = None,
        outcome: str = "RECORDED",
        at: datetime | str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if audit_id is not None:
            probe = (
                audit_id,
                self.deal_id,
                tenant_id,
                action,
                actor_id,
                outcome,
                dict(metadata or {}),
            )

            for existing in self.audit_log:
                if existing.audit_id == audit_id:
                    if existing.semantic_key() == probe:
                        return self

                    raise DealAuditConflictError(
                        "Audit identity is already bound "
                        "to different data."
                    )

        version = self.version + 1

        audit = DealAuditEntry.create(
            audit_id=audit_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            action=action,
            actor_id=actor_id,
            deal_version=version,
            outcome=outcome,
            at=at,
            metadata=metadata,
        )

        return replace(
            self,
            audit_log=self.audit_log + (audit,),
            version=version,
            updated_at=_dt(at),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
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
            "history": [
                item.to_dict()
                for item in self.history
            ],
            "source_of_truth": self.source_of_truth,
            "offers": [
                item.to_dict()
                for item in self.offers
            ],
            "negotiation": (
                self.negotiation.to_dict()
                if self.negotiation
                else None
            ),
            "milestones": [
                item.to_dict()
                for item in self.milestones
            ],
            "ownership_binding": (
                self.ownership_binding.to_dict()
                if self.ownership_binding
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


__all__ = [
    "Deal",
    "DealDomainError",
    "DealTransitionError",
    "DealTenantError",
    "DealConcurrencyError",
    "DealReferenceConflictError",
    "DealValidationError",
    "DealStatus",
    "DealPartyRole",
    "DealPartyRelationship",
    "DealHistoryEntry",
    "DealOffer",
    "DealOfferStatus",
    "DealNegotiation",
    "DealNegotiationStatus",
]
