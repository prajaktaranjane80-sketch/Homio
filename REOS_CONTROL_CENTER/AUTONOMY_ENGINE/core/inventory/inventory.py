"""
CORE-004 T01 — Inventory Domain

Owns:
- inventory identity
- project/development reference
- property identity
- unit identity
- inventory type vocabulary
- lifecycle-state vocabulary
- availability-state vocabulary
- tenant identity
- immutable identity semantics
- immutable inventory baseline

Does NOT own:
- hierarchy mutation
- lifecycle transition rules
- availability mutation
- reservation engine
- allocation engine
- provenance storage
- commercial state
- concurrency coordination
- authorization policy
- event transport
- REOS Control Center state
- ACRL reconstruction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping


class InventoryDomainError(ValueError):
    """Base CORE-004 inventory-domain error."""


class InventoryTenantViolation(
    InventoryDomainError
):
    """Raised when inventory is accessed across tenants."""


class InventoryProjectViolation(
    InventoryDomainError
):
    """Raised when inventory is used across projects."""


class InventoryType(str, Enum):
    """
    Canonical inventory hierarchy level.

    DEVELOPMENT
        Project/development identity.

    PROPERTY
        Property-level inventory beneath a project.

    UNIT
        Unit-level inventory beneath a property.
    """

    DEVELOPMENT = "DEVELOPMENT"
    PROPERTY = "PROPERTY"
    UNIT = "UNIT"


class LifecycleState(str, Enum):
    """
    Canonical lifecycle vocabulary.

    Transition ownership belongs to CORE-004 Part 04.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"
    ARCHIVED = "ARCHIVED"


class AvailabilityState(str, Enum):
    """
    Canonical availability vocabulary.

    Availability transition ownership belongs to Part 05.
    """

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BLOCKED = "BLOCKED"
    ALLOCATED = "ALLOCATED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _require_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise InventoryDomainError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise InventoryDomainError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _validate_aware_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventoryDomainError(
            f"{field_name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryDomainError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(
        timezone.utc
    )


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        datetime,
    ):
        return _validate_aware_datetime(
            value,
            "datetime",
        ).isoformat()

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        result: dict[str, Any] = {}

        for key, item in sorted(
            value.items(),
            key=lambda pair: str(pair[0]),
        ):
            if not isinstance(
                key,
                str,
            ):
                raise InventoryDomainError(
                    "Metadata keys must be strings."
                )

            result[key] = _canonicalize(
                item
            )

        return result

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise InventoryDomainError(
        "Unsupported inventory value type: "
        f"{type(value).__name__}"
    )


def _freeze_mapping(
    name: str,
    value: Mapping[str, Any] | None,
) -> MappingProxyType:
    if value is None:
        return MappingProxyType({})

    if not isinstance(
        value,
        Mapping,
    ):
        raise InventoryDomainError(
            f"{name} must be a mapping."
        )

    normalized: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(
            key,
            str,
        ):
            raise InventoryDomainError(
                f"{name} keys must be strings."
            )

        normalized[key] = _canonicalize(
            item
        )

    return MappingProxyType(
        normalized
    )


def _canonical_json(
    value: Mapping[str, Any],
) -> bytes:
    try:
        return json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InventoryDomainError(
            "Inventory identity cannot be "
            "canonically serialized."
        ) from exc


@dataclass(frozen=True, slots=True)
class InventoryIdentity:
    """
    Immutable identity of one inventory aggregate.

    Hierarchy rules:

    DEVELOPMENT
        project_id required
        property_id forbidden
        unit_id forbidden

    PROPERTY
        project_id required
        property_id required
        unit_id forbidden

    UNIT
        project_id required
        property_id required
        unit_id required

    The identity itself is immutable.

    Relationship reconstruction and parent/child validation belong to
    Part 03; this object only guarantees that one identity cannot encode
    an impossible hierarchy level.
    """

    inventory_id: str
    tenant_id: str
    inventory_type: InventoryType
    developer_id: str
    project_id: str
    property_id: str | None = None
    unit_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "inventory_id",
            _require_text(
                self.inventory_id,
                "inventory_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _require_text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "developer_id",
            _require_text(
                self.developer_id,
                "developer_id",
            ),
        )

        object.__setattr__(
            self,
            "project_id",
            _require_text(
                self.project_id,
                "project_id",
            ),
        )

        try:
            normalized_type = InventoryType(
                self.inventory_type
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
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
                _require_text(
                    self.property_id,
                    "property_id",
                ),
            )

        if self.unit_id is not None:
            object.__setattr__(
                self,
                "unit_id",
                _require_text(
                    self.unit_id,
                    "unit_id",
                ),
            )

        self._validate_identity_shape()

    def _validate_identity_shape(
        self,
    ) -> None:
        if (
            self.inventory_type
            is InventoryType.DEVELOPMENT
        ):
            if (
                self.property_id is not None
                or self.unit_id is not None
            ):
                raise InventoryDomainError(
                    "DEVELOPMENT inventory cannot "
                    "contain property_id or unit_id."
                )

        elif (
            self.inventory_type
            is InventoryType.PROPERTY
        ):
            if self.property_id is None:
                raise InventoryDomainError(
                    "PROPERTY inventory requires "
                    "property_id."
                )

            if self.unit_id is not None:
                raise InventoryDomainError(
                    "PROPERTY inventory cannot "
                    "contain unit_id."
                )

        elif (
            self.inventory_type
            is InventoryType.UNIT
        ):
            if self.property_id is None:
                raise InventoryDomainError(
                    "UNIT inventory requires "
                    "property_id."
                )

            if self.unit_id is None:
                raise InventoryDomainError(
                    "UNIT inventory requires "
                    "unit_id."
                )

    @property
    def identity_key(self) -> str:
        """
        Deterministic tenant-scoped identity.

        The complete hierarchy path is included, preventing collisions
        between development/property/unit identities.
        """
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
        """
        Fingerprint of immutable identity only.

        Mutable lifecycle, availability and commercial attributes are
        deliberately excluded.
        """
        payload = {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "inventory_type": (
                self.inventory_type.value
            ),
            "developer_id": self.developer_id,
            "project_id": self.project_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
        }

        return hashlib.sha256(
            _canonical_json(payload)
        ).hexdigest()

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise InventoryTenantViolation(
                "Inventory belongs to another tenant."
            )

    def assert_project(
        self,
        project_id: str,
    ) -> None:
        project_id = _require_text(
            project_id,
            "project_id",
        )

        if project_id != self.project_id:
            raise InventoryProjectViolation(
                "Inventory belongs to another project."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "inventory_type": (
                self.inventory_type.value
            ),
            "developer_id": self.developer_id,
            "project_id": self.project_id,
            "property_id": self.property_id,
            "unit_id": self.unit_id,
        }


