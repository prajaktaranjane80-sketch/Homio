from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DealOfferNegotiationError(ValueError):
    pass


class DealOfferStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class DealNegotiationStatus(str, Enum):
    OPEN = "OPEN"
    AGREED = "AGREED"
    CLOSED = "CLOSED"


def _ts(value: datetime | str | None) -> datetime:
    if value is None:
        value = datetime.now(timezone.utc)
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DealOfferNegotiationError(
                "Invalid ISO-8601 timestamp."
            ) from exc

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _id(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DealOfferNegotiationError(f"{name} is required.")
    return value.strip()


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

    @classmethod
    def create(
        cls,
        *,
        offer_id: str,
        deal_id: str,
        tenant_id: str,
        at: datetime | str | None = None,
        supersedes_offer_id: str | None = None,
    ) -> "DealOffer":
        stamp = _ts(at)

        return cls(
            _id(offer_id, "offer_id"),
            _id(deal_id, "deal_id"),
            _id(tenant_id, "tenant_id"),
            DealOfferStatus.DRAFT,
            1,
            stamp,
            stamp,
            supersedes_offer_id,
        )

    def transition(
        self,
        target: DealOfferStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
    ) -> "DealOffer":
        if tenant_id != self.tenant_id:
            raise DealOfferNegotiationError(
                "Offer belongs to a different tenant."
            )

        if expected_version != self.version:
            raise DealOfferNegotiationError(
                "Stale offer version."
            )

        target = DealOfferStatus(target)

        allowed = {
            DealOfferStatus.DRAFT: {
                DealOfferStatus.SUBMITTED,
                DealOfferStatus.WITHDRAWN,
            },
            DealOfferStatus.SUBMITTED: {
                DealOfferStatus.ACCEPTED,
                DealOfferStatus.REJECTED,
                DealOfferStatus.WITHDRAWN,
            },
            DealOfferStatus.ACCEPTED: set(),
            DealOfferStatus.REJECTED: set(),
            DealOfferStatus.WITHDRAWN: set(),
        }

        if target == self.status:
            return self

        if target not in allowed[self.status]:
            raise DealOfferNegotiationError(
                f"Invalid offer transition: "
                f"{self.status.value} -> {target.value}."
            )

        stamp = _ts(at)

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=stamp,
        )

    def to_dict(self) -> dict[str, Any]:
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
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        negotiation_id: str,
        deal_id: str,
        tenant_id: str,
        active_offer_id: str,
        at: datetime | str | None = None,
    ) -> "DealNegotiation":
        stamp = _ts(at)

        return cls(
            _id(negotiation_id, "negotiation_id"),
            _id(deal_id, "deal_id"),
            _id(tenant_id, "tenant_id"),
            _id(active_offer_id, "active_offer_id"),
            DealNegotiationStatus.OPEN,
            1,
            stamp,
            stamp,
        )

    def transition(
        self,
        target: DealNegotiationStatus | str,
        *,
        tenant_id: str,
        expected_version: int,
        at: datetime | str | None = None,
    ) -> "DealNegotiation":
        if tenant_id != self.tenant_id:
            raise DealOfferNegotiationError(
                "Negotiation belongs to a different tenant."
            )

        if expected_version != self.version:
            raise DealOfferNegotiationError(
                "Stale negotiation version."
            )

        target = DealNegotiationStatus(target)

        allowed = {
            DealNegotiationStatus.OPEN: {
                DealNegotiationStatus.AGREED,
                DealNegotiationStatus.CLOSED,
            },
            DealNegotiationStatus.AGREED: {
                DealNegotiationStatus.CLOSED,
            },
            DealNegotiationStatus.CLOSED: set(),
        }

        if target == self.status:
            return self

        if target not in allowed[self.status]:
            raise DealOfferNegotiationError(
                f"Invalid negotiation transition: "
                f"{self.status.value} -> {target.value}."
            )

        stamp = _ts(at)

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=stamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "active_offer_id": self.active_offer_id,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


__all__ = [
    "DealOfferNegotiationError",
    "DealOfferStatus",
    "DealOffer",
    "DealNegotiationStatus",
    "DealNegotiation",
]
