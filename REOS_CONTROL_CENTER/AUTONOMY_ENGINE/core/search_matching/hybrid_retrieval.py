from __future__ import annotations

from dataclasses import dataclass
import re
from math import isfinite
from typing import Iterable, Mapping, Sequence

from qdrant_client import QdrantClient, models

from .search_index_contract import InventoryIndexDocument


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


class HybridRetrievalError(ValueError):
    """Base CORE-005 hybrid retrieval error."""


class HybridTenantError(HybridRetrievalError):
    """Raised when tenant scope is invalid."""


class HybridQueryError(HybridRetrievalError):
    """Raised when the query contract is invalid."""


class HybridVectorError(HybridRetrievalError):
    """Raised when the vector query is invalid."""


class HybridCandidateError(HybridRetrievalError):
    """Raised when retrieved candidates violate the contract."""


def _require_tenant(tenant_id: str) -> str:
    if not isinstance(tenant_id, str):
        raise HybridTenantError(
            "tenant_id must be a string."
        )

    normalized = tenant_id.strip()

    if not normalized:
        raise HybridTenantError(
            "tenant_id must be a non-empty string."
        )

    return normalized


def _require_query(query_text: str) -> str:
    if not isinstance(query_text, str):
        raise HybridQueryError(
            "query_text must be a string."
        )

    normalized = query_text.strip()

    if not normalized:
        raise HybridQueryError(
            "query_text must be a non-empty string."
        )

    return normalized


def _require_positive_integer(
    value: int,
    *,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise HybridQueryError(
            f"{field_name} must be a positive integer."
        )

    return value


def _validate_vector(
    vector: Sequence[float],
) -> list[float]:
    if isinstance(vector, (str, bytes)):
        raise HybridVectorError(
            "vector must be a numeric sequence."
        )

    try:
        values = list(vector)
    except TypeError as exc:
        raise HybridVectorError(
            "vector must be a numeric sequence."
        ) from exc

    if not values:
        raise HybridVectorError(
            "vector cannot be empty."
        )

    normalized: list[float] = []

    for value in values:
        if isinstance(value, bool):
            raise HybridVectorError(
                "vector values must be finite numbers."
            )

        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise HybridVectorError(
                "vector values must be finite numbers."
            ) from exc

        if not isfinite(number):
            raise HybridVectorError(
                "vector values must be finite numbers."
            )

        normalized.append(number)

    return normalized


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        token.casefold()
        for token in _TOKEN_PATTERN.findall(value)
    )


def _document_text(
    document: InventoryIndexDocument,
) -> str:
    payload_text = ""

    for key, value in document.payload.items():
        if isinstance(value, (str, int, float, bool)):
            payload_text += f" {key} {value}"

    return " ".join(
        (
            document.name,
            document.inventory_code,
            document.inventory_type,
            document.lifecycle,
            document.availability,
            payload_text,
        )
    ).strip()


@dataclass(frozen=True, slots=True)
class HybridRetrievalConfig:
    """
    Deterministic retrieval-fusion configuration.

    RRF belongs to retrieval fusion, not business ranking.
    """

    rrf_k: int = 60
    candidate_multiplier: int = 3

    def __post_init__(self) -> None:
        if (
            isinstance(self.rrf_k, bool)
            or not isinstance(self.rrf_k, int)
            or self.rrf_k < 1
        ):
            raise HybridRetrievalError(
                "rrf_k must be a positive integer."
            )

        if (
            isinstance(self.candidate_multiplier, bool)
            or not isinstance(
                self.candidate_multiplier,
                int,
            )
            or self.candidate_multiplier < 1
        ):
            raise HybridRetrievalError(
                "candidate_multiplier must be "
                "a positive integer."
            )


