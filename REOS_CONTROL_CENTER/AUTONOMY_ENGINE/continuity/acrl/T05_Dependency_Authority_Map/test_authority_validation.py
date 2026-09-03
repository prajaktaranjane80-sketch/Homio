"""ACRL T05 — authority validation tests."""

from __future__ import annotations

import pytest

from .authority_validation import (
    AuthorityValidationStatus,
    validate_authority_map,
)
from .dependency_authority_map import (
    AuthorityDependency,
    AuthorityLevel,
    AuthoritySource,
    DependencyAuthorityMapBuilder,
    DependencyType,
)


def test_default_map_is_valid() -> None:
    report = validate_authority_map(
        DependencyAuthorityMapBuilder().build()
    )

    assert report.status == AuthorityValidationStatus.VALID
    assert report.valid is True
    assert report.failures == ()


def test_duplicate_dependency_is_invalid() -> None:
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
            dependency_type=DependencyType.AUTHORITATIVE,
            reason="one",
        ),
        AuthorityDependency(
            consumer="ACRL",
            source="REOS_STATE",
            dependency_type=DependencyType.AUTHORITATIVE,
            reason="two",
        ),
    )

    authority_map = builder.build(
        sources=sources,
        dependencies=dependencies,
    )

    report = validate_authority_map(
        authority_map
    )

    assert report.valid is False
    assert any(
        "Duplicate dependency" in failure
        for failure in report.failures
    )


def test_self_dependency_is_invalid() -> None:
    builder = DependencyAuthorityMapBuilder()

    source = AuthoritySource(
        source_id="REOS_STATE",
        path="data/state.json",
        level=AuthorityLevel.AUTHORITATIVE,
        purpose="state",
    )

    dependencies = (
        AuthorityDependency(
            consumer="ACRL",
            source="REOS_STATE",
            dependency_type=DependencyType.AUTHORITATIVE,
            reason="required-authority",
        ),
        AuthorityDependency(
            consumer="REOS_STATE",
            source="REOS_STATE",
            dependency_type=DependencyType.AUTHORITATIVE,
            reason="self",
        ),
    )

    authority_map = builder.build(
        sources=(source,),
        dependencies=dependencies,
    )

    report = validate_authority_map(
        authority_map
    )

    assert report.valid is False
    assert any(
        "Self dependency" in failure
        for failure in report.failures
    )
