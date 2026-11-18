import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (
    ChangeImpactAnalyzer,
    ChangeImpactSecurityError,
    ChangeImpactValidationError,
    ImpactLevel,
    T17Decision,
    T17RepositoryIntelligenceAdapter,
)

from AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    FileAuthority,
    FileRisk,
    SourceKind,
)


def build_repo(root: Path):
    (root / "app").mkdir(parents=True)
    (root / "app" / "__init__.py").write_text("")
    (root / "app" / "base.py").write_text("VALUE = 1\n")
    (root / "app" / "service.py").write_text(
        "from app.base import VALUE\nRESULT = VALUE\n"
    )
    (root / "app" / "api.py").write_text(
        "from app.service import RESULT\nPUBLIC = RESULT\n"
    )
    (root / "state.json").write_text("{}\n")
    return root


def engine(tmp_path):
    return ChangeImpactAnalyzer(build_repo(tmp_path / "repo"))


def test_direct_and_transitive_impact(tmp_path):
    report = engine(tmp_path).analyze(("app/base.py",))

    assert report.decision == T17Decision.ANALYZE

    assert any(
        x.impacted_path == "app/service.py"
        for x in report.dependency_impacts
    )

    assert any(
        x.impacted_path == "app/api.py"
        for x in report.dependency_impacts
    )


def test_distance(tmp_path):
    report = engine(tmp_path).analyze(("app/base.py",))

    distances = {
        x.impacted_path: x.distance
        for x in report.dependency_impacts
    }

    assert distances["app/service.py"] == 1
    assert distances["app/api.py"] == 2


def test_unknown_missing_path_blocks(tmp_path):
    report = engine(tmp_path).analyze(("missing.py",))

    assert report.decision == T17Decision.BLOCKED
    assert report.unknown_paths == ("missing.py",)
    assert report.ready_for_handoff is False


def test_existing_unknown_classification_blocks(tmp_path):
    root = build_repo(tmp_path / "repo")
    opaque = root / "opaque.payload"

    opaque.write_text(
        "unknown file type\n",
        encoding="utf-8",
    )

    report = ChangeImpactAnalyzer(root).analyze(
        ("opaque.payload",)
    )

    assert report.decision == T17Decision.BLOCKED
    assert report.unknown_paths == ("opaque.payload",)
    assert report.impacts[0].impact_level == ImpactLevel.UNKNOWN
    assert report.ready_for_handoff is False


def test_unregistered_extensionless_file_remains_unknown(tmp_path):
    root = build_repo(tmp_path / "repo")
    opaque = root / "unregistered_extensionless_file"

    opaque.write_text(
        "This is not the canonical backend master.\n",
        encoding="utf-8",
    )

    report = ChangeImpactAnalyzer(root).analyze(
        ("unregistered_extensionless_file",)
    )

    assert report.decision == T17Decision.BLOCKED
    assert report.unknown_paths == (
        "unregistered_extensionless_file",
    )
    assert report.ready_for_handoff is False


def test_protected_detected_and_handoff_blocked(tmp_path):
    report = engine(tmp_path).analyze(("state.json",))

    assert report.impacts[0].impact_level == ImpactLevel.PROTECTED
    assert report.protected_paths == ("state.json",)
    assert report.decision == T17Decision.BLOCKED
    assert report.ready_for_handoff is False


def test_path_normalization(tmp_path):
    report = engine(tmp_path).analyze((r".\app\base.py",))

    assert report.changed_paths == ("app/base.py",)


def test_idempotent_duplicate_paths(tmp_path):
    report = engine(tmp_path).analyze(
        ("app/base.py", "app/base.py")
    )

    assert report.changed_paths == ("app/base.py",)


def test_empty_rejected(tmp_path):
    with pytest.raises(ChangeImpactValidationError):
        engine(tmp_path).analyze(())


def test_traversal_rejected(tmp_path):
    with pytest.raises(ChangeImpactSecurityError):
        engine(tmp_path).analyze(("../outside.py",))


def test_report_fingerprint_and_validation(tmp_path):
    analyzer = engine(tmp_path)
    report = analyzer.analyze(("app/base.py",))

    assert len(report.fingerprint) == 64
    analyzer.validate_report(report)


