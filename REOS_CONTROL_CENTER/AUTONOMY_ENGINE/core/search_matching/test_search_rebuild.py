from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import Inventory, InventoryType
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import (
    InventoryIndexDocument,
    InventoryIndexingHook,
)
from AUTONOMY_ENGINE.core.search_matching.search_rebuild import (
    InMemorySearchRebuildSink,
    SearchRebuildCheckpoint,
    SearchRebuildError,
    SearchRebuildPipeline,
)


def make_inventory(
    *,
    tenant_id: str = "tenant-001",
    project_id: str = "project-001",
    inventory_code: str = "UNIT-001",
    name: str = "Unit 001",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_code=inventory_code,
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name=name,
        metadata={},
        at="2026-08-30T10:00:00+00:00",
    )


def vector_provider(document: InventoryIndexDocument):
    return [1.0, 0.0, 0.0, 0.0]


@pytest.fixture
def pipeline():
    return SearchRebuildPipeline(
        sink=InMemorySearchRebuildSink(),
    )


def test_rebuild_indexes_canonical_inventory(pipeline):
    inventory = make_inventory()

    report = pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    assert report.complete
    assert report.scanned == 1
    assert report.indexed == 1
    assert report.deleted_stale == 0


def test_rebuild_is_deterministic(pipeline):
    inventories = (
        make_inventory(inventory_code="UNIT-002"),
        make_inventory(inventory_code="UNIT-001"),
    )

    report = pipeline.rebuild(
        inventories,
        vector_provider=vector_provider,
    )

    assert report.completed_index_keys == tuple(
        sorted(report.completed_index_keys)
    )


def test_tenant_scope_limits_rebuild(pipeline):
    inventories = (
        make_inventory(
            tenant_id="tenant-001",
            inventory_code="UNIT-001",
        ),
        make_inventory(
            tenant_id="tenant-002",
            inventory_code="UNIT-002",
        ),
    )

    report = pipeline.rebuild(
        inventories,
        vector_provider=vector_provider,
        tenant_id="tenant-001",
    )

    assert report.scanned == 1
    assert report.indexed == 1