@dataclass(frozen=True, slots=True)
class Inventory:
    """
    Immutable canonical inventory baseline.

    Part 01 intentionally does not implement state transitions.

    Lifecycle mutation belongs to Part 04.
    Availability mutation belongs to Part 05.
    Concurrency/version conflict handling belongs to Part 08.
    """

    identity: InventoryIdentity
    name: str
    lifecycle: LifecycleState
    availability: AvailabilityState
    created_at: datetime
    updated_at: datetime
    version: int = 1
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.identity,
            InventoryIdentity,
        ):
            raise InventoryDomainError(
                "identity must be InventoryIdentity."
            )

        object.__setattr__(
            self,
            "name",
            _require_text(
                self.name,
                "name",
            ),
        )

        try:
            lifecycle = LifecycleState(
                self.lifecycle
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise InventoryDomainError(
                "lifecycle is invalid."
            ) from exc

        try:
            availability = AvailabilityState(
                self.availability
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise InventoryDomainError(
                "availability is invalid."
            ) from exc

        object.__setattr__(
            self,
            "lifecycle",
            lifecycle,
        )

        object.__setattr__(
            self,
            "availability",
            availability,
        )

        object.__setattr__(
            self,
            "created_at",
            _validate_aware_datetime(
                self.created_at,
                "created_at",
            ),
        )

        object.__setattr__(
            self,
            "updated_at",
            _validate_aware_datetime(
                self.updated_at,
                "updated_at",
            ),
        )

        if self.updated_at < self.created_at:
            raise InventoryDomainError(
                "updated_at cannot be earlier "
                "than created_at."
            )

        if (
            isinstance(self.version, bool)
            or not isinstance(
                self.version,
                int,
            )
            or self.version < 1
        ):
            raise InventoryDomainError(
                "version must be a positive integer."
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(
                "metadata",
                self.metadata,
            ),
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
        inventory_id: str,
        at: datetime | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Inventory":
        """
        Create the immutable baseline identity.

        New inventory always starts as:
            lifecycle = DRAFT
            availability = UNAVAILABLE

        The later lifecycle/availability layers decide when it may move.
        """
        timestamp = (
            _utc_now()
            if at is None
            else _validate_aware_datetime(
                at,
                "at",
            )
        )

        identity = InventoryIdentity(
            inventory_id=inventory_id,
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
            availability=(
                AvailabilityState.UNAVAILABLE
            ),
            created_at=timestamp,
            updated_at=timestamp,
            version=1,
            metadata=metadata or {},
        )

    @property
    def inventory_id(self) -> str:
        return self.identity.inventory_id

    @property
    def tenant_id(self) -> str:
        return self.identity.tenant_id

    @property
    def developer_id(self) -> str:
        return self.identity.developer_id

    @property
    def project_id(self) -> str:
        return self.identity.project_id

    @property
    def property_id(self) -> str | None:
        return self.identity.property_id

    @property
    def unit_id(self) -> str | None:
        return self.identity.unit_id

    @property
    def inventory_type(self) -> InventoryType:
        return self.identity.inventory_type

    @property
    def identity_key(self) -> str:
        return self.identity.identity_key

    @property
    def identity_fingerprint(self) -> str:
        return self.identity.fingerprint

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        self.identity.assert_tenant(
            tenant_id
        )

    def assert_project(
        self,
        project_id: str,
    ) -> None:
        self.identity.assert_project(
            project_id
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "name": self.name,
            "lifecycle": self.lifecycle.value,
            "availability": (
                self.availability.value
            ),
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
            "version": self.version,
            "metadata": dict(self.metadata),
            "identity_fingerprint": (
                self.identity_fingerprint
            ),
        }


__all__ = [
    "AvailabilityState",
    "Inventory",
    "InventoryDomainError",
    "InventoryIdentity",
    "InventoryProjectViolation",
    "InventoryTenantViolation",
    "InventoryType",
    "LifecycleState",
]
