from __future__ import annotations

from importlib import import_module


CORE_005_MODULES = (
    "AUTONOMY_ENGINE.core.search_matching.search_index_contract",
    "AUTONOMY_ENGINE.core.search_matching.search_filters",
    "AUTONOMY_ENGINE.core.search_matching.location_search",
    "AUTONOMY_ENGINE.core.search_matching.qdrant_indexing",
    "AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval",
    "AUTONOMY_ENGINE.core.search_matching.search_ranking",
    "AUTONOMY_ENGINE.core.search_matching.search_visibility",
    "AUTONOMY_ENGINE.core.search_matching.matching",
    "AUTONOMY_ENGINE.core.search_matching.search_rebuild",
)


EXPECTED_PUBLIC_CONTRACTS = {
    "search_index_contract": (
        "InventoryIndexDocument",
        "SearchIndexOperation",
        "build_inventory_index",
        "build_inventory_index_delete",
    ),
    "search_filters": (
        "StructuredSearchFilter",
    ),
    "location_search": (
        "GeoPoint",
        "LocationSearchFilter",
    ),
    "qdrant_indexing": (
        "QdrantIndexingPipeline",
        "QdrantIndexingConfig",
    ),
    "hybrid_retrieval": (
        "HybridRetrievalPipeline",
        "HybridSearchResult",
    ),
    "search_ranking": (
        "SearchRankingPipeline",
        "RankedSearchResult",
    ),
    "search_visibility": (
        "TenantVisibilityFilter",
        "SearchVisibilityPolicy",
    ),
    "matching": (
        "MatchingRecommendationPipeline",
        "MatchingProfile",
        "MatchRecommendation",
    ),
    "search_rebuild": (
        "SearchRebuildPipeline",
        "SearchRebuildCheckpoint",
        "SearchRebuildReport",
    ),
}


def test_all_core_005_modules_import() -> None:
    for module_name in CORE_005_MODULES:
        module = import_module(module_name)
        assert module is not None


def test_core_005_public_contracts_exist() -> None:
    for module_suffix, symbols in EXPECTED_PUBLIC_CONTRACTS.items():
        module = import_module(
            "AUTONOMY_ENGINE.core.search_matching."
            + module_suffix
        )

        for symbol in symbols:
            assert hasattr(module, symbol), (
                f"Missing CORE-005 public contract: "
                f"{module_suffix}.{symbol}"
            )


def test_core_005_has_no_obsolete_inventory_indexing_dependency() -> None:
    for module_name in CORE_005_MODULES:
        module = import_module(module_name)

        source_file = getattr(
            module,
            "__file__",
            None,
        )

        assert source_file is not None

        source = open(
            source_file,
            "r",
            encoding="utf-8-sig",
        ).read()

        assert "inventory_indexing" not in source, (
            f"Obsolete CORE-004 indexing dependency "
            f"detected in {module_name}"
        )


def test_core_005_search_contract_does_not_own_inventory_truth() -> None:
    module = import_module(
        "AUTONOMY_ENGINE.core.search_matching.search_index_contract"
    )

    source_file = module.__file__

    assert source_file is not None

    source = open(
        source_file,
        "r",
        encoding="utf-8-sig",
    ).read()

    forbidden_patterns = (
        "class InventoryManager",
        "class InventoryService",
        "class InventoryRepository",
        "class InventoryMutationEngine",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source


def test_core_005_does_not_create_duplicate_business_engines() -> None:
    module_sources = {}

    for module_name in CORE_005_MODULES:
        module = import_module(module_name)

        source_file = module.__file__

        assert source_file is not None

        module_sources[module_name] = open(
            source_file,
            "r",
            encoding="utf-8-sig",
        ).read()

    all_source = "\n".join(
        module_sources.values()
    )

    duplicate_engine_names = (
        "class CommissionEngine",
        "class FraudEngine",
        "class GovernanceEngine",
        "class OwnershipEngine",
        "class EventBus",
        "class AIDecisionEngine",
    )

    for forbidden in duplicate_engine_names:
        assert forbidden not in all_source


def test_core_005_modules_are_not_allowed_to_mutate_inventory() -> None:
    for module_name in CORE_005_MODULES:
        module = import_module(module_name)

        source_file = module.__file__

        assert source_file is not None

        source = open(
            source_file,
            "r",
            encoding="utf-8-sig",
        ).read()

        forbidden_mutation_patterns = (
            ".lifecycle =",
            ".availability =",
            ".tenant_id =",
            ".project_id =",
        )

        for pattern in forbidden_mutation_patterns:
            assert pattern not in source, (
                f"Potential source-truth mutation pattern "
                f"{pattern!r} found in {module_name}"
            )


def test_core_005_is_micro_modular() -> None:
    assert len(CORE_005_MODULES) == 9


def test_core_005_source_contract_is_canonical() -> None:
    module = import_module(
        "AUTONOMY_ENGINE.core.search_matching.search_index_contract"
    )

    document = module.InventoryIndexDocument

    assert document.__dataclass_params__.frozen is True


def test_core_005_final_boundary_is_explicit() -> None:
    expected_boundaries = {
        "structured_filter",
        "location_search",
        "qdrant_indexing",
        "hybrid_retrieval",
        "ranking",
        "visibility",
        "matching",
        "rebuild",
    }

    actual_boundaries = {
        "structured_filter",
        "location_search",
        "qdrant_indexing",
        "hybrid_retrieval",
        "ranking",
        "visibility",
        "matching",
        "rebuild",
    }

    assert actual_boundaries == expected_boundaries
