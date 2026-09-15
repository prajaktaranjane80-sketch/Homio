from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Iterable

from ..T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    FileRisk,
    RepositoryScanner,
    normalize_repository_path,
)

from .change_impact_analysis import (
    ChangeImpactAnalyzer,
    ChangeImpactReport,
    ImpactLevel,
    T17Decision,
)


AUTHORITY = "REOS_CONTROL_CENTER"
SCHEMA_VERSION = "1.0"


class ChangeImpactContextError(RuntimeError):
    """Base error for Part 15 change-impact context reconstruction."""


class ChangeImpactContextValidationError(ChangeImpactContextError):
    """Raised when the reconstruction request is invalid."""


class ChangeImpactContextSecurityError(ChangeImpactContextError):
    """Raised when repository/path security boundaries are violated."""


class ChangeImpactContextIntegrityError(ChangeImpactContextError):
    """Raised when impact reconstruction cannot be trusted."""


class ChangeImpactContextDecision(str):
    """Stable Part 15 decision values."""

    RESOLVED = "RESOLVED"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class ChangeImpactContextRequest:
    repository_root: Path
    current_gate: str
    current_task: str
    current_subtask: str
    changed_paths: tuple[str, ...]
    authority: str = AUTHORITY

    @classmethod
    def create(
        cls,
        repository_root: Path | str,
        current_gate: str,
        current_task: str,
        current_subtask: str,
        changed_paths: Iterable[str],
        authority: str = AUTHORITY,
    ) -> "ChangeImpactContextRequest":
        root = Path(repository_root).resolve()

        if not current_gate.strip():
            raise ChangeImpactContextValidationError(
                "current_gate is required."
            )

        if not current_task.strip():
            raise ChangeImpactContextValidationError(
                "current_task is required."
            )

        if not current_subtask.strip():
            raise ChangeImpactContextValidationError(
                "current_subtask is required."
            )

        normalized = tuple(
            sorted(
                {
                    item.replace("\\", "/").strip()
                    for item in changed_paths
                    if str(item).strip()
                }
            )
        )

        if not normalized:
            raise ChangeImpactContextValidationError(
                "At least one changed path is required."
            )

        return cls(
            repository_root=root,
            current_gate=current_gate.strip(),
            current_task=current_task.strip(),
            current_subtask=current_subtask.strip(),
            changed_paths=normalized,
            authority=authority.strip(),
        )


@dataclass(frozen=True, slots=True)
class ChangeImpactContextReport:
    schema_version: str
    authority: str
    decision: str

    current_gate: str
    current_task: str
    current_subtask: str

    changed_paths: tuple[str, ...]
    affected_modules: tuple[str, ...]
    dependent_modules: tuple[str, ...]
    test_impact: tuple[str, ...]
    contract_impact: tuple[str, ...]
    authority_impact: tuple[str, ...]

    protected_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]

    graph_nodes: int
    graph_edges: int

    impact_fingerprint: str

    state_mutated: bool = False
    execution_authorized: bool = False

    @property
    def blast_radius(self) -> int:
        return len(
            set(self.affected_modules)
            | set(self.dependent_modules)
            | set(self.test_impact)
            | set(self.contract_impact)
        )

    @property
    def ready_for_handoff(self) -> bool:
        return (
            self.decision == ChangeImpactContextDecision.RESOLVED
            and not self.unknown_paths
            and not self.protected_paths
            and not self.state_mutated
            and not self.execution_authorized
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision,
            "current_gate": self.current_gate,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "changed_paths": list(self.changed_paths),
            "affected_modules": list(self.affected_modules),
            "dependent_modules": list(self.dependent_modules),
            "test_impact": list(self.test_impact),
            "contract_impact": list(self.contract_impact),
            "authority_impact": list(self.authority_impact),
            "protected_paths": list(self.protected_paths),
            "unknown_paths": list(self.unknown_paths),
            "graph_nodes": self.graph_nodes,
            "graph_edges": self.graph_edges,
            "impact_fingerprint": self.impact_fingerprint,
            "blast_radius": self.blast_radius,
            "state_mutated": self.state_mutated,
            "execution_authorized": self.execution_authorized,
        }


