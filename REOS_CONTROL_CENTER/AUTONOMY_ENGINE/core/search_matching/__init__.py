"""CORE-005 Search & Matching Core."""

from .search_index_contract import (
    InventoryIndexDocument,
    InventoryIndexingError,
    InventoryIndexingHook,
    InventoryIndexStaleVersionError,
    SearchIndexContractError,
    SearchIndexDocumentError,
    SearchIndexOperation,
    SearchIndexScopeError,
    SearchIndexVersionError,
    build_inventory_index,
    build_inventory_index_delete,
)

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
