from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from .search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


class QdrantIndexingError(ValueError):
    """Base CORE-005 Qdrant indexing error."""


class QdrantConfigurationError(QdrantIndexingError):
    """Raised when Qdrant configuration is invalid."""


class QdrantVectorError(QdrantIndexingError):
    """Raised when a vector is invalid."""


class QdrantTenantViolation(QdrantIndexingError):
    """Raised when a tenant boundary is violated."""


class QdrantVersionViolation(QdrantIndexingError):
    """Raised when a stale indexing version is detected."""


class QdrantDocumentOperationError(QdrantIndexingError):
    """Raised when document operation does not match the requested action."""


def _require_tenant(tenant_id: str) -> str:
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise QdrantTenantViolation(
            "tenant_id must be a non-empty string."
        )

    return tenant_id.strip()


def deterministic_point_id(index_key: str) -> str:
    """Return one stable UUID for one canonical search index key."""

    if not isinstance(index_key, str) or not index_key.strip():
        raise QdrantIndexingError(
            "index_key must be a non-empty string."
        )

    return str(
        uuid5(
            NAMESPACE_URL,
            f"reos:qdrant:{index_key.strip()}",
        )
    )


def _validate_vector(
    vector: Sequence[float],
    *,
    expected_size: int,
) -> list[float]:
    if isinstance(vector, (str, bytes)):
        raise QdrantVectorError(
            "vector must be a numeric sequence."
        )

    try:
        values = list(vector)
    except TypeError as exc:
        raise QdrantVectorError(
            "vector must be a numeric sequence."
        ) from exc

    if len(values) != expected_size:
        raise QdrantVectorError(
            f"vector size must be {expected_size}; "
            f"received {len(values)}."
        )

    normalized: list[float] = []

    for value in values:
        if isinstance(value, bool):
            raise QdrantVectorError(
                "vector values must be finite numbers."
            )

        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise QdrantVectorError(
                "vector values must be finite numbers."
            ) from exc

        if not isfinite(number):
            raise QdrantVectorError(
                "vector values must be finite numbers."
            )

        normalized.append(number)

    return normalized


@dataclass(frozen=True, slots=True)
class QdrantIndexingConfig:
    collection_name: str = "reos_inventory_vectors"
    vector_size: int = 4
    distance: models.Distance = models.Distance.COSINE

    def __post_init__(self) -> None:
        if (
            not isinstance(self.collection_name, str)
            or not self.collection_name.strip()
        ):
            raise QdrantConfigurationError(
                "collection_name must be a non-empty string."
            )

        if (
            isinstance(self.vector_size, bool)
            or not isinstance(self.vector_size, int)
            or self.vector_size < 1
        ):
            raise QdrantConfigurationError(
                "vector_size must be a positive integer."
            )

        try:
            distance = models.Distance(self.distance)
        except (TypeError, ValueError) as exc:
            raise QdrantConfigurationError(
                "distance must be a valid Qdrant distance."
            ) from exc

        object.__setattr__(
            self,
            "collection_name",
            self.collection_name.strip(),
        )
        object.__setattr__(
            self,
            "distance",
            distance,
        )


