"""Adversarial tests for T01 Project DNA."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .project_dna import (
    ProjectDNAIntegrityError,
    ProjectDNASourceError,
    ProjectDNAReader,
)


def test_missing_state_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ProjectDNASourceError):
        ProjectDNAReader(tmp_path).read()


def test_non_object_state_fails_closed(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir(parents=True)

    (data / "state.json").write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(ProjectDNASourceError):
        ProjectDNAReader(tmp_path).read()


def test_wrong_canonical_source_fails_closed(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "schema_version": 3,
            "control_center_version": "7.0",
        },
        "constitution": {
            "canonical_source": "wrong.json",
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
            "current": "TEST",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()