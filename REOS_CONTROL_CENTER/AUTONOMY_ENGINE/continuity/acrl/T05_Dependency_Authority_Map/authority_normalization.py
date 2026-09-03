"""ACRL T05 — canonical authority/dependency normalization."""

from __future__ import annotations

from .dependency_authority_map import (
    AuthorityDependency,
    AuthoritySource,
    DependencyType,
)


def normalize_sources(
    sources: tuple[AuthoritySource, ...],
) -> tuple[AuthoritySource, ...]:
    """Return sources in deterministic identity order."""

    return tuple(
        sorted(
            sources,
            key=lambda item: (
                item.source_id,
                item.path,
                item.level.value,
                item.purpose,
                item.mutable_by,
            ),
        )
    )


def normalize_dependencies(
    dependencies: tuple[AuthorityDependency, ...],
) -> tuple[AuthorityDependency, ...]:
    """Return dependencies in deterministic identity order."""

    return tuple(
        sorted(
            dependencies,
            key=lambda item: (
                item.consumer,
                item.source,
                item.dependency_type.value,
                item.reason,
            ),
        )
    )


def canonical_map_payload(
    sources: tuple[AuthoritySource, ...],
    dependencies: tuple[AuthorityDependency, ...],
) -> dict[str, object]:
    """Return order-independent canonical payload."""

    normalized_sources = normalize_sources(sources)
    normalized_dependencies = normalize_dependencies(
        dependencies
    )

    return {
        "sources": [
            {
                "source_id": source.source_id,
                "path": source.path,
                "level": source.level.value,
                "purpose": source.purpose,
                "mutable_by": list(
                    sorted(source.mutable_by)
                ),
            }
            for source in normalized_sources
        ],
        "dependencies": [
            {
                "consumer": dependency.consumer,
                "source": dependency.source,
                "dependency_type": (
                    dependency.dependency_type.value
                ),
                "reason": dependency.reason,
            }
            for dependency in normalized_dependencies
        ],
    }


__all__ = [
    "canonical_map_payload",
    "normalize_dependencies",
    "normalize_sources",
]