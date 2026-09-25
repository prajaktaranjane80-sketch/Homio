
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

from qdrant_client import QdrantClient, models

from .inventory_indexing import InventoryIndexDocument


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


class HybridRetrievalError(ValueError):
    """Base error for hybrid retrieval."""


class HybridTenantError(HybridRetrievalError):
    """Raised when tenant scope is missing or invalid."""


class HybridQueryError(HybridRetrievalError):
    """Raised when the hybrid query is invalid."""


def _validate_tenant(tenant_id: str) -> str:
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise HybridTenantError(
            "tenant_id must be a non-empty string."
        )
    return tenant_id.strip()


def _validate_query_text(query_text: str) -> str:
    if not isinstance(query_text, str) or not query_text.strip():
        raise HybridQueryError(
            "query_text must be a non-empty string."
        )
    return query_text.strip()


def _validate_limit(limit: int) -> int:
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
    ):
        raise HybridQueryError(
            "limit must be a positive integer."
        )
    return limit


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        token.casefold()
        for token in _TOKEN_PATTERN.findall(value)
    )


def _document_text(
    document: InventoryIndexDocument,
) -> str:
    return " ".join(
        (
            document.name,
            document.inventory_code,
            document.inventory_type,
            document.lifecycle,
            document.availability,
        )
    )


def _lexical_rank(
    documents: Iterable[InventoryIndexDocument],
    *,
    tenant_id: str,
    query_text: str,
) -> list[InventoryIndexDocument]:
    query_tokens = set(_tokens(query_text))

    if not query_tokens:
        return []

    scored = []

    for document in documents:
        if document.tenant_id != tenant_id:
            continue

        document_text = _document_text(document)
        document_tokens = set(_tokens(document_text))

        overlap = sum(
            1
            for token in query_tokens
            if token in document_tokens
        )

        if overlap == 0:
            continue

        exact_phrase = (
            query_text.casefold()
            in document_text.casefold()
        )

        scored.append(
            (
                1 if exact_phrase else 0,
                overlap,
                document.index_key.casefold(),
                document,
            )
        )

    scored.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            item[2],
        )
    )

    return [
        item[3]
        for item in scored
    ]


@dataclass(frozen=True)
class HybridSearchResult:
    document: InventoryIndexDocument
    rrf_score: float
    lexical_rank: int | None
    vector_rank: int | None

    @property
    def inventory_id(self) -> str:
        return self.document.inventory_id

    @property
    def inventory_code(self) -> str:
        return self.document.inventory_code

    @property
    def tenant_id(self) -> str:
        return self.document.tenant_id

    @property
    def index_key(self) -> str:
        return self.document.index_key


@dataclass(frozen=True)
class HybridRetrievalPipeline:
    """
    Hybrid lexical/vector retrieval.

    Retrieval sources:
    - deterministic lexical candidate retrieval
    - Qdrant dense-vector retrieval

    Fusion:
    - Reciprocal Rank Fusion (RRF)

    Ranking/reranking policy belongs to CORE-005-T05.
    """

    client: QdrantClient
    collection_name: str
    lexical_documents: tuple[InventoryIndexDocument, ...]
    rrf_k: int = 60

    def __post_init__(self) -> None:
        if (
            not isinstance(self.collection_name, str)
            or not self.collection_name.strip()
        ):
            raise HybridRetrievalError(
                "collection_name must be a non-empty string."
            )

        if (
            isinstance(self.rrf_k, bool)
            or not isinstance(self.rrf_k, int)
            or self.rrf_k < 1
        ):
            raise HybridRetrievalError(
                "rrf_k must be a positive integer."
            )

    def _vector_candidates(
        self,
        vector: Sequence[float],
        *,
        tenant_id: str,
        candidate_limit: int,
    ):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=list(vector),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(
                            value=tenant_id
                        ),
                    )
                ]
            ),
            limit=candidate_limit,
            with_payload=True,
        )

        return response.points

    def search(
        self,
        *,
        tenant_id: str,
        query_text: str,
        vector: Sequence[float],
        limit: int,
        candidate_limit: int | None = None,
    ) -> tuple[HybridSearchResult, ...]:
        tenant_id = _validate_tenant(tenant_id)
        query_text = _validate_query_text(query_text)
        limit = _validate_limit(limit)

        if candidate_limit is None:
            candidate_limit = max(limit * 3, limit)

        candidate_limit = _validate_limit(
            candidate_limit
        )

        lexical_documents = _lexical_rank(
            self.lexical_documents,
            tenant_id=tenant_id,
            query_text=query_text,
        )[:candidate_limit]

        vector_points = self._vector_candidates(
            vector,
            tenant_id=tenant_id,
            candidate_limit=candidate_limit,
        )

        lexical_by_key = {
            document.index_key: (
                rank,
                document,
            )
            for rank, document in enumerate(
                lexical_documents,
                start=1,
            )
        }

        vector_by_key = {
            str(point.payload["index_key"]): (
                rank,
                point,
            )
            for rank, point in enumerate(
                vector_points,
                start=1,
            )
            if point.payload
            and point.payload.get("index_key")
        }

        documents_by_key = {
            document.index_key: document
            for document in self.lexical_documents
            if document.tenant_id == tenant_id
        }

        candidate_keys = (
            set(lexical_by_key)
            | set(vector_by_key)
        )

        results = []

        for index_key in candidate_keys:
            lexical_entry = lexical_by_key.get(
                index_key
            )
            vector_entry = vector_by_key.get(
                index_key
            )

            document = documents_by_key.get(
                index_key
            )

            if document is None:
                continue

            rrf_score = 0.0

            if lexical_entry is not None:
                rrf_score += 1.0 / (
                    self.rrf_k + lexical_entry[0]
                )

            if vector_entry is not None:
                rrf_score += 1.0 / (
                    self.rrf_k + vector_entry[0]
                )

            results.append(
                HybridSearchResult(
                    document=document,
                    rrf_score=rrf_score,
                    lexical_rank=(
                        lexical_entry[0]
                        if lexical_entry is not None
                        else None
                    ),
                    vector_rank=(
                        vector_entry[0]
                        if vector_entry is not None
                        else None
                    ),
                )
            )

        results.sort(
            key=lambda result: (
                -result.rrf_score,
                result.index_key.casefold(),
            )
        )

        return tuple(
            results[:limit]
        )


__all__ = [
    "HybridRetrievalError",
    "HybridQueryError",
    "HybridSearchResult",
    "HybridTenantError",
    "HybridRetrievalPipeline",
]
