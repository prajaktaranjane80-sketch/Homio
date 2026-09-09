from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from ..T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    FileAuthority,
    FileRisk,
    RepositoryFile,
    RepositoryScanner,
    normalize_repository_path,
)
from ..T16_Repository_Intelligence_File_Discovery.source_intelligence.dependency_graph import (
    DependencyGraph,
    build_dependency_graph,
)


class ChangeImpactError(RuntimeError):
    pass


class ChangeImpactValidationError(ChangeImpactError):
    pass


class ChangeImpactSecurityError(ChangeImpactError):
    pass


class ChangeImpactIntegrityError(ChangeImpactError):
    pass


class ChangeImpactCompatibilityError(ChangeImpactError):
    pass


class ImpactLevel(str, Enum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


class T17Decision(str, Enum):
    ANALYZE = "ANALYZE"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class ImpactReason(str, Enum):
    DIRECT_MATCH = "DIRECT_MATCH"
    DEPENDENCY_OF_CHANGED_MODULE = "DEPENDENCY_OF_CHANGED_MODULE"
    PROTECTED_FILE = "PROTECTED_FILE"
    UNKNOWN_PATH = "UNKNOWN_PATH"
    SECURITY_BOUNDARY = "SECURITY_BOUNDARY"
    GRAPH_UNAVAILABLE = "GRAPH_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ImpactPolicy:
    schema_version: str = "1.0"
    allow_state_mutation: bool = False
    allow_execution: bool = False
    allow_authority_change: bool = False
    allow_architecture_change: bool = False
    allow_self_approval: bool = False
    allow_unbounded_analysis: bool = False

    def validate(self) -> None:
        if self.schema_version != "1.0":
            raise ChangeImpactCompatibilityError(self.schema_version)
        if any((self.allow_state_mutation, self.allow_execution,
                self.allow_authority_change, self.allow_architecture_change,
                self.allow_self_approval, self.allow_unbounded_analysis)):
            raise ChangeImpactValidationError(
                "T17 is read-only, non-executing, bounded, and non-authoritative."
            )


@dataclass(frozen=True, slots=True)
class T17Provenance:
    source: str = "T16_REPOSITORY_INTELLIGENCE"
    authority: str = "REOS_CONTROL_CENTER"
    read_only: bool = True

    def validate(self) -> None:
        if self.source != "T16_REPOSITORY_INTELLIGENCE":
            raise ChangeImpactValidationError("Invalid provenance source.")
        if self.authority != "REOS_CONTROL_CENTER":
            raise ChangeImpactValidationError("Invalid authority.")
        if self.read_only is not True:
            raise ChangeImpactValidationError("T17 must remain read-only.")


@dataclass(frozen=True, slots=True)
class ChangeImpact:
    relative_path: str
    impact_level: ImpactLevel
    reason_code: ImpactReason
    authority: FileAuthority | None
    source_kind: str | None
    dependency_distance: int | None


@dataclass(frozen=True, slots=True)
class DependencyImpact:
    changed_path: str
    impacted_path: str
    distance: int
    relationship: str


@dataclass(frozen=True, slots=True)
class ChangeImpactReport:
    schema_version: str
    decision: T17Decision
    changed_paths: tuple[str, ...]
    impacts: tuple[ChangeImpact, ...]
    dependency_impacts: tuple[DependencyImpact, ...]
    protected_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]
    graph_nodes: int
    graph_edges: int
    fingerprint: str
    policy_schema: str
    provenance_source: str
    state_mutated: bool = False
    execution_authorized: bool = False

    @property
    def impacted_paths(self) -> tuple[str, ...]:
        return tuple(i.impacted_path for i in self.dependency_impacts)

    @property
    def ready_for_handoff(self) -> bool:
        return self.decision == T17Decision.ANALYZE and not self.unknown_paths and not self.state_mutated and not self.execution_authorized

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "changed_paths": list(self.changed_paths),
            "impacts": [
                {
                    "relative_path": i.relative_path,
                    "impact_level": i.impact_level.value,
                    "reason_code": i.reason_code.value,
                    "authority": i.authority.value if i.authority else None,
                    "source_kind": i.source_kind,
                    "dependency_distance": i.dependency_distance,
                }
                for i in self.impacts
            ],
            "dependency_impacts": [
                {
                    "changed_path": i.changed_path,
                    "impacted_path": i.impacted_path,
                    "distance": i.distance,
                    "relationship": i.relationship,
                }
                for i in self.dependency_impacts
            ],
            "protected_paths": list(self.protected_paths),
            "unknown_paths": list(self.unknown_paths),
            "graph_nodes": self.graph_nodes,
            "graph_edges": self.graph_edges,
            "fingerprint": self.fingerprint,
            "policy_schema": self.policy_schema,
            "provenance_source": self.provenance_source,
            "state_mutated": self.state_mutated,
            "execution_authorized": self.execution_authorized,
        }


