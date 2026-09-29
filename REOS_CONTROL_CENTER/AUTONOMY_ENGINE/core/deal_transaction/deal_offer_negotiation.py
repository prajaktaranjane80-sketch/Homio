from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from .deal_contract import utc_datetime


class DealOfferStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    COUNTERED = "COUNTERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class DealNegotiationStatus(str, Enum):
    OPEN = "OPEN"
    AGREED = "AGREED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class DealOffer:
    offer_id: str
    deal_id: str
    tenant_id: str
    status: DealOfferStatus
    version: int
    created_at: str
    updated_at: str
    terms: Mapping[str, Any] = field(default_factory=dict)
    supersedes_offer_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "offer_id",
            "deal_id",
            "tenant_id",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{name} is required."
                )

        if self.version < 1:
            raise ValueError(
                "offer version must be >= 1."
            )

        object.__setattr__(
            self,
            "status",
            DealOfferStatus(self.status),
        )

        object.__setattr__(
            self,
            "terms",
            dict(self.terms),
        )

    @classmethod
    def create(
        cls,
        *,
        offer_id: str | None,
        deal_id: str,
        tenant_id: str,
        at: Any = None,
        terms: Mapping[str, Any] | None = None,
        supersedes_offer_id: str | None = None,
    ) -> "DealOffer":
        timestamp = utc_datetime(at).isoformat()

        return cls(
            offer_id=offer_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            status=DealOfferStatus.DRAFT,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
            terms=dict(terms or {}),
            supersedes_offer_id=supersedes_offer_id,
        )

    def assert_scope(
        self,
        *,
        deal_id: str,
        tenant_id: str,
    ) -> None:
        if (
            self.deal_id != deal_id
            or self.tenant_id != tenant_id
        ):
            raise ValueError(
                "Offer crosses Deal or tenant scope."
            )

    def transition(
        self,
        target: DealOfferStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
        terms: Mapping[str, Any] | None = None,
    ) -> "DealOffer":
        self.assert_scope(
            deal_id=self.deal_id,
            tenant_id=tenant_id,
        )

        if expected_version != self.version:
            raise ValueError(
                "Stale offer version."
            )

        target = DealOfferStatus(target)

        allowed = {
            DealOfferStatus.DRAFT: {
                DealOfferStatus.SUBMITTED,
                DealOfferStatus.WITHDRAWN,
            },
            DealOfferStatus.SUBMITTED: {
                DealOfferStatus.COUNTERED,
                DealOfferStatus.ACCEPTED,
                DealOfferStatus.REJECTED,
                DealOfferStatus.WITHDRAWN,
                DealOfferStatus.EXPIRED,
            },
            DealOfferStatus.COUNTERED: {
                DealOfferStatus.ACCEPTED,
                DealOfferStatus.REJECTED,
                DealOfferStatus.WITHDRAWN,
                DealOfferStatus.EXPIRED,
            },
        }

        if target not in allowed.get(self.status, set()):
            raise ValueError(
                f"Invalid offer transition: "
                f"{self.status.value} -> "
                f"{target.value}"
            )

        timestamp = utc_datetime(at).isoformat()

        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=timestamp,
            terms=(
                dict(self.terms)
                if terms is None
                else dict(terms)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "terms": dict(self.terms),
            "supersedes_offer_id": self.supersedes_offer_id,
        }


@dataclass(frozen=True)
class DealNegotiation:
    negotiation_id: str
    deal_id: str
    tenant_id: str
    status: DealNegotiationStatus
    version: int
    active_offer_id: str
    history_offer_ids: tuple[str, ...]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError(
                "negotiation version must be >= 1."
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
        negotiation_id: str | None,
        deal_id: str,
        tenant_id: str,
        active_offer_id: str,
        at: Any = None,
    ) -> "DealNegotiation":
        timestamp = utc_datetime(at).isoformat()

        return cls(
            negotiation_id=(
                negotiation_id or str(uuid4())
            ),
            deal_id=deal_id,
            tenant_id=tenant_id,
            status=DealNegotiationStatus.OPEN,
            version=1,
            active_offer_id=active_offer_id,
            history_offer_ids=(active_offer_id,),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        target: DealNegotiationStatus,
        *,
        tenant_id: str,
        expected_version: int,
        at: Any = None,
        active_offer_id: str | None = None,
    ) -> "DealNegotiation":
        if tenant_id != self.tenant_id:
            raise ValueError(
                "Negotiation crosses tenant scope."
            )

        if expected_version != self.version:
            raise ValueError(
                "Stale negotiation version."
            )

        target = DealNegotiationStatus(target)

        allowed = {
            DealNegotiationStatus.OPEN: {
                DealNegotiationStatus.AGREED,
                DealNegotiationStatus.REJECTED,
                DealNegotiationStatus.CLOSED,
            },
            DealNegotiationStatus.AGREED: {
                DealNegotiationStatus.CLOSED,
            },
            DealNegotiationStatus.REJECTED: set(),
            DealNegotiationStatus.CLOSED: set(),
        }

        if target not in allowed[self.status]:
            raise ValueError(
                f"Invalid negotiation transition: "
                f"{self.status.value} -> "
                f"{target.value}"
            )

        timestamp = utc_datetime(at).isoformat()

        new_offer_id = (
            active_offer_id
            or self.active_offer_id
        )

        history = self.history_offer_ids

        if new_offer_id not in history:
            history = history + (new_offer_id,)

        return replace(
            self,
            status=target,
            version=self.version + 1,
            active_offer_id=new_offer_id,
            history_offer_ids=history,
            updated_at=timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "version": self.version,
            "active_offer_id": self.active_offer_id,
            "history_offer_ids": list(
                self.history_offer_ids
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
