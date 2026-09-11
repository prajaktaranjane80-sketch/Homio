from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from ..T03_State_Reconstruction.state_reconstruction import (
    ExecutionStateSnapshot,
)
from ..T12_Resume_Safety_Validation.resume_safety_validation import (
    ResumeSafetyReport,
)
from ..T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)

from .t19_identity import fingerprint
from .t19_models import (
    SelectedTest,
    T19Decision,
    TestCandidate,
    TestPriority,
    TestSelectionPlan,
    TestSelectionReason,
)
from .t19_validation import (
    validate_inputs,
)


EXCLUDED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
}

MAX_TEST_FILE_SIZE = 2 * 1024 * 1024
MAX_SELECTED_TESTS = 200


def _normalize(value: str) -> str:
    return value.replace("\\", "/").lstrip("./").lower()


def _module_to_path(module: str) -> str:
    return _normalize(
        module.replace(".", "/") + ".py"
    )


def _parse_imports(path: Path) -> tuple[str, ...]:
    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return ()

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                imports.add(item.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return tuple(sorted(imports))


def discover_tests(
    repository_root: Path | str,
) -> tuple[TestCandidate, ...]:
    root = Path(repository_root).resolve()

    if not root.is_dir():
        raise ValueError(
            f"Repository root does not exist: {root}"
        )

    candidates: list[TestCandidate] = []

    for path in root.rglob("*.py"):
        if any(
            part in EXCLUDED_DIRECTORIES
            for part in path.parts
        ):
            continue

        if path.stat().st_size > MAX_TEST_FILE_SIZE:
            continue

        name = path.name.lower()

        if not (
            name.startswith("test_")
            or name.endswith("_test.py")
        ):
            continue

        relative = _normalize(
            str(path.relative_to(root))
        )

        stem = path.stem.lower()

        if stem.startswith("test_"):
            stem = stem[5:]

        if stem.endswith("_test"):
            stem = stem[:-5]

        candidates.append(
            TestCandidate(
                path=relative,
                imports=_parse_imports(path),
                stem=stem,
                priority=TestPriority.NORMAL,
            )
        )

    return tuple(
        sorted(
            candidates,
            key=lambda item: item.path,
        )
    )


def _path_stem(path: str) -> str:
    stem = Path(path).stem.lower()

    if stem.startswith("test_"):
        stem = stem[5:]

    if stem.endswith("_test"):
        stem = stem[:-5]

    return stem


def _matches_source(
    test: TestCandidate,
    source_path: str,
) -> tuple[TestSelectionReason, ...]:
    source = _normalize(source_path)
    source_stem = _path_stem(source)

    reasons: list[TestSelectionReason] = []

    test_import_paths = {
        _module_to_path(item)
        for item in test.imports
    }

    if source in test_import_paths:
        reasons.append(
            TestSelectionReason.IMPORT_MATCH
        )

    if source_stem and source_stem == test.stem:
        reasons.append(
            TestSelectionReason.NAME_MATCH
        )

    source_parts = Path(source).parts[:-1]

    if source_parts:
        test_path = Path(test.path).parts

        if all(
            part in test_path
            for part in source_parts
        ):
            reasons.append(
                TestSelectionReason.NAME_MATCH
            )

    return tuple(
        dict.fromkeys(reasons)
    )


def _score(
    reasons: Iterable[TestSelectionReason],
    *,
    direct: bool,
    contract: bool,
    integration: bool,
) -> tuple[int, TestPriority]:
    reason_set = set(reasons)

    score = 0

    if direct:
        score += 100

    if TestSelectionReason.IMPORT_MATCH in reason_set:
        score += 80

    if TestSelectionReason.NAME_MATCH in reason_set:
        score += 50

    if contract:
        score += 35

    if integration:
        score += 25

    if TestSelectionReason.IMPACTED_CHANGE in reason_set:
        score += 40

    if score >= 100:
        return score, TestPriority.CRITICAL

    if score >= 70:
        return score, TestPriority.HIGH

    if score >= 35:
        return score, TestPriority.NORMAL

    return score, TestPriority.LOW


class T19TestSelectionEngine:
    """Deterministic, read-only intelligent test selector."""

    SCHEMA_VERSION = "1.0"

    def build_plan(
        self,
        *,
        repository_root: Path | str,
        state_snapshot: ExecutionStateSnapshot,
        resume_report: ResumeSafetyReport,
        impact_report: ChangeImpactReport,
        failure_paths: tuple[str, ...] = (),
    ) -> TestSelectionPlan:
        root = Path(repository_root).resolve()

        validate_inputs(
            state_snapshot,
            resume_report,
            impact_report,
            root,
        )

        candidates = discover_tests(root)

        changed = tuple(
            _normalize(path)
            for path in impact_report.changed_paths
        )

        impacted = tuple(
            _normalize(path)
            for path in impact_report.impacted_paths
        )

        all_relevant = tuple(
            dict.fromkeys(
                changed + impacted
            )
        )

        selected: dict[
            str,
            SelectedTest,
        ] = {}

        failure_set = {
            _normalize(path)
            for path in failure_paths
        }

        for test in candidates:
            reasons: list[TestSelectionReason] = []

            direct = False
            contract = (
                "contract" in test.path
            )
            integration = (
                "integration" in test.path
                or "regression" in test.path
            )

            for source in changed:
                matches = _matches_source(
                    test,
                    source,
                )

                if matches:
                    direct = True
                    reasons.append(
                        TestSelectionReason.DIRECT_CHANGE
                    )
                    reasons.extend(matches)

            for source in impacted:
                matches = _matches_source(
                    test,
                    source,
                )

                if matches:
                    reasons.append(
                        TestSelectionReason.IMPACTED_CHANGE
                    )
                    reasons.extend(matches)

            if contract and changed:
                reasons.append(
                    TestSelectionReason.CONTRACT_MATCH
                )

            if integration and impacted:
                reasons.append(
                    TestSelectionReason.INTEGRATION_MATCH
                )

            if _normalize(test.path) in failure_set:
                reasons.append(
                    TestSelectionReason.FAILURE_RELEVANT
                )

            reasons = list(
                dict.fromkeys(reasons)
            )

            if not reasons:
                continue

            score, priority = _score(
                reasons,
                direct=direct,
                contract=contract,
                integration=integration,
            )

            selected[test.path] = SelectedTest(
                path=test.path,
                priority=priority,
                reasons=tuple(reasons),
                score=score,
            )

        if not selected and candidates:
            fallback = tuple(
                candidates[: min(
                    len(candidates),
                    20,
                )]
            )

            selected = {
                item.path: SelectedTest(
                    path=item.path,
                    priority=TestPriority.LOW,
                    reasons=(
                        TestSelectionReason.FALLBACK_SMOKE,
                    ),
                    score=10,
                )
                for item in fallback
            }

            decision = T19Decision.FALLBACK
            explanation = (
                "No direct or impacted test match was found; "
                "a deterministic smoke subset was selected."
            )
        elif selected:
            decision = T19Decision.SELECT

            explanation = (
                "Tests were selected from changed paths, "
                "dependency impacts, imports, names, "
                "contract/integration signals, and failure relevance."
            )
        else:
            decision = T19Decision.BLOCK

            explanation = (
                "No test candidates were discovered in the repository."
            )

        selected_tests = tuple(
            sorted(
                selected.values(),
                key=lambda item: (
                    -item.score,
                    item.path,
                ),
            )[:MAX_SELECTED_TESTS]
        )

        base = {
            "schema_version": self.SCHEMA_VERSION,
            "decision": decision.value,
            "selected_tests": [
                {
                    "path": item.path,
                    "priority": item.priority.value,
                    "reasons": [
                        reason.value
                        for reason in item.reasons
                    ],
                    "score": item.score,
                }
                for item in selected_tests
            ],
            "candidate_count": len(candidates),
            "changed_paths": list(changed),
            "impacted_paths": list(impacted),
            "state_fingerprint": (
                state_snapshot.source_state_sha256
            ),
            "impact_fingerprint": (
                impact_report.fingerprint
            ),
            "explanation": explanation,
        }

        return TestSelectionPlan(
            schema_version=self.SCHEMA_VERSION,
            decision=decision,
            selected_tests=selected_tests,
            candidate_count=len(candidates),
            changed_paths=changed,
            impacted_paths=impacted,
            state_fingerprint=(
                state_snapshot.source_state_sha256
            ),
            impact_fingerprint=(
                impact_report.fingerprint
            ),
            plan_fingerprint=fingerprint(base),
            explanation=explanation,
        )


def select_tests(
    *,
    repository_root: Path | str,
    state_snapshot: ExecutionStateSnapshot,
    resume_report: ResumeSafetyReport,
    impact_report: ChangeImpactReport,
    failure_paths: tuple[str, ...] = (),
) -> TestSelectionPlan:
    return T19TestSelectionEngine().build_plan(
        repository_root=repository_root,
        state_snapshot=state_snapshot,
        resume_report=resume_report,
        impact_report=impact_report,
        failure_paths=failure_paths,
    )


__all__ = [
    "T19TestSelectionEngine",
    "discover_tests",
    "select_tests",
]
