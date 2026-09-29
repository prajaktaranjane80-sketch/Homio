@'
from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.search_matching.matching import (
    MatchExplanation,
    MatchRecommendation,
    MatchingCandidateError,
    MatchingCriteriaError,
    MatchingProfile,
    MatchingRecommendationPipeline,
    MatchingTenantError,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
)


def make_document(
    *,
    index_key: str = "idx-001",
    tenant_id: str = "tenant-a",
    project_id: str = "project-a",
    inventory_id: str = "inventory-001",
    inventory_code: str = "UNIT-001",
    inventory_type: str = "UNIT",
    lifecycle: str = "ACTIVE",
    availability: str = "AVAILABLE",
    name: str = "Premium Two Bedroom",
    inventory_version: int = 1,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_id=inventory_id,
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        lifecycle=lifecycle,
        availability=availability,
        name=name,
        inventory_version=inventory_version,
        index_key=index_key,
    )


@pytest.fixture
def pipeline() -> MatchingRecommendationPipeline:
    return MatchingRecommendationPipeline()


def test_basic_matching_returns_recommendation(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(tenant_id="tenant-a"),
        (make_document(),),
    )

    assert len(results) == 1
    assert isinstance(results[0], MatchRecommendation)
    assert results[0].index_key == "idx-001"
    assert results[0].tenant_id == "tenant-a"


def test_matching_is_tenant_safe(pipeline) -> None:
    with pytest.raises(MatchingTenantError):
        pipeline.match(
            MatchingProfile(tenant_id="tenant-a"),
            (
                make_document(
                    tenant_id="tenant-b",
                ),
            ),
        )


def test_required_inventory_type_is_enforced(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            required_inventory_types=("UNIT",),
        ),
        (
            make_document(
                index_key="unit",
                inventory_type="UNIT",
            ),
            make_document(
                index_key="property",
                inventory_id="inventory-002",
                inventory_code="PROPERTY-001",
                inventory_type="PROPERTY",
            ),
        ),
    )

    assert [item.index_key for item in results] == ["unit"]
    assert "required_inventory_type" in (
        results[0].explanation.hard_constraints_passed
    )


def test_required_project_is_enforced(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            required_project_ids=("project-a",),
        ),
        (
            make_document(
                index_key="project-a",
                project_id="project-a",
            ),
            make_document(
                index_key="project-b",
                inventory_id="inventory-002",
                inventory_code="UNIT-002",
                project_id="project-b",
            ),
        ),
    )

    assert [item.index_key for item in results] == ["project-a"]


def test_required_availability_is_enforced(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            required_availability=("AVAILABLE",),
        ),
        (
            make_document(
                index_key="available",
                availability="AVAILABLE",
            ),
            make_document(
                index_key="sold",
                inventory_id="inventory-002",
                inventory_code="UNIT-002",
                availability="SOLD",
            ),
        ),
    )

    assert [item.index_key for item in results] == ["available"]


def test_excluded_keyword_is_hard_block(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            excluded_keywords=("studio",),
        ),
        (
            make_document(
                index_key="good",
                name="Premium Two Bedroom",
            ),
            make_document(
                index_key="blocked",
                inventory_id="inventory-002",
                inventory_code="UNIT-002",
                name="Premium Studio",
            ),
        ),
    )

    assert [item.index_key for item in results] == ["good"]


def test_preferred_inventory_type_changes_score(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            preferred_inventory_types=("UNIT",),
        ),
        (
            make_document(
                index_key="unit",
                inventory_type="UNIT",
            ),
            make_document(
                index_key="property",
                inventory_id="inventory-002",
                inventory_code="PROPERTY-001",
                inventory_type="PROPERTY",
            ),
        ),
    )

    assert results[0].index_key == "unit"
    assert results[0].score > results[1].score
    assert "preferred_inventory_type" in (
        results[0].explanation.soft_preferences_matched
    )


def test_preferred_project_is_explainable(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            preferred_project_ids=("project-b",),
        ),
        (
            make_document(
                index_key="target",
                project_id="project-b",
            ),
            make_document(
                index_key="other",
                inventory_id="inventory-002",
                inventory_code="UNIT-002",
                project_id="project-a",
            ),
        ),
    )

    assert results[0].index_key == "target"
    assert "preferred_project" in (
        results[0].explanation.soft_preferences_matched
    )


