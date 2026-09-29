from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class DealOwnershipError(ValueError):
    pass


class DealOwnershipConflictError(DealOwnershipError):
    pass


class DealOwnershipTenantError(DealOwnershipError):
    pass


@dataclass(frozen=True)
class DealOwnershipBinding:
    binding_id: str
    deal_id: str
    tenant_id: str
    lead_id: str
    ownership_record_id: str
    owner_id: str
    bound_at: datetime
    authority: str = "ARCH-011"
    authority_version: str = "1.0"

    def __post_init__(self) -> None:
        for name in (
            "binding_id",
            "deal_id",
            "tenant_id",
            "lead_id",
            "ownership_record_id",
            "owner_id",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise DealOwnershipError(
                    f"{name} is required."
                )

        if self.authority != "ARCH-011":
            raise DealOwnershipError(
                "Ownership authority must remain ARCH-011."
            )

        if self.bound_at.tzinfo is None:
            raise DealOwnershipError(
                "bound_at must be timezone-aware."
            )

    @property
    def reference_key(self) -> str:
        return (
            f"{self.tenant_id}:"
            f"{self.deal_id}:"
            f"{self.ownership_record_id}"
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
            raise DealOwnershipTenantError(
                "Ownership binding crosses Deal scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "lead_id": self.lead_id,
            "ownership_record_id": self.ownership_record_id,
            "owner_id": self.owner_id,
            "bound_at": self.bound_at.isoformat(),
            "authority": self.authority,
            "authority_version": self.authority_version,
            "reference_key": self.reference_key,
        }
