"""
CORE-005 / Point 13 — Contract + Adversarial Regression.

This is the final CORE-005 architectural regression layer.

It verifies the 13-point structure without introducing
another business/search engine.
"""

from __future__ import annotations

import inspect

import pytest

from .acrl_integration import (
    ACRLIntegrationContract,
    ACRLReconstructionManifest,
)
from .matching import (
    MatchingProfile,
    MatchingRecommendationPipeline,
)
from .projection_sync import (
    ProjectionOperation,
    SearchProjectionSynchronizer,
)
from .reos_integration import (
    REOSIntegrationContract,
    REOSIntegrationDecision,
    REOSVerificationEvidence,
)
from .runtime_adapter import (
    BackendIndependentSearchRuntime,
    RuntimeAdapterRegistry,
    RuntimeBackendIdentity,
)
from .search_consistency import (
    ConsistencyEvent,
    ConsistencyStatus,
    SearchConsistencyTracker,
)
from .search_domain import (
    SearchPagination,
    SearchRequest,
    SearchTenantContext,
)
from .search_execution import (
    SearchExecutionCandidate,
)
from .search_filters import (
    StructuredSearchFilter,
)
from .search_index_contract import (
    EXPECTED_INDEX_FINGERPRINT,
    SEARCH_INDEXED_FIELDS,
    SEARCH_INDEX_VERSION,
    SEARCH_SCHEMA_VERSION,
    InventoryIndexDocument,
    SearchIndexOperation,
    calculate_index_fingerprint,
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
from .search_security import (
    SearchAuthorizationContext,
    SearchSecurityBoundary,
    SearchSecurityPolicy,
)
from .search_visibility import (
    SearchVisibilityPolicy,
    TenantVisibilityFilter,
)


CORE_005_MODULES = (
    "search_domain",
    "search_index_contract",
    "search_filters",
    "location_search",
    "qdrant_indexing",
    "hybrid_retrieval",
    "search_execution",
    "projection_sync",
    "search_ranking",
    "search_visibility",
    "search_security",
    "matching",
    "search_consistency",
    "search_observability",
    "reos_integration",
    "acrl_integration",
    "runtime_adapter",
    "search_rebuild",
)


def make_document(
    tenant_id: str = "tenant-a",
    index_key: str = "inv-001",
    version: int = 1,
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
        inventory_version=version,
        index_key=index_key,
        schema_version=SEARCH_SCHEMA_VERSION,
        index_version=SEARCH_INDEX_VERSION,
        index_fingerprint=EXPECTED_INDEX_FINGERPRINT,
        operation=SearchIndexOperation.UPSERT,
        payload={
            "public_label": "Premium",
            "private_key": "SHOULD_NOT_LEAK",
        },
    )


def test_core005_modules_have_no_obvious_duplicate_business_engines():
    forbidden = (
        "class CommissionEngine",
        "class FraudEngine",
        "class GovernanceEngine",
        "class OwnershipEngine",
        "class EventBus",
        "class AIDecisionEngine",
    )

    from pathlib import Path

    root = Path(__file__).resolve().parent

    for module_name in CORE_005_MODULES:
        path = root / f"{module_name}.py"

        if not path.exists():
            continue

        source = path.read_text(
            encoding="utf-8-sig"
        )

        for marker in forbidden:
            assert marker not in source


def test_index_fingerprint_is_deterministic():
    first = calculate_index_fingerprint()
    second = calculate_index_fingerprint()

    assert first == second
    assert first == EXPECTED_INDEX_FINGERPRINT
    assert len(first) == 64


def test_index_schema_contract_is_explicit():
    assert SEARCH_SCHEMA_VERSION >= 1
    assert SEARCH_INDEX_VERSION >= 1
    assert SEARCH_INDEXED_FIELDS
    assert len(
        SEARCH_INDEXED_FIELDS
    ) == len(
        set(SEARCH_INDEXED_FIELDS)
    )


def test_search_domain_has_tenant_boundary():
    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        ),
        filters=StructuredSearchFilter(
            tenant_id="tenant-a"
        ),
        pagination=SearchPagination(
            page=1,
            page_size=20,
        ),
    )

    assert (
        request.tenant.tenant_id
        == "tenant-a"
    )


