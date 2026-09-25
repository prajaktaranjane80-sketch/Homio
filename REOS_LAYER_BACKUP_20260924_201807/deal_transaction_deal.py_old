from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from .deal_offer_negotiation import (
    DealOffer,
    DealOfferStatus,
    DealNegotiation,
    DealNegotiationStatus,
)
from enum import Enum
from typing import Any
from uuid import uuid4

from .deal_transaction_milestones import DealTransactionMilestone
from .deal_ownership_integration import DealOwnershipBinding


class DealDomainError(ValueError):
    """Base error for Deal aggregate failures."""


class DealTransitionError(DealDomainError):
    """Raised when a Deal lifecycle transition is invalid."""


class DealTenantError(DealDomainError):
    """Raised when a Deal operation crosses tenant boundaries."""


class DealConcurrencyError(DealDomainError):
    """Raised when a stale Deal version attempts a mutation."""


class DealReferenceConflictError(DealDomainError):
    """Raised when bound opportunity references are silently substituted."""


class DealValidationError(DealDomainError):
    """Raised when Deal identity or required references are invalid."""


class DealPartyRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    BROKER = "BROKER"
    BUILDER = "BUILDER"


@dataclass(frozen=True)
class DealPartyRelationship:
    """Immutable tenant-scoped relationship view for a Deal party."""

    deal_id: str
    tenant_id: str
    role: DealPartyRole
    party_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.deal_id, str) or not self.deal_id.strip():
            raise DealValidationError("deal_id is required.")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise DealValidationError("tenant_id is required.")
        if not isinstance(self.party_id, str) or not self.party_id.strip():
            raise DealValidationError("party_id is required.")

        object.__setattr__(self, "role", DealPartyRole(self.role))

    @property
    def relationship_key(self) -> str:
        return f"{self.tenant_id}:{self.deal_id}:{self.role.value}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_key": self.relationship_key,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "role": self.role.value,
            "party_id": self.party_id,
        }
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
                if self.from_status is not None
                else None
            ),
            "to_status": self.to_status.value,
            "version": self.version,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason,
        }


_NOMINAL_TRANSITIONS: dict[DealStatus, frozenset[DealStatus]] = {
    DealStatus.QUALIFIED: frozenset({DealStatus.MATCHED}),
    DealStatus.MATCHED: frozenset({DealStatus.VISIT_PENDING}),
    DealStatus.VISIT_PENDING: frozenset({DealStatus.VISITED}),
    DealStatus.VISITED: frozenset({DealStatus.OFFERED}),
    DealStatus.OFFERED: frozenset(
        {
            DealStatus.NEGOTIATING,
            DealStatus.BOOKING_PENDING,
        }
    ),
    DealStatus.NEGOTIATING: frozenset(
        {
            DealStatus.OFFERED,
            DealStatus.BOOKING_PENDING,
        }
    ),
    DealStatus.BOOKING_PENDING: frozenset({DealStatus.BOOKED}),
    DealStatus.BOOKED: frozenset({DealStatus.AGREEMENT_PENDING}),
    DealStatus.AGREEMENT_PENDING: frozenset({DealStatus.AGREED}),
    DealStatus.AGREED: frozenset({DealStatus.REGISTRATION_PENDING}),
    DealStatus.REGISTRATION_PENDING: frozenset({DealStatus.REGISTERED}),
    DealStatus.REGISTERED: frozenset({DealStatus.COMPLETION_PENDING}),
    DealStatus.COMPLETION_PENDING: frozenset({DealStatus.COMPLETED}),
    DealStatus.COMPLETED: frozenset(),
    DealStatus.CANCELLED: frozenset(),
    DealStatus.EXPIRED: frozenset(),
    DealStatus.REJECTED: frozenset(),
    DealStatus.DISPUTED: frozenset(),
    DealStatus.FRAUD_BLOCKED: frozenset(),
}


