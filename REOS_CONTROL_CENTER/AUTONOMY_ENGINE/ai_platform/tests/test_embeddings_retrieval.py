from __future__ import annotations

from typing import Iterable

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AuthorizationDecision,
    DataClassification,
    EmbeddingPurpose,
    EmbeddingRequest,
    ModelRoute,
    ProviderEmbeddingRequest,
    ProviderEmbeddingResponse,
    RequestContext,
)
from AUTONOMY_ENGINE.ai_platform.embeddings import EmbeddingService
from AUTONOMY_ENGINE.ai_platform.errors import (
    AuthorizationDeniedError,
    EmbeddingCompatibilityError,
    EmbeddingPolicyDeniedError,
    ProviderUnavailableError,
    RetrievalResultInvalidError,
    RetrievalSourceStaleError,
)
from AUTONOMY_ENGINE.ai_platform.model_registry import (
    ModelDefinition,
    ModelRegistry,
)
from AUTONOMY_ENGINE.ai_platform.retrieval_adapter import (
    RetrievalAdapter,
    RetrievalRequest,
)
from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridRetrievalPipeline,
    HybridSearchResult,
)
from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


class FakeEmbeddingProvider:
    def __init__(
        self,
        *,
        vector: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0),
        model_version: str = "embedding-model-v1",
    ) -> None:
        self.vector = vector
        self.model_version = model_version
        self.last_request: ProviderEmbeddingRequest | None = None

    def embed(
        self,
        request: ProviderEmbeddingRequest,
    ) -> ProviderEmbeddingResponse:
        self.last_request = request
        return ProviderEmbeddingResponse(
            model_id="embedding-model",
            model_version=self.model_version,
            vector=self.vector,
            provider_request_id="provider-call-1",
        )


class FakeEmbeddingResolver:
    def __init__(self, provider: FakeEmbeddingProvider | None) -> None:
        self.provider = provider

    def get(self, provider_id: str):
        return self.provider if provider_id == "fake-provider" else None


class FakeDataPolicy:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.requests: list[EmbeddingRequest] = []

    def allow_embedding(self, request: EmbeddingRequest) -> bool:
        self.requests.append(request)
        return self.allowed


class FakeAccess:
    def __init__(
        self,
        *,
        search_allowed: bool = True,
        denied_inventory_ids: Iterable[str] = (),
    ) -> None:
        self.search_allowed = search_allowed
        self.denied_inventory_ids = set(denied_inventory_ids)

    def authorize_search(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            self.search_allowed,
            "search-decision-1",
            "allowed" if self.search_allowed else "denied",
        )

    def authorize_inventory(
        self,
        context: RequestContext,
        *,
        inventory_id: str,
    ) -> AuthorizationDecision:
        allowed = inventory_id not in self.denied_inventory_ids
        return AuthorizationDecision(
            allowed,
            "inventory-decision-1",
            "allowed" if allowed else "denied",
        )


class FakeVersionPort:
    def __init__(
        self,
        versions: dict[tuple[str, str], int] | None = None,
    ) -> None:
        self.versions = versions or {}

    def current_inventory_version(
        self,
        *,
        tenant_id: str,
        inventory_id: str,
    ) -> int | None:
        return self.versions.get((tenant_id, inventory_id))


class FixedPipeline:
    """A controlled retrieval result source for malformed-result tests."""

    def __init__(self, results) -> None:
        self.results = results

    def search(self, **kwargs):
        return self.results


def make_embedding_service(
    *,
    provider: FakeEmbeddingProvider | None = None,
    policy: FakeDataPolicy | None = None,
    dimension: int | None = 4,
) -> tuple[EmbeddingService, FakeEmbeddingProvider, FakeDataPolicy]:
    selected_provider = provider or FakeEmbeddingProvider()
    selected_policy = policy or FakeDataPolicy()

    definition = ModelDefinition(
        route=ModelRoute(
            provider_id="fake-provider",
            model_id="embedding-model",
            max_input_chars=16_000,
            max_output_tokens=1,
        ),
        provider_version="fake-provider-v1",
        model_version="embedding-model-v1",
        capabilities=("embeddings",),
        embedding_dimension=dimension,
    )

    registry = ModelRegistry(
        (definition,),
        allowed_provider_ids=("fake-provider",),
    )

    service = EmbeddingService(
        model_registry=registry,
        provider_resolver=FakeEmbeddingResolver(selected_provider),
        data_policy=selected_policy,
    )
    return service, selected_provider, selected_policy


