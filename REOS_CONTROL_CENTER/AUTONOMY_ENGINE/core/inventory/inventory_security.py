"""
CORE-004 T09 — Security & Tenant Boundary

Owns:
- tenant isolation
- inventory ownership boundary
- actor identity
- access authorization boundary
- mutation authorization boundary
- cross-tenant rejection
- IDOR protection
- sensitive commercial-data boundary

Does NOT own:
- authentication
- role/permission creation
- membership management
- authorization policy engine
- inventory persistence
- lifecycle
- availability
- provenance
- commercial calculations
- event transport
- REOS state
- ACRL execution

CORE-001 remains the identity / authorization authority.

CORE-004 consumes and verifies an externally established authorization
context; it does not create a second authorization engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet

from .inventory import Inventory
from .inventory_commercial_state import (
    CommercialStateSnapshot,
)
from .inventory_provenance import (
    InventoryProvenance,
)


class InventorySecurityError(
    PermissionError
):
    """Base CORE-004 security error."""


class InventoryTenantBoundaryViolation(
    InventorySecurityError
):
    """Cross-tenant access or mutation attempt."""


class InventoryCapabilityViolation(
    InventorySecurityError
):
    """Required externally granted capability is absent."""


class InventorySecurityContextError(
    InventorySecurityError
):
    """Security context is malformed or inactive."""


class InventoryOwnershipViolation(
    InventorySecurityError
):
    """Actor is outside the externally established ownership scope."""


class SensitiveCommercialDataViolation(
    InventorySecurityError
):
    """Sensitive commercial data was requested without capability."""


class InventoryCapability(str, Enum):
    READ_INVENTORY = "READ_INVENTORY"
    CREATE_INVENTORY = "CREATE_INVENTORY"
    UPDATE_INVENTORY = "UPDATE_INVENTORY"
    TRANSITION_INVENTORY = "TRANSITION_INVENTORY"
    CHANGE_AVAILABILITY = "CHANGE_AVAILABILITY"
    RESERVE_INVENTORY = "RESERVE_INVENTORY"
    ALLOCATE_INVENTORY = "ALLOCATE_INVENTORY"
    READ_PROVENANCE = "READ_PROVENANCE"
    UPDATE_PROVENANCE = "UPDATE_PROVENANCE"
    READ_COMMERCIAL_STATE = "READ_COMMERCIAL_STATE"
    UPDATE_COMMERCIAL_STATE = "UPDATE_COMMERCIAL_STATE"


def _text(
    value: str,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise InventorySecurityContextError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventorySecurityContextError(
            f"{name} cannot be empty."
        )

    return value


def _time(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventorySecurityContextError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventorySecurityContextError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class InventorySecurityContext:
    """
    Immutable externally authorized request context.

    authorization_reference is evidence that CORE-001 or another upstream
    policy authority made the authorization decision.

    CORE-004 only validates that the supplied context is coherent.
    """

    tenant_id: str
    actor_id: str
    capabilities: FrozenSet[InventoryCapability]
    authorization_reference: str
    issued_at: datetime
    expires_at: datetime | None = None
    request_id: str | None = None
    ownership_scope: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "actor_id",
            _text(
                self.actor_id,
                "actor_id",
            ),
        )

        if not isinstance(
            self.capabilities,
            frozenset,
        ):
            raise InventorySecurityContextError(
                "capabilities must be frozenset."
            )

        for capability in self.capabilities:
            if not isinstance(
                capability,
                InventoryCapability,
            ):
                raise InventorySecurityContextError(
                    "capabilities contains invalid value."
                )

        object.__setattr__(
            self,
            "authorization_reference",
            _text(
                self.authorization_reference,
                "authorization_reference",
            ),
        )

        object.__setattr__(
            self,
            "issued_at",
            _time(
                self.issued_at,
                "issued_at",
            ),
        )

        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _time(
                    self.expires_at,
                    "expires_at",
                ),
            )

            if (
                self.expires_at
                <= self.issued_at
            ):
                raise InventorySecurityContextError(
                    "expires_at must be later than issued_at."
                )

        if self.request_id is not None:
            object.__setattr__(
                self,
                "request_id",
                _text(
                    self.request_id,
                    "request_id",
                ),
            )

        if not isinstance(
            self.ownership_scope,
            frozenset,
        ):
            raise InventorySecurityContextError(
                "ownership_scope must be frozenset."
            )

        normalized_scope = frozenset(
            _text(
                item,
                "ownership_scope",
            )
            for item in self.ownership_scope
        )

        object.__setattr__(
            self,
            "ownership_scope",
            normalized_scope,
        )

    def assert_active(
        self,
        *,
        now: datetime | None = None,
    ) -> None:
        timestamp = (
            datetime.now(timezone.utc)
            if now is None
            else _time(now, "now")
        )

        if timestamp < self.issued_at:
            raise InventorySecurityContextError(
                "Security context is not active."
            )

        if (
            self.expires_at is not None
            and timestamp >= self.expires_at
        ):
            raise InventorySecurityContextError(
                "Security context has expired."
            )

    def ensure_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise InventoryTenantBoundaryViolation(
                "Security context tenant does not match resource tenant."
            )

    def ensure_inventory(
        self,
        inventory: Inventory,
    ) -> None:
        if not isinstance(
            inventory,
            Inventory,
        ):
            raise InventorySecurityContextError(
                "inventory must be Inventory."
            )

        self.ensure_tenant(
            inventory.tenant_id
        )

    def ensure_provenance(
        self,
        provenance: InventoryProvenance,
    ) -> None:
        if provenance.tenant_id != self.tenant_id:
            raise InventoryTenantBoundaryViolation(
                "Provenance tenant does not match security context."
            )

    def ensure_commercial_state(
        self,
        state: CommercialStateSnapshot,
    ) -> None:
        if state.tenant_id != self.tenant_id:
            raise InventoryTenantBoundaryViolation(
                "Commercial-state tenant does not match "
                "security context."
            )

    def ensure_ownership(
        self,
        inventory: Inventory,
    ) -> None:
        """
        IDOR protection.

        When an ownership scope is supplied, inventory access must be
        explicitly scoped to that inventory/project boundary.

        Empty ownership_scope means only that no additional CORE-004
        ownership restriction was supplied; it does not bypass tenant or
        capability checks.
        """
        self.ensure_inventory(
            inventory
        )

        if not self.ownership_scope:
            return

        allowed = {
            inventory.inventory_id,
            inventory.project_id,
        }

        if not allowed.intersection(
            self.ownership_scope
        ):
            raise InventoryOwnershipViolation(
                "Actor is outside the inventory ownership scope."
            )

    def require(
        self,
        capability: InventoryCapability,
    ) -> None:
        if not isinstance(
            capability,
            InventoryCapability,
        ):
            raise InventoryCapabilityViolation(
                "capability must be InventoryCapability."
            )

        if capability not in self.capabilities:
            raise InventoryCapabilityViolation(
                "Capability not granted: "
                f"{capability.value}"
            )

    def require_read(
        self,
    ) -> None:
        self.assert_active()
        self.require(
            InventoryCapability.READ_INVENTORY
        )

    def require_mutation(
        self,
        capability: InventoryCapability,
    ) -> None:
        self.assert_active()

        if capability not in {
            InventoryCapability.CREATE_INVENTORY,
            InventoryCapability.UPDATE_INVENTORY,
            InventoryCapability.TRANSITION_INVENTORY,
            InventoryCapability.CHANGE_AVAILABILITY,
            InventoryCapability.RESERVE_INVENTORY,
            InventoryCapability.ALLOCATE_INVENTORY,
            InventoryCapability.UPDATE_PROVENANCE,
            InventoryCapability.UPDATE_COMMERCIAL_STATE,
        }:
            raise InventoryCapabilityViolation(
                "Capability is not a valid mutation capability."
            )

        self.require(
            capability
        )

    def require_sensitive_commercial_read(
        self,
    ) -> None:
        self.assert_active()

        if (
            InventoryCapability.READ_COMMERCIAL_STATE
            not in self.capabilities
        ):
            raise SensitiveCommercialDataViolation(
                "Sensitive commercial-data capability is missing."
            )

    def authorize_inventory_read(
        self,
        inventory: Inventory,
    ) -> None:
        self.require_read()
        self.ensure_inventory(
            inventory
        )
        self.ensure_ownership(
            inventory
        )

    def authorize_inventory_mutation(
        self,
        inventory: Inventory,
        capability: InventoryCapability,
    ) -> None:
        self.require_mutation(
            capability
        )
        self.ensure_inventory(
            inventory
        )
        self.ensure_ownership(
            inventory
        )

    def authorize_provenance_read(
        self,
        inventory: Inventory,
        provenance: InventoryProvenance,
    ) -> None:
        self.require(
            InventoryCapability.READ_PROVENANCE
        )
        self.ensure_inventory(
            inventory
        )
        self.ensure_provenance(
            provenance
        )
        self.ensure_ownership(
            inventory
        )

    def authorize_commercial_read(
        self,
        inventory: Inventory,
        state: CommercialStateSnapshot,
    ) -> None:
        self.require_sensitive_commercial_read()
        self.ensure_inventory(
            inventory
        )
        self.ensure_commercial_state(
            state
        )
        self.ensure_ownership(
            inventory
        )


__all__ = [
    "InventorySecurityError",
    "InventoryTenantBoundaryViolation",
    "InventoryCapabilityViolation",
    "InventorySecurityContextError",
    "InventoryOwnershipViolation",
    "SensitiveCommercialDataViolation",
    "InventoryCapability",
    "InventorySecurityContext",
]
