from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DealOfferError(ValueError):
    """Base error for offer state violations."""


class DealOfferTransitionError(DealOfferError):
    """Raised when an offer state transition is invalid."""


class DealOfferTenantError(DealOfferError):
    """Raised when an offer crosses its tenant boundary."""


class DealOfferConcurrencyError(DealOfferError):
    """Raised when an offer version is stale."""


class DealNegotiationError(ValueError):
    """Base error for negotiation state violations."""


class DealNegotiationTransitionError(DealNegotiationError):
    """Raised when a negotiation state transition is invalid."""


class DealNegotiationTenantError(DealNegotiationError):
    """Raised when a negotiation crosses its tenant boundary."""


class DealNegotiationConcurrencyError(DealNegotiationError):
    """Raised when a negotiation version is stale."""


class DealOfferStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class DealNegotiationStatus(str, Enum):
    OPEN = "OPEN"
    PAUSED = "PAUSED"
    CONCLUDED = "CONCLUDED"
    ABORTED = "ABORTED"


_ALLOWED_OFFER_TRANSITIONS: dict[
    DealOfferStatus, frozenset[DealOfferStatus]
] = {
    DealOfferStatus.DRAFT: frozenset(
        {
            DealOfferStatus.SUBMITTED,
            DealOfferStatus.WITHDRAWN,
            DealOfferStatus.EXPIRED,
        }
    ),
    DealOfferStatus.SUBMITTED: frozenset(
        {
            DealOfferStatus.ACCEPTED,
            DealOfferStatus.REJECTED,
            DealOfferStatus.WITHDRAWN,
            DealOfferStatus.EXPIRED,
        }
    ),
    DealOfferStatus.ACCEPTED: frozenset(),
    DealOfferStatus.REJECTED: frozenset(),
    DealOfferStatus.WITHDRAWN: frozenset(),
    DealOfferStatus.EXPIRED: frozenset(),
}


_ALLOWED_NEGOTIATION_TRANSITIONS: dict[
    DealNegotiationStatus, frozenset[DealNegotiationStatus]
] = {
    DealNegotiationStatus.OPEN: frozenset(
        {
            DealNegotiationStatus.PAUSED,
            DealNegotiationStatus.CONCLUDED,
            DealNegotiationStatus.ABORTED,
        }
    ),
    DealNegotiationStatus.PAUSED: frozenset(
        {
            DealNegotiationStatus.OPEN,
            DealNegotiationStatus.CONCLUDED,
            DealNegotiationStatus.ABORTED,
        }
    ),
    DealNegotiationStatus.CONCLUDED: frozenset(),
    DealNegotiationStatus.ABORTED: frozenset(),
}


@dataclass(frozen=True)
class DealOffer:
    """Immutable offer state owned by the Deal aggregate."""

    offer_id: str
    deal_id: str
    tenant_id: str
    status: DealOfferStatus
    version: int
    created_at: datetime
    updated_at: datetime
    supersedes_offer_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("offer_id", "deal_id", "tenant_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise DealOfferError(f"{field_name} is required.")

        if self.version < 1:
            raise DealOfferError("version must be >= 1.")

        object.__setattr__(self, "status", DealOfferStatus(self.status))

        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise DealOfferError("Offer timestamps must be timezone-aware.")

    @classmethod
    def create(
        cls,
        *,
        offer_id: str,
        deal_id: str,
        tenant_id: str,
        at: datetime | None = None,
        supersedes_offer_id: str | None = None,
    ) -> "DealOffer":
        timestamp = at or _utc_now()

        return cls(
            offer_id=offer_id,
            deal_id=deal_id,
            tenant_id=tenant_id,
            status=DealOfferStatus.DRAFT,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
            supersedes_offer_id=supersedes_offer_id,
        )

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise DealOfferTenantError(
                "Offer belongs to a different tenant."
            )

    def transition(
        self,
        target: DealOfferStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | None = None,
    ) -> "DealOffer":
        self.assert_tenant(tenant_id)

        if expected_version != self.version:
            raise DealOfferConcurrencyError(
                f"Expected offer version {self.version}, "
                f"received {expected_version}."
            )

        target = DealOfferStatus(target)

        if target not in _ALLOWED_OFFER_TRANSITIONS[self.status]:
            raise DealOfferTransitionError(
                "Invalid offer transition: "
                f"{self.status.value} -> {target.value}."
            )

        timestamp = at or _utc_now()

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=timestamp,
        )

    def to_dict(self) -> dict:
        return {
            "offer_id": self.offer_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "supersedes_offer_id": self.supersedes_offer_id,
        }


