from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class DealOwnershipError(ValueError):
    """Base ownership integration error."""


class DealOwnershipValidationError(DealOwnershipError):
    """Invalid ownership binding data."""


class DealOwnershipTenantError(DealOwnershipError):
    """Ownership binding crosses tenant boundary."""


@dataclass(frozen=True)
class DealOwnershipBinding:
    """Immutable reference from Deal to the authoritative ownership engine."""

    binding_id: str
    deal_id: str
    tenant_id: str
    lead_id: str
    ownership_record_id: str
    owner_id: str
    bound_at: datetime
    authority: str = "ARCH-011"

    def __post_init__(self) -> None:
        for field_name in (
            "binding_id",
            "deal_id",
            "tenant_id",
            "lead_id",
            "ownership_record_id",
            "owner_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise DealOwnershipValidationError(
                    f"{field_name} is required."
                )

        if self.authority != "ARCH-011":
            raise DealOwnershipValidationError(
                "Deal ownership authority must remain ARCH-011."
            )

        if self.bound_at.tzinfo is None:
            raise DealOwnershipValidationError(
                "bound_at must be timezone-aware."
            )

    @property
    def reference_key(self) -> str:
        return f"{self.tenant_id}:{self.deal_id}:{self.ownership_record_id}"

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise DealOwnershipTenantError(
                "Ownership binding belongs to a different tenant."
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
            "reference_key": self.reference_key,
        }


__all__ = [
    "DealOwnershipBinding",
    "DealOwnershipError",
    "DealOwnershipTenantError",
    "DealOwnershipValidationError",
]
