from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from typing import Callable, Iterable, Protocol, Sequence

from ..inventory.inventory import Inventory
from .search_index_contract import (
    InventoryIndexDocument,
    SearchIndexDocumentError,
    SearchIndexOperation,
    build_inventory_index,
    build_inventory_index_delete,
)


class SearchRebuildError(RuntimeError):
    """Base rebuild/recovery error."""


class SearchRebuildConfigurationError(
    SearchRebuildError
):
    """Raised when rebuild configuration is invalid."""


class SearchRebuildTenantError(
    SearchRebuildError
):
    """Raised when rebuild scope is invalid."""


class SearchRebuildConflictError(
    SearchRebuildError
):
    """Raised for duplicate or conflicting source identities."""


class SearchRebuildSinkError(
    SearchRebuildError
):
    """Raised when the indexing sink fails."""


class SearchRebuildSink(Protocol):
    def upsert(
        self,
        document: InventoryIndexDocument,
        vector: Sequence[float],
        *,
        tenant_id: str,
    ) -> str:
        ...

    def delete(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> str:
        ...


VectorProvider = Callable[
    [InventoryIndexDocument],
    Sequence[float],
]


def _require_tenant(
    tenant_id: str | None,
) -> str | None:
    if tenant_id is None:
        return None

    if not isinstance(
        tenant_id,
        str,
    ):
        raise SearchRebuildTenantError(
            "tenant_id must be a string."
        )

    normalized = tenant_id.strip()

    if not normalized:
        raise SearchRebuildTenantError(
            "tenant_id cannot be empty."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class SearchRebuildCheckpoint:
    """
    Immutable recovery checkpoint.

    completed_index_keys is the exact successfully committed
    projection set at the moment the checkpoint was produced.
    """

    run_id: str
    completed_index_keys: tuple[str, ...] = ()
    updated_at: datetime = (
        datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.run_id,
                str,
            )
            or not self.run_id.strip()
        ):
            raise SearchRebuildConfigurationError(
                "run_id must be a non-empty string."
            )

        normalized_keys = tuple(
            sorted(
                set(
                    self.completed_index_keys
                )
            )
        )

        for index_key in normalized_keys:
            if (
                not isinstance(
                    index_key,
                    str,
                )
                or not index_key.strip()
            ):
                raise SearchRebuildConfigurationError(
                    "checkpoint keys must be "
                    "non-empty strings."
                )

        if not isinstance(
            self.updated_at,
            datetime,
        ):
            raise SearchRebuildConfigurationError(
                "updated_at must be datetime."
            )

        object.__setattr__(
            self,
            "run_id",
            self.run_id.strip(),
        )

        object.__setattr__(
            self,
            "completed_index_keys",
            normalized_keys,
        )

    @property
    def completed(self) -> frozenset[str]:
        return frozenset(
            self.completed_index_keys
        )

    def with_completed(
        self,
        index_key: str,
    ) -> "SearchRebuildCheckpoint":
        if not isinstance(
            index_key,
            str,
        ) or not index_key.strip():
            raise SearchRebuildConfigurationError(
                "index_key must be non-empty."
            )

        return SearchRebuildCheckpoint(
            run_id=self.run_id,
            completed_index_keys=(
                self.completed_index_keys
                + (index_key.strip(),)
            ),
            updated_at=datetime.now(
                timezone.utc
            ),
        )


@dataclass(frozen=True, slots=True)
class SearchRebuildReport:
    run_id: str
    scanned: int
    indexed: int
    skipped: int
    deleted_stale: int
    completed_index_keys: tuple[str, ...]
    checkpoint: SearchRebuildCheckpoint
    resumed: bool

    @property
    def complete(self) -> bool:
        return (
            self.checkpoint is not None
            and self.scanned
            >= 0
            and self.indexed
            + self.skipped
            == self.scanned
        )


class SearchRebuildFailure(
    SearchRebuildError
):
    """
    Recovery-aware rebuild failure.

    checkpoint exposes exactly what was successfully
    completed before failure.
    """

    def __init__(
        self,
        message: str,
        checkpoint: SearchRebuildCheckpoint,
        *,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message,
            checkpoint,
        )
        self.checkpoint = checkpoint
        self.cause = cause


@dataclass(slots=True)
class InMemorySearchRebuildSink:
    """
    Test-only deterministic sink.

    This is not a production indexing engine.
    It exists only to verify rebuild semantics.
    """

    documents: dict[
        str,
        InventoryIndexDocument,
    ]
    vectors: dict[
        str,
        tuple[float, ...],
    ]

    def __init__(self) -> None:
        self.documents = {}
        self.vectors = {}

    def upsert(
        self,
        document: InventoryIndexDocument,
        vector: Sequence[float],
        *,
        tenant_id: str,
    ) -> str:
        document.assert_tenant(
            tenant_id
        )

        if document.operation is not (
            SearchIndexOperation.UPSERT
        ):
            raise SearchRebuildSinkError(
                "Sink upsert requires UPSERT."
            )

        normalized_vector = tuple(
            float(value)
            for value in vector
        )

        existing = self.documents.get(
            document.index_key
        )

        if (
            existing is not None
            and existing.inventory_version
            > document.inventory_version
        ):
            raise SearchRebuildSinkError(
                "Older rebuild document cannot replace "
                "a newer indexed version."
            )

        self.documents[
            document.index_key
        ] = document

        self.vectors[
            document.index_key
        ] = normalized_vector

        return document.index_key

    def delete(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> str:
        document.assert_tenant(
            tenant_id
        )

        if document.operation is not (
            SearchIndexOperation.DELETE
        ):
            raise SearchRebuildSinkError(
                "Sink delete requires DELETE."
            )

        if expected_version is not None:
            document.assert_version(
                expected_version
            )

        self.documents.pop(
            document.index_key,
            None,
        )

        self.vectors.pop(
            document.index_key,
            None,
        )

        return document.index_key


def _delete_projection(
    document: InventoryIndexDocument,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_id=document.inventory_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        lifecycle=document.lifecycle,
        availability=document.availability,
        name=document.name,
        inventory_version=document.inventory_version,
        index_key=document.index_key,
        operation=SearchIndexOperation.DELETE,
        payload=document.payload,
    )


@dataclass(frozen=True, slots=True)
class SearchRebuildPipeline:
    """
    Canonical search rebuild/recovery coordinator.

    Source:
        CORE-004 Inventory.

    Projection:
        CORE-005 InventoryIndexDocument.

    Runtime sink:
        existing CORE-005 indexing adapter.

    Recovery:
        immutable checkpoint + resume.

    Stale cleanup:
        executed only after complete successful source scan.

    No source-of-truth mutation occurs.
    """

    sink: SearchRebuildSink

    def __post_init__(self) -> None:
        if not hasattr(
            self.sink,
            "upsert",
        ) or not hasattr(
            self.sink,
            "delete",
        ):
            raise SearchRebuildConfigurationError(
                "sink must provide upsert and delete."
            )

    def _materialize_sources(
        self,
        inventories: Iterable[Inventory],
        *,
        tenant_id: str | None,
    ) -> tuple[
        InventoryIndexDocument,
        ...
    ]:
        documents: list[
            InventoryIndexDocument
        ] = []

        seen: set[str] = set()

        for inventory in inventories:
            if not isinstance(
                inventory,
                Inventory,
            ):
                raise SearchRebuildConfigurationError(
                    "rebuild source must contain Inventory."
                )

            if (
                tenant_id is not None
                and inventory.tenant_id
                != tenant_id
            ):
                continue

            document = build_inventory_index(
                inventory
            )

            if document.index_key in seen:
                raise SearchRebuildConflictError(
                    "Duplicate inventory identity in "
                    "rebuild source: "
                    f"{document.index_key}"
                )

            seen.add(
                document.index_key
            )
            documents.append(
                document
            )

        documents.sort(
            key=lambda document:
                document.index_key.casefold()
        )

        return tuple(documents)

    def rebuild(
        self,
        inventories: Iterable[Inventory],
        *,
        vector_provider: VectorProvider,
        tenant_id: str | None = None,
        checkpoint: SearchRebuildCheckpoint | None = None,
        existing_index_documents: Iterable[
            InventoryIndexDocument
        ] = (),
    ) -> SearchRebuildReport:
        if not callable(
            vector_provider
        ):
            raise SearchRebuildConfigurationError(
                "vector_provider must be callable."
            )

        tenant_id = _require_tenant(
            tenant_id
        )

        if checkpoint is None:
            checkpoint = SearchRebuildCheckpoint(
                run_id=str(
                    uuid.uuid4()
                )
            )
            resumed = False
        else:
            if not isinstance(
                checkpoint,
                SearchRebuildCheckpoint,
            ):
                raise SearchRebuildConfigurationError(
                    "checkpoint must be SearchRebuildCheckpoint."
                )
            resumed = True

        source_documents = (
            self._materialize_sources(
                inventories,
                tenant_id=tenant_id,
            )
        )

        completed = set(
            checkpoint.completed
        )

        indexed = 0
        skipped = 0

        current_checkpoint = checkpoint

        for document in source_documents:
            if (
                document.index_key
                in completed
            ):
                skipped += 1
                continue

            if (
                tenant_id is not None
                and document.tenant_id
                != tenant_id
            ):
                raise SearchRebuildTenantError(
                    "Materialized document crossed "
                    "the rebuild tenant boundary."
                )

            try:
                vector = vector_provider(
                    document
                )

                if vector is None:
                    raise SearchRebuildSinkError(
                        "vector_provider returned None."
                    )

                self.sink.upsert(
                    document,
                    vector,
                    tenant_id=document.tenant_id,
                )

                indexed += 1

                current_checkpoint = (
                    current_checkpoint.with_completed(
                        document.index_key
                    )
                )

                completed.add(
                    document.index_key
                )

            except SearchRebuildFailure:
                raise

            except Exception as exc:
                raise SearchRebuildFailure(
                    (
                        "Search rebuild failed while "
                        f"processing {document.index_key}."
                    ),
                    current_checkpoint,
                    cause=exc,
                ) from exc

        # Existing-index cleanup is intentionally delayed
        # until the source rebuild completed successfully.
        existing_documents = tuple(
            existing_index_documents
        )

        current_keys = {
            document.index_key
            for document in source_documents
        }

        stale_documents: list[
            InventoryIndexDocument
        ] = []

        for document in existing_documents:
            if (
                not isinstance(
                    document,
                    InventoryIndexDocument,
                )
            ):
                raise SearchRebuildConfigurationError(
                    "existing_index_documents must contain "
                    "InventoryIndexDocument values."
                )

            if (
                tenant_id is not None
                and document.tenant_id
                != tenant_id
            ):
                continue

            if (
                document.index_key
                not in current_keys
            ):
                stale_documents.append(
                    document
                )

        stale_documents.sort(
            key=lambda document:
                document.index_key.casefold()
        )

        deleted_stale = 0

        try:
            for document in stale_documents:
                delete_document = (
                    _delete_projection(
                        document
                    )
                )

                self.sink.delete(
                    delete_document,
                    tenant_id=document.tenant_id,
                    expected_version=(
                        document.inventory_version
                    ),
                )

                deleted_stale += 1

        except Exception as exc:
            raise SearchRebuildFailure(
                (
                    "Search rebuild completed source "
                    "projection but failed during "
                    "stale cleanup."
                ),
                current_checkpoint,
                cause=exc,
            ) from exc

        return SearchRebuildReport(
            run_id=current_checkpoint.run_id,
            scanned=len(
                source_documents
            ),
            indexed=indexed,
            skipped=skipped,
            deleted_stale=deleted_stale,
            completed_index_keys=(
                current_checkpoint
                .completed_index_keys
            ),
            checkpoint=current_checkpoint,
            resumed=resumed,
        )


__all__ = [
    "InMemorySearchRebuildSink",
    "SearchRebuildCheckpoint",
    "SearchRebuildConfigurationError",
    "SearchRebuildConflictError",
    "SearchRebuildError",
    "SearchRebuildFailure",
    "SearchRebuildPipeline",
    "SearchRebuildReport",
    "SearchRebuildSink",
    "SearchRebuildSinkError",
    "SearchRebuildTenantError",
]