def test_preferred_availability_is_explainable(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            preferred_availability=("RESERVED",),
        ),
        (
            make_document(
                availability="RESERVED",
            ),
        ),
    )

    assert "preferred_availability" in (
        results[0].explanation.soft_preferences_matched
    )


def test_preferred_inventory_code_is_supported(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            preferred_inventory_codes=("UNIT-777",),
        ),
        (
            make_document(
                index_key="target",
                inventory_code="UNIT-777",
            ),
            make_document(
                index_key="other",
                inventory_id="inventory-002",
                inventory_code="UNIT-001",
            ),
        ),
    )

    assert results[0].index_key == "target"
    assert "preferred_inventory_code" in (
        results[0].explanation.soft_preferences_matched
    )


def test_keyword_preference_is_supported(pipeline) -> None:
    results = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            preferred_keywords=("premium", "bedroom"),
        ),
        (
            make_document(
                index_key="premium",
                name="Premium Two Bedroom",
            ),
            make_document(
                index_key="standard",
                inventory_id="inventory-002",
                inventory_code="UNIT-002",
                name="Standard Apartment",
            ),
        ),
    )

    assert results[0].index_key == "premium"
    assert "preferred_keywords" in (
        results[0].explanation.soft_preferences_matched
    )


def test_recommendation_order_is_deterministic(pipeline) -> None:
    candidates = (
        make_document(
            index_key="idx-b",
            inventory_code="UNIT-002",
        ),
        make_document(
            index_key="idx-a",
            inventory_id="inventory-002",
            inventory_code="UNIT-003",
        ),
        make_document(
            index_key="idx-c",
            inventory_id="inventory-003",
            inventory_code="UNIT-004",
        ),
    )

    first = pipeline.match(
        MatchingProfile(tenant_id="tenant-a"),
        candidates,
    )
    second = pipeline.match(
        MatchingProfile(tenant_id="tenant-a"),
        candidates,
    )

    assert first == second
    assert [item.index_key for item in first] == [
        "idx-a",
        "idx-b",
        "idx-c",
    ]


def test_empty_candidates_are_safe(pipeline) -> None:
    assert (
        pipeline.match(
            MatchingProfile(tenant_id="tenant-a"),
            (),
        )
        == ()
    )


def test_blank_tenant_is_rejected() -> None:
    with pytest.raises(MatchingCriteriaError):
        MatchingProfile(tenant_id="   ")


def test_invalid_inventory_type_is_rejected() -> None:
    with pytest.raises(MatchingCriteriaError):
        MatchingProfile(
            tenant_id="tenant-a",
            required_inventory_types=("NOT_A_REAL_TYPE",),
        )


def test_invalid_profile_type_is_rejected(pipeline) -> None:
    with pytest.raises(MatchingCriteriaError):
        pipeline.match(
            object(),  # type: ignore[arg-type]
            (),
        )


def test_invalid_candidate_type_is_rejected(pipeline) -> None:
    with pytest.raises(MatchingCandidateError):
        pipeline.match(
            MatchingProfile(tenant_id="tenant-a"),
            (object(),),  # type: ignore[arg-type]
        )


def test_duplicate_candidate_identity_is_rejected(pipeline) -> None:
    document = make_document()

    with pytest.raises(MatchingCandidateError):
        pipeline.match(
            MatchingProfile(tenant_id="tenant-a"),
            (document, document),
        )


def test_source_documents_are_not_mutated(pipeline) -> None:
    first = make_document()
    second = make_document(
        index_key="idx-002",
        inventory_id="inventory-002",
        inventory_code="UNIT-002",
    )
    candidates = (first, second)

    before = (
        first,
        second,
    )

    pipeline.match(
        MatchingProfile(tenant_id="tenant-a"),
        candidates,
    )

    after = (
        first,
        second,
    )

    assert after == before


def test_explanation_is_transparent(pipeline) -> None:
    result = pipeline.match(
        MatchingProfile(
            tenant_id="tenant-a",
            required_inventory_types=("UNIT",),
            preferred_keywords=("premium",),
        ),
        (make_document(),),
    )[0]

    assert isinstance(result.explanation, MatchExplanation)
    payload = result.explanation.to_dict()

    assert payload["hard_constraints_passed"] == [
        "required_inventory_type"
    ]
    assert "preferred_keywords" in (
        payload["soft_preferences_matched"]
    )
    assert payload["excluded_reasons"] == []
'@ | Set-Content -Encoding UTF8 AUTONOMY_ENGINE\core\search_matching\test_matching.py
