from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

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


@dataclass(frozen=True)
class DealPartyRelationship:
    deal_id: str
    tenant_id: str
    role: DealPartyRole
    party_id: str

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "party_id",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise DealValidationError(
                    f"{name} is required."
                )

        object.__setattr__(
            self,
            "role",
            DealPartyRole(self.role),
        )

    @property
    def relationship_key(self) -> str:
        return (
            f"{self.tenant_id}:"
            f"{self.deal_id}:"
            f"{self.role.value}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_key": self.relationship_key,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "role": self.role.value,
            "party_id": self.party_id,
        }


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


_NOMINAL: dict[
    DealStatus,
    frozenset[DealStatus],
] = {
    DealStatus.QUALIFIED: frozenset({
        DealStatus.MATCHED,
    }),
    DealStatus.MATCHED: frozenset({
        DealStatus.VISIT_PENDING,
    }),
    DealStatus.VISIT_PENDING: frozenset({
        DealStatus.VISITED,
    }),
    DealStatus.VISITED: frozenset({
        DealStatus.OFFERED,
    }),
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


_PRE_BOOKING_EXPIRY = frozenset({
    DealStatus.QUALIFIED,
    DealStatus.MATCHED,
    DealStatus.VISIT_PENDING,
    DealStatus.VISITED,
    DealStatus.OFFERED,
    DealStatus.NEGOTIATING,
    DealStatus.BOOKING_PENDING,
    DealStatus.AGREEMENT_PENDING,
})

_REJECTION_STATES = _PRE_BOOKING_EXPIRY

_DISPUTE_STATES = frozenset({
    DealStatus.BOOKED,
    DealStatus.AGREEMENT_PENDING,
    DealStatus.AGREED,
    DealStatus.REGISTRATION_PENDING,
    DealStatus.REGISTERED,
    DealStatus.COMPLETION_PENDING,
})

_NON_TERMINAL = (
    frozenset(_NOMINAL)
    - {
        DealStatus.COMPLETED,
        DealStatus.CANCELLED,
        DealStatus.EXPIRED,
        DealStatus.REJECTED,
        DealStatus.DISPUTED,
        DealStatus.FRAUD_BLOCKED,
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_id(
    value: str,
    name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealValidationError(
            f"{name} must be a non-empty string."
        )
    return value.strip()


def _dt(
    value: datetime | str | None,
) -> datetime:
    if value is None:
        value = _utc_now()
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise DealValidationError(
                "Invalid ISO-8601 timestamp."
            ) from exc

    if not isinstance(value, datetime):
        raise DealValidationError(
            "Timestamp must be datetime, string, or None."
        )

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Deal:
    """
    Canonical CORE-006 Deal aggregate.

    Deal is the single authoritative owner of:
    - Deal identity
    - lifecycle state
    - aggregate version
    - parties
    - opportunity binding
    - offer/negotiation state
    - transaction milestones
    - ownership reference
    - evidence references
    - Deal-local audit references
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

    offers: tuple[DealOffer, ...] = (
        field(default_factory=tuple)
    )
    negotiation: DealNegotiation | None = None

    milestones: tuple[
        DealTransactionMilestone,
        ...,
    ] = field(default_factory=tuple)

    ownership_binding: (
        DealOwnershipBinding | None
    ) = None

    evidence: tuple[Any, ...] = field(
        default_factory=tuple
    )

    audit_log: tuple[Any, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "customer_id",
            "broker_id",
        ):
            object.__setattr__(
                self,
                name,
                _require_id(
                    getattr(self, name),
                    name,
                ),
            )

        for name in (
            "builder_id",
            "project_id",
            "unit_id",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _require_id(value, name),
                )

        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
            or self.version < 1
        ):
            raise DealValidationError(
                "version must be an integer >= 1."
            )

        object.__setattr__(
            self,
            "status",
            DealStatus(self.status),
        )

        object.__setattr__(
            self,
            "source_of_truth",
            _require_id(
                self.source_of_truth,
                "source_of_truth",
            ),
        )

        if self.source_of_truth != "deal":
            raise DealValidationError(
                "Deal source_of_truth must remain 'deal'."
            )

        if (
            self.created_at.tzinfo is None
            or self.updated_at.tzinfo is None
        ):
            raise DealValidationError(
                "Deal timestamps must be timezone-aware."
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
        timestamp = _dt(at)

        deal = cls(
            deal_id=deal_id or str(uuid4()),
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
            history=(),
        )

        return replace(
            deal,
            history=(
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=None,
                    to_status=(
                        DealStatus.QUALIFIED
                    ),
                    version=1,
                    changed_at=timestamp,
                    reason="DEAL_CREATED",
                ),
            ),
        )

    @property
    def identity_key(self) -> str:
        return (
            f"{self.tenant_id}:"
            f"{self.deal_id}"
        )

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
    def party_relationships(
        self,
    ) -> tuple[
        DealPartyRelationship,
        ...,
    ]:
        items = [
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
        ]

        return tuple(
            DealPartyRelationship(
                self.deal_id,
                self.tenant_id,
                role,
                party_id,
            )
            for role, party_id in items
            if party_id is not None
        )

    def party_for(
        self,
        role: DealPartyRole,
    ) -> str | None:
        role = DealPartyRole(role)

        for item in self.party_relationships:
            if item.role is role:
                return item.party_id

        return None

    @property
    def current_offer(
        self,
    ) -> DealOffer | None:
        return (
            self.offers[-1]
            if self.offers
            else None
        )

    @property
    def is_terminal(self) -> bool:
        return (
            self.status
            not in _NON_TERMINAL
        )

    def _tenant(
        self,
        tenant_id: str,
    ) -> None:
        if tenant_id != self.tenant_id:
            raise DealTenantError(
                "Deal operation belongs "
                "to a different tenant."
            )

    def _version(
        self,
        expected_version: int | None,
    ) -> None:
        if expected_version is None:
            return

        if (
            isinstance(expected_version, bool)
            or not isinstance(
                expected_version,
                int,
            )
            or expected_version < 1
        ):
            raise DealConcurrencyError(
                "expected_version must be "
                "an integer >= 1."
            )

        if expected_version != self.version:
            raise DealConcurrencyError(
                f"Deal version is stale; "
                f"expected {expected_version}, "
                f"current {self.version}."
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

        values = tuple(
            _require_id(value, name)
            for value, name in (
                (builder_id, "builder_id"),
                (project_id, "project_id"),
                (unit_id, "unit_id"),
            )
        )

        if self.opportunity_bound:
            if (
                self.builder_id,
                self.project_id,
                self.unit_id,
            ) == values:
                return self

            raise DealReferenceConflictError(
                "Deal opportunity binding already exists."
            )

        timestamp = _dt(at)

        return replace(
            self,
            builder_id=values[0],
            project_id=values[1],
            unit_id=values[2],
            version=self.version + 1,
            updated_at=timestamp,
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

        if target == self.status:
            raise DealTransitionError(
                "Deal cannot transition "
                "to its current status."
            )

        allowed = set(
            _NOMINAL[self.status]
        )

        if (
            target == DealStatus.CANCELLED
            and self.status
            in _NON_TERMINAL
        ):
            allowed.add(target)

        if (
            target == DealStatus.EXPIRED
            and self.status
            in _PRE_BOOKING_EXPIRY
        ):
            allowed.add(target)

        if (
            target == DealStatus.REJECTED
            and self.status
            in _REJECTION_STATES
        ):
            allowed.add(target)

        if (
            target
            == DealStatus.FRAUD_BLOCKED
            and self.status
            in _NON_TERMINAL
        ):
            allowed.add(target)

        if (
            target == DealStatus.DISPUTED
            and self.status
            in _DISPUTE_STATES
        ):
            allowed.add(target)

        if target not in allowed:
            raise DealTransitionError(
                "Invalid Deal transition: "
                f"{self.status.value} -> "
                f"{target.value}."
            )

        if (
            target
            in (
                _NON_TERMINAL
                | {
                    DealStatus.COMPLETED
                }
            )
            and not self.opportunity_bound
        ):
            raise DealTransitionError(
                f"{target.value} requires a "
                "fully bound "
                "builder/project/unit "
                "opportunity."
            )

        timestamp = _dt(at)

        entry = DealHistoryEntry(
            history_id=str(uuid4()),
            from_status=self.status,
            to_status=target,
            version=self.version + 1,
            changed_at=timestamp,
            reason=reason,
        )

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=timestamp,
            history=(
                self.history
                + (entry,)
            ),
        )

    def create_offer(
        self,
        offer_id: str,
        *,
        tenant_id: str,
        expected_version: int,
        supersedes_offer_id: str | None = None,
        at: datetime | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot create offers."
            )

        if not self.opportunity_bound:
            raise DealReferenceConflictError(
                "Offer requires a bound opportunity."
            )

        if self.status not in (
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        ):
            raise DealTransitionError(
                "Offers require VISITED, "
                "OFFERED or NEGOTIATING state."
            )

        if any(
            item.offer_id == offer_id
            for item in self.offers
        ):
            return self

        if (
            supersedes_offer_id is not None
            and not any(
                item.offer_id
                == supersedes_offer_id
                for item in self.offers
            )
        ):
            raise DealReferenceConflictError(
                "supersedes_offer_id must "
                "reference an existing offer."
            )

        timestamp = at or _utc_now()

        offer = DealOffer.create(
            offer_id=offer_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            at=timestamp,
            supersedes_offer_id=(
                supersedes_offer_id
            ),
        )

        return replace(
            self,
            offers=(
                self.offers
                + (offer,)
            ),
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
        self._tenant(tenant_id)
        self._version(expected_version)

        index = next(
            (
                i
                for i, item
                in enumerate(self.offers)
                if item.offer_id == offer_id
            ),
            None,
        )

        if index is None:
            raise DealReferenceConflictError(
                "Offer does not belong to this Deal."
            )

        offer = self.offers[index]

        if (
            offer.status
            is DealOfferStatus.SUBMITTED
        ):
            return self

        updated_offer = offer.transition(
            DealOfferStatus.SUBMITTED,
            tenant_id=tenant_id,
            expected_version=offer.version,
            at=at,
        )

        offers = list(self.offers)
        offers[index] = updated_offer

        timestamp = at or _utc_now()

        if self.status not in (
            DealStatus.VISITED,
            DealStatus.OFFERED,
            DealStatus.NEGOTIATING,
        ):
            raise DealTransitionError(
                "Offer submission requires "
                "VISITED, OFFERED or "
                "NEGOTIATING state."
            )

        target = (
            DealStatus.OFFERED
            if self.status
            is DealStatus.VISITED
            else self.status
        )

        history = self.history

        if target is not self.status:
            history += (
                DealHistoryEntry(
                    history_id=str(uuid4()),
                    from_status=self.status,
                    to_status=target,
                    version=self.version + 1,
                    changed_at=timestamp,
                    reason="OFFER_SUBMITTED",
                ),
            )

        return replace(
            self,
            status=target,
            offers=tuple(offers),
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
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.status is not DealStatus.OFFERED:
            raise DealTransitionError(
                "Negotiation can only start "
                "from OFFERED."
            )

        if self.negotiation is not None:
            if (
                self.negotiation.negotiation_id
                == negotiation_id
            ):
                return self

            raise DealReferenceConflictError(
                "Deal already has a negotiation reference."
            )

        active = (
            self.current_offer
            if offer_id is None
            else next(
                (
                    item
                    for item in self.offers
                    if item.offer_id
                    == offer_id
                ),
                None,
            )
        )

        if active is None:
            raise DealReferenceConflictError(
                "Negotiation requires "
                "an existing offer."
            )

        if (
            active.status
            is not DealOfferStatus.SUBMITTED
        ):
            raise DealTransitionError(
                "Negotiation requires "
                "a SUBMITTED offer."
            )

        timestamp = at or _utc_now()

        negotiation = DealNegotiation.create(
            negotiation_id=negotiation_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            active_offer_id=active.offer_id,
            at=timestamp,
        )

        entry = DealHistoryEntry(
            history_id=str(uuid4()),
            from_status=self.status,
            to_status=DealStatus.NEGOTIATING,
            version=self.version + 1,
            changed_at=timestamp,
            reason="NEGOTIATION_STARTED",
        )

        return replace(
            self,
            status=DealStatus.NEGOTIATING,
            negotiation=negotiation,
            version=self.version + 1,
            updated_at=timestamp,
            history=(
                self.history
                + (entry,)
            ),
        )

    def transition_negotiation(
        self,
        target: DealNegotiationStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.negotiation is None:
            raise DealReferenceConflictError(
                "Deal has no negotiation reference."
            )

        updated = (
            self.negotiation.transition(
                target,
                tenant_id=tenant_id,
                expected_version=(
                    self.negotiation.version
                ),
                at=at,
            )
        )

        timestamp = at or _utc_now()

        return replace(
            self,
            negotiation=updated,
            version=self.version + 1,
            updated_at=timestamp,
        )

    def advance_transaction_milestone(
        self,
        target: DealStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        reference_id: str | None = None,
        at: datetime | str | None = None,
        reason: str | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        target = DealStatus(target)

        milestone_targets = {
            DealStatus.BOOKING_PENDING,
            DealStatus.BOOKED,
            DealStatus.AGREEMENT_PENDING,
            DealStatus.AGREED,
            DealStatus.REGISTRATION_PENDING,
            DealStatus.REGISTERED,
            DealStatus.COMPLETION_PENDING,
            DealStatus.COMPLETED,
        }

        if target not in milestone_targets:
            raise DealTransitionError(
                f"{target.value} is not "
                "a transaction milestone target."
            )

        timestamp = _dt(at)

        updated = self.transition(
            target,
            tenant_id=tenant_id,
            expected_version=self.version,
            reason=(
                reason
                or f"TRANSACTION_MILESTONE:"
                f"{target.value}"
            ),
            at=timestamp,
        )

        milestone = (
            DealTransactionMilestone(
                milestone_id=str(uuid4()),
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
                from_status=self.status,
                to_status=target,
                sequence=(
                    len(self.milestones)
                    + 1
                ),
                deal_version=(
                    updated.version
                ),
                occurred_at=timestamp,
                reference_id=reference_id,
            )
        )

        return replace(
            updated,
            milestones=(
                self.milestones
                + (milestone,)
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
        at: datetime | None = None,
    ) -> "Deal":
        self._tenant(tenant_id)
        self._version(expected_version)

        if self.is_terminal:
            raise DealReferenceConflictError(
                "Terminal deals cannot "
                "change ownership binding."
            )

        if self.ownership_binding is not None:
            current = self.ownership_binding

            if (
                current.ownership_record_id
                == ownership_record_id
                and current.lead_id == lead_id
                and current.owner_id == owner_id
            ):
                return self

            raise DealReferenceConflictError(
                "Deal ownership binding already exists; "
                "substitution is forbidden."
            )

        timestamp = at or _utc_now()

        binding = DealOwnershipBinding(
            binding_id=binding_id,
            deal_id=self.deal_id,
            tenant_id=self.tenant_id,
            lead_id=lead_id,
            ownership_record_id=(
                ownership_record_id
            ),
            owner_id=owner_id,
            bound_at=timestamp,
        )

        return replace(
            self,
            ownership_binding=binding,
            version=self.version + 1,
            updated_at=timestamp,
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

        self._tenant(tenant_id)
        self._version(expected_version)

        candidate = (
            evidence_id,
            self.deal_id,
            tenant_id,
            evidence_type,
            reference,
            dict(metadata or {}),
        )

        for existing in self.evidence:
            if (
                existing.evidence_id
                != evidence_id
            ):
                continue

            if (
                existing.semantic_key()
                == candidate
            ):
                return self

            raise DealEvidenceConflictError(
                f"Evidence id {evidence_id!r} "
                "is already bound with different "
                "immutable data."
            )

        new_version = self.version + 1

        evidence = (
            DealEvidenceReference.create(
                evidence_id=evidence_id,
                deal_id=self.deal_id,
                tenant_id=self.tenant_id,
                evidence_type=evidence_type,
                reference=reference,
                deal_version=new_version,
                at=at,
                metadata=metadata,
            )
        )

        timestamp = _dt(at)

        return replace(
            self,
            version=new_version,
            updated_at=timestamp,
            evidence=(
                self.evidence
                + (evidence,)
            ),
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

        self._tenant(tenant_id)
        self._version(expected_version)

        for existing in self.audit_log:
            if (
                audit_id is None
                or existing.audit_id
                != audit_id
            ):
                continue

            candidate = (
                audit_id,
                self.deal_id,
                tenant_id,
                action,
                actor_id,
                outcome,
                dict(metadata or {}),
            )

            if (
                existing.semantic_key()
                == candidate
            ):
                return self

            raise DealAuditConflictError(
                f"Audit id {audit_id!r} "
                "is already recorded with "
                "different immutable data."
            )

        new_version = self.version + 1

        audit = DealAuditEntry.create(
            audit_id=audit_id,
            deal_id=self.deal_id,
            tenant_id=tenant_id,
            action=action,
            actor_id=actor_id,
            deal_version=new_version,
            outcome=outcome,
            at=at,
            metadata=metadata,
        )

        timestamp = _dt(at)

        return replace(
            self,
            version=new_version,
            updated_at=timestamp,
            audit_log=(
                self.audit_log
                + (audit,)
            ),
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
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
            "source_of_truth": (
                self.source_of_truth
            ),
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
]
