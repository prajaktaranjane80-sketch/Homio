from __future__ import annotations

from dataclasses import replace
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

from .impact_dependency import (
    build_reverse_dependencies,
    collect_dependency_impacts,
)

from .impact_errors import (
    ChangeImpactCompatibilityError,
    ChangeImpactError,
    ChangeImpactIntegrityError,
    ChangeImpactSecurityError,
    ChangeImpactValidationError,
)

from .impact_identity import fingerprint_report

from .impact_integration import build_handoff

from .impact_metrics import metrics

from .impact_models import (
    ChangeImpact,
    ChangeImpactReport,
    DependencyImpact,
    ImpactIntegrationHandoff,
    T17Metrics,
)

from .impact_policy import ImpactPolicy

from .impact_provenance import T17Provenance

from .impact_registry import (
    ImpactLevel,
    ImpactReason,
    T17Decision,
)

from .impact_security import (
    T17PathSecurity,
)

from .impact_validation import (
    validate_report_contract,
)


class T17RepositoryIntelligenceAdapter:
    def __init__(
        self,
        repository_root: Path,
    ) -> None:
        self.repository_root = (
            repository_root.resolve()
        )

    def files(
        self,
    ) -> tuple[RepositoryFile, ...]:
        return RepositoryScanner(
            self.repository_root
        ).scan()

    def dependency_graph(
        self,
    ) -> DependencyGraph:
        return build_dependency_graph(
            self.repository_root
        )