@dataclass(frozen=True, slots=True)
class T17Metrics:
    total_changed_paths: int
    direct_impacts: int
    indirect_impacts: int
    protected_impacts: int
    unknown_paths: int
    graph_nodes: int
    graph_edges: int

    @classmethod
    def from_report(cls, report: ChangeImpactReport) -> "T17Metrics":
        return cls(
            total_changed_paths=len(report.changed_paths),
            direct_impacts=sum(i.impact_level == ImpactLevel.DIRECT for i in report.impacts),
            indirect_impacts=sum(i.impact_level == ImpactLevel.INDIRECT for i in report.impacts),
            protected_impacts=sum(i.impact_level == ImpactLevel.PROTECTED for i in report.impacts),
            unknown_paths=len(report.unknown_paths),
            graph_nodes=report.graph_nodes,
            graph_edges=report.graph_edges,
        )


@dataclass(frozen=True, slots=True)
class ImpactIntegrationHandoff:
    report_fingerprint: str
    decision: str
    changed_paths: tuple[str, ...]
    impacted_paths: tuple[str, ...]
    ready_for_handoff: bool


class T17RepositoryIntelligenceAdapter:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()

    def files(self) -> tuple[RepositoryFile, ...]:
        return RepositoryScanner(self.repository_root).scan()

    def dependency_graph(self) -> DependencyGraph:
        return build_dependency_graph(self.repository_root)


