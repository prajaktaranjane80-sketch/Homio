"""ACRL T05 — normalization tests."""

from __future__ import annotations

from .authority_normalization import (
    canonical_map_payload,
)
from .dependency_authority_map import (
    AuthorityDependency,
    AuthorityLevel,
    AuthoritySource,
    DependencyType,
)


def _source(
    source_id: str,
) -> AuthoritySource:
    return AuthoritySource(
        source_id=source_id,
        path=source_id,
        level=AuthorityLevel.DERIVED,
        purpose="test",
    )


def _dependency(
    consumer: str,
    source: str,
) -> AuthorityDependency:
    return AuthorityDependency(
        consumer=consumer,
        source=source,
        dependency_type=DependencyType.DERIVED_FROM,
        reason="test",
    )


def test_normalization_is_order_independent() -> None:
    first = canonical_map_payload(
        (_source("B"), _source("A")),
        (
            _dependency("Z", "B"),
            _dependency("A", "A"),
        ),
    )

    second = canonical_map_payload(
        (_source("A"), _source("B")),
        (
            _dependency("A", "A"),
            _dependency("Z", "B"),
        ),
    )

    assert first == second


def test_mutable_by_is_normalized() -> None:
    first = AuthoritySource(
        source_id="A",
        path="a",
        level=AuthorityLevel.AUTHORITATIVE,
        purpose="test",
        mutable_by=("B", "A"),
    )

    payload = canonical_map_payload(
        (first,),
        (),
    )

    assert payload["sources"][0]["mutable_by"] == [
        "A",
        "B",
    ]