@dataclass(frozen=True, slots=True)
class HybridSearchResult:
    """
    Immutable fused retrieval candidate.

    Ranking policy is intentionally deferred to CORE-005 T05.
    """

    document: InventoryIndexDocument
    rrf_score: float
    lexical_rank: int | None
    vector_rank: int | None
    lexical_score: float
    vector_score: float

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

    @property
    def source(
        self,
    ) -> str:
        if (
            self.lexical_rank is not None
            and self.vector_rank is not None
        ):
            return "HYBRID"

        if self.lexical_rank is not None:
            return "LEXICAL"

        if self.vector_rank is not None:
            return "VECTOR"

        return "NONE"


def _lexical_candidates(
    documents: Iterable[InventoryIndexDocument],
    *,
    tenant_id: str,
    query_text: str,
) -> list[
    tuple[
        InventoryIndexDocument,
        float,
        bool,
    ]
]:
    query_tokens = set(_tokens(query_text))

    if not query_tokens:
        return []

    candidates: list[
        tuple[
            InventoryIndexDocument,
            float,
            bool,
        ]
    ] = []

    for document in documents:
        if document.tenant_id != tenant_id:
            continue

        text = _document_text(document)
        document_tokens = set(_tokens(text))

        overlap = query_tokens.intersection(
            document_tokens
        )

        if not overlap:
            continue

        name_tokens = set(
            _tokens(document.name)
        )
        code_tokens = set(
            _tokens(document.inventory_code)
        )

        score = float(
            len(overlap)
        )

        score += (
            2.0
            * len(
                overlap.intersection(
                    name_tokens
                )
            )
        )

        score += (
            3.0
            * len(
                overlap.intersection(
                    code_tokens
                )
            )
        )

        exact_phrase = (
            query_text.casefold()
            in text.casefold()
        )

        if exact_phrase:
            score += 5.0

        candidates.append(
            (
                document,
                score,
                exact_phrase,
            )
        )

    candidates.sort(
        key=lambda item: (
            -int(item[2]),
            -item[1],
            item[0].index_key.casefold(),
        )
    )

    return candidates


