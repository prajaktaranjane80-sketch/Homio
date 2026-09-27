from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.search_matching.search_rebuild import (
    InMemorySearchRebuildSink,
    SearchRebuildCheckpoint,
    SearchRebuildFailure,
    SearchRebuildPipeline,
)


def make_inventory(
    *,
    tenant_id: str = "tenant-a",
    inventory_id: str = "inventory-a",
    project_id: str = "project-a",
    property_id: str = "property-a",
    unit_id: str = "unit-a",
    name: str = "Unit A",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        developer_id="developer-a",
        project_id=project_id,
        inventory_type=InventoryType.UNIT,
        name=name,
        property_id=property_id,
        unit_id=unit_id,
        inventory_id=inventory_id,
        metadata={},
        at="2026-09-01T10:00:00+00:00",
    )


def vector_provider(
    document,
):
    return (
        1.0,
        0.0,
        0.0,
        0.0,
    )


@pytest.fixture
def pipeline():
    return SearchRebuildPipeline(
        sink=InMemorySearchRebuildSink()
    )


def test_rebuild_indexes_canonical_inventory(
    pipeline,
) -> None:
    inventory = make_inventory()

    report = pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    assert report.complete
    assert report.scanned == 1
    assert report.indexed == 1
    assert report.skipped == 0
    assert report.deleted_stale == 0


def test_rebuild_is_deterministic(
    pipeline,
) -> None:
    first = make_inventory(
        inventory_id="inventory-b",
        unit_id="unit-b",
    )
    second = make_inventory(
        inventory_id="inventory-a",
        unit_id="unit-a",
    )

    report = pipeline.rebuild(
        (first, second),
        vector_provider=vector_provider,
    )

    assert report.completed_index_keys == tuple(
        sorted(
            report.completed_index_keys
        )
    )


def test_tenant_scope_limits_source(
    pipeline,
) -> None:
    first = make_inventory(
        tenant_id="tenant-a",
        inventory_id="inventory-a",
        unit_id="unit-a",
    )

    second = make_inventory(
        tenant_id="tenant-b",
        inventory_id="inventory-b",
        unit_id="unit-b",
    )

    report = pipeline.rebuild(
        (first, second),
        vector_provider=vector_provider,
        tenant_id="tenant-a",
    )

    assert report.scanned == 1
    assert report.indexed == 1


def test_resume_skips_completed_items(
    pipeline,
) -> None:
    first = make_inventory(
        inventory_id="inventory-a",
        unit_id="unit-a",
    )

    second = make_inventory(
        inventory_id="inventory-b",
        unit_id="unit-b",
    )

    checkpoint = SearchRebuildCheckpoint(
        run_id="resume-run",
        completed_index_keys=(
            first.identity_key,
        ),
    )

    report = pipeline.rebuild(
        (first, second),
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert report.resumed
    assert report.skipped == 1
    assert report.indexed == 1
    assert len(
        report.completed_index_keys
    ) == 2


def test_failure_exposes_recovery_checkpoint(
) -> None:
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(
        sink=sink
    )

    first = make_inventory(
        inventory_id="inventory-a",
        unit_id="unit-a",
    )

    second = make_inventory(
        inventory_id="inventory-b",
        unit_id="unit-b",
    )

    calls = {"count": 0}

    def failing_provider(
        document,
    ):
        calls["count"] += 1

        if calls["count"] == 2:
            raise RuntimeError(
                "embedding unavailable"
            )

        return (
            1.0,
            0.0,
            0.0,
            0.0,
        )

    with pytest.raises(
        SearchRebuildFailure
    ) as exc_info:
        pipeline.rebuild(
            (first, second),
            vector_provider=failing_provider,
        )

    checkpoint = (
        exc_info.value.checkpoint
    )

    assert checkpoint.run_id
    assert checkpoint.completed_index_keys == (
        first.identity_key,
    )

    report = pipeline.rebuild(
        (first, second),
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert report.resumed
    assert report.indexed == 1
    assert report.skipped == 1
    assert report.complete


def test_stale_document_is_deleted_after_success(
    pipeline,
) -> None:
    stale = make_inventory(
        inventory_id="inventory-stale",
        unit_id="unit-stale",
    )

    pipeline.rebuild(
        (stale,),
        vector_provider=vector_provider,
    )

    current = make_inventory(
        inventory_id="inventory-current",
        unit_id="unit-current",
    )

    existing = tuple(
        pipeline.sink.documents.values()
    )

    report = pipeline.rebuild(
        (current,),
        vector_provider=vector_provider,
        existing_index_documents=existing,
    )

    assert report.deleted_stale == 1

    assert (
        stale.identity_key
        not in pipeline.sink.documents
    )


def test_stale_cleanup_does_not_run_when_source_rebuild_fails(
) -> None:
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(
        sink=sink
    )

    stale = make_inventory(
        inventory_id="inventory-stale",
        unit_id="unit-stale",
    )

    pipeline.rebuild(
        (stale,),
        vector_provider=vector_provider,
    )

    current = make_inventory(
        inventory_id="inventory-current",
        unit_id="unit-current",
    )

    existing = tuple(
        pipeline.sink.documents.values()
    )

    def failing_provider(
        document,
    ):
        raise RuntimeError(
            "vector runtime unavailable"
        )

    with pytest.raises(
        SearchRebuildFailure
    ):
        pipeline.rebuild(
            (current,),
            vector_provider=failing_provider,
            existing_index_documents=existing,
        )

    assert (
        stale.identity_key
        in sink.documents
    )


def test_rebuild_does_not_mutate_inventory(
    pipeline,
) -> None:
    inventory = make_inventory()

    before = inventory.to_dict()

    pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    assert inventory.to_dict() == before


def test_vector_is_stored_as_immutable_tuple(
    pipeline,
) -> None:
    inventory = make_inventory()

    pipeline.rebuild(
        (inventory,),
        vector_provider=lambda document: [
            1,
            2,
            3,
            4,
        ],
    )

    assert (
        pipeline.sink.vectors[
            inventory.identity_key
        ]
        == (
            1.0,
            2.0,
            3.0,
            4.0,
        )
    )


def test_empty_source_is_safe(
    pipeline,
) -> None:
    report = pipeline.rebuild(
        (),
        vector_provider=vector_provider,
    )

    assert report.complete
    assert report.scanned == 0
    assert report.indexed == 0
    assert report.skipped == 0


def test_cross_tenant_stale_document_is_preserved(
    pipeline,
) -> None:
    foreign = make_inventory(
        tenant_id="tenant-b",
        inventory_id="foreign",
        unit_id="foreign",
    )

    pipeline.rebuild(
        (foreign,),
        vector_provider=vector_provider,
    )

    existing = tuple(
        pipeline.sink.documents.values()
    )

    pipeline.rebuild(
        (),
        vector_provider=vector_provider,
        tenant_id="tenant-a",
        existing_index_documents=existing,
    )

    assert (
        foreign.identity_key
        in pipeline.sink.documents
    )


def test_duplicate_source_identity_is_rejected(
    pipeline,
) -> None:
    inventory = make_inventory()

    with pytest.raises(Exception):
        pipeline.rebuild(
            (
                inventory,
                inventory,
            ),
            vector_provider=vector_provider,
        )


def test_resume_run_id_is_preserved(
    pipeline,
) -> None:
    checkpoint = SearchRebuildCheckpoint(
        run_id="stable-run"
    )

    report = pipeline.rebuild(
        (make_inventory(),),
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert (
        report.run_id
        == "stable-run"
    )
