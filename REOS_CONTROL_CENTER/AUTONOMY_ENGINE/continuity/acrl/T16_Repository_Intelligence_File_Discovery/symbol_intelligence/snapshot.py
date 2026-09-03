"""T16 PART-03 — Deterministic repository intelligence snapshot."""

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
from AUTONOMY_ENGINE.continuity.acrl.source_intelligence.dependency_graph import (
    DependencyGraph,
    build_dependency_graph,
)

from .lineage import (
    EvidenceLineage,
    derived_evidence,
    observed_evidence,
)
from .symbols import (
    SymbolRecord,
    extract_symbols,
)


class SymbolSnapshotError(RuntimeError):
    """Raised when the symbol snapshot cannot be created safely."""


@dataclass(frozen=True, slots=True)
class SymbolIntelligenceSnapshot:
    """Immutable deterministic T16 PART-03 snapshot."""

    repository_identity_hash: str
    topology_fingerprint: str
    dependency_graph: DependencyGraph
    symbols: tuple[SymbolRecord, ...]
    evidence: EvidenceLineage


def inspect_symbol_intelligence(
    root: Path,
) -> SymbolIntelligenceSnapshot:
    """Build a deterministic repository symbol-intelligence snapshot."""

    try:
        identity = identify_repository(root)

        topology = RepositoryTopologyScanner(root).scan()

        topology_fingerprint = fingerprint_topology(
            topology,
        )

        dependency_graph = build_dependency_graph(
            root,
        )

        source_paths = sorted(
            {
                entry.relative_path
                for entry in topology.entries
                if entry.relative_path.endswith(
                    (".py", ".pyi")
                )
            }
        )

        symbols: list[SymbolRecord] = []

        for relative_path in source_paths:
            symbols.extend(
                extract_symbols(
                    root,
                    relative_path,
                )
            )

        symbols.sort(
            key=lambda item: (
                item.source_path,
                item.line_number,
                item.qualified_name,
                item.kind,
            )
        )

        return SymbolIntelligenceSnapshot(
            repository_identity_hash=identity.identity_hash,
            topology_fingerprint=topology_fingerprint,
            dependency_graph=dependency_graph,
            symbols=tuple(symbols),
            evidence=derived_evidence(
                source="T16 PART-01 + PART-02 + PART-03",
                explanation=(
                    "Symbols are statically derived from repository "
                    "topology using Python AST analysis and linked "
                    "with the existing deterministic dependency graph."
                ),
            ),
        )

    except (OSError, RuntimeError) as exc:
        if isinstance(exc, SymbolSnapshotError):
            raise

        raise SymbolSnapshotError(
            "Unable to construct T16 PART-03 symbol snapshot."
        ) from exc


__all__ = [
    "SymbolIntelligenceSnapshot",
    "SymbolSnapshotError",
    "inspect_symbol_intelligence",
]