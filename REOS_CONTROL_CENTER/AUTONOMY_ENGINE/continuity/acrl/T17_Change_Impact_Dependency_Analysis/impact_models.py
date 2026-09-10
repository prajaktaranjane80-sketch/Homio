from __future__ import annotations

from dataclasses import dataclass

from .impact_registry import (
    FileAuthority,
    ImpactLevel,
    ImpactReason,
    T17Decision,
)


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
        return tuple(
            item.impacted_path
            for item in self.dependency_impacts
        )

    @property
    def ready_for_handoff(self) -> bool:
        return (
            self.decision == T17Decision.ANALYZE
            and not self.unknown_paths
            and not self.state_mutated
            and not self.execution_authorized
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "changed_paths": list(self.changed_paths),
            "impacts": [
                {
                    "relative_path": item.relative_path,
                    "impact_level": item.impact_level.value,
                    "reason_code": item.reason_code.value,
                    "authority": (
                        item.authority.value
                        if item.authority
                        else None
                    ),
                    "source_kind": item.source_kind,
                    "dependency_distance": item.dependency_distance,
                }
                for item in self.impacts
            ],
            "dependency_impacts": [
                {
                    "changed_path": item.changed_path,
                    "impacted_path": item.impacted_path,
                    "distance": item.distance,
                    "relationship": item.relationship,
                }
                for item in self.dependency_impacts
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
    def from_report(
        cls,
        report: ChangeImpactReport,
    ) -> "T17Metrics":
        return cls(
            total_changed_paths=len(report.changed_paths),
            direct_impacts=sum(
                item.impact_level == ImpactLevel.DIRECT
                for item in report.impacts
            ),
            indirect_impacts=sum(
                item.impact_level == ImpactLevel.INDIRECT
                for item in report.impacts
            ),
            protected_impacts=sum(
                item.impact_level == ImpactLevel.PROTECTED
                for item in report.impacts
            ),
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


__all__ = [
    "ChangeImpact",
    "DependencyImpact",
    "ChangeImpactReport",
    "T17Metrics",
    "ImpactIntegrationHandoff",
]
