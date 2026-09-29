from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DealPartyRole(str, Enum):
    BUYER = "BUYER"
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    BUILDER = "BUILDER"
    BROKER = "BROKER"
    REPRESENTATIVE = "REPRESENTATIVE"


class DealPartyLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REMOVED = "REMOVED"


@dataclass(frozen=True)
class DealPartyRelationship:
    deal_id: str
    tenant_id: str
    role: DealPartyRole
    party_id: str
    relationship_version: int = 1
    lifecycle: DealPartyLifecycle = DealPartyLifecycle.ACTIVE
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "party_id",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{name} must be a non-empty string."
                )

        if self.relationship_version < 1:
            raise ValueError(
                "relationship_version must be >= 1."
            )

        object.__setattr__(
            self,
            "role",
            DealPartyRole(self.role),
        )

        object.__setattr__(
            self,
            "lifecycle",
            DealPartyLifecycle(self.lifecycle),
        )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata or {}),
        )

    @property
    def relationship_key(self) -> str:
        return (
            f"{self.tenant_id}:"
            f"{self.deal_id}:"
            f"{self.role.value}:"
            f"{self.party_id}"
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
                "Party relationship crosses Deal scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "role": self.role.value,
            "party_id": self.party_id,
            "relationship_version": self.relationship_version,
            "lifecycle": self.lifecycle.value,
            "relationship_key": self.relationship_key,
            "metadata": dict(self.metadata or {}),
        }