def make_embedding_request(
    *,
    purpose: EmbeddingPurpose = EmbeddingPurpose.QUERY,
    classification: DataClassification = DataClassification.CONFIDENTIAL,
) -> EmbeddingRequest:
    if purpose is EmbeddingPurpose.DOCUMENT:
        return EmbeddingRequest(
            request_id="request-1",
            tenant_id="tenant-1",
            model_id="embedding-model",
            text="Premium two bedroom apartment",
            classification=classification,
            purpose=purpose,
            source_reference="CORE-004.Inventory",
            record_id="inventory-1",
            source_version=1,
        )

    return EmbeddingRequest(
        request_id="request-1",
        tenant_id="tenant-1",
        model_id="embedding-model",
        text="Premium two bedroom apartment",
        classification=classification,
        purpose=purpose,
    )


def make_document(
    *,
    tenant_id: str,
    inventory_id: str,
    name: str,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-1",
        inventory_id=inventory_id,
        inventory_code=inventory_id.upper(),
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name=name,
        inventory_version=1,
        index_key=f"{tenant_id}:{inventory_id}",
        operation=SearchIndexOperation.UPSERT,
    )


def make_context() -> RequestContext:
    return RequestContext(
        principal_id="user-1",
        tenant_id="tenant-1",
        authentication_context_ref="auth-context-1",
        correlation_id="trace-1",
    )


def make_retrieval_adapter(
    *,
    documents: tuple[InventoryIndexDocument, ...] | None = None,
    versions: dict[tuple[str, str], int] | None = None,
    denied_inventory_ids: Iterable[str] = (),
    search_allowed: bool = True,
    pipeline_override=None,
    index_dimension: int = 4,
) -> tuple[RetrievalAdapter, FakeEmbeddingProvider, FakeDataPolicy]:
    selected_documents = documents or (
        make_document(
            tenant_id="tenant-1",
            inventory_id="inventory-1",
            name="Premium two bedroom apartment",
        ),
        make_document(
            tenant_id="tenant-1",
            inventory_id="inventory-2",
            name="Compact office",
        ),
        make_document(
            tenant_id="tenant-2",
            inventory_id="inventory-3",
            name="Premium two bedroom apartment",
        ),
    )

    if pipeline_override is None:
        client = QdrantClient(":memory:")
        collection_name = "ai001_t03_retrieval"

        indexer = QdrantIndexingPipeline(
            client=client,
            config=QdrantIndexingConfig(
                collection_name=collection_name,
                vector_size=4,
            ),
        )

        for document in selected_documents:
            indexer.upsert(
                document,
                (1.0, 0.0, 0.0, 0.0),
                tenant_id=document.tenant_id,
            )

        pipeline = HybridRetrievalPipeline(
            client=client,
            collection_name=collection_name,
            lexical_documents=selected_documents,
        )
    else:
        pipeline = pipeline_override

    default_versions = {
        (document.tenant_id, document.inventory_id): document.inventory_version
        for document in selected_documents
    }
    selected_versions = default_versions if versions is None else versions

    provider = FakeEmbeddingProvider()
    policy = FakeDataPolicy()
    embeddings, _, _ = make_embedding_service(
        provider=provider,
        policy=policy,
    )

    adapter = RetrievalAdapter(
        embeddings=embeddings,
        retrieval_pipeline=pipeline,
        access=FakeAccess(
            search_allowed=search_allowed,
            denied_inventory_ids=denied_inventory_ids,
        ),
        source_versions=FakeVersionPort(selected_versions),
        index_dimension=index_dimension,
    )

    return adapter, provider, policy


def make_retrieval_request() -> RetrievalRequest:
    return RetrievalRequest(
        request_id="request-1",
        query_text="Premium two bedroom",
        embedding_model_id="embedding-model",
        context=make_context(),
        limit=10,
    )


def test_document_embedding_preserves_model_and_source_provenance() -> None:
    service, provider, _ = make_embedding_service()

    result = service.embed(
        make_embedding_request(
            purpose=EmbeddingPurpose.DOCUMENT,
            classification=DataClassification.INTERNAL,
        )
    )

    assert result.model_id == "embedding-model"
    assert result.model_version == "embedding-model-v1"
    assert result.dimension == 4
    assert result.source_reference == "CORE-004.Inventory"
    assert result.record_id == "inventory-1"
    assert result.source_version == 1
    assert provider.last_request is not None
    assert not hasattr(provider.last_request, "tenant_id")


def test_query_embedding_does_not_claim_document_identity() -> None:
    service, provider, policy = make_embedding_service()
    result = service.embed(make_embedding_request())

    assert result.purpose is EmbeddingPurpose.QUERY
    assert result.source_reference is None
    assert result.record_id is None
    assert policy.requests[0].classification is DataClassification.CONFIDENTIAL
    assert provider.last_request is not None
    assert not hasattr(provider.last_request, "tenant_id")


def test_embedding_policy_denial_happens_before_provider_call() -> None:
    provider = FakeEmbeddingProvider()
    policy = FakeDataPolicy(allowed=False)
    service, _, _ = make_embedding_service(provider=provider, policy=policy)

    with pytest.raises(EmbeddingPolicyDeniedError):
        service.embed(make_embedding_request())

    assert provider.last_request is None