def test_state_not_mutated(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = (root / "state.json").read_bytes()

    ChangeImpactAnalyzer(root).analyze(("app/base.py",))

    assert (root / "state.json").read_bytes() == before


def test_read_only_flags(tmp_path):
    report = engine(tmp_path).analyze(("app/base.py",))

    assert report.state_mutated is False
    assert report.execution_authorized is False


def test_shell_scripts_are_known_direct_sources(tmp_path):
    root = build_repo(tmp_path / "repo")
    shell_script = root / "scripts" / "wiring_tests.sh"
    shell_script.parent.mkdir(parents=True)
    shell_script.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n",
        encoding="utf-8",
    )

    adapter = T17RepositoryIntelligenceAdapter(root)
    classified = next(
        item
        for item in adapter.files()
        if item.relative_path == "scripts/wiring_tests.sh"
    )

    assert classified.source_kind.value == "SHELL"
    assert classified.authority == FileAuthority.AUTHORITATIVE
    assert classified.risk == FileRisk.NORMAL
    assert classified.is_symlink is False

    report = ChangeImpactAnalyzer(root).analyze(
        ("scripts/wiring_tests.sh",)
    )

    assert report.decision == T17Decision.ANALYZE
    assert report.unknown_paths == ()
    assert report.protected_paths == ()
    assert report.ready_for_handoff is True

    impact = next(
        item
        for item in report.impacts
        if item.relative_path == "scripts/wiring_tests.sh"
    )
    assert impact.impact_level == ImpactLevel.DIRECT
    assert impact.source_kind == "SHELL"
    assert impact.authority == FileAuthority.AUTHORITATIVE


def test_shell_symlink_remains_blocked_by_repository_boundary(tmp_path):
    root = build_repo(tmp_path / "repo")
    outside = tmp_path / "outside.sh"
    outside.write_text(
        "#!/usr/bin/env bash\nSECRET=true\n",
        encoding="utf-8",
    )

    link = root / "untrusted.sh"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(
            f"Platform does not support symlink creation: {exc}"
        )

    with pytest.raises(
        ChangeImpactSecurityError,
        match="Changed path escapes repository boundary",
    ):
        ChangeImpactAnalyzer(root).analyze(
            ("untrusted.sh",)
        )


def test_typescript_backend_sources_and_tests_are_classified_safely(
    tmp_path,
):
    root = build_repo(tmp_path / "repo")

    source = (
        root
        / "backend"
        / "src"
        / "security"
        / "api-security.ts"
    )
    source.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    source.write_text(
        "export const securityBoundary = true;\n",
        encoding="utf-8",
    )

    test_file = (
        root
        / "backend"
        / "tests"
        / "api-security.test.ts"
    )
    test_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    test_file.write_text(
        "import { describe, it } from 'vitest';\n",
        encoding="utf-8",
    )

    adapter = T17RepositoryIntelligenceAdapter(root)
    classified = {
        item.relative_path: item
        for item in adapter.files()
    }

    source_item = classified[
        "backend/src/security/api-security.ts"
    ]
    test_item = classified[
        "backend/tests/api-security.test.ts"
    ]

    assert source_item.source_kind.value == "TYPESCRIPT"
    assert source_item.authority == FileAuthority.AUTHORITATIVE
    assert source_item.risk == FileRisk.NORMAL
    assert source_item.is_symlink is False

    assert test_item.source_kind == SourceKind.TEST
    assert test_item.authority == FileAuthority.DERIVED
    assert test_item.risk == FileRisk.NORMAL
    assert test_item.is_symlink is False

    analyzer = ChangeImpactAnalyzer(root)
    report = analyzer.analyze(
        (
            "backend/src/security/api-security.ts",
            "backend/tests/api-security.test.ts",
        )
    )
    analyzer.validate_report(report)

    assert report.decision == T17Decision.ANALYZE
    assert report.unknown_paths == ()
    assert report.protected_paths == ()
    assert report.ready_for_handoff is True


def test_typescript_symlink_remains_blocked_by_repository_boundary(
    tmp_path,
):
    root = build_repo(tmp_path / "repo")
    outside = tmp_path / "outside.ts"
    outside.write_text(
        "export const secret = true;\n",
        encoding="utf-8",
    )

    link = root / "untrusted.ts"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(
            f"Platform does not support symlink creation: {exc}"
        )

    with pytest.raises(
        ChangeImpactSecurityError,
        match="Changed path escapes repository boundary",
    ):
        ChangeImpactAnalyzer(root).analyze(
            ("untrusted.ts",)
        )


def test_exact_backend_master_is_known_documentation(
    tmp_path,
):
    root = build_repo(tmp_path / "repo")

    relative_path = (
        "REOS_CONTROL_CENTER/architecture/backend/plans/"
        "HOMIO_Backend_Structure"
    )

    master = root / relative_path
    master.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    master.write_text(
        "# HOMIO Backend Structure\n\n"
        "Canonical backend architecture and dependency contract.\n",
        encoding="utf-8",
    )

    adapter = T17RepositoryIntelligenceAdapter(root)

    classified = next(
        item
        for item in adapter.files()
        if item.relative_path == relative_path
    )

    assert classified.source_kind == SourceKind.DOCUMENTATION
    assert classified.authority == FileAuthority.DERIVED
    assert classified.risk == FileRisk.NORMAL
    assert classified.is_symlink is False

    analyzer = ChangeImpactAnalyzer(root)
    report = analyzer.analyze((relative_path,))
    analyzer.validate_report(report)

    assert report.decision == T17Decision.ANALYZE
    assert report.unknown_paths == ()
    assert report.protected_paths == ()
    assert report.ready_for_handoff is True

    impact = next(
        item
        for item in report.impacts
        if item.relative_path == relative_path.lower()
    )

    assert impact.impact_level == ImpactLevel.DIRECT
    assert impact.source_kind == SourceKind.DOCUMENTATION.value
    assert impact.authority == FileAuthority.DERIVED


