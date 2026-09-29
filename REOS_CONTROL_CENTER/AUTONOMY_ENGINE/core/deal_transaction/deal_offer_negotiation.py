from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DealOfferError(ValueError):
    pass


class DealOfferTransitionError(DealOfferError):
    pass


class DealOfferTenantError(DealOfferError):
    pass


class DealOfferConcurrencyError(DealOfferError):
    pass


class DealNegotiationError(ValueError):
    pass


class DealNegotiationTransitionError(DealNegotiationError):
    pass


class DealNegotiationTenantError(DealNegotiationError):
    pass


class DealNegotiationConcurrencyError(DealNegotiationError):
    pass


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


_OFFER_TRANSITIONS = {
    DealOfferStatus.DRAFT: frozenset({
        DealOfferStatus.SUBMITTED,
        DealOfferStatus.WITHDRAWN,
        DealOfferStatus.EXPIRED,
    }),
    DealOfferStatus.SUBMITTED: frozenset({
        DealOfferStatus.ACCEPTED,
        DealOfferStatus.REJECTED,
        DealOfferStatus.WITHDRAWN,
        DealOfferStatus.EXPIRED,
    }),
    DealOfferStatus.ACCEPTED: frozenset(),
    DealOfferStatus.REJECTED: frozenset(),
    DealOfferStatus.WITHDRAWN: frozenset(),
    DealOfferStatus.EXPIRED: frozenset(),
}


_NEGOTIATION_TRANSITIONS = {
    DealNegotiationStatus.OPEN: frozenset({
        DealNegotiationStatus.PAUSED,
        DealNegotiationStatus.CONCLUDED,
        DealNegotiationStatus.ABORTED,
    }),
    DealNegotiationStatus.PAUSED: frozenset({
        DealNegotiationStatus.OPEN,
        DealNegotiationStatus.CONCLUDED,
        DealNegotiationStatus.ABORTED,
    }),
    DealNegotiationStatus.CONCLUDED: frozenset(),
    DealNegotiationStatus.ABORTED: frozenset(),
}


def _validate_version(value: int, label: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise ValueError(
            f"{label} must be an integer >= 1."
        )


def _validate_timestamp(
    value: datetime,
    label: str,
) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
    ):
        raise ValueError(
            f"{label} must be timezone-aware."
        )


@dataclass(frozen=True)
class DealOffer:
    offer_id: str
    deal_id: str
    tenant_id: str
    status: DealOfferStatus
    version: int
    created_at: datetime
    updated_at: datetime
    supersedes_offer_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "offer_id",
            "deal_id",
            "tenant_id",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise DealOfferError(
                    f"{name} is required."
                )

        _validate_version(self.version, "version")
        _validate_timestamp(
            self.created_at,
            "created_at",
        )
        _validate_timestamp(
            self.updated_at,
            "updated_at",
        )

        object.__setattr__(
            self,
            "status",
            DealOfferStatus(self.status),
        )

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
        _validate_timestamp(timestamp, "at")

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

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
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

        if target not in _OFFER_TRANSITIONS[self.status]:
            raise DealOfferTransitionError(
                f"Invalid offer transition: "
                f"{self.status.value} -> {target.value}."
            )

        timestamp = at or _utc_now()
        _validate_timestamp(timestamp, "at")

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
        for name in (
            "negotiation_id",
            "deal_id",
            "tenant_id",
            "active_offer_id",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise DealNegotiationError(
                    f"{name} is required."
                )

        _validate_version(self.version, "version")

        if (
            isinstance(self.round_number, bool)
            or not isinstance(
                self.round_number,
                int,
            )
            or self.round_number < 1
        ):
            raise DealNegotiationError(
                "round_number must be an integer >= 1."
            )

        _validate_timestamp(
            self.created_at,
            "created_at",
        )
        _validate_timestamp(
            self.updated_at,
            "updated_at",
        )

        object.__setattr__(
            self,
            "status",
            DealNegotiationStatus(self.status),
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

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
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
                f"Expected negotiation version "
                f"{self.version}, received "
                f"{expected_version}."
            )

        target = DealNegotiationStatus(target)

        if target not in _NEGOTIATION_TRANSITIONS[
            self.status
        ]:
            raise DealNegotiationTransitionError(
                f"Invalid negotiation transition: "
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
                f"Expected negotiation version "
                f"{self.version}, received "
                f"{expected_version}."
            )

        if self.status not in (
            DealNegotiationStatus.OPEN,
            DealNegotiationStatus.PAUSED,
        ):
            raise DealNegotiationTransitionError(
                "Cannot advance a closed negotiation."
            )

        if (
            not isinstance(active_offer_id, str)
            or not active_offer_id.strip()
        ):
            raise DealNegotiationError(
                "active_offer_id is required."
            )

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
