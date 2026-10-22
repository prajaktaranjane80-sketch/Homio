"""T16 deterministic dependency graph for Python and web source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..repository_discovery.classification import (
    EntryKind,
    SourceClassification,
)
from ..repository_discovery.topology import (
    RepositoryTopologyScanner,
)
from .source_parser import (
    ImportEvidence,
    SourceParseError,
    parse_imports,
)
from .web_source_parser import (
    WEB_SOURCE_SUFFIXES,
    WebSourceParseError,
    parse_web_imports,
)


class DependencyGraphError(RuntimeError):
    """Raised when dependency graph construction fails."""


PYTHON_SOURCE_SUFFIXES = frozenset({".py", ".pyi"})
ALL_SOURCE_SUFFIXES = PYTHON_SOURCE_SUFFIXES | WEB_SOURCE_SUFFIXES


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """One observed source-to-import relationship."""

    source_path: str
    imported_name: str
    import_kind: str
    line_number: int
    resolved_path: str | None = None


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """Immutable deterministic dependency graph."""

    nodes: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]


def _module_name_from_path(relative_path: str) -> str | None:
    """Convert a Python source path to its importable module name."""
    path = Path(relative_path)

    if path.suffix.lower() not in PYTHON_SOURCE_SUFFIXES:
        return None

    parts = list(path.with_suffix("").parts)

    if parts and parts[-1] == "__init__":
        parts.pop()

    if not parts:
        return None

    return ".".join(parts)


def build_dependency_graph(root: Path) -> DependencyGraph:
    """Build read-only static dependency evidence for supported sources."""
    repository_root = Path(root).resolve()

    try:
        topology = RepositoryTopologyScanner(repository_root).scan()

        nodes = sorted(
            entry.relative_path
            for entry in topology.entries
            if entry.kind == EntryKind.FILE
            and not entry.is_symlink
            and Path(entry.relative_path).suffix.lower()
            in ALL_SOURCE_SUFFIXES
            and (
                Path(entry.relative_path).suffix.lower()
                in WEB_SOURCE_SUFFIXES
                or entry.classification
                in {
                    SourceClassification.SOURCE,
                    SourceClassification.TEST,
                }
            )
        )

        edges: list[DependencyEdge] = []

        for source_path in nodes:
            suffix = Path(source_path).suffix.lower()

            if suffix in PYTHON_SOURCE_SUFFIXES:
                try:
                    imports: tuple[ImportEvidence, ...] = parse_imports(
                        repository_root,
                        source_path,
                    )
                except SourceParseError:
                    # Preserve the existing Python fail-tolerant contract.
                    continue

                for item in imports:
                    edges.append(
                        DependencyEdge(
                            source_path=item.source_path,
                            imported_name=item.imported_name,
                            import_kind=item.import_kind,
                            line_number=item.line_number,
                        )
                    )
                continue

            try:
                web_imports = parse_web_imports(
                    repository_root,
                    source_path,
                )
            except WebSourceParseError as exc:
                raise DependencyGraphError(
                    f"Cannot build a trusted web dependency graph for {source_path}."
                ) from exc

            for item in web_imports:
                edges.append(
                    DependencyEdge(
                        source_path=item.source_path,
                        imported_name=item.imported_name,
                        import_kind=item.import_kind,
                        line_number=item.line_number,
                        resolved_path=item.resolved_path,
                    )
                )

        edges.sort(
            key=lambda edge: (
                edge.source_path,
                edge.line_number,
                edge.imported_name,
                edge.import_kind,
                edge.resolved_path or "",
            )
        )

        return DependencyGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
        )

    except DependencyGraphError:
        raise
    except OSError as exc:
        raise DependencyGraphError(
            "Unable to construct repository dependency graph."
        ) from exc


__all__ = [
    "ALL_SOURCE_SUFFIXES",
    "PYTHON_SOURCE_SUFFIXES",
    "WEB_SOURCE_SUFFIXES",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphError",
    "build_dependency_graph",
]