@dataclass(frozen=True)
class DealNegotiation:
    """Immutable negotiation state owned by the Deal aggregate."""

    negotiation_id: str
    deal_id: str
    tenant_id: str
    active_offer_id: str
    status: DealNegotiationStatus
    version: int
    round_number: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "negotiation_id",
            "deal_id",
            "tenant_id",
            "active_offer_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise DealNegotiationError(f"{field_name} is required.")

        if self.version < 1:
            raise DealNegotiationError("version must be >= 1.")

        if self.round_number < 1:
            raise DealNegotiationError("round_number must be >= 1.")

        object.__setattr__(
            self,
            "status",
            DealNegotiationStatus(self.status),
        )

        if (
            self.created_at.tzinfo is None
            or self.updated_at.tzinfo is None
        ):
            raise DealNegotiationError(
                "Negotiation timestamps must be timezone-aware."
            )

    @classmethod
    def create(
        cls,
        *,
        negotiation_id: str,
        deal_id: str,
        tenant_id: str,
        active_offer_id: str,
        at: datetime | None = None,
    ) -> "DealNegotiation":
        timestamp = at or _utc_now()

        return cls(
            negotiation_id=negotiation_id,
            deal_id=deal_id,
            tenant_id=tenant_id,
            active_offer_id=active_offer_id,
            status=DealNegotiationStatus.OPEN,
            version=1,
            round_number=1,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise DealNegotiationTenantError(
                "Negotiation belongs to a different tenant."
            )

    def transition(
        self,
        target: DealNegotiationStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | None = None,
    ) -> "DealNegotiation":
        self.assert_tenant(tenant_id)

        if expected_version != self.version:
            raise DealNegotiationConcurrencyError(
                f"Expected negotiation version {self.version}, "
                f"received {expected_version}."
            )

        target = DealNegotiationStatus(target)

        if target not in _ALLOWED_NEGOTIATION_TRANSITIONS[self.status]:
            raise DealNegotiationTransitionError(
                "Invalid negotiation transition: "
                f"{self.status.value} -> {target.value}."
            )

        timestamp = at or _utc_now()

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=timestamp,
        )

    def advance_round(
        self,
        *,
        tenant_id: str,
        expected_version: int,
        active_offer_id: str,
        at: datetime | None = None,
    ) -> "DealNegotiation":
        self.assert_tenant(tenant_id)

        if expected_version != self.version:
            raise DealNegotiationConcurrencyError(
                f"Expected negotiation version {self.version}, "
                f"received {expected_version}."
            )

        if self.status not in (
            DealNegotiationStatus.OPEN,
            DealNegotiationStatus.PAUSED,
        ):
            raise DealNegotiationTransitionError(
                "Cannot advance a closed negotiation."
            )

        if not isinstance(active_offer_id, str) or not active_offer_id.strip():
            raise DealNegotiationError("active_offer_id is required.")

        timestamp = at or _utc_now()

        return replace(
            self,
            active_offer_id=active_offer_id,
            round_number=self.round_number + 1,
            version=self.version + 1,
            updated_at=timestamp,
        )

    def to_dict(self) -> dict:
        return {
            "negotiation_id": self.negotiation_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "active_offer_id": self.active_offer_id,
            "status": self.status.value,
            "version": self.version,
            "round_number": self.round_number,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


__all__ = [
    "DealOffer",
    "DealOfferConcurrencyError",
    "DealOfferError",
    "DealOfferStatus",
    "DealOfferTenantError",
    "DealOfferTransitionError",
    "DealNegotiation",
    "DealNegotiationConcurrencyError",
    "DealNegotiationError",
    "DealNegotiationStatus",
    "DealNegotiationTenantError",
    "DealNegotiationTransitionError",
]
