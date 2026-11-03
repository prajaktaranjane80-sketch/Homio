from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (
    ChangeImpactAnalyzer,
    ChangeImpactSecurityError,
    ChangeImpactValidationError,
    ImpactLevel,
    T17Decision,
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