_PRE_BOOKING_EXPIRY_STATES = frozenset(
    {
        DealStatus.QUALIFIED,
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
        DealStatus.AGREEMENT_PENDING,
    }
)

_REJECTION_STATES = frozenset(
    {
        DealStatus.QUALIFIED,
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
        DealStatus.AGREEMENT_PENDING,
    }
)

_DISPUTE_STATES = frozenset(
    {
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
    }
)

_NON_TERMINAL_STATES = frozenset(
    {
        DealStatus.QUALIFIED,
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
    }
)


def _require_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealValidationError(
            f"{field_name} must be a non-empty string."
        )
    return value.strip()


def _coerce_datetime(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DealValidationError(
                "at must be a valid ISO-8601 datetime."
            ) from exc

    if not isinstance(value, datetime):
        raise DealValidationError(
            "at must be a datetime, ISO-8601 string, or None."
        )

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Deal:
    """
    Canonical Deal aggregate for CORE-006-T01.

    Owns:
        identity
        tenant
        customer/broker references
        builder/project/unit references
        lifecycle state
        version
        immutable history

    Does not own:
        commission calculation
        trust/fraud scoring authority
        search indexing
        AI authority
        global governance policy
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
    offers: tuple[DealOffer, ...] = field(default_factory=tuple)
    negotiation: DealNegotiation | None = None
    milestones: tuple[DealTransactionMilestone, ...] = field(default_factory=tuple)
    ownership_binding: DealOwnershipBinding | None = None
    evidence: tuple[DealEvidenceReference, ...] = ()
    audit_log: tuple[DealAuditEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.deal_id, "deal_id")
        _require_id(self.tenant_id, "tenant_id")
        _require_id(self.customer_id, "customer_id")
        _require_id(self.broker_id, "broker_id")

        for field_name in (
            "builder_id",
            "project_id",
            "unit_id",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_id(value, field_name)

        if self.version < 1:
            raise DealValidationError("version must be >= 1.")

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
        timestamp = _coerce_datetime(at)

        deal = cls(
            deal_id=deal_id or str(uuid4()),
            tenant_id=_require_id(tenant_id, "tenant_id"),
            customer_id=_require_id(customer_id, "customer_id"),
            broker_id=_require_id(broker_id, "broker_id"),
            builder_id=(
                _require_id(builder_id, "builder_id")
                if builder_id is not None
                else None
            ),
            project_id=(
                _require_id(project_id, "project_id")
                if project_id is not None
                else None
            ),
            unit_id=(
                _require_id(unit_id, "unit_id")
                if unit_id is not None
                else None
            ),
            status=DealStatus.QUALIFIED,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
            history=(),
        )

        creation_history = DealHistoryEntry(
            history_id=str(uuid4()),
            from_status=None,
            to_status=DealStatus.QUALIFIED,
            version=1,
            changed_at=timestamp,
            reason="DEAL_CREATED",
        )

        return cls(
            **{
                **deal.__dict__,
                "history": (creation_history,),
            }
        )

    @property
    def identity_key(self) -> str:
        return f"{self.tenant_id}:{self.deal_id}"

    @property
    def party_relationships(self) -> tuple[DealPartyRelationship, ...]:
        """Return the canonical current party relationships for this Deal."""
        bindings = [
            (DealPartyRole.CUSTOMER, self.customer_id),
            (DealPartyRole.BROKER, self.broker_id),
            (DealPartyRole.BUILDER, self.builder_id),
        ]

        return tuple(
            DealPartyRelationship(
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
                role=role,
                party_id=party_id,
            )
            for role, party_id in bindings
            if party_id is not None
        )

    def party_for(self, role: DealPartyRole) -> str | None:
        role = DealPartyRole(role)

        for relationship in self.party_relationships:
            if relationship.role is role:
                return relationship.party_id

        return None

    @property
    def is_terminal(self) -> bool:
        return self.status not in _NON_TERMINAL_STATES

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

    def _assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise DealTenantError(
                "Deal operation belongs to a different tenant."
            )

    def _assert_version(self, expected_version: int | None) -> None:
        if expected_version is None:
            return

        if expected_version < 1:
            raise DealConcurrencyError(
                "expected_version must be >= 1."
            )

        if expected_version != self.version:
            raise DealConcurrencyError(
                "Deal version is stale; refresh before mutating."
            )

    @property
    def current_offer(self) -> DealOffer | None:
        return self.offers[-1] if self.offers else None

    def create_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        supersedes_offer_id: str | None = None,
        at: datetime | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot create offers."
            )

        if not self.opportunity_bound:
            raise DealReferenceConflictError(
                "Offer requires a bound builder/project/unit opportunity."
            )

        if self.status not in (
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        ):
            raise DealTransitionError(
                "Offers can only be created after a deal reaches VISITED."
            )

        if any(
            existing.offer_id == offer_id
            for existing in self.offers
        ):
            return self

        if supersedes_offer_id is not None and not any(
            existing.offer_id == supersedes_offer_id
            for existing in self.offers
        ):
            raise DealReferenceConflictError(
                "supersedes_offer_id must reference an existing offer."
            )

        timestamp = at or _utc_now()

        offer = DealOffer.create(
            offer_id=offer_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            at=timestamp,
            supersedes_offer_id=supersedes_offer_id,
        )

        return replace(
            self,
            offers=self.offers + (offer,),
            version=self.version + 1,
            updated_at=timestamp,
        )

    def submit_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        offer_index = next(
            (
                index
                for index, existing in enumerate(self.offers)
                if existing.offer_id == offer_id
            ),
            None,
        )

        if offer_index is None:
            raise DealReferenceConflictError(
                "Offer does not belong to this Deal."
            )

        offer = self.offers[offer_index]

        if offer.status is DealOfferStatus.SUBMITTED:
            return self

        updated_offer = offer.transition(
            DealOfferStatus.SUBMITTED,
            tenant_id=tenant_id,
            expected_version=offer.version,
            at=at,
        )

        updated_offers = list(self.offers)
        updated_offers[offer_index] = updated_offer

        timestamp = at or _utc_now()
        target_status = self.status

        if self.status is DealStatus.VISITED:
            target_status = DealStatus.OFFERED
        elif self.status not in (
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        ):
            raise DealTransitionError(
                "Offer submission is only valid from VISITED, "
                "OFFERED or NEGOTIATING."
            )

        history = self.history

        if target_status is not self.status:
            history = history + (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=target_status,
                    version=self.version + 1,
                    changed_at=timestamp,
                    reason="OFFER_SUBMITTED",
                ),
            )

        return replace(
            self,
            status=target_status,
            offers=tuple(updated_offers),
            version=self.version + 1,
            updated_at=timestamp,
            history=history,
        )

    def start_negotiation(
        self,
        negotiation_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        offer_id: str | None = None,
        at: datetime | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot start negotiations."
            )

        if self.status is not DealStatus.OFFERED:
            raise DealTransitionError(
                "Negotiation can only start from OFFERED."
            )

        if self.negotiation is not None:
            if self.negotiation.negotiation_id == negotiation_id:
                return self
            raise DealReferenceConflictError(
                "Deal already has a negotiation reference."
            )

        active_offer = (
            self.current_offer
            if offer_id is None
            else next(
                (
                    existing
                    for existing in self.offers
                    if existing.offer_id == offer_id
                ),
                None,
            )
        )

        if active_offer is None:
            raise DealReferenceConflictError(
                "Negotiation requires an existing offer."
            )

        if active_offer.status is not DealOfferStatus.SUBMITTED:
            raise DealTransitionError(
                "Negotiation requires a SUBMITTED offer."
            )

        timestamp = at or _utc_now()

        negotiation = DealNegotiation.create(
            negotiation_id=negotiation_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            active_offer_id=active_offer.offer_id,
            at=timestamp,
        )

        history = self.history + (
            DealHistoryEntry(
                history_id=str(uuid4()),
                from_status=self.status,
                to_status=DealStatus.NEGOTIATING,
                version=self.version + 1,
                changed_at=timestamp,
                reason="NEGOTIATION_STARTED",
            ),
        )

        return replace(
            self,
            status=DealStatus.NEGOTIATING,
            negotiation=negotiation,
            version=self.version + 1,
            updated_at=timestamp,
            history=history,
        )

    def transition_negotiation(
        self,
        target: DealNegotiationStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.negotiation is None:
            raise DealReferenceConflictError(
                "Deal has no negotiation reference."
            )

        updated_negotiation = self.negotiation.transition(
            target,
            tenant_id=tenant_id,
            expected_version=self.negotiation.version,
            at=at,
        )

        timestamp = at or _utc_now()
        updated_status = self.status
        history = self.history

        if target in (
            DealNegotiationStatus.CONCLUDED,
            DealNegotiationStatus.ABORTED,
        ):
            if self.status is not DealStatus.NEGOTIATING:
                raise DealTransitionError(
                    "Negotiation can only close while Deal is NEGOTIATING."
                )

            updated_status = DealStatus.OFFERED
            history = history + (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=updated_status,
                    version=self.version + 1,
                    changed_at=timestamp,
                    reason=f"NEGOTIATION_{target.value}",
                ),
            )

        return replace(
            self,
            status=updated_status,
            negotiation=updated_negotiation,
            version=self.version + 1,
            updated_at=timestamp,
            history=history,
        )

    def advance_negotiation_round(
        self,
        *,
        tenant_id: str,
        expected_version: int,
        active_offer_id: str,
        at: datetime | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.negotiation is None:
            raise DealReferenceConflictError(
                "Deal has no negotiation reference."
            )

        if not any(
            existing.offer_id == active_offer_id
            for existing in self.offers
        ):
            raise DealReferenceConflictError(
                "Negotiation round must reference an existing offer."
            )

        updated_negotiation = self.negotiation.advance_round(
            tenant_id=tenant_id,
            expected_version=self.negotiation.version,
            active_offer_id=active_offer_id,
            at=at,
        )

        return replace(
            self,
            negotiation=updated_negotiation,
            version=self.version + 1,
            updated_at=at or _utc_now(),
        )

    @property
    def last_transaction_milestone(self) -> DealTransactionMilestone | None:
        return self.milestones[-1] if self.milestones else None

    def advance_transaction_milestone(
        self,
        target: DealStatus,
        *,
        tenant_id: str,
        expected_version: int,
        reference_id: str | None = None,
        at: str | None = None,
    ) -> "Deal":
        """Advance the canonical Deal lifecycle and append one milestone."""
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        target = DealStatus(target)

        transaction_statuses = {
            DealStatus.BOOKING_PENDING,
            DealStatus.BOOKED,
            DealStatus.AGREEMENT_PENDING,
            DealStatus.AGREED,
            DealStatus.REGISTRATION_PENDING,
            DealStatus.REGISTERED,
            DealStatus.COMPLETION_PENDING,
            DealStatus.COMPLETED,
        }

        if target not in transaction_statuses:
            raise DealTransitionError(
                f"{target.value} is not a transaction milestone."
            )

        updated = self.transition(
            target,
            tenant_id=tenant_id,
            expected_version=expected_version,
            at=at,
        )

        timestamp = (
            datetime.fromisoformat(updated.updated_at)
            if isinstance(updated.updated_at, str)
            else updated.updated_at
        )

        milestone = DealTransactionMilestone(
            milestone_id=str(uuid4()),
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            from_status=self.status,
            to_status=target,
            sequence=len(self.milestones) + 1,
            deal_version=updated.version,
            occurred_at=timestamp,
            reference_id=reference_id,
        )

        return replace(
            updated,
            milestones=self.milestones + (milestone,),
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
        from .deal_evidence_audit import (
            DealEvidenceConflictError,
            DealEvidenceReference,
        )

        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        candidate_semantics = (
            evidence_id,
            self.deal_id,
            tenant_id,
            evidence_type,
            reference,
            dict(metadata or {}),
        )

        for existing in self.evidence:
            if existing.evidence_id != evidence_id:
                continue

            if existing.semantic_key() == candidate_semantics:
                return self

            raise DealEvidenceConflictError(
                f"Evidence id {evidence_id!r} is already bound "
                "with different immutable data."
            )

        new_version = self.version + 1
        evidence = DealEvidenceReference.create(
            evidence_id=evidence_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            deal_version=new_version,
            at=at,
            metadata=metadata,
        )

        return replace(
            self,
            version=new_version,
            evidence=self.evidence + (evidence,),
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
        from .deal_evidence_audit import (
            DealAuditConflictError,
            DealAuditEntry,
        )

        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        for existing in self.audit_log:
            if audit_id is None or existing.audit_id != audit_id:
                continue

            candidate_semantics = (
                audit_id,
                self.deal_id,
                tenant_id,
                action,
                actor_id,
                outcome,
                dict(metadata or {}),
            )

            if existing.semantic_key() == candidate_semantics:
                return self

            raise DealAuditConflictError(
                f"Audit id {audit_id!r} is already recorded "
                "with different immutable data."
            )

        new_version = self.version + 1
        audit = DealAuditEntry.create(
            audit_id=audit_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            action=action,
            actor_id=actor_id,
            deal_version=new_version,
            outcome=outcome,
            at=at,
            metadata=metadata,
        )

        return replace(
            self,
            version=new_version,
            audit_log=self.audit_log + (audit,),
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
        at: datetime | None = None,
    ) -> "Deal":
        """Bind the Deal to the authoritative ARCH-011 ownership record."""
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot change ownership binding."
            )

        timestamp = at or datetime.now(timezone.utc)

        if self.ownership_binding is not None:
            existing = self.ownership_binding

            if (
                existing.ownership_record_id == ownership_record_id
                and existing.lead_id == lead_id
                and existing.owner_id == owner_id
            ):
                return self

            raise DealReferenceConflictError(
                "Deal ownership binding already exists; "
                "silent substitution is forbidden."
            )

        binding = DealOwnershipBinding(
            binding_id=binding_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            ownership_record_id=ownership_record_id,
            owner_id=owner_id,
            bound_at=timestamp,
        )

        return replace(
            self,
            ownership_binding=binding,
            version=self.version + 1,
            updated_at=timestamp,
        )

    def bind_party(
        self,
        role: DealPartyRole,
        party_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        at: str | None = None,
    ) -> "Deal":
        """Bind one canonical party relationship without silent substitution."""
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        role = DealPartyRole(role)

        if not isinstance(party_id, str) or not party_id.strip():
            raise DealValidationError("party_id is required.")

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot change party relationships."
            )

        current_party_id = self.party_for(role)

        if current_party_id == party_id:
            return self

        if current_party_id is not None:
            raise DealReferenceConflictError(
                f"Cannot silently replace existing {role.value} party."
            )

        timestamp = at or _utc_now()

        updates: dict[str, Any] = {
            "updated_at": timestamp,
            "version": self.version + 1,
        }

        if role is DealPartyRole.CUSTOMER:
            updates["customer_id"] = party_id
        elif role is DealPartyRole.BROKER:
            updates["broker_id"] = party_id
        elif role is DealPartyRole.BUILDER:
            updates["builder_id"] = party_id

        return replace(self, **updates)

    def bind_opportunity(
        self,
        *,
        builder_id: str,
        project_id: str,
        unit_id: str,
        tenant_id: str,
        expected_version: int | None = None,
        at: datetime | str | None = None,
    ) -> "Deal":
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        if self.status not in {
            DealStatus.QUALIFIED,
            DealStatus.MATCHED,
            DealStatus.VISIT_PENDING,
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        }:
            raise DealReferenceConflictError(
                "Opportunity references cannot be changed at this "
                f"Deal status: {self.status.value}."
            )

        builder_id = _require_id(builder_id, "builder_id")
        project_id = _require_id(project_id, "project_id")
        unit_id = _require_id(unit_id, "unit_id")

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

        if any(value is not None for value in existing):
            if existing != requested:
                raise DealReferenceConflictError(
                    "Existing opportunity references cannot be silently "
                    "substituted."
                )

            return self

        timestamp = _coerce_datetime(at)

        return Deal(
            **{
                **self.__dict__,
                "builder_id": builder_id,
                "project_id": project_id,
                "unit_id": unit_id,
                "version": self.version + 1,
                "updated_at": timestamp,
            }
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
        self._assert_tenant(tenant_id)
        self._assert_version(expected_version)

        target = DealStatus(target)

        if target == self.status:
            raise DealTransitionError(
                "Deal cannot transition to its current status."
            )

        allowed = set(
            _NOMINAL_TRANSITIONS.get(
                self.status,
                frozenset(),
            )
        )

        if target == DealStatus.CANCELLED and self.status in _NON_TERMINAL_STATES:
            allowed.add(target)

        if target == DealStatus.EXPIRED and self.status in _PRE_BOOKING_EXPIRY_STATES:
            allowed.add(target)

        if target == DealStatus.REJECTED and self.status in _REJECTION_STATES:
            allowed.add(target)

        if target == DealStatus.FRAUD_BLOCKED and self.status in _NON_TERMINAL_STATES:
            allowed.add(target)

        if target == DealStatus.DISPUTED and self.status in _DISPUTE_STATES:
            allowed.add(target)

        if target not in allowed:
            raise DealTransitionError(
                f"Invalid Deal transition: "
                f"{self.status.value} -> {target.value}."
            )

        if target in {
            DealStatus.MATCHED,
            DealStatus.VISIT_PENDING,
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
            DealStatus.BOOKING_PENDING,
            DealStatus.BOOKED,
            DealStatus.AGREEMENT_PENDING,
            DealStatus.AGREED,
            DealStatus.REGISTRATION_PENDING,
            DealStatus.REGISTERED,
            DealStatus.COMPLETION_PENDING,
            DealStatus.COMPLETED,
        } and not self.opportunity_bound:
            raise DealTransitionError(
                f"{target.value} requires a fully bound "
                "builder/project/unit opportunity."
            )

        timestamp = _coerce_datetime(at)

        history_entry = DealHistoryEntry(
            history_id=str(uuid4()),
            from_status=self.status,
            to_status=target,
            version=self.version + 1,
            changed_at=timestamp,
            reason=reason,
        )

        return Deal(
            **{
                **self.__dict__,
                "status": target,
                "version": self.version + 1,
                "updated_at": timestamp,
                "history": self.history + (history_entry,),
            }
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
                entry.to_dict()
                for entry in self.history
            ],
            "source_of_truth": self.source_of_truth,
            "offers": [offer.to_dict() for offer in self.offers],
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
            "milestones": [
                milestone.to_dict()
                for milestone in self.milestones
            ],
            "negotiation": (
                self.negotiation.to_dict()
                if self.negotiation is not None
                else None
            ),
        }


__all__ = [
    "Deal",    "DealOffer",
    "DealOfferStatus",
    "DealNegotiation",
    "DealNegotiationStatus",
    "DealStatus",
    "DealHistoryEntry",
    "DealDomainError",
    "DealTransitionError",
    "DealTenantError",
    "DealConcurrencyError",
    "DealReferenceConflictError",
    "DealValidationError",
]










