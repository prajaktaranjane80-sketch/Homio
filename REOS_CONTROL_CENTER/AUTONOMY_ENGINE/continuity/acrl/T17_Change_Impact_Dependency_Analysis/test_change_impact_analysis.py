"""ACRL T17-T01 — Change Impact Analysis tests.

The T17 test surface owns its own repository fixture.

Design rules:
- no dependency on global conftest.py
- no dependency on another test module's fixture
- deterministic temporary repository
- read-only analyzer verification
- unknown paths fail closed
- Windows/POSIX path normalization is exercised
"""

from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.change_impact_analysis import (
    ChangeImpactAnalyzer,
    ImpactLevel,
)


def build_repository(root: Path) -> Path:
    """Build the minimal deterministic repository required by T17."""

    root.mkdir(
        parents=False,
        exist_ok=False,
    )

    (root / "core").mkdir(
        parents=False,
        exist_ok=False,
    )

    (root / "tests").mkdir(
        parents=False,
        exist_ok=False,
    )

    (root / "main.py").write_text(
        "from core.domain import Domain\n\n"
        "VALUE = Domain\n",
        encoding="utf-8",
    )

    (root / "core" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    (root / "core" / "domain.py").write_text(
        "class Domain:\n"
        "    pass\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_domain.py").write_text(
        "from core.domain import Domain\n\n"
        "\n"
        "def test_domain():\n"
        "    assert Domain is not None\n",
        encoding="utf-8",
    )

    return root


def test_unknown_change_has_unknown_impact(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    analyzer = ChangeImpactAnalyzer(repository)

    report = analyzer.analyze(
        ("does/not/exist.py",)
    )

    assert report.changed_paths == (
        "does/not/exist.py",
    )

    assert len(report.impacts) == 1
    assert report.impacts[0].impact_level == ImpactLevel.UNKNOWN


def test_repository_file_is_classified(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    analyzer = ChangeImpactAnalyzer(repository)

    report = analyzer.analyze(
        ("main.py",)
    )

    assert report.changed_paths == (
        "main.py",
    )

    assert len(report.impacts) == 1
    assert report.impacts[0].relative_path == "main.py"


def test_analysis_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    analyzer = ChangeImpactAnalyzer(repository)

    first = analyzer.analyze(
        ("main.py",)
    )

    second = analyzer.analyze(
        ("main.py",)
    )

    assert first == second


def test_multiple_paths_are_normalized(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    analyzer = ChangeImpactAnalyzer(repository)

    report = analyzer.analyze(
        (
            r".\main.py",
            r".\core\domain.py",
        )
    )

    assert set(report.changed_paths) == {
    "main.py",
    "core/domain.py",
    }


def test_report_has_fingerprint(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    analyzer = ChangeImpactAnalyzer(repository)

    report = analyzer.analyze(
        ("main.py",)
    )

    assert len(report.fingerprint) == 64

    assert all(
        character in "0123456789abcdef"
        for character in report.fingerprint
    )