def test_exact_backend_activation_inventory_is_t17_handoff_ready():
    repository_root = Path(__file__).resolve().parents[5]
    wrapper_path = (
        repository_root
        / ".github/actions/homio-backend-ci/transitions/"
        / "backend-workstream-activation/scripts/"
        / "activate_backend_workstream_wrapper.py"
    )

    assert wrapper_path.is_file()

    spec = importlib.util.spec_from_file_location(
        "homio_backend_activation_inventory_preflight",
        wrapper_path,
    )
    assert spec is not None
    assert spec.loader is not None

    wrapper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = wrapper
    spec.loader.exec_module(wrapper)

    assert len(wrapper.REPAIRED_ACTIVATION_PATHS) == 20

    source_paths = wrapper.source_paths_for_t17(
        wrapper.REPAIRED_ACTIVATION_PATHS
    )

    assert len(source_paths) == 19
    assert "REOS_CONTROL_CENTER/PS Output" not in source_paths
    assert (
        ".github/actions/homio-backend-ci/verification/scripts/"
        "financial_context_tenant.sh"
    ) in source_paths
    assert (
        ".github/actions/homio-backend-ci/verification/scripts/"
        "wiring_tests.sh"
    ) in source_paths

    analyzer = ChangeImpactAnalyzer(repository_root)
    report = analyzer.analyze(source_paths)
    analyzer.validate_report(report)

    assert report.ready_for_handoff is True, (
        f"T17 activation preflight is not ready: "
        f"decision={report.decision.value}, "
        f"protected={report.protected_paths}, "
        f"unknown={report.unknown_paths}"
    )
    assert report.decision == T17Decision.ANALYZE
    assert report.protected_paths == ()
    assert report.unknown_paths == ()


def _guard_literal_assignment(
    tree: ast.Module,
    name: str,
):
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        matches = any(
            isinstance(target, ast.Name)
            and target.id == name
            for target in node.targets
        )

        if matches:
            return node.value

    raise AssertionError(
        f"Required guarded-transition constant is missing: {name}"
    )


def test_b2_dependency_correction_inventory_matches_guard_and_t17():
    repository_root = Path(__file__).resolve().parents[5]

    guard_path = (
        repository_root
        / ".github/actions/homio-backend-ci/transitions/"
        / "backend-b2-dependency-correction/scripts/"
        / "guarded_transition.py"
    )

    assert guard_path.is_file()

    guard_tree = ast.parse(
        guard_path.read_text(encoding="utf-8"),
        filename=str(guard_path),
    )

    baseline_head = ast.literal_eval(
        _guard_literal_assignment(
            guard_tree,
            "BASELINE_HEAD",
        )
    )

    master_path = ast.literal_eval(
        _guard_literal_assignment(
            guard_tree,
            "MASTER_PATH",
        )
    )

    expected_paths_node = _guard_literal_assignment(
        guard_tree,
        "EXPECTED_SOURCE_PATHS",
    )

    assert isinstance(expected_paths_node, ast.Set)

    expected_paths = set()

    for element in expected_paths_node.elts:
        if (
            isinstance(element, ast.Name)
            and element.id == "MASTER_PATH"
        ):
            expected_paths.add(master_path)
        else:
            expected_paths.add(
                ast.literal_eval(element)
            )

    changed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            baseline_head,
            "HEAD",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    actual_paths = set(
        changed.stdout.splitlines()
    )

    assert actual_paths == expected_paths, (
        "B2 dependency correction source-path inventory differs from "
        "the guarded exact-SHA allowlist; "
        f"missing={sorted(expected_paths - actual_paths)}; "
        f"unexpected={sorted(actual_paths - expected_paths)}"
    )

    analyzer = ChangeImpactAnalyzer(
        repository_root
    )
    report = analyzer.analyze(
        tuple(sorted(actual_paths))
    )
    analyzer.validate_report(report)

    assert report.ready_for_handoff is True, (
        "B2 dependency correction T17 preflight is not ready: "
        f"decision={report.decision.value}; "
        f"unknown={list(report.unknown_paths)}; "
        f"protected={list(report.protected_paths)}"
    )
    assert report.unknown_paths == ()
    assert report.protected_paths == ()
    assert report.state_mutated is False
    assert report.execution_authorized is False
