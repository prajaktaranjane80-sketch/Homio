"""
CORE-005 / Point 02 — Search Index Contract.

Defines the canonical contract for the derived search projection.

Source of truth:
    CORE-004 Inventory

This module owns:
- index schema contract
- source-of-truth reference
- indexed-field contract
- schema version
- index version
- index fingerprint
- stale-index detection
- projection document validation

This module does NOT own:
- canonical inventory state
- inventory lifecycle
- inventory availability transitions
- search execution
- query parsing
- ranking
- matching
- authorization policy
- event transport
- Qdrant runtime behavior
- Control Center state
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Callable, Mapping

from ..inventory.inventory import Inventory


class SearchIndexContractError(ValueError):
    """Base CORE-005 search-index contract error."""


class SearchIndexScopeError(SearchIndexContractError):
    """Raised when search index scope is invalid."""


class SearchIndexVersionError(SearchIndexContractError):
    """Raised when index/source versions are invalid or stale."""


class SearchIndexSchemaError(SearchIndexContractError):
    """Raised when index schema metadata is invalid."""


class SearchIndexDocumentError(SearchIndexContractError):
    """Raised when an index document is malformed."""


class SearchIndexOperation(str, Enum):
    """Supported derived-index operations."""

    UPSERT = "UPSERT"
    DELETE = "DELETE"


SEARCH_SCHEMA_VERSION = 1
SEARCH_INDEX_VERSION = 1
SEARCH_SOURCE_DOMAIN = "CORE-004.Inventory"

SEARCH_INDEXED_FIELDS: tuple[str, ...] = (
    "tenant_id",
    "project_id",
    "inventory_id",
    "inventory_code",
    "inventory_type",
    "lifecycle",
    "availability",
    "name",
    "inventory_version",
    "index_key",
)


def _require_text(
    value: str,
    field_name: str,
) -> str:
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


def _require_positive_integer(
    value: int,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise SearchIndexVersionError(
            f"{field_name} must be a positive integer."
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


def calculate_index_fingerprint(
    *,
    schema_version: int = SEARCH_SCHEMA_VERSION,
    index_version: int = SEARCH_INDEX_VERSION,
    source_domain: str = SEARCH_SOURCE_DOMAIN,
    indexed_fields: tuple[str, ...] = SEARCH_INDEXED_FIELDS,
) -> str:
    """
    Calculate the deterministic schema/index fingerprint.

    The fingerprint describes the projection contract itself,
    not an individual inventory record.
    """
    schema_version = _require_positive_integer(
        schema_version,
        "schema_version",
    )

    index_version = _require_positive_integer(
        index_version,
        "index_version",
    )

    source_domain = _require_text(
        source_domain,
        "source_domain",
    )

    normalized_fields = tuple(indexed_fields)

    if not normalized_fields:
        raise SearchIndexSchemaError(
            "indexed_fields cannot be empty."
        )

    if len(set(normalized_fields)) != len(
        normalized_fields
    ):
        raise SearchIndexSchemaError(
            "indexed_fields cannot contain duplicates."
        )

    for field_name in normalized_fields:
        _require_text(
            field_name,
            "indexed_field",
        )

    payload = {
        "schema_version": schema_version,
        "index_version": index_version,
        "source_domain": source_domain,
        "indexed_fields": list(normalized_fields),
    }

    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


EXPECTED_INDEX_FINGERPRINT = calculate_index_fingerprint()


@dataclass(frozen=True, slots=True)
class InventoryIndexDocument:
    """
    Immutable derived search-index document.

    Every document carries:
    - source identity
    - source version
    - schema version
    - index version
    - schema/index fingerprint

    The object can never become business source of truth.
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

    schema_version: int = SEARCH_SCHEMA_VERSION
    index_version: int = SEARCH_INDEX_VERSION
    index_fingerprint: str = ""
    operation: SearchIndexOperation = SearchIndexOperation.UPSERT
    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        for field_name in (
            "tenant_id",
            "project_id",
            "inventory_id",
            "inventory_code",
            "inventory_type",
            "lifecycle",
            "availability",
            "name",
            "index_key",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "inventory_version",
            _require_positive_integer(
                self.inventory_version,
                "inventory_version",
            ),
        )

        object.__setattr__(
            self,
            "schema_version",
            _require_positive_integer(
                self.schema_version,
                "schema_version",
            ),
        )

        object.__setattr__(
            self,
            "index_version",
            _require_positive_integer(
                self.index_version,
                "index_version",
            ),
        )

        expected_fingerprint = (
            calculate_index_fingerprint(
                schema_version=self.schema_version,
                index_version=self.index_version,
            )
        )

        supplied_fingerprint = (
            self.index_fingerprint.strip()
            if isinstance(
                self.index_fingerprint,
                str,
            )
            else ""
        )

        if not supplied_fingerprint:
            supplied_fingerprint = (
                expected_fingerprint
            )

        if (
            supplied_fingerprint
            != expected_fingerprint
        ):
            raise SearchIndexSchemaError(
                "index_fingerprint does not match "
                "the declared schema/index contract."
            )

        object.__setattr__(
            self,
            "index_fingerprint",
            supplied_fingerprint,
        )

        try:
            operation = SearchIndexOperation(
                self.operation
            )
        except (TypeError, ValueError) as exc:
            raise SearchIndexDocumentError(
                "operation must be UPSERT or DELETE."
            ) from exc

        object.__setattr__(
            self,
            "operation",
            operation,
        )

        object.__setattr__(
            self,
            "payload",
            _freeze_payload(self.payload),
        )

    @property
    def is_upsert(self) -> bool:
        return (
            self.operation
            is SearchIndexOperation.UPSERT
        )

    @property
    def is_delete(self) -> bool:
        return (
            self.operation
            is SearchIndexOperation.DELETE
        )

    @property
    def source_reference(self) -> str:
        return SEARCH_SOURCE_DOMAIN

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise SearchIndexScopeError(
                "Search document belongs to another tenant."
            )

    def assert_source_version(
        self,
        source_version: int,
    ) -> None:
        source_version = _require_positive_integer(
            source_version,
            "source_version",
        )

        if source_version != self.inventory_version:
            raise SearchIndexVersionError(
                "Search document source version does not "
                "match the supplied source version."
            )

    def assert_schema_compatibility(
        self,
        *,
        schema_version: int,
        index_version: int,
        index_fingerprint: str,
    ) -> None:
        schema_version = _require_positive_integer(
            schema_version,
            "schema_version",
        )

        index_version = _require_positive_integer(
            index_version,
            "index_version",
        )

        if (
            schema_version
            != self.schema_version
        ):
            raise SearchIndexSchemaError(
                "Search document schema version mismatch."
            )

        if (
            index_version
            != self.index_version
        ):
            raise SearchIndexVersionError(
                "Search document index version mismatch."
            )

        if (
            index_fingerprint
            != self.index_fingerprint
        ):
            raise SearchIndexSchemaError(
                "Search document fingerprint mismatch."
            )

    def is_stale_against(
        self,
        source_version: int,
    ) -> bool:
        source_version = _require_positive_integer(
            source_version,
            "source_version",
        )

        return (
            self.inventory_version
            < source_version
        )

    def assert_not_stale_against(
        self,
        source_version: int,
    ) -> None:
        if self.is_stale_against(
            source_version
        ):
            raise SearchIndexVersionError(
                "Search document is stale against "
                "the current source version."
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
            "schema_version": self.schema_version,
            "index_version": self.index_version,
            "index_fingerprint": self.index_fingerprint,
            "source_reference": self.source_reference,
            "operation": self.operation.value,
            "payload": dict(self.payload),
        }