def test_resume_skips_successfully_completed_items(pipeline):
    inventories = (
        make_inventory(inventory_code="UNIT-001"),
        make_inventory(inventory_code="UNIT-002"),
    )

    checkpoint = SearchRebuildCheckpoint(
        run_id="run-001",
        completed_index_keys=(
            "tenant-001:project-001:UNIT-001",
        ),
    )

    report = pipeline.rebuild(
        inventories,
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert report.resumed
    assert report.skipped == 1
    assert report.indexed == 1
    assert len(report.completed_index_keys) == 2


def test_failed_vector_generation_is_resumable():
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(sink=sink)

    inventories = (
        make_inventory(inventory_code="UNIT-001"),
        make_inventory(inventory_code="UNIT-002"),
    )

    calls = {"count": 0}

    def failing_provider(document):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("embedding unavailable")
        return [1.0, 0.0, 0.0, 0.0]

    with pytest.raises(SearchRebuildError) as exc_info:
        pipeline.rebuild(
            inventories,
            vector_provider=failing_provider,
            checkpoint=SearchRebuildCheckpoint(run_id="run-002"),
        )

    checkpoint = exc_info.value.args[1]

    assert checkpoint.run_id == "run-002"
    assert len(checkpoint.completed_index_keys) == 1

    report = pipeline.rebuild(
        inventories,
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert report.indexed == 1
    assert report.skipped == 1
    assert report.complete


def test_existing_stale_document_is_deleted(pipeline):
    sink = pipeline.sink

    stale_inventory = make_inventory(
        inventory_code="UNIT-999",
    )

    stale_document = InventoryIndexingHook().build_upsert(
        stale_inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    sink.upsert(
        stale_document,
        [1.0, 0.0, 0.0, 0.0],
    )

    current_inventory = make_inventory(
        inventory_code="UNIT-001",
    )

    report = pipeline.rebuild(
        (current_inventory,),
        vector_provider=vector_provider,
        existing_index_documents=(stale_document,),
    )

    assert report.deleted_stale == 1
    assert stale_document.index_key not in sink.documents


def test_stale_cleanup_is_not_run_when_rebuild_fails():
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(sink=sink)

    stale_inventory = make_inventory(
        inventory_code="UNIT-999",
    )

    stale_document = InventoryIndexingHook().build_upsert(
        stale_inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    sink.upsert(
        stale_document,
        [1.0, 0.0, 0.0, 0.0],
    )

    def failing_provider(document):
        raise RuntimeError("vector service unavailable")

    with pytest.raises(SearchRebuildError):
        pipeline.rebuild(
            (make_inventory(inventory_code="UNIT-001"),),
            vector_provider=failing_provider,
            existing_index_documents=(stale_document,),
        )

    assert stale_document.index_key in sink.documents


def test_rebuild_does_not_mutate_inventory(pipeline):
    inventory = make_inventory()
    before = inventory.to_dict()

    pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    assert inventory.to_dict() == before


def test_vector_is_persisted_as_immutable_tuple(pipeline):
    sink = pipeline.sink
    inventory = make_inventory()

    pipeline.rebuild(
        (inventory,),
        vector_provider=lambda document: [1, 2, 3, 4],
    )

    key = inventory.identity_key

    assert sink.vectors[key] == (1.0, 2.0, 3.0, 4.0)


def test_empty_vector_is_rejected(pipeline):
    with pytest.raises(SearchRebuildError):
        pipeline.rebuild(
            (make_inventory(),),
            vector_provider=lambda document: [],
        )


def test_non_finite_vector_is_rejected(pipeline):
    with pytest.raises(SearchRebuildError):
        pipeline.rebuild(
            (make_inventory(),),
            vector_provider=lambda document: [1.0, float("nan")],
        )


def test_completed_checkpoint_normalizes_keys():
    checkpoint = SearchRebuildCheckpoint(
        run_id="run-003",
        completed_index_keys=(
            "b",
            "a",
            "b",
            " ",
        ),
    )

    assert checkpoint.completed_index_keys == ("a", "b")
    assert checkpoint.completed == frozenset({"a", "b"})


def test_report_exposes_resume_checkpoint(pipeline):
    report = pipeline.rebuild(
        (make_inventory(),),
        vector_provider=vector_provider,
    )

    checkpoint = report.checkpoint

    assert checkpoint.run_id == report.run_id
    assert checkpoint.completed_index_keys == (
        "tenant-001:project-001:UNIT-001",
    )


def test_empty_source_is_safe(pipeline):
    report = pipeline.rebuild(
        (),
        vector_provider=vector_provider,
    )

    assert report.complete
    assert report.scanned == 0
    assert report.indexed == 0


def test_cross_tenant_stale_data_is_not_deleted():
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(sink=sink)

    other_tenant = make_inventory(
        tenant_id="tenant-002",
        inventory_code="UNIT-999",
    )

    document = InventoryIndexingHook().build_upsert(
        other_tenant,
        tenant_id="tenant-002",
        project_id="project-001",
        expected_version=1,
    )

    sink.upsert(
        document,
        [1.0, 0.0, 0.0, 0.0],
    )

    pipeline.rebuild(
        (),
        vector_provider=vector_provider,
        tenant_id="tenant-001",
        existing_index_documents=(document,),
    )

    assert document.index_key in sink.documents


def test_same_source_rebuild_is_idempotent(pipeline):
    inventory = make_inventory()

    first = pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    second = pipeline.rebuild(
        (inventory,),
        vector_provider=vector_provider,
    )

    assert first.indexed == 1
    assert second.indexed == 1
    assert len(pipeline.sink.documents) == 1
    assert len(pipeline.sink.vectors) == 1


def test_stale_cleanup_order_is_deterministic(pipeline):
    stale_a = make_inventory(inventory_code="UNIT-002")
    stale_b = make_inventory(inventory_code="UNIT-003")

    docs = (
        InventoryIndexingHook().build_upsert(
            stale_b,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        ),
        InventoryIndexingHook().build_upsert(
            stale_a,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        ),
    )

    deleted = []

    class RecordingSink(InMemorySearchRebuildSink):
        def delete(self, index_key):
            deleted.append(index_key)
            super().delete(index_key)

    recording_pipeline = SearchRebuildPipeline(
        sink=RecordingSink(),
    )

    report = recording_pipeline.rebuild(
        (),
        vector_provider=vector_provider,
        existing_index_documents=docs,
    )

    assert report.deleted_stale == 2
    assert deleted == sorted(deleted)


def test_run_id_is_preserved_during_resume():
    sink = InMemorySearchRebuildSink()
    pipeline = SearchRebuildPipeline(sink=sink)

    checkpoint = SearchRebuildCheckpoint(run_id="stable-run")

    report = pipeline.rebuild(
        (make_inventory(),),
        vector_provider=vector_provider,
        checkpoint=checkpoint,
    )

    assert report.run_id == "stable-run"
