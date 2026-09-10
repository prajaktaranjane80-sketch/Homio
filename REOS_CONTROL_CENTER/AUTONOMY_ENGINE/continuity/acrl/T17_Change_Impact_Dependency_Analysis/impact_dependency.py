from __future__ import annotations

from pathlib import Path

from ..T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    normalize_repository_path,
)

from ..T16_Repository_Intelligence_File_Discovery.source_intelligence.dependency_graph import (
    DependencyGraph,
)

from .impact_models import DependencyImpact


def module_name(
    relative_path: str,
) -> str:
    path = Path(relative_path)

    if path.suffix.lower() not in {
        ".py",
        ".pyi",
    }:
        return ""

    parts = list(
        path.with_suffix("").parts
    )

    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts)


def resolve_import(
    source_path: str,
    imported_name: str,
    modules: dict[str, str],
) -> str | None:
    source = module_name(source_path)

    if not source or not imported_name:
        return None

    raw = imported_name.strip()

    if raw.startswith("."):
        level = len(raw) - len(raw.lstrip("."))

        tail = raw[level:].strip(".")
        source_parts = source.split(".")

        base = (
            source_parts[:-level]
            if level <= len(source_parts)
            else []
        )

        candidate = ".".join(
            base + ([tail] if tail else [])
        )
    else:
        candidate = raw

    if candidate in modules:
        return modules[candidate]

    children = sorted(
        value
        for key, value in modules.items()
        if key.startswith(candidate + ".")
    )

    return children[0] if children else None


def build_reverse_dependencies(
    graph: DependencyGraph,
) -> dict[str, tuple[str, ...]]:
    modules = {
        module_name(node): node
        for node in graph.nodes
        if module_name(node)
    }

    reverse: dict[str, set[str]] = {}

    for edge in graph.edges:
        target = resolve_import(
            edge.source_path,
            edge.imported_name,
            modules,
        )

        if target:
            reverse.setdefault(
                target,
                set(),
            ).add(
                edge.source_path
            )

    return {
        key: tuple(
            sorted(
                values,
                key=normalize_repository_path,
            )
        )
        for key, values in reverse.items()
    }


def collect_dependency_impacts(
    changed_path: str,
    reverse_dependencies: dict[str, tuple[str, ...]],
) -> tuple[DependencyImpact, ...]:
    impacts: list[DependencyImpact] = []

    queue = [
        (changed_path, 0)
    ]

    visited = {
        changed_path
    }

    while queue:
        current, distance = queue.pop(0)

        for dependent in reverse_dependencies.get(
            current,
            (),
        ):
            if dependent in visited:
                continue

            visited.add(dependent)

            next_distance = distance + 1

            impacts.append(
                DependencyImpact(
                    changed_path=changed_path,
                    impacted_path=dependent,
                    distance=next_distance,
                    relationship="REVERSE_DEPENDENCY",
                )
            )

            queue.append(
                (
                    dependent,
                    next_distance,
                )
            )

    return tuple(impacts)


__all__ = [
    "DependencyImpact",
    "module_name",
    "resolve_import",
    "build_reverse_dependencies",
    "collect_dependency_impacts",
]