def _inventory_code(
    inventory: Inventory,
) -> str:
    """
    Derive a stable search-facing inventory code.

    CORE-004 intentionally has no separate
    inventory_code source field.
    """
    return (
        inventory.unit_id
        or inventory.property_id
        or inventory.inventory_id
    )


def _base_payload(
    inventory: Inventory,
) -> dict[str, Any]:
    return {
        "developer_id": inventory.developer_id,
        "project_id": inventory.project_id,
        "property_id": inventory.property_id,
        "unit_id": inventory.unit_id,
        "identity_fingerprint": (
            inventory.identity_fingerprint
        ),
        "metadata": dict(
            inventory.metadata
        ),
    }


def build_inventory_index(
    inventory: Inventory,
) -> InventoryIndexDocument:
    """
    Build a canonical UPSERT projection from CORE-004.

    No source mutation occurs.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise SearchIndexDocumentError(
            "inventory must be a CORE-004 Inventory."
        )

    return InventoryIndexDocument(
        tenant_id=inventory.tenant_id,
        project_id=inventory.project_id,
        inventory_id=inventory.inventory_id,
        inventory_code=_inventory_code(
            inventory
        ),
        inventory_type=(
            inventory.inventory_type.value
        ),
        lifecycle=(
            inventory.lifecycle.value
        ),
        availability=(
            inventory.availability.value
        ),
        name=inventory.name,
        inventory_version=inventory.version,
        index_key=inventory.identity_key,
        schema_version=SEARCH_SCHEMA_VERSION,
        index_version=SEARCH_INDEX_VERSION,
        index_fingerprint=(
            EXPECTED_INDEX_FINGERPRINT
        ),
        operation=SearchIndexOperation.UPSERT,
        payload=_base_payload(
            inventory
        ),
    )


def build_inventory_index_delete(
    inventory: Inventory,
) -> InventoryIndexDocument:
    """
    Build a canonical DELETE projection.

    The Inventory snapshot remains the identity source,
    but the DELETE operation never mutates CORE-004.
    """
    if not isinstance(
        inventory,
        Inventory,
    ):
        raise SearchIndexDocumentError(
            "inventory must be a CORE-004 Inventory."
        )

    return InventoryIndexDocument(
        tenant_id=inventory.tenant_id,
        project_id=inventory.project_id,
        inventory_id=inventory.inventory_id,
        inventory_code=_inventory_code(
            inventory
        ),
        inventory_type=(
            inventory.inventory_type.value
        ),
        lifecycle=(
            inventory.lifecycle.value
        ),
        availability=(
            inventory.availability.value
        ),
        name=inventory.name,
        inventory_version=inventory.version,
        index_key=inventory.identity_key,
        schema_version=SEARCH_SCHEMA_VERSION,
        index_version=SEARCH_INDEX_VERSION,
        index_fingerprint=(
            EXPECTED_INDEX_FINGERPRINT
        ),
        operation=SearchIndexOperation.DELETE,
        payload=_base_payload(
            inventory
        ),
    )


@dataclass(frozen=True, slots=True)
class InventoryIndexingHook:
    """
    Thin projection hook.

    This is intentionally NOT an indexing engine.
    Runtime adapters consume InventoryIndexDocument later.
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
        document = build_inventory_index(
            inventory
        )

        if self.on_upsert is not None:
            self.on_upsert(document)

        return document

    def delete(
        self,
        inventory: Inventory,
    ) -> InventoryIndexDocument:
        document = build_inventory_index_delete(
            inventory
        )

        if self.on_delete is not None:
            self.on_delete(document)

        return document


# Historical aliases are retained only for
# compatibility with already-created CORE-005 code.
InventoryIndexingError = SearchIndexContractError
InventoryIndexStaleVersionError = (
    SearchIndexVersionError
)


__all__ = [
    "SEARCH_SCHEMA_VERSION",
    "SEARCH_INDEX_VERSION",
    "SEARCH_SOURCE_DOMAIN",
    "SEARCH_INDEXED_FIELDS",
    "EXPECTED_INDEX_FINGERPRINT",
    "calculate_index_fingerprint",
    "InventoryIndexDocument",
    "InventoryIndexingError",
    "InventoryIndexingHook",
    "InventoryIndexStaleVersionError",
    "SearchIndexContractError",
    "SearchIndexDocumentError",
    "SearchIndexOperation",
    "SearchIndexScopeError",
    "SearchIndexSchemaError",
    "SearchIndexVersionError",
    "build_inventory_index",
    "build_inventory_index_delete",
]
