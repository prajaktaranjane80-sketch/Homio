"""Authoritative CORE-004 inventory domain.

This module owns canonical inventory identity and the immutable domain
representation used by later CORE-004 contracts.

It does not:
- persist state
- perform search indexing
- acquire inventory
- store evidence
- mutate REOS Control Center state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


class InventoryDomainError(ValueError):
    """Base error for invalid inventory-domain data."""


class InventoryTenantViolation(InventoryDomainError):
    """Raised when a caller crosses the inventory tenant boundary."""


class InventoryProjectViolation(InventoryDomainError):
    """Raised when inventory is used outside its project boundary."""


class InventoryType(str, Enum):
    """Canonical inventory hierarchy level."""

    DEVELOPMENT = "DEVELOPMENT"
    PROPERTY = "PROPERTY"
    UNIT = "UNIT"


class LifecycleState(str, Enum):
    """Canonical lifecycle vocabulary shared by CORE-004."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"
    ARCHIVED = "ARCHIVED"


class AvailabilityState(str, Enum):
    """Canonical availability vocabulary shared by CORE-004."""

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    ALLOCATED = "ALLOCATED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InventoryDomainError(f"{name} is required.")
    return value.strip()


def _freeze_mapping(
    name: str,
    value: Mapping[str, Any] | None,
) -> MappingProxyType:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise InventoryDomainError(f"{name} must be a mapping.")

    frozen = {str(key): item for key, item in value.items()}

    try:
        json.dumps(
            frozen,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    except (TypeError, ValueError) as exc:
        raise InventoryDomainError(
            f"{name} contains unsupported values."
        ) from exc

    return MappingProxyType(frozen)


def _canonical_payload(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InventoryDomainError(
            "Inventory identity contains non-canonical values."
        ) from exc


@dataclass(frozen=True)
class InventoryIdentity:
    """Immutable, tenant-scoped identity for one inventory aggregate.

    project_id is the canonical project/development identity.
    It is not duplicated as an independently owned development identifier.
    """

    inventory_id: str
    tenant_id: str
    inventory_type: InventoryType
    developer_id: str
    project_id: str
    property_id: str | None = None
    unit_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "inventory_id",
            "tenant_id",
            "developer_id",
            "project_id",
        ):
            object.__setattr__(
                self,
                name,
                _require_text(name, getattr(self, name)),
            )

        try:
            normalized_type = InventoryType(self.inventory_type)
        except (TypeError, ValueError) as exc:
            raise InventoryDomainError(
                "inventory_type is invalid."
            ) from exc

        object.__setattr__(
            self,
            "inventory_type",
            normalized_type,
        )

        if self.property_id is not None:
            object.__setattr__(
                self,
                "property_id",
                _require_text("property_id", self.property_id),
            )

        if self.unit_id is not None:
            object.__setattr__(
                self,
                "unit_id",
                _require_text("unit_id", self.unit_id),
            )

        if normalized_type is InventoryType.DEVELOPMENT:
            if self.property_id is not None or self.unit_id is not None:
                raise InventoryDomainError(
                    "DEVELOPMENT inventory cannot carry "
                    "property_id or unit_id."
                )

        elif normalized_type is InventoryType.PROPERTY:
            if self.property_id is None or self.unit_id is not None:
                raise InventoryDomainError(
                    "PROPERTY inventory requires property_id "
                    "and forbids unit_id."
                )

        elif normalized_type is InventoryType.UNIT:
            if self.property_id is None or self.unit_id is None:
                raise InventoryDomainError(
                    "UNIT inventory requires both property_id "
                    "and unit_id."
                )

    @property
    def identity_key(self) -> str:
        return ":".join(
            (
                self.tenant_id,
                self.inventory_type.value,
                self.project_id,
                self.property_id or "-",
                self.unit_id or "-",
                self.inventory_id,
            )
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "inventory_type": self.inventory_type.value,
            "developer_id": self.developer_id,
            "project_id": self.project_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
        }

        return sha256(
            _canonical_payload(payload)
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "inventory_type": self.inventory_type.value,
            "developer_id": self.developer_id,
            "project_id": self.project_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
        }


@dataclass(frozen=True)
class InventoryEvent:
    """Persistence-neutral event emitted by the inventory domain."""

    event_id: str
    event_type: str
    inventory_id: str
    tenant_id: str
    inventory_version: int
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_text("event_id", self.event_id),
        )

        object.__setattr__(
            self,
            "event_type",
            _require_text("event_type", self.event_type),
        )

        object.__setattr__(
            self,
            "inventory_id",
            _require_text("inventory_id", self.inventory_id),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _require_text("tenant_id", self.tenant_id),
        )

        if (
            not isinstance(self.inventory_version, int)
            or self.inventory_version < 1
        ):
            raise InventoryDomainError(
                "inventory_version must be a positive integer."
            )

        object.__setattr__(
            self,
            "payload",
            _freeze_mapping("payload", self.payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "inventory_version": self.inventory_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class Inventory:
    """Canonical immutable inventory aggregate baseline for CORE-004."""

    identity: InventoryIdentity
    name: str
    lifecycle: LifecycleState
    availability: AvailabilityState
    created_at: str
    updated_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, InventoryIdentity):
            raise InventoryDomainError(
                "identity must be an InventoryIdentity."
            )

        object.__setattr__(
            self,
            "name",
            _require_text("name", self.name),
        )

        try:
            object.__setattr__(
                self,
                "lifecycle",
                LifecycleState(self.lifecycle),
            )

            object.__setattr__(
                self,
                "availability",
                AvailabilityState(self.availability),
            )
        except (TypeError, ValueError) as exc:
            raise InventoryDomainError(
                "Invalid inventory state."
            ) from exc

        if (
            not isinstance(self.version, int)
            or self.version < 1
        ):
            raise InventoryDomainError(
                "version must be a positive integer."
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping("metadata", self.metadata),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        developer_id: str,
        project_id: str,
        inventory_type: InventoryType,
        name: str,
        property_id: str | None = None,
        unit_id: str | None = None,
        inventory_id: str | None = None,
        at: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Inventory":
        timestamp = at or _utc_now()

        identity = InventoryIdentity(
            inventory_id=inventory_id or str(uuid4()),
            tenant_id=tenant_id,
            inventory_type=inventory_type,
            developer_id=developer_id,
            project_id=project_id,
            property_id=property_id,
            unit_id=unit_id,
        )

        return cls(
            identity=identity,
            name=name,
            lifecycle=LifecycleState.DRAFT,
            availability=AvailabilityState.UNAVAILABLE,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=metadata or {},
        )

    @property
    def inventory_id(self) -> str:
        return self.identity.inventory_id

    @property
    def tenant_id(self) -> str:
        return self.identity.tenant_id

    @property
    def project_id(self) -> str:
        return self.identity.project_id

    @property
    def inventory_type(self) -> InventoryType:
        return self.identity.inventory_type

    @property
    def identity_fingerprint(self) -> str:
        return self.identity.fingerprint

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise InventoryTenantViolation(
                "Inventory belongs to a different tenant."
            )

    def assert_project(self, project_id: str) -> None:
        if project_id != self.project_id:
            raise InventoryProjectViolation(
                "Inventory belongs to a different project."
            )

    def created_event(
        self,
        *,
        at: str | None = None,
    ) -> InventoryEvent:
        timestamp = at or self.created_at

        return InventoryEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_CREATED",
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            inventory_version=self.version,
            occurred_at=timestamp,
            payload={
                "inventory_type": self.inventory_type.value,
                "project_id": self.project_id,
                "property_id": self.identity.property_id,
                "unit_id": self.identity.unit_id,
                "identity_fingerprint": self.identity_fingerprint,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "name": self.name,
            "lifecycle": self.lifecycle.value,
            "availability": self.availability.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "identity_fingerprint": self.identity_fingerprint,
        }


__all__ = [
    "AvailabilityState",
    "Inventory",
    "InventoryDomainError",
    "InventoryEvent",
    "InventoryIdentity",
    "InventoryProjectViolation",
    "InventoryTenantViolation",
    "InventoryType",
    "LifecycleState",
]
