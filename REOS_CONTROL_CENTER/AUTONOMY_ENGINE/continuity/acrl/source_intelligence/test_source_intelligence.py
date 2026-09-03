"""T16 PART-02 — Source intelligence tests."""

from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.source_intelligence.dependency_graph import (
    build_dependency_graph,
)
from AUTONOMY_ENGINE.continuity.acrl.source_intelligence.intelligence import (
    inspect_source_intelligence,
)
from AUTONOMY_ENGINE.continuity.acrl.source_intelligence.source_parser import (
    parse_imports,
)


def build_repository(root: Path) -> Path:
    """Create a deterministic source repository."""

    root.mkdir(
        parents=False,
        exist_ok=False,
    )

    (root / "core").mkdir()
    (root / "tests").mkdir()

    (root / "main.py").write_text(
        "from core.domain import Domain\n",
        encoding="utf-8",
    )

    (root / "core" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    (root / "core" / "domain.py").write_text(
        "import pathlib\n\n"
        "class Domain:\n"
        "    pass\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_domain.py").write_text(
        "from core.domain import Domain\n\n"
        "def test_domain():\n"
        "    assert Domain is not None\n",
        encoding="utf-8",
    )

    return root


def test_import_parser_extracts_imports(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    evidence = parse_imports(
        repository,
        "main.py",
    )

    assert len(evidence) == 1
    assert evidence[0].imported_name == "core.domain"
    assert evidence[0].import_kind == "FROM_IMPORT"


def test_dependency_graph_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    first = build_dependency_graph(repository)
    second = build_dependency_graph(repository)

    assert first == second


def test_dependency_graph_contains_source_nodes(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    graph = build_dependency_graph(repository)

    assert "main.py" in graph.nodes
    assert "core/domain.py" in graph.nodes
    assert "tests/test_domain.py" in graph.nodes


def test_dependency_graph_contains_observed_edges(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    graph = build_dependency_graph(repository)

    assert any(
        edge.source_path == "main.py"
        and edge.imported_name == "core.domain"
        for edge in graph.edges
    )


def test_source_intelligence_links_part01(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    intelligence = inspect_source_intelligence(repository)

    assert len(
        intelligence.repository_identity_hash
    ) == 64

    assert len(
        intelligence.topology_fingerprint
    ) == 64

    assert intelligence.dependency_graph.nodes


def test_source_intelligence_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    first = inspect_source_intelligence(repository)
    second = inspect_source_intelligence(repository)

    assert first == second
