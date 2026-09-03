"""Tests for T01 fingerprint evidence."""

from __future__ import annotations

import json
from pathlib import Path

from .fingerprint import (
    extract_project_fingerprints,
    fingerprints_match,
)
from .project_dna import ProjectDNAReader


def _write_state(root: Path) -> None:
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
            "type": "Global AI Real Estate OS",
            "north_star": "Test.",
            "operating_principle": "Test.",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_extracts_existing_fingerprints(tmp_path: Path) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()
    fingerprints = extract_project_fingerprints(dna)

    assert len(fingerprints.source_state_sha256) == 64
    assert len(fingerprints.semantic_state_sha256) == 64
    assert fingerprints_match(fingerprints, fingerprints)