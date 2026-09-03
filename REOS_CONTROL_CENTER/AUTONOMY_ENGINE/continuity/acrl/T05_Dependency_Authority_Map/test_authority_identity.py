"""ACRL T05 — authority identity tests."""

from __future__ import annotations

from .authority_identity import (
    build_authority_map_identity,
)
from .dependency_authority_map import (
    AuthorityDependency,
    AuthorityLevel,
    AuthoritySource,
    DependencyAuthorityMapBuilder,
    DependencyType,
)


def test_default_identity_is_deterministic() -> None:
    first = build_authority_map_identity(
        DependencyAuthorityMapBuilder().build()
    )
    second = build_authority_map_identity(
        DependencyAuthorityMapBuilder().build()
    )

    assert first.identity_key() == second.identity_key()


def test_identity_ignores_collection_order() -> None:
    builder = DependencyAuthorityMapBuilder()

    sources = tuple(
        reversed(builder._default_sources())
    )

    dependencies = tuple(
        reversed(builder._default_dependencies())
    )

    first_map = builder.build(
        sources=builder._default_sources(),
        dependencies=builder._default_dependencies(),
    )

    second_map = builder.build(
        sources=sources,
        dependencies=dependencies,
    )

    first = build_authority_map_identity(first_map)
    second = build_authority_map_identity(second_map)

    assert (
        first.canonical_sha256
        == second.canonical_sha256
    )