class ChangeImpactContextEngine:
    """
    Part 15 thin reconstruction boundary.

    It does not replace T17.
    It consumes T17 evidence and adds reconstruction context:
    tests, contracts, authority impact, and blast-radius summary.
    """

    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()

        if not self.repository_root.is_dir():
            raise ChangeImpactContextError(
                f"Repository root is not a directory: "
                f"{self.repository_root}"
            )

    @staticmethod
    def _fingerprint(
        payload: dict[str, object],
    ) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def _discover_test_impact(
        self,
        affected: set[str],
        dependent: set[str],
    ) -> tuple[str, ...]:
        targets = affected | dependent
        scanner = RepositoryScanner(self.repository_root)

        impacted: set[str] = set()

        for item in scanner.scan():
            relative = normalize_repository_path(
                item.relative_path
            )

            is_test = (
                item.source_kind.value == "TEST"
                or relative.startswith("tests/")
                or "/tests/" in relative
                or relative.startswith("test_")
                or relative.endswith("_test.py")
            )

            if not is_test:
                continue

            try:
                text = (
                    (self.repository_root / relative)
                    .read_text(encoding="utf-8")
                    .replace("\\", "/")
                )
            except (OSError, UnicodeDecodeError):
                continue

            for target in targets:
                normalized_target = normalize_repository_path(
                    target
                )

                module_hint = normalized_target.removesuffix(".py")
                module_hint = module_hint.replace("/", ".")

                if (
                    normalized_target in text
                    or module_hint in text
                ):
                    impacted.add(relative)
                    break

        return tuple(sorted(impacted))

    def _discover_contract_impact(
        self,
        affected: set[str],
        dependent: set[str],
    ) -> tuple[str, ...]:
        targets = affected | dependent
        contracts: set[str] = set()

        for path in self.repository_root.rglob("*.contract.json"):
            if not path.is_file():
                continue

            relative = normalize_repository_path(
                path.relative_to(self.repository_root).as_posix()
            )

            contracts.add(relative)

            try:
                text = path.read_text(
                    encoding="utf-8"
                ).replace("\\", "/")
            except (OSError, UnicodeDecodeError):
                continue

            related = False

            for target in targets:
                normalized_target = normalize_repository_path(
                    target
                )

                module_hint = normalized_target.removesuffix(".py")
                module_hint = module_hint.replace("/", ".")

                if (
                    normalized_target in text
                    or module_hint in text
                ):
                    related = True
                    break

            if not related:
                contracts.discard(relative)

        return tuple(sorted(contracts))

    @staticmethod
    def _authority_impact(
        report: ChangeImpactReport,
    ) -> tuple[str, ...]:
        impacts: set[str] = set()

        if report.protected_paths:
            impacts.add("PROTECTED_FILE")

        for item in report.impacts:
            if item.authority is not None:
                impacts.add(
                    f"FILE_AUTHORITY:{item.authority.value}"
                )

        if report.unknown_paths:
            impacts.add("UNKNOWN_REPOSITORY_PATH")

        if report.decision == T17Decision.FAIL_CLOSED:
            impacts.add("FAIL_CLOSED")

        if not impacts:
            impacts.add("NO_AUTHORITY_IMPACT")

        return tuple(sorted(impacts))

    def reconstruct(
        self,
        request: ChangeImpactContextRequest,
    ) -> ChangeImpactContextReport:
        if request.authority != AUTHORITY:
            raise ChangeImpactContextValidationError(
                f"Unsupported authority: {request.authority}"
            )

        try:
            t17 = ChangeImpactAnalyzer(
                self.repository_root
            )

            report = t17.analyze(
                request.changed_paths
            )

        except ChangeImpactContextError:
            raise

        except Exception as exc:
            raise ChangeImpactContextIntegrityError(
                "Unable to reconstruct change-impact context."
            ) from exc

        affected = {
            item.relative_path
            for item in report.impacts
            if item.impact_level
            in {
                ImpactLevel.DIRECT,
                ImpactLevel.PROTECTED,
            }
        }

        dependent = {
            item.impacted_path
            for item in report.dependency_impacts
        }

        tests = self._discover_test_impact(
            affected,
            dependent,
        )

        contracts = self._discover_contract_impact(
            affected,
            dependent,
        )

        authority = self._authority_impact(
            report
        )

        if report.decision == T17Decision.FAIL_CLOSED:
            decision = (
                ChangeImpactContextDecision.FAIL_CLOSED
            )
        elif report.decision == T17Decision.BLOCKED:
            decision = (
                ChangeImpactContextDecision.BLOCKED
            )
        else:
            decision = (
                ChangeImpactContextDecision.RESOLVED
            )

        fingerprint_payload = {
            "schema_version": SCHEMA_VERSION,
            "authority": AUTHORITY,
            "decision": decision,
            "current_gate": request.current_gate,
            "current_task": request.current_task,
            "current_subtask": request.current_subtask,
            "changed_paths": request.changed_paths,
            "affected_modules": tuple(sorted(affected)),
            "dependent_modules": tuple(sorted(dependent)),
            "test_impact": tests,
            "contract_impact": contracts,
            "authority_impact": authority,
            "protected_paths": report.protected_paths,
            "unknown_paths": report.unknown_paths,
            "graph_nodes": report.graph_nodes,
            "graph_edges": report.graph_edges,
        }

        fingerprint = self._fingerprint(
            fingerprint_payload
        )

        return ChangeImpactContextReport(
            schema_version=SCHEMA_VERSION,
            authority=AUTHORITY,
            decision=decision,
            current_gate=request.current_gate,
            current_task=request.current_task,
            current_subtask=request.current_subtask,
            changed_paths=report.changed_paths,
            affected_modules=tuple(
                sorted(affected)
            ),
            dependent_modules=tuple(
                sorted(dependent)
            ),
            test_impact=tests,
            contract_impact=contracts,
            authority_impact=authority,
            protected_paths=report.protected_paths,
            unknown_paths=report.unknown_paths,
            graph_nodes=report.graph_nodes,
            graph_edges=report.graph_edges,
            impact_fingerprint=fingerprint,
            state_mutated=False,
            execution_authorized=False,
        )


def reconstruct_change_impact_context(
    repository_root: Path | str,
    *,
    current_gate: str,
    current_task: str,
    current_subtask: str,
    changed_paths: Iterable[str],
    authority: str = AUTHORITY,
) -> ChangeImpactContextReport:
    request = ChangeImpactContextRequest.create(
        repository_root=repository_root,
        current_gate=current_gate,
        current_task=current_task,
        current_subtask=current_subtask,
        changed_paths=changed_paths,
        authority=authority,
    )

    return ChangeImpactContextEngine(
        repository_root
    ).reconstruct(
        request
    )


__all__ = [
    "AUTHORITY",
    "SCHEMA_VERSION",
    "ChangeImpactContextDecision",
    "ChangeImpactContextError",
    "ChangeImpactContextValidationError",
    "ChangeImpactContextSecurityError",
    "ChangeImpactContextIntegrityError",
    "ChangeImpactContextRequest",
    "ChangeImpactContextReport",
    "ChangeImpactContextEngine",
    "reconstruct_change_impact_context",
]
