"""T16 deterministic repository source-intelligence projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.fingerprint import (
    fingerprint_topology,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.identity import (
    identify_repository,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.topology import (
    RepositoryTopologyScanner,
)

from .dependency_graph import (
    ALL_SOURCE_SUFFIXES,
    DependencyGraph,
    build_dependency_graph,
)


@dataclass(frozen=True, slots=True)
class SourceIntelligence:
    """Immutable T16 source-intelligence snapshot."""

    repository_identity_hash: str
    topology_fingerprint: str
    source_nodes: tuple[str, ...]
    dependency_graph: DependencyGraph


def inspect_source_intelligence(
    root: Path,
) -> SourceIntelligence:
    """Create a deterministic source and dependency snapshot."""
    repository_root = Path(root).resolve()

    identity = identify_repository(repository_root)
    topology = RepositoryTopologyScanner(repository_root).scan()
    graph = build_dependency_graph(repository_root)

    source_nodes = tuple(
        sorted(
            entry.relative_path
            for entry in topology.entries
            if Path(entry.relative_path).suffix.lower()
            in ALL_SOURCE_SUFFIXES
        )
    )

    return SourceIntelligence(
        repository_identity_hash=identity.identity_hash,
        topology_fingerprint=fingerprint_topology(topology),
        source_nodes=source_nodes,
        dependency_graph=graph,
    )


__all__ = [
    "SourceIntelligence",
    "inspect_source_intelligence",
]
