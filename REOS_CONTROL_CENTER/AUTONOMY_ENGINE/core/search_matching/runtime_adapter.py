"""
CORE-005 / Point 12 — Runtime Adapter Boundary.

Provides backend-independent contracts for:

- search backend abstraction
- index adapter
- backend-independent query execution
- rebuild adapter
- runtime capability discovery

Existing backend implementations remain adapters.
The domain layer does not import backend-specific types.

This module does NOT:
- create a second search engine
- create a second indexing engine
- own Qdrant policy
- own source truth
- own ranking
- own matching
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, Sequence

from .search_domain import SearchRequest
from .search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


class RuntimeAdapterError(ValueError):
    """Base runtime adapter error."""


class RuntimeAdapterConfigurationError(
    RuntimeAdapterError
):
    """Raised for invalid adapter configuration."""


class RuntimeAdapterCapabilityError(
    RuntimeAdapterError
):
    """Raised when an adapter cannot provide a capability."""


class RuntimeAdapterOperationError(
    RuntimeAdapterError
):
    """Raised when an adapter operation is invalid."""


@dataclass(frozen=True, slots=True)
class RuntimeBackendIdentity:
    """
    Backend identity metadata.

    Domain code consumes this metadata without depending on
    the backend's SDK/client classes.
    """

    backend_name: str
    adapter_name: str
    adapter_version: str
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        for field_name in (
            "backend_name",
            "adapter_name",
            "adapter_version",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise RuntimeAdapterConfigurationError(
                    f"{field_name} must be non-empty."
                )


@dataclass(frozen=True, slots=True)
class RuntimeSearchHit:
    """
    Backend-neutral search hit.

    Payload remains derived projection data.
    """

    index_key: str
    score: float | None = None
    payload: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.index_key,
                str,
            )
            or not self.index_key.strip()
        ):
            raise RuntimeAdapterOperationError(
                "index_key must be non-empty."
            )

        if self.score is not None:
            try:
                normalized = float(
                    self.score
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise RuntimeAdapterOperationError(
                    "score must be numeric."
                ) from exc

            object.__setattr__(
                self,
                "score",
                normalized,
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise RuntimeAdapterOperationError(
                "payload must be mapping."
            )

        object.__setattr__(
            self,
            "payload",
            dict(self.payload),
        )


class SearchBackendAdapter(Protocol):
    """
    Backend-independent search contract.

    Concrete backends implement this protocol outside the domain.
    """

    @property
    def identity(
        self,
    ) -> RuntimeBackendIdentity:
        ...

    def search(
        self,
        request: SearchRequest,
        *,
        limit: int,
    ) -> tuple[RuntimeSearchHit, ...]:
        ...


class SearchIndexAdapter(Protocol):
    """
    Derived-index write boundary.

    The concrete adapter owns backend-specific translation.
    """

    @property
    def identity(
        self,
    ) -> RuntimeBackendIdentity:
        ...

    def apply(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
        vector: Sequence[float] | None = None,
    ) -> str:
        ...


class SearchRebuildAdapter(Protocol):
    """
    Deterministic rebuild boundary.

    No source mutation is permitted.
    """

    def rebuild(
        self,
        documents: Iterable[
            InventoryIndexDocument
        ],
    ) -> tuple[str, ...]:
        ...


@dataclass(frozen=True, slots=True)
class RuntimeAdapterRegistry:
    """
    Explicit adapter set.

    There is exactly one adapter for each runtime responsibility.
    """

    backend: SearchBackendAdapter
    index: SearchIndexAdapter
    rebuild: SearchRebuildAdapter

    def validate(
        self,
    ) -> RuntimeBackendIdentity:
        backend_identity = self.backend.identity
        index_identity = self.index.identity

        if (
            backend_identity.backend_name
            != index_identity.backend_name
        ):
            raise RuntimeAdapterConfigurationError(
                "Search backend and index adapter backend "
                "identities do not match."
            )

        return backend_identity


@dataclass(frozen=True, slots=True)
class BackendIndependentSearchRuntime:
    """
    Thin runtime facade.

    It does not implement retrieval/ranking/business logic.
    It only delegates through the adapter contracts.
    """

    adapters: RuntimeAdapterRegistry

    def backend_identity(
        self,
    ) -> RuntimeBackendIdentity:
        return self.adapters.validate()

    def search(
        self,
        request: SearchRequest,
        *,
        limit: int,
    ) -> tuple[RuntimeSearchHit, ...]:
        if (
            isinstance(
                limit,
                bool,
            )
            or not isinstance(
                limit,
                int,
            )
            or limit < 1
        ):
            raise RuntimeAdapterOperationError(
                "limit must be positive."
            )

        self.adapters.validate()

        return self.adapters.backend.search(
            request,
            limit=limit,
        )


class QdrantIndexAdapter:
    """
    Adapter around the existing CORE-005 Qdrant indexing boundary.

    This is only translation.
    `QdrantIndexingPipeline` remains the existing indexing contract.
    """

    def __init__(
        self,
        pipeline: Any,
        *,
        backend_name: str = "QDRANT",
        adapter_version: str = "1",
    ) -> None:
        required_methods = (
            "upsert",
            "delete",
        )

        for method_name in required_methods:
            if not hasattr(
                pipeline,
                method_name,
            ):
                raise RuntimeAdapterConfigurationError(
                    "pipeline is missing required method: "
                    f"{method_name}"
                )

        self._pipeline = pipeline
        self._identity = RuntimeBackendIdentity(
            backend_name=backend_name,
            adapter_name="QdrantIndexAdapter",
            adapter_version=adapter_version,
            capabilities=frozenset(
                {
                    "UPSERT",
                    "DELETE",
                    "TENANT_BOUNDARY",
                    "VERSION_BOUNDARY",
                }
            ),
        )

    @property
    def identity(
        self,
    ) -> RuntimeBackendIdentity:
        return self._identity

    def apply(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
        vector: Sequence[float] | None = None,
    ) -> str:
        if not isinstance(
            document,
            InventoryIndexDocument,
        ):
            raise RuntimeAdapterOperationError(
                "document must be InventoryIndexDocument."
            )

        if (
            document.operation
            is SearchIndexOperation.UPSERT
        ):
            if vector is None:
                raise RuntimeAdapterOperationError(
                    "UPSERT requires vector at adapter boundary."
                )

            return self._pipeline.upsert(
                document,
                vector,
                tenant_id=tenant_id,
            )

        if (
            document.operation
            is SearchIndexOperation.DELETE
        ):
            return self._pipeline.delete(
                document,
                tenant_id=tenant_id,
            )

        raise RuntimeAdapterOperationError(
            "Unsupported index operation."
        )


class DeterministicRebuildAdapter:
    """
    Generic rebuild adapter.

    A concrete backend writer is injected; this class does not
    implement another rebuild engine.
    """

    def __init__(
        self,
        writer,
    ) -> None:
        if not callable(writer):
            raise RuntimeAdapterConfigurationError(
                "writer must be callable."
            )

        self._writer = writer

    def rebuild(
        self,
        documents: Iterable[
            InventoryIndexDocument
        ],
    ) -> tuple[str, ...]:
        materialized = list(documents)

        for document in materialized:
            if not isinstance(
                document,
                InventoryIndexDocument,
            ):
                raise RuntimeAdapterOperationError(
                    "rebuild documents must contain "
                    "InventoryIndexDocument values."
                )

        materialized.sort(
            key=lambda document: (
                document.tenant_id.casefold(),
                document.index_key.casefold(),
                document.inventory_version,
            )
        )

        return tuple(
            str(
                self._writer(document)
            )
            for document in materialized
        )


__all__ = [
    "RuntimeAdapterError",
    "RuntimeAdapterConfigurationError",
    "RuntimeAdapterCapabilityError",
    "RuntimeAdapterOperationError",
    "RuntimeBackendIdentity",
    "RuntimeSearchHit",
    "SearchBackendAdapter",
    "SearchIndexAdapter",
    "SearchRebuildAdapter",
    "RuntimeAdapterRegistry",
    "BackendIndependentSearchRuntime",
    "QdrantIndexAdapter",
    "DeterministicRebuildAdapter",
]