@dataclass(frozen=True, slots=True)
class QdrantIndexingPipeline:
    """
    CORE-005 Qdrant indexing boundary.

    Owns:
    - deterministic point identity
    - vector validation
    - tenant validation
    - indexed-version protection
    - UPSERT / DELETE translation
    - thin Qdrant runtime interaction

    Does NOT own:
    - canonical inventory truth
    - lifecycle transitions
    - business ownership
    - ranking
    - matching
    - visibility policy
    - search orchestration
    """

    client: QdrantClient
    config: QdrantIndexingConfig = QdrantIndexingConfig()

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections

        if any(
            collection.name == self.config.collection_name
            for collection in collections
        ):
            return

        self.client.create_collection(
            collection_name=self.config.collection_name,
            vectors_config=models.VectorParams(
                size=self.config.vector_size,
                distance=self.config.distance,
            ),
        )

    def _existing_point(
        self,
        document: InventoryIndexDocument,
    ):
        point_id = deterministic_point_id(
            document.index_key
        )

        points = self.client.retrieve(
            collection_name=self.config.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            return None

        return points[0]

    def _assert_tenant(
        self,
        document: InventoryIndexDocument,
        tenant_id: str,
    ) -> str:
        normalized_tenant = _require_tenant(tenant_id)

        if normalized_tenant != document.tenant_id:
            raise QdrantTenantViolation(
                "Qdrant request belongs to a different tenant."
            )

        return normalized_tenant

    def _assert_expected_version(
        self,
        document: InventoryIndexDocument,
        expected_version: int | None,
    ) -> None:
        if expected_version is None:
            return

        if (
            isinstance(expected_version, bool)
            or not isinstance(expected_version, int)
            or expected_version < 1
        ):
            raise QdrantVersionViolation(
                "expected_version must be a positive integer."
            )

        if document.inventory_version != expected_version:
            raise QdrantVersionViolation(
                "Expected document version does not match "
                "inventory version."
            )

    def _assert_stored_version_allows_write(
        self,
        document: InventoryIndexDocument,
    ) -> None:
        existing = self._existing_point(document)

        if existing is None:
            return

        payload = existing.payload or {}
        stored_version = payload.get(
            "inventory_version"
        )

        if stored_version is None:
            raise QdrantVersionViolation(
                "Existing Qdrant point has no inventory_version."
            )

        if (
            isinstance(stored_version, bool)
            or not isinstance(stored_version, int)
            or stored_version < 1
        ):
            raise QdrantVersionViolation(
                "Existing Qdrant point has an invalid "
                "inventory_version."
            )

        if stored_version > document.inventory_version:
            raise QdrantVersionViolation(
                "Indexing request is older than the stored "
                "Qdrant document version."
            )

    def build_point(
        self,
        document: InventoryIndexDocument,
        vector: Sequence[float],
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> models.PointStruct:
        self._assert_tenant(
            document,
            tenant_id,
        )

        self._assert_expected_version(
            document,
            expected_version,
        )

        if document.operation is not SearchIndexOperation.UPSERT:
            raise QdrantDocumentOperationError(
                "build_point only accepts UPSERT documents."
            )

        normalized_vector = _validate_vector(
            vector,
            expected_size=self.config.vector_size,
        )

        payload = dict(document.payload)

        payload.update(
            {
                "index_key": document.index_key,
                "inventory_id": document.inventory_id,
                "tenant_id": document.tenant_id,
                "project_id": document.project_id,
                "inventory_code": document.inventory_code,
                "inventory_type": document.inventory_type,
                "lifecycle": document.lifecycle,
                "availability": document.availability,
                "inventory_version": document.inventory_version,
                "operation": document.operation.value,
            }
        )

        return models.PointStruct(
            id=deterministic_point_id(
                document.index_key
            ),
            vector=normalized_vector,
            payload=payload,
        )

    def upsert(
        self,
        document: InventoryIndexDocument,
        vector: Sequence[float],
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> str:
        self.ensure_collection()

        self._assert_tenant(
            document,
            tenant_id,
        )

        self._assert_expected_version(
            document,
            expected_version,
        )

        if document.operation is not SearchIndexOperation.UPSERT:
            raise QdrantDocumentOperationError(
                "upsert only accepts UPSERT documents."
            )

        self._assert_stored_version_allows_write(
            document
        )

        point = self.build_point(
            document,
            vector,
            tenant_id=tenant_id,
            expected_version=expected_version,
        )

        self.client.upsert(
            collection_name=self.config.collection_name,
            points=[point],
            wait=True,
        )

        return str(point.id)

    def upsert_many(
        self,
        items: Iterable[
            tuple[
                InventoryIndexDocument,
                Sequence[float],
            ]
        ],
        *,
        tenant_id: str,
    ) -> tuple[str, ...]:
        self.ensure_collection()

        materialized = list(items)

        if not materialized:
            return ()

        points: list[models.PointStruct] = []

        for document, vector in materialized:
            self._assert_tenant(
                document,
                tenant_id,
            )

            if document.operation is not SearchIndexOperation.UPSERT:
                raise QdrantDocumentOperationError(
                    "upsert_many only accepts UPSERT documents."
                )

            self._assert_stored_version_allows_write(
                document
            )

            points.append(
                self.build_point(
                    document,
                    vector,
                    tenant_id=tenant_id,
                )
            )

        self.client.upsert(
            collection_name=self.config.collection_name,
            points=points,
            wait=True,
        )

        return tuple(
            str(point.id)
            for point in points
        )

    def delete(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> str:
        self.ensure_collection()

        self._assert_tenant(
            document,
            tenant_id,
        )

        self._assert_expected_version(
            document,
            expected_version,
        )

        if document.operation is not SearchIndexOperation.DELETE:
            raise QdrantDocumentOperationError(
                "delete only accepts DELETE documents."
            )

        existing = self._existing_point(
            document
        )

        if existing is not None:
            payload = existing.payload or {}
            stored_version = payload.get(
                "inventory_version"
            )

            if (
                isinstance(stored_version, int)
                and not isinstance(stored_version, bool)
                and stored_version > document.inventory_version
            ):
                raise QdrantVersionViolation(
                    "Delete request is older than the stored "
                    "Qdrant document version."
                )

        point_id = deterministic_point_id(
            document.index_key
        )

        self.client.delete(
            collection_name=self.config.collection_name,
            points_selector=models.PointIdsList(
                points=[point_id],
            ),
            wait=True,
        )

        return point_id


__all__ = [
    "QdrantConfigurationError",
    "QdrantDocumentOperationError",
    "QdrantIndexingConfig",
    "QdrantIndexingError",
    "QdrantIndexingPipeline",
    "QdrantTenantViolation",
    "QdrantVectorError",
    "QdrantVersionViolation",
    "deterministic_point_id",
]
