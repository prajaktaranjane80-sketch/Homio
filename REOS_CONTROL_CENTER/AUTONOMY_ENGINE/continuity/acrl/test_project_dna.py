"""ACRL T01 — Project DNA tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.project_dna import (
    ProjectDNAIntegrityError,
    ProjectDNASourceError,
    ProjectDNAReader,
)


def _write_state(
    root: Path,
    *,
    canonical_source: str = "data/state.json",
    chat_memory: bool = True,
    single_source: bool = True,
    architecture_before_code: bool = True,
    duplicate_logic: bool = True,
) -> None:
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
            "canonical_source": canonical_source,
            "architecture_before_code": architecture_before_code,
            "single_source_of_truth": single_source,
            "micro_modular": True,
            "no_duplicate_logic": duplicate_logic,
            "no_silent_architecture_changes": True,
            "chat_history_is_not_project_memory": chat_memory,
        },
        "project": {
            "name": "HOMIO",
            "type": "Global AI Real Estate OS + International Brokerage + SaaS",
            "north_star": (
                "Generate genuine property demand, acquire verified "
                "inventory, protect lead/deal ownership, protect "
                "commission, automate operations, and scale internationally."
            ),
            "operating_principle": (
                "AI automates; governance controls; evidence protects; "
                "humans approve irreversible/high-risk actions."
            ),
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_reads_authoritative_project_dna(tmp_path: Path) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()

    assert dna.product == "HOMIO / REOS"
    assert dna.project_name == "HOMIO"
    assert dna.phase == "PRE-CODING ARCHITECTURE"
    assert dna.canonical_source == "data/state.json"
    assert dna.chat_history_is_not_project_memory is True


def test_projection_is_serializable(tmp_path: Path) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()
    payload = dna.to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["authority"]["canonical_source"] == "data/state.json"
    assert isinstance(payload["source_state_sha256"], str)
    assert len(payload["source_state_sha256"]) == 64


def test_resume_identity_contains_only_compact_authority_context(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    identity = ProjectDNAReader(tmp_path).read().resume_identity()

    assert "PROJECT=HOMIO" in identity
    assert "CANONICAL_SOURCE=data/state.json" in identity
    assert "CHAT_MEMORY=NON_AUTHORITATIVE" in identity
    assert "DUPLICATE_LOGIC=FORBIDDEN" in identity


def test_rejects_wrong_canonical_source(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        canonical_source="PROJECT_CONTINUITY/continuity_state.json",
    )

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_rejects_chat_as_project_memory(tmp_path: Path) -> None:
    _write_state(tmp_path, chat_memory=False)

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_rejects_multiple_sources_of_truth(tmp_path: Path) -> None:
    _write_state(tmp_path, single_source=False)

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_rejects_architecture_after_code_model(tmp_path: Path) -> None:
    _write_state(tmp_path, architecture_before_code=False)

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_rejects_duplicate_logic_policy(tmp_path: Path) -> None:
    _write_state(tmp_path, duplicate_logic=False)

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_missing_authoritative_state_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ProjectDNASourceError):
        ProjectDNAReader(tmp_path).read()


def test_state_fingerprint_changes_after_state_change(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ProjectDNAReader(tmp_path)

    first = reader.read().source_state_sha256

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["project"]["name"] = "HOMIO-CHANGED"

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    second = reader.read().source_state_sha256

    assert first != second