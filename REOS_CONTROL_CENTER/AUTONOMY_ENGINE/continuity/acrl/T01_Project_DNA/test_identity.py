"""Tests for T01 Project Identity."""

from __future__ import annotations

from pathlib import Path

from .identity import build_project_identity
from .project_dna import ProjectDNAReader


def _write_state(root: Path) -> None:
    import json

    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "version": "3.4",
            "schema_version": 3,
            "updated_at": "2026-08-30T00:00:00+05:30",
            "control_center_version": "7.0",
        },
        "constitution": {
            "canonical_source": "data/state.json",
            "architecture_before_code": True,
            "single_source_of_truth": True,
            "micro_modular": True,
            "no_duplicate_logic": True,
            "no_silent_architecture_changes": True,
            "chat_history_is_not_project_memory": True,
        },
        "project": {
            "name": "HOMIO",
            "type": "Global AI Real Estate OS + International Brokerage + SaaS",
            "north_star": "Test north star.",
            "operating_principle": "Test operating principle.",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_identity_is_deterministic(tmp_path: Path) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()

    first = build_project_identity(dna)
    second = build_project_identity(dna)

    assert first == second
    assert len(first.identity_sha256) == 64
    assert first.project_name == "HOMIO"