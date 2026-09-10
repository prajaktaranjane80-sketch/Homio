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


def test_unknown_blocks(tmp_path):
    report = engine(tmp_path).analyze(("missing.py",))

    assert report.decision == T17Decision.BLOCKED
    assert report.unknown_paths == ("missing.py",)


def test_protected_detected(tmp_path):
    report = engine(tmp_path).analyze(("state.json",))

    assert report.impacts[0].impact_level == ImpactLevel.PROTECTED


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
    e = engine(tmp_path)
    r = e.analyze(("app/base.py",))

    assert len(r.fingerprint) == 64
    e.validate_report(r)


def test_state_not_mutated(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = (root / "state.json").read_bytes()

    ChangeImpactAnalyzer(root).analyze(("app/base.py",))

    assert (root / "state.json").read_bytes() == before


def test_read_only_flags(tmp_path):
    r = engine(tmp_path).analyze(("app/base.py",))

    assert r.state_mutated is False
    assert r.execution_authorized is False
