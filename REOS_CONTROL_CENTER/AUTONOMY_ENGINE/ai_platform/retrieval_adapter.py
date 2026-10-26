"""Tenant-scoped adapter over HOMIO's existing CORE-005 retrieval pipeline.

This module consumes the existing search/retrieval owner. It does not own a
vector database, ranking policy, canonical inventory truth, or indexing lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from ..core.search_matching.hybrid_retrieval import (
    HybridRetrievalPipeline,
    HybridSearchResult,
)
from ..core.search_matching.search_index_contract import (
    SEARCH_SOURCE_DOMAIN,
    InventoryIndexDocument,
    SearchIndexOperation,
)
from .contracts import (
    AuthorizationDecision,
    DataClassification,
    EmbeddingPurpose,
    EmbeddingRequest,
    RequestContext,
    _identifier,
    _positive_int,
    _text,
)
from .embeddings import EmbeddingService
from .errors import (
    AIPlatformError,
    AuthorizationDeniedError,
    AuthorizationServiceUnavailableError,
    EmbeddingCompatibilityError,
    InvalidRequestError,
    RequestContextMissingError,
    RetrievalResultInvalidError,
    RetrievalSourceStaleError,
    RetrievalUnavailableError,
)
from .ports import InventoryVersionPort, RetrievalAccessPort


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    request_id: str
    query_text: str
    embedding_model_id: str
    context: RequestContext | None
    limit: int = 10
    candidate_limit: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _identifier(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "query_text",
            _text(
                self.query_text,
                "query_text",
                16_000,
                allow_multiline=False,
            ),
        )
        object.__setattr__(
            self,
            "embedding_model_id",
            _identifier(self.embedding_model_id, "embedding_model_id"),
        )

        _positive_int(self.limit, "limit")

        if self.candidate_limit is not None:
            _positive_int(self.candidate_limit, "candidate_limit")
            if self.candidate_limit < self.limit:
                raise ValueError(
                    "candidate_limit must be greater than or equal to limit"
                )


@dataclass(frozen=True, slots=True)
class RetrievedSource:
    """A retrieval candidate with provenance, not canonical business truth."""

    tenant_id: str
    source_reference: str
    record_id: str
    source_version: int
    project_id: str
    inventory_code: str
    inventory_type: str
    lifecycle: str
    availability: str
    name: str
    index_key: str
    index_schema_version: int
    index_version: int
    index_fingerprint: str
    source_kind: str
    lexical_rank: int | None
    vector_rank: int | None
    lexical_score: float
    vector_score: float
    rrf_score: float

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "source_reference",
            "record_id",
            "project_id",
            "inventory_code",
            "inventory_type",
            "lifecycle",
            "availability",
            "index_key",
            "index_fingerprint",
            "source_kind",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        object.__setattr__(
            self,
            "name",
            _text(self.name, "name", 512),
        )

        for name in (
            "source_version",
            "index_schema_version",
            "index_version",
        ):
            _positive_int(getattr(self, name), name)

        for name in ("lexical_rank", "vector_rank"):
            value = getattr(self, name)
            if value is not None:
                _positive_int(value, name)

        if self.lexical_rank is None and self.vector_rank is None:
            raise ValueError(
                "a retrieved source must have a lexical or vector rank"
            )

        for name in ("lexical_score", "vector_score", "rrf_score"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be finite")
            if not isfinite(float(value)):
                raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class RetrievalResponse:
    request_id: str
    tenant_id: str
    embedding_model_id: str
    embedding_model_version: str
    embedding_dimension: int
    results: tuple[RetrievedSource, ...]

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "tenant_id",
            "embedding_model_id",
            "embedding_model_version",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        _positive_int(self.embedding_dimension, "embedding_dimension")
        values = tuple(self.results)

        if any(not isinstance(item, RetrievedSource) for item in values):
            raise TypeError("results must contain RetrievedSource values")

        object.__setattr__(self, "results", values)


class RetrievalAdapter:
    """Authorize and provenance-check candidates from the existing search owner."""

    def __init__(
        self,
        *,
        embeddings: EmbeddingService,
        retrieval_pipeline: HybridRetrievalPipeline,
        access: RetrievalAccessPort,
        source_versions: InventoryVersionPort,
        index_dimension: int,
        max_results: int = 20,
        max_candidate_limit: int = 100,
    ) -> None:
        if any(
            dependency is None
            for dependency in (
                embeddings,
                retrieval_pipeline,
                access,
                source_versions,
            )
        ):
            raise ValueError("all retrieval adapter dependencies are required")

        if not callable(getattr(retrieval_pipeline, "search", None)):
            raise TypeError("retrieval_pipeline must expose search")
        if not callable(getattr(access, "authorize_search", None)):
            raise TypeError("access must expose authorize_search")
        if not callable(getattr(access, "authorize_inventory", None)):
            raise TypeError("access must expose authorize_inventory")
        if not callable(
            getattr(source_versions, "current_inventory_version", None)
        ):
            raise TypeError(
                "source_versions must expose current_inventory_version"
            )

        _positive_int(index_dimension, "index_dimension")
        _positive_int(max_results, "max_results")
        _positive_int(max_candidate_limit, "max_candidate_limit")

        if max_results > max_candidate_limit:
            raise ValueError(
                "max_results cannot exceed max_candidate_limit"
            )

        self._embeddings = embeddings
        self._retrieval_pipeline = retrieval_pipeline
        self._access = access
        self._source_versions = source_versions
        self._index_dimension = index_dimension
        self._max_results = max_results
        self._max_candidate_limit = max_candidate_limit

    @staticmethod
    def _decision(callable_, *args, **kwargs) -> AuthorizationDecision:
        try:
            decision = callable_(*args, **kwargs)
        except Exception:
            raise AuthorizationServiceUnavailableError() from None

        if not isinstance(decision, AuthorizationDecision):
            raise AuthorizationServiceUnavailableError()

        return decision

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        if not isinstance(request, RetrievalRequest):
            raise InvalidRequestError()

        context = request.context
        if not isinstance(context, RequestContext):
            raise RequestContextMissingError()

        if request.limit > self._max_results:
            raise InvalidRequestError()

        if (
            request.candidate_limit is not None
            and request.candidate_limit > self._max_candidate_limit
        ):
            raise InvalidRequestError()

        search_decision = self._decision(
            self._access.authorize_search,
            context,
            operation="inventory.search",
        )
        if not search_decision.allowed:
            raise AuthorizationDeniedError()

        embedding = self._embeddings.embed(
            EmbeddingRequest(
                request_id=request.request_id,
                tenant_id=context.tenant_id,
                model_id=request.embedding_model_id,
                text=request.query_text,
                classification=DataClassification.CONFIDENTIAL,
                purpose=EmbeddingPurpose.QUERY,
            )
        )

        if embedding.dimension != self._index_dimension:
            raise EmbeddingCompatibilityError()

        try:
            raw_results = self._retrieval_pipeline.search(
                tenant_id=context.tenant_id,
                query_text=request.query_text,
                vector=embedding.vector,
                limit=request.limit,
                candidate_limit=request.candidate_limit,
            )
            candidates = tuple(raw_results)
        except AIPlatformError:
            raise
        except Exception:
            raise RetrievalUnavailableError() from None

        released: list[RetrievedSource] = []

        for candidate in candidates:
            if not isinstance(candidate, HybridSearchResult):
                raise RetrievalResultInvalidError()

            document = candidate.document
            if not isinstance(document, InventoryIndexDocument):
                raise RetrievalResultInvalidError()

            if (
                candidate.tenant_id != context.tenant_id
                or document.tenant_id != context.tenant_id
            ):
                raise RetrievalResultInvalidError()

            if document.source_reference != SEARCH_SOURCE_DOMAIN:
                raise RetrievalResultInvalidError()

            if document.operation is not SearchIndexOperation.UPSERT:
                raise RetrievalResultInvalidError()

            if (
                candidate.lexical_rank is None
                and candidate.vector_rank is None
            ):
                raise RetrievalResultInvalidError()

            inventory_decision = self._decision(
                self._access.authorize_inventory,
                context,
                inventory_id=document.inventory_id,
            )
            if not inventory_decision.allowed:
                continue

            try:
                current_version = (
                    self._source_versions.current_inventory_version(
                        tenant_id=context.tenant_id,
                        inventory_id=document.inventory_id,
                    )
                )
            except Exception:
                raise RetrievalUnavailableError() from None

            if current_version is None:
                raise RetrievalSourceStaleError()

            if (
                isinstance(current_version, bool)
                or not isinstance(current_version, int)
                or current_version < 1
            ):
                raise RetrievalResultInvalidError()

            if current_version != document.inventory_version:
                raise RetrievalSourceStaleError()

            try:
                released.append(
                    RetrievedSource(
                        tenant_id=document.tenant_id,
                        source_reference=document.source_reference,
                        record_id=document.inventory_id,
                        source_version=document.inventory_version,
                        project_id=document.project_id,
                        inventory_code=document.inventory_code,
                        inventory_type=document.inventory_type,
                        lifecycle=document.lifecycle,
                        availability=document.availability,
                        name=document.name,
                        index_key=document.index_key,
                        index_schema_version=document.schema_version,
                        index_version=document.index_version,
                        index_fingerprint=document.index_fingerprint,
                        source_kind=candidate.source,
                        lexical_rank=candidate.lexical_rank,
                        vector_rank=candidate.vector_rank,
                        lexical_score=candidate.lexical_score,
                        vector_score=candidate.vector_score,
                        rrf_score=candidate.rrf_score,
                    )
                )
            except (TypeError, ValueError):
                raise RetrievalResultInvalidError() from None

        return RetrievalResponse(
            request_id=request.request_id,
            tenant_id=context.tenant_id,
            embedding_model_id=embedding.model_id,
            embedding_model_version=embedding.model_version,
            embedding_dimension=embedding.dimension,
            results=tuple(released),
        )


__all__ = [
    "RetrievalAdapter",
    "RetrievalRequest",
    "RetrievalResponse",
    "RetrievedSource",
]
