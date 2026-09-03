"""T16 PART-03 — Symbol intelligence tests."""

from __future__ import annotations

from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.symbol_intelligence.lineage import (
    ConfidenceLevel,
    EvidenceKind,
    derived_evidence,
    inferred_evidence,
    observed_evidence,
    unknown_evidence,
)
from AUTONOMY_ENGINE.continuity.acrl.symbol_intelligence.snapshot import (
    inspect_symbol_intelligence,
)
from AUTONOMY_ENGINE.continuity.acrl.symbol_intelligence.symbols import (
    SymbolKind,
    extract_symbols,
)


def build_repository(root: Path) -> Path:
    """Create a deterministic repository fixture."""

    root.mkdir(
        parents=False,
        exist_ok=False,
    )

    (root / "core").mkdir()
    (root / "tests").mkdir()

    (root / "main.py").write_text(
        "from core.domain import Domain\n\n"
        "VALUE = 10\n\n"
        "def run():\n"
        "    return Domain()\n",
        encoding="utf-8",
    )

    (root / "core" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    (root / "core" / "domain.py").write_text(
        "class Domain:\n"
        "    def execute(self):\n"
        "        return True\n\n"
        "    async def execute_async(self):\n"
        "        return True\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_domain.py").write_text(
        "from core.domain import Domain\n\n"
        "def test_domain():\n"
        "    assert Domain is not None\n",
        encoding="utf-8",
    )

    return root


def test_symbol_extraction_finds_class_and_methods(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    symbols = extract_symbols(
        repository,
        "core/domain.py",
    )

    qualified_names = {
        symbol.qualified_name
        for symbol in symbols
    }

    assert "Domain" in qualified_names
    assert "Domain.execute" in qualified_names
    assert "Domain.execute_async" in qualified_names


def test_symbol_kinds_are_correct(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    symbols = extract_symbols(
        repository,
        "core/domain.py",
    )

    by_name = {
        symbol.qualified_name: symbol
        for symbol in symbols
    }

    assert by_name["Domain"].kind == SymbolKind.CLASS
    assert by_name["Domain.execute"].kind == SymbolKind.METHOD
    assert (
        by_name["Domain.execute_async"].kind
        == SymbolKind.ASYNC_METHOD
    )


def test_top_level_function_is_detected(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    symbols = extract_symbols(
        repository,
        "main.py",
    )

    assert any(
        symbol.qualified_name == "run"
        and symbol.kind == SymbolKind.FUNCTION
        for symbol in symbols
    )


def test_symbol_results_are_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    first = extract_symbols(
        repository,
        "main.py",
    )

    second = extract_symbols(
        repository,
        "main.py",
    )

    assert first == second


def test_lineage_levels_are_explicit() -> None:
    observed = observed_evidence(
        "filesystem",
        "Entry was directly observed.",
    )

    derived = derived_evidence(
        "ast",
        "Symbol was deterministically derived.",
    )

    inferred = inferred_evidence(
        "analysis",
        "Relationship was inferred.",
    )

    unknown = unknown_evidence(
        "unavailable",
        "Evidence is unavailable.",
    )

    assert observed.evidence_kind == EvidenceKind.OBSERVED
    assert observed.confidence == ConfidenceLevel.HIGH

    assert derived.evidence_kind == EvidenceKind.DERIVED
    assert derived.confidence == ConfidenceLevel.HIGH

    assert inferred.evidence_kind == EvidenceKind.INFERRED
    assert inferred.confidence == ConfidenceLevel.MEDIUM

    assert unknown.evidence_kind == EvidenceKind.UNKNOWN
    assert unknown.confidence == ConfidenceLevel.UNKNOWN


def test_snapshot_links_part01_and_part02(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    snapshot = inspect_symbol_intelligence(
        repository,
    )

    assert len(
        snapshot.repository_identity_hash
    ) == 64

    assert len(
        snapshot.topology_fingerprint
    ) == 64

    assert snapshot.dependency_graph.nodes
    assert snapshot.symbols

    assert (
        snapshot.evidence.evidence_kind
        == EvidenceKind.DERIVED
    )

    assert (
        snapshot.evidence.confidence
        == ConfidenceLevel.HIGH
    )


def test_snapshot_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    first = inspect_symbol_intelligence(
        repository,
    )

    second = inspect_symbol_intelligence(
        repository,
    )

    assert first == second
