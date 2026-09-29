"""
CORE-005 hardening — deterministic reproducibility regression.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .acrl_integration import ACRLIntegrationContract
from .search_domain import (
    SearchRequest,
    SearchTenantContext,
)
from .search_index_contract import (
    EXPECTED_INDEX_FINGERPRINT,
    InventoryIndexDocument,
    SearchIndexOperation,
)
from .search_observability import (
    SearchEvidence,
    SearchIndexHealthEvidence,
    SearchVersionEvidence,
    build_search_correlation,
)
from .search_ranking import (
    RANKING_VERSION,
    RankingCandidate,
    SearchRankingPipeline,
)


def make_document(
    *,
    index_key: str,
    tenant_id: str = "tenant-a",
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-001",
        inventory_id=index_key,
        inventory_code=index_key,
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name="Premium Apartment",
        inventory_version=1,
        index_key=index_key,
        operation=SearchIndexOperation.UPSERT,
    )


def test_ranking_fingerprint_is_independent_of_input_permutation() -> None:
    first_candidate = RankingCandidate(
        document=make_document(
            index_key="tenant-a:inv-001"
        ),
        retrieval_score=2.0,
        lexical_score=1.0,
        vector_score=0.5,
    )

    second_candidate = RankingCandidate(
        document=make_document(
            index_key="tenant-a:inv-002"
        ),
        retrieval_score=1.0,
        lexical_score=2.0,
        vector_score=0.5,
    )

    pipeline = SearchRankingPipeline()

    first = pipeline.rank(
        (
            first_candidate,
            second_candidate,
        )
    )

    second = pipeline.rank(
        (
            second_candidate,
            first_candidate,
        )
    )

    assert first == second

    assert (
        pipeline.reproducibility_fingerprint(first)
        == pipeline.reproducibility_fingerprint(second)
    )


def test_search_request_identity_is_stable_after_reconstruction() -> None:
    request_a = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a",
            actor_id="actor-001",
            roles=("broker",),
            capabilities=("search:read",),
        ),
        query="Premium Apartment",
    )

    request_b = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a",
            actor_id="actor-001",
            roles=("broker",),
            capabilities=("search:read",),
        ),
        query="  premium   apartment  ",
    )

    assert request_a.identity == request_b.identity

    assert (
        request_a.to_identity_payload()
        == request_b.to_identity_payload()
    )


def test_observability_fingerprint_is_stable_with_fixed_timestamp() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        )
    )

    correlation = build_search_correlation(
        request,
        "corr-core005-001",
    )

    timestamp = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    def build() -> SearchEvidence:
        return SearchEvidence(
            correlation=correlation,
            versions=SearchVersionEvidence(
                source_version=7,
                projection_version=7,
                ranking_version=RANKING_VERSION,
            ),
            index_health=SearchIndexHealthEvidence(
                status="HEALTHY",
                indexed_documents=10,
                stale_documents=0,
                failed_documents=0,
                schema_version=1,
                index_version=1,
                index_fingerprint=EXPECTED_INDEX_FINGERPRINT,
            ),
            result_count=10,
            generated_at=timestamp,
        )

    first = build()
    second = build()

    assert first.to_dict() == second.to_dict()

    assert (
        first.reproducibility_fingerprint()
        == second.reproducibility_fingerprint()
    )


def test_acrl_manifest_fingerprint_is_stable() -> None:
    contract = ACRLIntegrationContract()

    first = contract.discover()
    second = contract.discover()

    assert first.to_dict() == second.to_dict()
    assert first.fingerprint() == second.fingerprint()


def test_index_contract_fingerprint_is_stable_across_calls() -> None:
    from .search_index_contract import (
        calculate_index_fingerprint,
    )

    first = calculate_index_fingerprint()
    second = calculate_index_fingerprint()

    assert (
        first
        == second
        == EXPECTED_INDEX_FINGERPRINT
    )
