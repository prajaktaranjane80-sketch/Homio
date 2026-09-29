from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class DealExternalAuthority(str, Enum):
    IDENTITY = "CORE-001"
    EVENT_PLATFORM = "CORE-002"
    LEAD_OWNERSHIP = "CORE-003"
    INVENTORY = "CORE-004"
    SEARCH = "CORE-005"

    OWNERSHIP_ENGINE = "ARCH-011"
    EVIDENCE = "ARCH-014"
    GOVERNANCE = "ARCH-017"
    POLICY = "ARCH-018"

    FRAUD = "CORE-007"
    COMMISSION = "CORE-008"
    AI = "AI"


class DealExternalContractError(ValueError):
    pass


@dataclass(frozen=True)
class DealExternalReference:
    deal_id: str
    tenant_id: str
    authority: DealExternalAuthority
    reference_id: str
    reference_type: str
    authority_version: str
    created_at: str
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        for name in (
            "deal_id",
            "tenant_id",
            "reference_id",
            "reference_type",
            "authority_version",
            "created_at",
        ):
            value = getattr(self, name)

            if not isinstance(value, str) or not value.strip():
                raise DealExternalContractError(
                    f"{name} is required."
                )

        object.__setattr__(
            self,
            "authority",
            DealExternalAuthority(self.authority),
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
            raise DealExternalContractError(
                "External reference crosses Deal scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "authority": self.authority.value,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "authority_version": self.authority_version,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "DealExternalAuthority",
    "DealExternalContractError",
    "DealExternalReference",
]
