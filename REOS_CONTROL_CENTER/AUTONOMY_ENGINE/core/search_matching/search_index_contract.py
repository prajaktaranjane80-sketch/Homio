"""
CORE-005 — Canonical Search Index Contract.

Search is a derived projection of canonical CORE-004 Inventory.

This module owns ONLY the search-index projection contract.

It does NOT own:
- canonical inventory truth
- inventory lifecycle transitions
- inventory availability transitions
- business ownership
- deal state
- commission
- fraud
- governance
- event transport
- Qdrant client behavior
- ranking policy
- matching policy
- Control Center state

Canonical source:
    AUTONOMY_ENGINE.core.inventory.inventory.Inventory
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping

from ..inventory.inventory import Inventory


class SearchIndexContractError(ValueError):
    """Base CORE-005 search-index contract error."""


class SearchIndexScopeError(SearchIndexContractError):
    """Raised when tenant/project/index scope is invalid."""


class SearchIndexVersionError(SearchIndexContractError):
    """Raised when an index document version is invalid or stale."""


class SearchIndexDocumentError(SearchIndexContractError):
    """Raised when an index document is malformed."""


class SearchIndexOperation(str, Enum):
    UPSERT = "UPSERT"
    DELETE = "DELETE"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise SearchIndexDocumentError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise SearchIndexDocumentError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _require_version(value: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise SearchIndexVersionError(
            "inventory_version must be a positive integer."
        )

    return value


def _freeze_payload(
    payload: Mapping[str, Any] | None,
) -> MappingProxyType:
    if payload is None:
        return MappingProxyType({})

    if not isinstance(payload, Mapping):
        raise SearchIndexDocumentError(
            "payload must be a mapping."
        )

    normalized: dict[str, Any] = {}

    for key, value in payload.items():
        if not isinstance(key, str):
            raise SearchIndexDocumentError(
                "payload keys must be strings."
            )

        normalized[key] = value

    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class InventoryIndexDocument:
    """
    Immutable derived search projection of canonical Inventory.

    One document represents one search-visible projection state.
    The document can never become the business source of truth.
    """

    tenant_id: str
    project_id: str
    inventory_id: str
    inventory_code: str
    inventory_type: str
    lifecycle: str
    availability: str
    name: str
    inventory_version: int
    index_key: str
    operation: SearchIndexOperation = SearchIndexOperation.UPSERT
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _require_text(self.tenant_id, "tenant_id"),
        )
        object.__setattr__(
            self,
            "project_id",
            _require_text(self.project_id, "project_id"),
        )
        object.__setattr__(
            self,
            "inventory_id",
            _require_text(self.inventory_id, "inventory_id"),
        )
        object.__setattr__(
            self,
            "inventory_code",
            _require_text(self.inventory_code, "inventory_code"),
        )
        object.__setattr__(
            self,
            "inventory_type",
            _require_text(self.inventory_type, "inventory_type"),
        )
        object.__setattr__(
            self,
            "lifecycle",
            _require_text(self.lifecycle, "lifecycle"),
        )
        object.__setattr__(
            self,
            "availability",
            _require_text(self.availability, "availability"),
        )
        object.__setattr__(
            self,
            "name",
            _require_text(self.name, "name"),
        )
        object.__setattr__(
            self,
            "inventory_version",
            _require_version(self.inventory_version),
        )
        object.__setattr__(
            self,
            "index_key",
            _require_text(self.index_key, "index_key"),
        )

        try:
            operation = SearchIndexOperation(self.operation)
        except (TypeError, ValueError) as exc:
            raise SearchIndexDocumentError(
                "operation must be UPSERT or DELETE."
            ) from exc

        object.__setattr__(self, "operation", operation)
        object.__setattr__(
            self,
            "payload",
            _freeze_payload(self.payload),
        )

        if self.operation is SearchIndexOperation.UPSERT:
            if not self.name:
                raise SearchIndexDocumentError(
                    "UPSERT document requires name."
                )

    @property
    def is_upsert(self) -> bool:
        return self.operation is SearchIndexOperation.UPSERT

    @property
    def is_delete(self) -> bool:
        return self.operation is SearchIndexOperation.DELETE

    def assert_tenant(self, tenant_id: str) -> None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise SearchIndexScopeError(
                "Search document belongs to another tenant."
            )

    def assert_version(
        self,
        expected_version: int,
    ) -> None:
        expected_version = _require_version(
            expected_version
        )

        if expected_version != self.inventory_version:
            raise SearchIndexVersionError(
                "Search document targets a stale inventory version."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_id": self.inventory_id,
            "inventory_code": self.inventory_code,
            "inventory_type": self.inventory_type,
            "lifecycle": self.lifecycle,
            "availability": self.availability,
            "name": self.name,
            "inventory_version": self.inventory_version,
            "index_key": self.index_key,
            "operation": self.operation.value,
            "payload": dict(self.payload),
        }


def _inventory_code(inventory: Inventory) -> str:
    """
    Derive a stable search-facing inventory code.

    CORE-004 has no separate inventory_code field.
    """
    return (
        inventory.unit_id
        or inventory.property_id
        or inventory.inventory_id
    )


def _base_payload(inventory: Inventory) -> dict[str, Any]:
    return {
        "developer_id": inventory.developer_id,
        "project_id": inventory.project_id,
        "property_id": inventory.property_id,
        "unit_id": inventory.unit_id,
        "identity_fingerprint": inventory.identity_fingerprint,
        "metadata": dict(inventory.metadata),
    }


def build_inventory_index(
    inventory: Inventory,
) -> InventoryIndexDocument:
    """
    Build the canonical UPSERT projection from CORE-004 Inventory.

    No mutation is performed.
    """
    if not isinstance(inventory, Inventory):
        raise SearchIndexDocumentError(
            "inventory must be a CORE-004 Inventory."
        )

    return InventoryIndexDocument(
        tenant_id=inventory.tenant_id,
        project_id=inventory.project_id,
        inventory_id=inventory.inventory_id,
        inventory_code=_inventory_code(inventory),
        inventory_type=inventory.inventory_type.value,
        lifecycle=inventory.lifecycle.value,
        availability=inventory.availability.value,
        name=inventory.name,
        inventory_version=inventory.version,
        index_key=inventory.identity_key,
        operation=SearchIndexOperation.UPSERT,
        payload=_base_payload(inventory),
    )


def build_inventory_index_delete(
    inventory: Inventory,
) -> InventoryIndexDocument:
    """
    Build the canonical DELETE projection for one Inventory identity.
    """
    if not isinstance(inventory, Inventory):
        raise SearchIndexDocumentError(
            "inventory must be a CORE-004 Inventory."
        )

    return InventoryIndexDocument(
        tenant_id=inventory.tenant_id,
        project_id=inventory.project_id,
        inventory_id=inventory.inventory_id,
        inventory_code=_inventory_code(inventory),
        inventory_type=inventory.inventory_type.value,
        lifecycle=inventory.lifecycle.value,
        availability=inventory.availability.value,
        name=inventory.name,
        inventory_version=inventory.version,
        index_key=inventory.identity_key,
        operation=SearchIndexOperation.DELETE,
        payload=_base_payload(inventory),
    )


@dataclass(frozen=True, slots=True)
class InventoryIndexingHook:
    """
    Thin projection hook.

    This is NOT an indexing engine.
    It produces canonical derived documents only.
    Runtime adapters consume those documents later.
    """

    on_upsert: Callable[
        [InventoryIndexDocument],
        None,
    ] | None = None

    on_delete: Callable[
        [InventoryIndexDocument],
        None,
    ] | None = None

    def upsert(
        self,
        inventory: Inventory,
    ) -> InventoryIndexDocument:
        document = build_inventory_index(inventory)

        if self.on_upsert is not None:
            self.on_upsert(document)

        return document

    def delete(
        self,
        inventory: Inventory,
    ) -> InventoryIndexDocument:
        document = build_inventory_index_delete(inventory)

        if self.on_delete is not None:
            self.on_delete(document)

        return document


# Historical names retained ONLY as exception aliases.
# They do not recreate the removed CORE-004 indexing subsystem.
InventoryIndexingError = SearchIndexContractError
InventoryIndexStaleVersionError = SearchIndexVersionError


__all__ = [
    "InventoryIndexDocument",
    "InventoryIndexingError",
    "InventoryIndexingHook",
    "InventoryIndexStaleVersionError",
    "SearchIndexContractError",
    "SearchIndexDocumentError",
    "SearchIndexOperation",
    "SearchIndexScopeError",
    "SearchIndexVersionError",
    "build_inventory_index",
    "build_inventory_index_delete",
]