def _module_name(relative_path: str) -> str:
    path = Path(relative_path)
    if path.suffix.lower() not in {".py", ".pyi"}:
        return ""
    parts = list(path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_import(source_path: str, imported_name: str, modules: dict[str, str]) -> str | None:
    source = _module_name(source_path)
    if not source or not imported_name:
        return None
    raw = imported_name.strip()
    if raw.startswith("."):
        level = len(raw) - len(raw.lstrip("."))
        tail = raw[level:].strip(".")
        source_parts = source.split(".")
        base = source_parts[:-level] if level <= len(source_parts) else []
        candidate = ".".join(base + ([tail] if tail else []))
    else:
        candidate = raw
    if candidate in modules:
        return modules[candidate]
    children = sorted(v for k, v in modules.items() if k.startswith(candidate + "."))
    return children[0] if children else None


def _reverse_dependencies(graph: DependencyGraph) -> dict[str, tuple[str, ...]]:
    modules = {_module_name(node): node for node in graph.nodes if _module_name(node)}
    reverse: dict[str, set[str]] = {}
    for edge in graph.edges:
        target = _resolve_import(edge.source_path, edge.imported_name, modules)
        if target:
            reverse.setdefault(target, set()).add(edge.source_path)
    return {k: tuple(sorted(v, key=normalize_repository_path)) for k, v in reverse.items()}


class ChangeImpactAnalyzer:
    SCHEMA_VERSION = "1.0"

    def __init__(self, repository_root: Path | str, *, policy: ImpactPolicy | None = None, provenance: T17Provenance | None = None) -> None:
        self.repository_root = Path(repository_root).resolve()
        if not self.repository_root.is_dir():
            raise ChangeImpactError(f"Repository root is not a directory: {self.repository_root}")
        self.policy = policy or ImpactPolicy()
        self.provenance = provenance or T17Provenance()
        self.policy.validate()
        self.provenance.validate()

    @staticmethod
    def _normalize(paths: Iterable[str]) -> tuple[str, ...]:
        values = []
        for raw in paths:
            if not isinstance(raw, str) or not raw.strip():
                raise ChangeImpactValidationError("Changed paths must be non-empty strings.")
            normalized = normalize_repository_path(raw)
            if normalized == ".." or normalized.startswith("../") or "/../" in normalized:
                raise ChangeImpactSecurityError("Changed path escapes repository boundary.")
            values.append(normalized)
        return tuple(sorted(set(values)))

    def analyze(self, changed_paths: Iterable[str]) -> ChangeImpactReport:
        changed = self._normalize(changed_paths)
        if not changed:
            raise ChangeImpactValidationError("At least one changed path is required.")

        adapter = T17RepositoryIntelligenceAdapter(self.repository_root)
        file_map = {normalize_repository_path(f.relative_path): f for f in adapter.files()}
        graph = adapter.dependency_graph()
        reverse = _reverse_dependencies(graph)

        impacts: list[ChangeImpact] = []
        dependencies: list[DependencyImpact] = []
        protected: set[str] = set()
        unknown: set[str] = set()

        for path in changed:
            item = file_map.get(path)
            if item is None:
                unknown.add(path)
                impacts.append(ChangeImpact(path, ImpactLevel.UNKNOWN, ImpactReason.UNKNOWN_PATH, None, None, None))
                continue
            level = ImpactLevel.PROTECTED if item.risk == FileRisk.PROTECTED else ImpactLevel.DIRECT
            reason = ImpactReason.PROTECTED_FILE if level == ImpactLevel.PROTECTED else ImpactReason.DIRECT_MATCH
            if level == ImpactLevel.PROTECTED:
                protected.add(path)
            impacts.append(ChangeImpact(path, level, reason, item.authority, item.source_kind.value, 0))

            queue = [(path, 0)]
            visited = {path}
            while queue:
                current, distance = queue.pop(0)
                for dependent in reverse.get(current, ()):
                    if dependent in visited:
                        continue
                    visited.add(dependent)
                    next_distance = distance + 1
                    dependencies.append(DependencyImpact(path, dependent, next_distance, "REVERSE_DEPENDENCY"))
                    dep_file = file_map.get(dependent)
                    if dep_file:
                        impacts.append(ChangeImpact(dependent, ImpactLevel.PROTECTED if dep_file.risk == FileRisk.PROTECTED else ImpactLevel.INDIRECT,
                                                     ImpactReason.DEPENDENCY_OF_CHANGED_MODULE, dep_file.authority, dep_file.source_kind.value, next_distance))
                    queue.append((dependent, next_distance))

        # Collapse impact records by strongest severity and nearest distance.
        rank = {ImpactLevel.PROTECTED: 4, ImpactLevel.DIRECT: 3, ImpactLevel.INDIRECT: 2, ImpactLevel.UNKNOWN: 1}
        best: dict[str, ChangeImpact] = {}
        for impact in impacts:
            prior = best.get(impact.relative_path)
            if prior is None or rank[impact.impact_level] > rank[prior.impact_level] or (rank[impact.impact_level] == rank[prior.impact_level] and (impact.dependency_distance or 999) < (prior.dependency_distance or 999)):
                best[impact.relative_path] = impact

        impact_tuple = tuple(sorted(best.values(), key=lambda i: normalize_repository_path(i.relative_path)))
        dependency_tuple = tuple(sorted(set(dependencies), key=lambda i: (normalize_repository_path(i.changed_path), i.distance, normalize_repository_path(i.impacted_path))))
        decision = T17Decision.FAIL_CLOSED if protected and unknown else T17Decision.BLOCKED if unknown else T17Decision.ANALYZE
        fingerprint = self._fingerprint(changed, impact_tuple, dependency_tuple, tuple(sorted(protected)), tuple(sorted(unknown)), len(graph.nodes), len(graph.edges))
        return ChangeImpactReport(self.SCHEMA_VERSION, decision, changed, impact_tuple, dependency_tuple,
                                  tuple(sorted(protected)), tuple(sorted(unknown)), len(graph.nodes), len(graph.edges),
                                  fingerprint, self.policy.schema_version, self.provenance.source, False, False)

    def validate_report(self, report: ChangeImpactReport) -> None:
        if not isinstance(report, ChangeImpactReport):
            raise ChangeImpactValidationError("Invalid T17 report.")
        if report.schema_version != self.SCHEMA_VERSION:
            raise ChangeImpactCompatibilityError("Unsupported T17 schema.")
        if report.state_mutated or report.execution_authorized:
            raise ChangeImpactSecurityError("T17 report violates read-only boundary.")
        expected = self._fingerprint(report.changed_paths, report.impacts, report.dependency_impacts,
                                     report.protected_paths, report.unknown_paths, report.graph_nodes, report.graph_edges)
        if expected != report.fingerprint:
            raise ChangeImpactIntegrityError("T17 fingerprint mismatch.")

    @staticmethod
    def metrics(report: ChangeImpactReport) -> T17Metrics:
        return T17Metrics.from_report(report)

    @staticmethod
    def build_handoff(report: ChangeImpactReport) -> ImpactIntegrationHandoff:
        return ImpactIntegrationHandoff(report.fingerprint, report.decision.value, report.changed_paths, report.impacted_paths, report.ready_for_handoff)

    @staticmethod
    def _fingerprint(changed, impacts, dependencies, protected, unknown, nodes, edges) -> str:
        payload = {
            "schema_version": "1.0", "changed_paths": list(changed),
            "impacts": [i.__dict__ if hasattr(i, "__dict__") else {"relative_path": i.relative_path, "impact_level": i.impact_level.value, "reason_code": i.reason_code.value, "authority": i.authority.value if i.authority else None, "source_kind": i.source_kind, "dependency_distance": i.dependency_distance} for i in impacts],
            "dependencies": [{"changed_path": i.changed_path, "impacted_path": i.impacted_path, "distance": i.distance, "relationship": i.relationship} for i in dependencies],
            "protected": list(protected), "unknown": list(unknown), "graph_nodes": nodes, "graph_edges": edges,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


__all__ = [name for name in globals() if not name.startswith("_")]
