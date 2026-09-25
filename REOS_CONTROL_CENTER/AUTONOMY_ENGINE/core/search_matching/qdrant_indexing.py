from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

from qdrant_client import QdrantClient, models

from .inventory_indexing import (
    InventoryIndexDocument,
    InventoryIndexOperation,
)


class QdrantIndexingError(ValueError):
    """Base error for Qdrant indexing failures."""


class QdrantVectorError(QdrantIndexingError):
    """Raised when a supplied vector is invalid."""


class QdrantTenantViolation(QdrantIndexingError):
    """Raised when tenant scope is invalid."""


class QdrantVersionViolation(QdrantIndexingError):
    """Raised when indexing version requirements are violated."""


@dataclass(frozen=True)
class QdrantIndexingConfig:
    collection_name: str = "reos_inventory_vectors"
    vector_size: int = 4
    distance: models.Distance = models.Distance.COSINE

    def __post_init__(self) -> None:
        if (
            not isinstance(self.collection_name, str)
            or not self.collection_name.strip()
        ):
            raise QdrantIndexingError(
                "collection_name must be a non-empty string."
            )

        if isinstance(self.vector_size, bool) or self.vector_size < 1:
            raise QdrantIndexingError(
                "vector_size must be >= 1."
            )

        object.__setattr__(
            self,
            "collection_name",
            self.collection_name.strip(),
        )

        object.__setattr__(
            self,
            "distance",
            models.Distance(self.distance),
        )


def deterministic_point_id(index_key: str) -> str:
    """Return one stable Qdrant UUID for one canonical inventory key."""

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


@dataclass(frozen=True)
class QdrantIndexingPipeline:
    client: QdrantClient
    config: QdrantIndexingConfig = QdrantIndexingConfig()

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections

        if any(
            item.name == self.config.collection_name
            for item in collections
        ):
            return

        self.client.create_collection(
            collection_name=self.config.collection_name,
            vectors_config=models.VectorParams(
                size=self.config.vector_size,
                distance=self.config.distance,
            ),
        )

    def build_point(
        self,
        document: InventoryIndexDocument,
        vector: Sequence[float],
        *,
        tenant_id: str,
        expected_version: int | None = None,
    ) -> models.PointStruct:
        if tenant_id != document.tenant_id:
            raise QdrantTenantViolation(
                "Qdrant indexing request belongs to a different tenant."
            )

        if expected_version is not None:
            if expected_version < 1:
                raise QdrantVersionViolation(
                    "expected_version must be >= 1."
                )

            if expected_version != document.inventory_version:
                raise QdrantVersionViolation(
                    "Qdrant indexing request targets a stale version."
                )

        if document.operation is not InventoryIndexOperation.UPSERT:
            raise QdrantIndexingError(
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
            id=deterministic_point_id(document.index_key),
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

        points = [
            self.build_point(
                document,
                vector,
                tenant_id=tenant_id,
            )
            for document, vector in items
        ]

        if not points:
            return ()

        self.client.upsert(
            collection_name=self.config.collection_name,
            points=points,
            wait=True,
        )

        return tuple(str(point.id) for point in points)

    def delete(
        self,
        document: InventoryIndexDocument,
        *,
        tenant_id: str,
    ) -> str:
        if tenant_id != document.tenant_id:
            raise QdrantTenantViolation(
                "Qdrant deletion request belongs to a different tenant."
            )

        if document.operation is not InventoryIndexOperation.DELETE:
            raise QdrantIndexingError(
                "delete only accepts DELETE documents."
            )

        self.ensure_collection()

        point_id = deterministic_point_id(document.index_key)

        self.client.delete(
            collection_name=self.config.collection_name,
            points_selector=models.PointIdsList(
                points=[point_id],
            ),
            wait=True,
        )

        return point_id


__all__ = [
    "QdrantIndexingConfig",
    "QdrantIndexingError",
    "QdrantIndexingPipeline",
    "QdrantTenantViolation",
    "QdrantVectorError",
    "QdrantVersionViolation",
    "deterministic_point_id",
]
