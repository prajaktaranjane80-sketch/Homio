"""
CORE-005 hardening — runtime adapter isolation regression.
"""

from __future__ import annotations

import pytest

from .runtime_adapter import (
    BackendIndependentSearchRuntime,
    RuntimeAdapterConfigurationError,
    RuntimeAdapterOperationError,
    RuntimeAdapterRegistry,
    RuntimeBackendIdentity,
    RuntimeSearchHit,
)
from .search_domain import (
    SearchRequest,
    SearchTenantContext,
)


class FakeBackend:
    @property
    def identity(self) -> RuntimeBackendIdentity:
        return RuntimeBackendIdentity(
            backend_name="FAKE",
            adapter_name="FakeBackend",
            adapter_version="1",
            capabilities=frozenset({"SEARCH"}),
        )

    def search(
        self,
        request: SearchRequest,
        *,
        limit: int,
    ) -> tuple[RuntimeSearchHit, ...]:
        assert request.tenant.tenant_id == "tenant-a"
        assert limit == 5

        return (
            RuntimeSearchHit(
                index_key="tenant-a:inv-001",
                score=1.0,
                payload={
                    "adapter": "fake"
                },
            ),
        )


class FakeIndex:
    @property
    def identity(self) -> RuntimeBackendIdentity:
        return RuntimeBackendIdentity(
            backend_name="FAKE",
            adapter_name="FakeIndex",
            adapter_version="1",
            capabilities=frozenset({"UPSERT"}),
        )


class MismatchedIndex:
    @property
    def identity(self) -> RuntimeBackendIdentity:
        return RuntimeBackendIdentity(
            backend_name="OTHER",
            adapter_name="OtherIndex",
            adapter_version="1",
            capabilities=frozenset({"UPSERT"}),
        )


class FakeRebuild:
    def rebuild(
        self,
        documents,
    ):
        return tuple(
            document.index_key
            for document in documents
        )


def make_request() -> SearchRequest:
    return SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        )
    )


def test_runtime_delegates_through_backend_contract() -> None:
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

    results = runtime.search(
        make_request(),
        limit=5,
    )

    assert isinstance(results, tuple)
    assert (
        results[0].index_key
        == "tenant-a:inv-001"
    )
    assert (
        results[0].payload["adapter"]
        == "fake"
    )


def test_runtime_rejects_backend_index_identity_drift() -> None:
    registry = RuntimeAdapterRegistry(
        backend=FakeBackend(),
        index=MismatchedIndex(),
        rebuild=FakeRebuild(),
    )

    with pytest.raises(
        RuntimeAdapterConfigurationError
    ):
        registry.validate()


def test_runtime_facade_rejects_invalid_limit_before_backend_call() -> None:
    registry = RuntimeAdapterRegistry(
        backend=FakeBackend(),
        index=FakeIndex(),
        rebuild=FakeRebuild(),
    )

    runtime = BackendIndependentSearchRuntime(
        adapters=registry
    )

    with pytest.raises(
        RuntimeAdapterOperationError
    ):
        runtime.search(
            make_request(),
            limit=0,
        )


def test_registry_is_immutable() -> None:
    registry = RuntimeAdapterRegistry(
        backend=FakeBackend(),
        index=FakeIndex(),
        rebuild=FakeRebuild(),
    )

    with pytest.raises(AttributeError):
        registry.backend = FakeBackend()  # type: ignore[misc]


def test_adapter_identity_is_explicit_and_versioned() -> None:
    identity = FakeBackend().identity

    assert identity.backend_name == "FAKE"
    assert identity.adapter_name == "FakeBackend"
    assert identity.adapter_version == "1"
    assert "SEARCH" in identity.capabilities
