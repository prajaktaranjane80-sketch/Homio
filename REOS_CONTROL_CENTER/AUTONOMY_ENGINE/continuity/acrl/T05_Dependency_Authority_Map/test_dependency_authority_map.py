"""ACRL T05 — Dependency & Authority Map tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.dependency_authority_map import (
    AuthorityConflictError,
    AuthorityDependency,
    AuthorityLevel,
    AuthorityMapIntegrityError,
    AuthoritySource,
    DependencyAuthorityMapBuilder,
    DependencyType,
    build_dependency_authority_map,
)


def test_default_map_contains_primary_reos_state() -> None:
    result = build_dependency_authority_map()

    assert result.primary_authority == "REOS_STATE"

    source = result.source("REOS_STATE")

    assert source.path == "data/state.json"
    assert source.level == AuthorityLevel.AUTHORITATIVE


def test_architecture_is_authoritative() -> None:
    result = build_dependency_authority_map()

    source = result.source("REOS_ARCHITECTURE")

    assert source.level == AuthorityLevel.AUTHORITATIVE


def test_controller_is_authoritative() -> None:
    result = build_dependency_authority_map()

    source = result.source("REOS_CONTROLLER")

    assert source.level == AuthorityLevel.AUTHORITATIVE


def test_acrl_is_derived_not_primary_authority() -> None:
    result = build_dependency_authority_map()

    source = result.source("ACRL")

    assert source.level == AuthorityLevel.DERIVED
    assert result.primary_authority != "ACRL"


def test_chat_context_is_not_authoritative() -> None:
    result = build_dependency_authority_map()

    source = result.source("CHAT_CONTEXT")

    assert source.level == AuthorityLevel.CONTEXT

    dependencies = result.dependencies_for("ACRL")

    chat_dependency = next(
        item
        for item in dependencies
        if item.source == "CHAT_CONTEXT"
    )

    assert (
        chat_dependency.dependency_type
        == DependencyType.CONTEXT_ONLY
    )


def test_acrl_depends_on_reos_state() -> None:
    result = build_dependency_authority_map()

    dependencies = result.dependencies_for("ACRL")

    assert any(
        item.source == "REOS_STATE"
        and item.dependency_type
        == DependencyType.AUTHORITATIVE
        for item in dependencies
    )


def test_acrl_depends_on_architecture() -> None:
    result = build_dependency_authority_map()

    dependencies = result.dependencies_for("ACRL")

    assert any(
        item.source == "REOS_ARCHITECTURE"
        and item.dependency_type
        == DependencyType.AUTHORITATIVE
        for item in dependencies
    )


def test_new_chat_consumes_acrl_continuity() -> None:
    result = build_dependency_authority_map()

    dependencies = result.dependencies_for("NEW_CHAT")

    assert any(
        item.source == "ACRL"
        and item.dependency_type
        == DependencyType.DERIVED_FROM
        for item in dependencies
    )


def test_fingerprint_is_deterministic() -> None:
    first = build_dependency_authority_map()
    second = build_dependency_authority_map()

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64


def test_duplicate_source_ids_are_rejected() -> None:
    source = AuthoritySource(
        source_id="DUPLICATE",
        path="x",
        level=AuthorityLevel.CONTEXT,
        purpose="test",
    )

    builder = DependencyAuthorityMapBuilder()

    with pytest.raises(AuthorityMapIntegrityError):
        builder.build(
            sources=(
                AuthoritySource(
                    source_id="REOS_STATE",
                    path="data/state.json",
                    level=AuthorityLevel.AUTHORITATIVE,
                    purpose="state",
                ),
                source,
                AuthoritySource(
                    source_id="DUPLICATE",
                    path="y",
                    level=AuthorityLevel.CONTEXT,
                    purpose="test",
                ),
            ),
            dependencies=(),
        )


def test_primary_authority_cannot_be_removed() -> None:
    builder = DependencyAuthorityMapBuilder()

    sources = (
        AuthoritySource(
            source_id="OTHER",
            path="other",
            level=AuthorityLevel.AUTHORITATIVE,
            purpose="other",
        ),
    )

    with pytest.raises(AuthorityConflictError):
        builder.build(
            sources=sources,
            dependencies=(),
        )


def test_unknown_dependency_source_is_rejected() -> None:
    builder = DependencyAuthorityMapBuilder()

    sources = (
        AuthoritySource(
            source_id="REOS_STATE",
            path="data/state.json",
            level=AuthorityLevel.AUTHORITATIVE,
            purpose="state",
        ),
    )

    dependencies = (
        AuthorityDependency(
            consumer="ACRL",
            source="UNKNOWN",
            dependency_type=DependencyType.AUTHORITATIVE,
            reason="invalid",
        ),
    )

    with pytest.raises(AuthorityMapIntegrityError):
        builder.build(
            sources=sources,
            dependencies=dependencies,
        )


def test_acrl_without_authoritative_dependency_is_rejected() -> None:
    builder = DependencyAuthorityMapBuilder()

    sources = (
        AuthoritySource(
            source_id="REOS_STATE",
            path="data/state.json",
            level=AuthorityLevel.AUTHORITATIVE,
            purpose="state",
        ),
    )

    dependencies = (
        AuthorityDependency(
            consumer="ACRL",
            source="REOS_STATE",
            dependency_type=DependencyType.CONTEXT_ONLY,
            reason="invalid authority classification",
        ),
    )

    with pytest.raises(AuthorityConflictError):
        builder.build(
            sources=sources,
            dependencies=dependencies,
        )


def test_serializable_projection_contains_authority_and_dependencies() -> None:
    result = build_dependency_authority_map()

    payload = result.to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["primary_authority"] == "REOS_STATE"
    assert payload["sources"]
    assert payload["dependencies"]
    assert len(payload["fingerprint"]) == 64