class ChangeImpactAnalyzer:
    SCHEMA_VERSION = "1.0"

    def __init__(
        self,
        repository_root: Path | str,
        *,
        policy: ImpactPolicy | None = None,
        provenance: T17Provenance | None = None,
    ) -> None:
        self.repository_root = Path(
            repository_root
        ).resolve()

        if not self.repository_root.is_dir():
            raise ChangeImpactError(
                "Repository root is not a directory: "
                f"{self.repository_root}"
            )

        self.policy = (
            policy
            or ImpactPolicy()
        )

        self.provenance = (
            provenance
            or T17Provenance()
        )

        self.policy.validate()
        self.provenance.validate()

        self._security = T17PathSecurity(
            self.repository_root
        )

    def _normalize(
        self,
        paths: Iterable[str],
    ) -> tuple[str, ...]:
        try:
            return self._security.normalize_changed_paths(
                paths
            )

        except ChangeImpactSecurityError:
            raise

        except ValueError as exc:
            raise ChangeImpactValidationError(
                str(exc)
            ) from exc

    def analyze(
        self,
        changed_paths: Iterable[str],
    ) -> ChangeImpactReport:
        changed = self._normalize(
            changed_paths
        )

        if not changed:
            raise ChangeImpactValidationError(
                "At least one changed path is required."
            )

        adapter = (
            T17RepositoryIntelligenceAdapter(
                self.repository_root
            )
        )

        file_map = {
            normalize_repository_path(
                item.relative_path
            ): item
            for item in adapter.files()
        }

        graph = adapter.dependency_graph()

        reverse = build_reverse_dependencies(
            graph
        )

        impacts: list[ChangeImpact] = []
        dependencies: list[DependencyImpact] = []

        protected: set[str] = set()
        unknown: set[str] = set()

        for path in changed:
            item = file_map.get(
                path
            )

            if item is None:
                unknown.add(path)

                impacts.append(
                    ChangeImpact(
                        relative_path=path,
                        impact_level=ImpactLevel.UNKNOWN,
                        reason_code=ImpactReason.UNKNOWN_PATH,
                        authority=None,
                        source_kind=None,
                        dependency_distance=None,
                    )
                )

                continue

            if item.risk == FileRisk.PROTECTED:
                level = (
                    ImpactLevel.PROTECTED
                )

                reason = (
                    ImpactReason.PROTECTED_FILE
                )

                protected.add(path)

            else:
                level = (
                    ImpactLevel.DIRECT
                )

                reason = (
                    ImpactReason.DIRECT_MATCH
                )

            impacts.append(
                ChangeImpact(
                    relative_path=path,
                    impact_level=level,
                    reason_code=reason,
                    authority=item.authority,
                    source_kind=item.source_kind.value,
                    dependency_distance=0,
                )
            )

            dependency_impacts = (
                collect_dependency_impacts(
                    path,
                    reverse,
                )
            )

            dependencies.extend(
                dependency_impacts
            )

            for dependency in dependency_impacts:
                dep_file = file_map.get(
                    dependency.impacted_path
                )

                if dep_file is None:
                    continue

                if (
                    dep_file.risk
                    == FileRisk.PROTECTED
                ):
                    dep_level = (
                        ImpactLevel.PROTECTED
                    )

                    dep_reason = (
                        ImpactReason.PROTECTED_FILE
                    )

                else:
                    dep_level = (
                        ImpactLevel.INDIRECT
                    )

                    dep_reason = (
                        ImpactReason.DEPENDENCY_OF_CHANGED_MODULE
                    )

                impacts.append(
                    ChangeImpact(
                        relative_path=dependency.impacted_path,
                        impact_level=dep_level,
                        reason_code=dep_reason,
                        authority=dep_file.authority,
                        source_kind=dep_file.source_kind.value,
                        dependency_distance=dependency.distance,
                    )
                )

        severity = {
            ImpactLevel.PROTECTED: 4,
            ImpactLevel.DIRECT: 3,
            ImpactLevel.INDIRECT: 2,
            ImpactLevel.UNKNOWN: 1,
        }

        best: dict[
            str,
            ChangeImpact,
        ] = {}

        for impact in impacts:
            previous = best.get(
                impact.relative_path
            )

            if previous is None:
                best[
                    impact.relative_path
                ] = impact
                continue

            if severity[
                impact.impact_level
            ] > severity[
                previous.impact_level
            ]:
                best[
                    impact.relative_path
                ] = impact
                continue

            if (
                severity[
                    impact.impact_level
                ]
                == severity[
                    previous.impact_level
                ]
                and (
                    impact.dependency_distance
                    if impact.dependency_distance is not None
                    else 999
                )
                < (
                    previous.dependency_distance
                    if previous.dependency_distance is not None
                    else 999
                )
            ):
                best[
                    impact.relative_path
                ] = impact

        impact_tuple = tuple(
            sorted(
                best.values(),
                key=lambda item:
                normalize_repository_path(
                    item.relative_path
                ),
            )
        )

        dependency_tuple = tuple(
            sorted(
                set(dependencies),
                key=lambda item: (
                    normalize_repository_path(
                        item.changed_path
                    ),
                    item.distance,
                    normalize_repository_path(
                        item.impacted_path
                    ),
                ),
            )
        )

        decision = (
            T17Decision.FAIL_CLOSED
            if protected and unknown
            else (
                T17Decision.BLOCKED
                if unknown
                else T17Decision.ANALYZE
            )
        )

        provisional = ChangeImpactReport(
            schema_version=self.SCHEMA_VERSION,
            decision=decision,
            changed_paths=changed,
            impacts=impact_tuple,
            dependency_impacts=dependency_tuple,
            protected_paths=tuple(
                sorted(protected)
            ),
            unknown_paths=tuple(
                sorted(unknown)
            ),
            graph_nodes=len(
                graph.nodes
            ),
            graph_edges=len(
                graph.edges
            ),
            fingerprint="",
            policy_schema=self.policy.schema_version,
            provenance_source=self.provenance.source,
            state_mutated=False,
            execution_authorized=False,
        )

        finalized = replace(
            provisional,
            fingerprint=fingerprint_report(
                provisional
            ),
        )

        return finalized

    def validate_report(
        self,
        report: ChangeImpactReport,
    ) -> None:
        validate_report_contract(
            self,
            report,
        )

    @staticmethod
    def metrics(
        report: ChangeImpactReport,
    ) -> T17Metrics:
        return metrics(
            report
        )

    @staticmethod
    def build_handoff(
        report: ChangeImpactReport,
    ) -> ImpactIntegrationHandoff:
        return build_handoff(
            report
        )


__all__ = [
    "ChangeImpactAnalyzer",
    "ChangeImpactError",
    "ChangeImpactValidationError",
    "ChangeImpactSecurityError",
    "ChangeImpactIntegrityError",
    "ChangeImpactCompatibilityError",
    "ChangeImpact",
    "DependencyImpact",
    "ChangeImpactReport",
    "T17Metrics",
    "ImpactIntegrationHandoff",
    "ImpactPolicy",
    "T17Provenance",
    "ImpactLevel",
    "T17Decision",
    "ImpactReason",
]