def test_security_blocks_cross_tenant_result():
    security = SearchSecurityBoundary()

    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    with pytest.raises(Exception):
        security.enforce_tenant_result_boundary(
            context,
            (
                make_document(
                    tenant_id="tenant-b"
                ),
            ),
        )


def test_security_removes_sensitive_payload_fields():
    security = SearchSecurityBoundary(
        policy=SearchSecurityPolicy(
            blocked_payload_fields=frozenset(
                {
                    "private_key",
                }
            )
        )
    )

    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    result = security.enforce_tenant_result_boundary(
        context,
        (make_document(),),
    )

    assert (
        "private_key"
        not in result[0].payload
    )


def test_visibility_preserves_tenant_boundary():
    visibility = TenantVisibilityFilter(
        tenant_id="tenant-a",
        policy=SearchVisibilityPolicy(),
    )

    from .search_ranking import RankedSearchResult
    from .search_ranking import RankingExplanation

    ranking = RankedSearchResult(
        document=make_document(),
        score=1.0,
        rank=1,
        explanation=RankingExplanation(
            features=(),
            ranking_version=RANKING_VERSION,
        ),
    )

    assert visibility.is_visible(
        ranking
    )


def test_consistency_detects_duplicate_and_out_of_order():
    tracker = SearchConsistencyTracker()

    first = ConsistencyEvent(
        event_id="event-1",
        tenant_id="tenant-a",
        index_key="inv-001",
        source_version=2,
    )

    assert tracker.observe_event(
        first
    ) is ConsistencyStatus.CURRENT

    duplicate = tracker.observe_event(
        first
    )

    assert duplicate is ConsistencyStatus.DUPLICATE

    older = ConsistencyEvent(
        event_id="event-0",
        tenant_id="tenant-a",
        index_key="inv-001",
        source_version=1,
    )

    assert tracker.observe_event(
        older
    ) is ConsistencyStatus.OUT_OF_ORDER


def test_ranking_is_reproducible():
    pipeline = SearchRankingPipeline()

    candidate = RankingCandidate(
        document=make_document(),
        retrieval_score=2.0,
        lexical_score=1.0,
        vector_score=0.5,
    )

    first = pipeline.rank(
        (candidate,)
    )

    second = pipeline.rank(
        (candidate,)
    )

    assert first == second

    assert (
        pipeline.reproducibility_fingerprint(
            first
        )
        == pipeline.reproducibility_fingerprint(
            second
        )
    )


def test_matching_is_tenant_safe():
    pipeline = MatchingRecommendationPipeline()

    profile = MatchingProfile(
        tenant_id="tenant-a"
    )

    with pytest.raises(Exception):
        pipeline.match(
            profile,
            (
                make_document(
                    tenant_id="tenant-b"
                ),
            ),
        )


def test_observability_contains_version_evidence():
    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        )
    )

    correlation = build_search_correlation(
        request,
        "corr-001",
    )

    evidence = SearchEvidence(
        correlation=correlation,
        versions=SearchVersionEvidence(
            source_version=1,
            projection_version=1,
            ranking_version=RANKING_VERSION,
        ),
        index_health=SearchIndexHealthEvidence(
            status="HEALTHY",
            indexed_documents=1,
            stale_documents=0,
            failed_documents=0,
            schema_version=SEARCH_SCHEMA_VERSION,
            index_version=SEARCH_INDEX_VERSION,
            index_fingerprint=EXPECTED_INDEX_FINGERPRINT,
        ),
        result_count=1,
    )

    assert evidence.is_reproducible
    assert evidence.reproducibility_fingerprint()


