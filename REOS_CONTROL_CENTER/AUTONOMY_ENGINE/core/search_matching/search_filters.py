"""
CORE-005 T01 — Structured Search Filters.

Filters only the derived CORE-005 InventoryIndexDocument projection.
Never mutates canonical CORE-004 Inventory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..inventory.inventory import (
    AvailabilityState,
    InventoryType,
    LifecycleState,
)
from .search_index_contract import InventoryIndexDocument


class StructuredSearchFilterError(ValueError):
    """Base error for invalid structured search filters."""


class StructuredSearchTenantError(StructuredSearchFilterError):
    """Raised when tenant scope is missing or invalid."""


def _normalize_required(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        error = (
            StructuredSearchTenantError
            if field_name == "tenant_id"
            else StructuredSearchFilterError
        )
        raise error(
            f"{field_name} must be a non-empty string."
        )

    return value.strip()


def _normalize_strings(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise StructuredSearchFilterError(
            f"{field_name} must be an iterable of strings."
        )

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise StructuredSearchFilterError(
            f"{field_name} must be iterable."
        ) from exc

    normalized: list[str] = []

    for value in iterator:
        normalized.append(
            _normalize_required(
                value,
                field_name,
            )
        )

    return tuple(
        sorted(
            set(normalized),
            key=str.casefold,
        )
    )


def _normalize_enum_values(
    values,
    enum_type,
    field_name: str,
):
    if isinstance(values, (str, bytes)):
        raise StructuredSearchFilterError(
            f"{field_name} must be an iterable of enum values."
        )

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise StructuredSearchFilterError(
            f"{field_name} must be iterable."
        ) from exc

    normalized = []

    for value in iterator:
        try:
            normalized.append(enum_type(value))
        except (TypeError, ValueError) as exc:
            raise StructuredSearchFilterError(
                f"{field_name} contains invalid value: {value!r}."
            ) from exc

    return tuple(
        sorted(
            set(normalized),
            key=lambda item: item.value,
        )
    )


@dataclass(frozen=True, slots=True)
class StructuredSearchFilter:
    """
    Immutable deterministic structured-search contract.

    Mandatory boundary:
        tenant_id

    Supported predicates:
        project
        inventory code
        inventory type
        lifecycle
        availability
        name substring

    Does NOT own:
        location search
        vector retrieval
        ranking
        matching
        visibility policy ownership
        canonical inventory mutation
    """

    tenant_id: str
    project_ids: tuple[str, ...] = ()
    inventory_codes: tuple[str, ...] = ()
    inventory_types: tuple[InventoryType, ...] = ()
    lifecycle_states: tuple[LifecycleState, ...] = ()
    availability_states: tuple[AvailabilityState, ...] = ()
    name_contains: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _normalize_required(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "project_ids",
            _normalize_strings(
                self.project_ids,
                "project_ids",
            ),
        )

        object.__setattr__(
            self,
            "inventory_codes",
            _normalize_strings(
                self.inventory_codes,
                "inventory_codes",
            ),
        )

        object.__setattr__(
            self,
            "inventory_types",
            _normalize_enum_values(
                self.inventory_types,
                InventoryType,
                "inventory_types",
            ),
        )

        object.__setattr__(
            self,
            "lifecycle_states",
            _normalize_enum_values(
                self.lifecycle_states,
                LifecycleState,
                "lifecycle_states",
            ),
        )

        object.__setattr__(
            self,
            "availability_states",
            _normalize_enum_values(
                self.availability_states,
                AvailabilityState,
                "availability_states",
            ),
        )

        if self.name_contains is not None:
            object.__setattr__(
                self,
                "name_contains",
                _normalize_required(
                    self.name_contains,
                    "name_contains",
                ).casefold(),
            )

    def matches(
        self,
        document: InventoryIndexDocument,
    ) -> bool:
        if not isinstance(
            document,
            InventoryIndexDocument,
        ):
            raise StructuredSearchFilterError(
                "document must be InventoryIndexDocument."
            )

        # Tenant boundary is always evaluated first.
        if document.tenant_id != self.tenant_id:
            return False

        if (
            self.project_ids
            and document.project_id not in self.project_ids
        ):
            return False

        if (
            self.inventory_codes
            and document.inventory_code
            not in self.inventory_codes
        ):
            return False

        if self.inventory_types:
            allowed = {
                item.value
                for item in self.inventory_types
            }

            if document.inventory_type not in allowed:
                return False

        if self.lifecycle_states:
            allowed = {
                item.value
                for item in self.lifecycle_states
            }

            if document.lifecycle not in allowed:
                return False

        if self.availability_states:
            allowed = {
                item.value
                for item in self.availability_states
            }

            if document.availability not in allowed:
                return False

        if (
            self.name_contains is not None
            and self.name_contains
            not in document.name.casefold()
        ):
            return False

        return True

    def apply(
        self,
        documents: Iterable[InventoryIndexDocument],
    ) -> tuple[InventoryIndexDocument, ...]:
        try:
            iterator = iter(documents)
        except TypeError as exc:
            raise StructuredSearchFilterError(
                "documents must be iterable."
            ) from exc

        matched = [
            document
            for document in iterator
            if self.matches(document)
        ]

        # Search filtering must never become business ranking.
        matched.sort(
            key=lambda document:
                document.index_key.casefold()
        )

        return tuple(matched)


__all__ = [
    "StructuredSearchFilter",
    "StructuredSearchFilterError",
    "StructuredSearchTenantError",
]