@dataclass(frozen=True, slots=True)
class HybridRetrievalPipeline:
    """
    CORE-005 retrieval boundary.

    Sources:
        1. deterministic lexical candidate retrieval
        2. Qdrant vector candidate retrieval

    Fusion:
        Reciprocal Rank Fusion.

    Not responsible for:
        ranking policy
        reranking
        visibility policy
        matching/recommendation
        business truth
    """

    client: QdrantClient
    collection_name: str
    lexical_documents: tuple[
        InventoryIndexDocument,
        ...
    ]
    config: HybridRetrievalConfig = HybridRetrievalConfig()

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.collection_name,
                str,
            )
            or not self.collection_name.strip()
        ):
            raise HybridRetrievalError(
                "collection_name must be "
                "a non-empty string."
            )

        if not isinstance(
            self.client,
            QdrantClient,
        ):
            raise HybridRetrievalError(
                "client must be QdrantClient."
            )

        for document in self.lexical_documents:
            if not isinstance(
                document,
                InventoryIndexDocument,
            ):
                raise HybridCandidateError(
                    "lexical_documents must contain "
                    "InventoryIndexDocument values."
                )

        object.__setattr__(
            self,
            "collection_name",
            self.collection_name.strip(),
        )

        object.__setattr__(
            self,
            "lexical_documents",
            tuple(self.lexical_documents),
        )

    def _vector_candidates(
        self,
        vector: Sequence[float],
        *,
        tenant_id: str,
        candidate_limit: int,
    ):
        validated_vector = _validate_vector(
            vector
        )

        try:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=validated_vector,
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
                with_vectors=False,
            )
        except Exception as exc:
            raise HybridRetrievalError(
                "Vector retrieval failed."
            ) from exc

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
        tenant_id = _require_tenant(
            tenant_id
        )

        query_text = _require_query(
            query_text
        )

        limit = _require_positive_integer(
            limit,
            field_name="limit",
        )

        if candidate_limit is None:
            candidate_limit = max(
                limit
                * self.config.candidate_multiplier,
                limit,
            )

        candidate_limit = _require_positive_integer(
            candidate_limit,
            field_name="candidate_limit",
        )

        lexical_candidates = _lexical_candidates(
            self.lexical_documents,
            tenant_id=tenant_id,
            query_text=query_text,
        )[
            :candidate_limit
        ]

        lexical_by_key: dict[
            str,
            tuple[
                int,
                float,
            ],
        ] = {}

        document_by_key: dict[
            str,
            InventoryIndexDocument,
        ] = {}

        for rank, (
            document,
            lexical_score,
            _exact_phrase,
        ) in enumerate(
            lexical_candidates,
            start=1,
        ):
            lexical_by_key[
                document.index_key
            ] = (
                rank,
                lexical_score,
            )

            document_by_key[
                document.index_key
            ] = document

        vector_points = self._vector_candidates(
            vector,
            tenant_id=tenant_id,
            candidate_limit=candidate_limit,
        )

        vector_by_key: dict[
            str,
            tuple[
                int,
                float,
            ],
        ] = {}

        for rank, point in enumerate(
            vector_points,
            start=1,
        ):
            payload = point.payload

            if not isinstance(
                payload,
                Mapping,
            ):
                continue

            payload_tenant = payload.get(
                "tenant_id"
            )

            if payload_tenant != tenant_id:
                continue

            index_key = payload.get(
                "index_key"
            )

            if not isinstance(
                index_key,
                str,
            ) or not index_key.strip():
                continue

            # A vector result is never allowed to create
            # or invent a business document.
            document = document_by_key.get(
                index_key
            )

            if document is None:
                document = next(
                    (
                        item
                        for item
                        in self.lexical_documents
                        if (
                            item.index_key
                            == index_key
                            and item.tenant_id
                            == tenant_id
                        )
                    ),
                    None,
                )

            if document is None:
                # Stale/orphaned vector candidate:
                # fail closed and never expose it.
                continue

            if document.tenant_id != tenant_id:
                continue

            vector_score = getattr(
                point,
                "score",
                0.0,
            )

            try:
                vector_score = float(
                    vector_score
                )
            except (
                TypeError,
                ValueError,
            ):
                vector_score = 0.0

            if not isfinite(
                vector_score
            ):
                vector_score = 0.0

            vector_by_key[
                index_key
            ] = (
                rank,
                vector_score,
            )

            document_by_key[
                index_key
            ] = document

        candidate_keys = (
            set(lexical_by_key)
            | set(vector_by_key)
        )

        results: list[
            HybridSearchResult
        ] = []

        for index_key in candidate_keys:
            document = document_by_key.get(
                index_key
            )

            if document is None:
                continue

            lexical_entry = lexical_by_key.get(
                index_key
            )

            vector_entry = vector_by_key.get(
                index_key
            )

            lexical_rank = (
                lexical_entry[0]
                if lexical_entry is not None
                else None
            )

            vector_rank = (
                vector_entry[0]
                if vector_entry is not None
                else None
            )

            lexical_score = (
                lexical_entry[1]
                if lexical_entry is not None
                else 0.0
            )

            vector_score = (
                vector_entry[1]
                if vector_entry is not None
                else 0.0
            )

            rrf_score = 0.0

            if lexical_rank is not None:
                rrf_score += (
                    1.0
                    / (
                        self.config.rrf_k
                        + lexical_rank
                    )
                )

            if vector_rank is not None:
                rrf_score += (
                    1.0
                    / (
                        self.config.rrf_k
                        + vector_rank
                    )
                )

            results.append(
                HybridSearchResult(
                    document=document,
                    rrf_score=rrf_score,
                    lexical_rank=lexical_rank,
                    vector_rank=vector_rank,
                    lexical_score=lexical_score,
                    vector_score=vector_score,
                )
            )

        # This is retrieval-fusion ordering only.
        # Business relevance ranking remains T05.
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
    "HybridCandidateError",
    "HybridQueryError",
    "HybridRetrievalConfig",
    "HybridRetrievalError",
    "HybridRetrievalPipeline",
    "HybridSearchResult",
    "HybridTenantError",
    "HybridVectorError",
]
