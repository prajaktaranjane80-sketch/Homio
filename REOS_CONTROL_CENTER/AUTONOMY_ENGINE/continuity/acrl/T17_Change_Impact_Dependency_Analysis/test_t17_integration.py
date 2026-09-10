from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (
    ChangeImpactAnalyzer,
)


def test_handoff_is_non_executing(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "x.py").write_text("X=1\n")

    report = ChangeImpactAnalyzer(root).analyze(("x.py",))
    handoff = ChangeImpactAnalyzer.build_handoff(report)

    assert handoff.ready_for_handoff is True
    assert report.execution_authorized is False
