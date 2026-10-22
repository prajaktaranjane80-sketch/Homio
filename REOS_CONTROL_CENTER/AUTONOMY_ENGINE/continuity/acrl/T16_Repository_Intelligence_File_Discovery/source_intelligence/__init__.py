"""T16 source intelligence and deterministic dependency graph."""

from .dependency_graph import (
    ALL_SOURCE_SUFFIXES,
    PYTHON_SOURCE_SUFFIXES,
    WEB_SOURCE_SUFFIXES,
    DependencyEdge,
    DependencyGraph,
    DependencyGraphError,
    build_dependency_graph,
)
from .intelligence import (
    SourceIntelligence,
    inspect_source_intelligence,
)
from .source_parser import (
    ImportEvidence,
    SourceParseError,
    parse_imports,
)
from .web_source_parser import (
    CSS_SOURCE_SUFFIXES,
    WebImportEvidence,
    WebSourceParseError,
    parse_web_imports,
    resolve_web_import,
)

__all__ = [
    "ALL_SOURCE_SUFFIXES",
    "CSS_SOURCE_SUFFIXES",
    "PYTHON_SOURCE_SUFFIXES",
    "WEB_SOURCE_SUFFIXES",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphError",
    "ImportEvidence",
    "SourceIntelligence",
    "SourceParseError",
    "WebImportEvidence",
    "WebSourceParseError",
    "build_dependency_graph",
    "inspect_source_intelligence",
    "parse_imports",
    "parse_web_imports",
    "resolve_web_import",
]