def test_unregistered_embedding_provider_fails_closed() -> None:
    definition = ModelDefinition(
        route=ModelRoute("fake-provider", "embedding-model", 16_000, 1),
        provider_version="fake-provider-v1",
        model_version="embedding-model-v1",
        capabilities=("embeddings",),
        embedding_dimension=4,
    )
    service = EmbeddingService(
        model_registry=ModelRegistry(
            (definition,),
            allowed_provider_ids=("fake-provider",),
        ),
        provider_resolver=FakeEmbeddingResolver(None),
        data_policy=FakeDataPolicy(),
    )

    with pytest.raises(ProviderUnavailableError):
        service.embed(make_embedding_request())


def test_embedding_vector_dimension_mismatch_is_rejected() -> None:
    service, _, _ = make_embedding_service(
        provider=FakeEmbeddingProvider(vector=(1.0, 0.0))
    )

    with pytest.raises(EmbeddingCompatibilityError):
        service.embed(make_embedding_request())


def test_embedding_model_version_mismatch_is_rejected() -> None:
    service, _, _ = make_embedding_service(
        provider=FakeEmbeddingProvider(model_version="unapproved-version")
    )

    with pytest.raises(EmbeddingCompatibilityError):
        service.embed(make_embedding_request())


def test_registry_must_supply_embedding_dimension() -> None:
    service, _, _ = make_embedding_service(dimension=None)

    with pytest.raises(EmbeddingCompatibilityError):
        service.embed(make_embedding_request())


def test_existing_retrieval_pipeline_enforces_tenant_scope_and_provenance() -> None:
    adapter, _, _ = make_retrieval_adapter()
    response = adapter.retrieve(make_retrieval_request())

    assert response.tenant_id == "tenant-1"
    assert response.embedding_dimension == 4
    assert response.results
    assert all(item.tenant_id == "tenant-1" for item in response.results)
    assert "inventory-3" not in {
        item.record_id for item in response.results
    }
    assert all(
        item.source_reference == "CORE-004.Inventory"
        for item in response.results
    )
    assert all(item.source_version == 1 for item in response.results)


def test_retrieval_does_not_release_resource_denied_candidates() -> None:
    adapter, _, _ = make_retrieval_adapter(
        denied_inventory_ids=("inventory-1",)
    )
    response = adapter.retrieve(make_retrieval_request())

    assert "inventory-1" not in {
        item.record_id for item in response.results
    }


def test_search_authorization_denial_stops_before_embedding() -> None:
    adapter, provider, _ = make_retrieval_adapter(search_allowed=False)

    with pytest.raises(AuthorizationDeniedError):
        adapter.retrieve(make_retrieval_request())

    assert provider.last_request is None


def test_stale_source_version_is_rejected() -> None:
    document = make_document(
        tenant_id="tenant-1",
        inventory_id="inventory-1",
        name="Premium two bedroom apartment",
    )
    adapter, _, _ = make_retrieval_adapter(
        documents=(document,),
        versions={("tenant-1", "inventory-1"): 2},
    )

    with pytest.raises(RetrievalSourceStaleError):
        adapter.retrieve(make_retrieval_request())


def test_missing_canonical_source_is_rejected() -> None:
    document = make_document(
        tenant_id="tenant-1",
        inventory_id="inventory-1",
        name="Premium two bedroom apartment",
    )
    adapter, _, _ = make_retrieval_adapter(
        documents=(document,),
        versions={},
    )

    with pytest.raises(RetrievalSourceStaleError):
        adapter.retrieve(make_retrieval_request())


def test_malformed_retrieval_candidate_is_rejected() -> None:
    adapter, _, _ = make_retrieval_adapter(
        pipeline_override=FixedPipeline(("not-a-HybridSearchResult",))
    )

    with pytest.raises(RetrievalResultInvalidError):
        adapter.retrieve(make_retrieval_request())


def test_cross_tenant_candidate_is_rejected_defensively() -> None:
    foreign_document = make_document(
        tenant_id="tenant-2",
        inventory_id="inventory-foreign",
        name="Private listing",
    )
    foreign_candidate = HybridSearchResult(
        document=foreign_document,
        rrf_score=0.2,
        lexical_rank=None,
        vector_rank=1,
        lexical_score=0.0,
        vector_score=0.2,
    )
    adapter, _, _ = make_retrieval_adapter(
        pipeline_override=FixedPipeline((foreign_candidate,))
    )

    with pytest.raises(RetrievalResultInvalidError):
        adapter.retrieve(make_retrieval_request())


def test_retrieval_rejects_index_dimension_mismatch() -> None:
    adapter, _, _ = make_retrieval_adapter(index_dimension=3)

    with pytest.raises(EmbeddingCompatibilityError):
        adapter.retrieve(make_retrieval_request())