def test_reos_contract_is_read_only():
    contract = REOSIntegrationContract()

    report = contract.verify_compatibility(
        REOSVerificationEvidence(
            component="CORE-005",
            verification_id="core005-final",
            verified=True,
            test_reference="test_core005_regression.py",
        )
    )

    assert (
        report.decision
        is REOSIntegrationDecision.COMPATIBLE
    )

    assert (
        report.profile.project_state_mutation_allowed
        is False
    )

    assert (
        report.profile.gate_approval_allowed
        is False
    )


def test_acrl_manifest_is_reconstructable():
    contract = ACRLIntegrationContract()

    manifest = contract.discover()

    assert isinstance(
        manifest,
        ACRLReconstructionManifest,
    )

    assert (
        "CORE-004.Inventory"
        in {
            dependency.component
            for dependency
            in manifest.dependencies
        }
    )

    assert manifest.reconstruction_steps


def test_acrl_detects_ranking_drift():
    contract = ACRLIntegrationContract()

    report = contract.verify_runtime(
        schema_version=SEARCH_SCHEMA_VERSION,
        index_version=SEARCH_INDEX_VERSION,
        index_fingerprint=EXPECTED_INDEX_FINGERPRINT,
        ranking_version=RANKING_VERSION + 1,
    )

    assert report.drift_detected
    assert "ranking_version" in (
        report.differences
    )


def test_projection_sync_rebuild_is_derived_only():
    synchronizer = SearchProjectionSynchronizer()

    documents = synchronizer.rebuild_documents(
        ()
    )

    assert documents == ()


def test_execution_candidate_accepts_canonical_document():
    candidate = SearchExecutionCandidate(
        document=make_document(),
        score=1.0,
    )

    assert candidate.document.index_key == "inv-001"


def test_runtime_registry_has_explicit_adapter_boundary():
    class FakeBackend:
        @property
        def identity(self):
            return RuntimeBackendIdentity(
                backend_name="FAKE",
                adapter_name="FakeBackend",
                adapter_version="1",
                capabilities=frozenset(
                    {"SEARCH"}
                ),
            )

        def search(
            self,
            request,
            *,
            limit,
        ):
            return ()

    class FakeIndex:
        @property
        def identity(self):
            return RuntimeBackendIdentity(
                backend_name="FAKE",
                adapter_name="FakeIndex",
                adapter_version="1",
                capabilities=frozenset(
                    {"UPSERT"}
                ),
            )

    class FakeRebuild:
        def rebuild(
            self,
            documents,
        ):
            return ()

    registry = RuntimeAdapterRegistry(
        backend=FakeBackend(),
        index=FakeIndex(),
        rebuild=FakeRebuild(),
    )

    runtime = BackendIndependentSearchRuntime(
        adapters=registry
    )

    assert (
        runtime.backend_identity().backend_name
        == "FAKE"
    )

    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        )
    )

    assert runtime.search(
        request,
        limit=10,
    ) == ()


def test_projection_modules_do_not_write_control_center_state():
    from pathlib import Path

    root = Path(__file__).resolve().parent

    protected_markers = (
        "state.json",
        "save_state(",
        "materialize_current_gate(",
    )

    inspected = (
        "projection_sync.py",
        "search_observability.py",
        "reos_integration.py",
        "acrl_integration.py",
        "runtime_adapter.py",
    )

    for name in inspected:
        source = (
            root / name
        ).read_text(
            encoding="utf-8-sig"
        )

        for marker in protected_markers:
            assert marker not in source


def test_core005_public_surface_is_modular():
    from pathlib import Path

    root = Path(__file__).resolve().parent

    expected = {
        "search_domain.py",
        "search_index_contract.py",
        "search_filters.py",
        "location_search.py",
        "qdrant_indexing.py",
        "hybrid_retrieval.py",
        "search_execution.py",
        "projection_sync.py",
        "search_ranking.py",
        "search_visibility.py",
        "search_security.py",
        "matching.py",
        "search_consistency.py",
        "search_observability.py",
        "reos_integration.py",
        "acrl_integration.py",
        "runtime_adapter.py",
        "search_rebuild.py",
    }

    actual = {
        path.name
        for path in root.glob("*.py")
        if not path.name.startswith("test_")
    }

    assert expected.issubset(actual)
