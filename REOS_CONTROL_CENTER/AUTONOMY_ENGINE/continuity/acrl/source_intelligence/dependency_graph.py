"""T16 PART-02 — Deterministic source dependency graph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.classification import (
    SourceClassification,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.topology import (
    RepositoryTopologyScanner,
)

from .source_parser import (
    ImportEvidence,
    SourceParseError,
    parse_imports,
)


class DependencyGraphError(RuntimeError):
    """Raised when dependency graph construction fails."""


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """One observed source-to-import relationship."""

    source_path: str
    imported_name: str
    import_kind: str
    line_number: int


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """Immutable deterministic dependency graph."""

    nodes: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]


def _module_name_from_path(relative_path: str) -> str | None:
    """Convert a Python repository path into its module name."""

    path = Path(relative_path)

    if path.suffix.lower() not in {".py", ".pyi"}:
        return None

    parts = list(path.with_suffix("").parts)

    if not parts:
        return None

    if parts[-1] == "__init__":
        parts.pop()

    if not parts:
        return None

    return ".".join(parts)


def build_dependency_graph(
    root: Path,
) -> DependencyGraph:
    """Build deterministic static dependency evidence."""

    try:
        topology = RepositoryTopologyScanner(root).scan()

        nodes = sorted(
            entry.relative_path
            for entry in topology.entries
            if entry.classification
            in {
                SourceClassification.SOURCE,
                SourceClassification.TEST,
            }
            and entry.relative_path.endswith((".py", ".pyi"))
        )

        edges: list[DependencyEdge] = []

        for source_path in nodes:
            evidence: tuple[ImportEvidence, ...]

            try:
                evidence = parse_imports(
                    root,
                    source_path,
                )
            except SourceParseError:
                # Parsing failure is represented by absence of derived
                # dependency evidence for this source. The source itself
                # remains part of the graph.
                continue

            for item in evidence:
                edges.append(
                    DependencyEdge(
                        source_path=item.source_path,
                        imported_name=item.imported_name,
                        import_kind=item.import_kind,
                        line_number=item.line_number,
                    )
                )

        edges.sort(
            key=lambda edge: (
                edge.source_path,
                edge.imported_name,
                edge.import_kind,
                edge.line_number,
            )
        )

        return DependencyGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
        )

    except OSError as exc:
        raise DependencyGraphError(
            "Unable to construct repository dependency graph."
        ) from exc


__all__ = [
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphError",
    "build_dependency_graph",
]