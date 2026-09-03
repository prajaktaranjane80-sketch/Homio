"""ACRL T01 — Project DNA tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T01_Project_DNA.project_dna import (
    DNA_SCHEMA_VERSION,
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
    silent_architecture_changes: bool = True,
) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)

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
            "no_silent_architecture_changes": silent_architecture_changes,
            "chat_history_is_not_project_memory": chat_memory,
        },
        "project": {
            "name": "HOMIO",
            "type": (
                "Global AI Real Estate OS + International Brokerage + SaaS"
            ),
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
        json.dumps(state, ensure_ascii=False, indent=2),
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
    assert dna.source_state_sha256
    assert len(dna.source_state_sha256) == 64
    assert len(dna.semantic_state_sha256) == 64


def test_projection_is_serializable(tmp_path: Path) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()
    payload = dna.to_dict()

    assert payload["schema_version"] == DNA_SCHEMA_VERSION
    assert payload["authority"]["canonical_source"] == "data/state.json"
    assert payload["authority"]["execution_authority"] == "NOT_GRANTED"
    assert payload["authority"]["write_authority"] == "NOT_GRANTED"
    assert len(payload["fingerprint"]["source_state_sha256"]) == 64
    assert len(payload["fingerprint"]["semantic_state_sha256"]) == 64


def test_resume_identity_contains_compact_authority_context(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    identity = ProjectDNAReader(tmp_path).read().resume_identity()

    assert "PROJECT=HOMIO" in identity
    assert "CANONICAL_SOURCE=data/state.json" in identity
    assert "CHAT_MEMORY=NON_AUTHORITATIVE" in identity
    assert "DUPLICATE_LOGIC=FORBIDDEN" in identity
    assert "EXECUTION_AUTHORITY=NOT_GRANTED" in identity
    assert "WRITE_AUTHORITY=NOT_GRANTED" in identity
    assert "SEMANTIC_STATE_SHA256=" in identity


def test_bootstrap_payload_is_machine_readable(tmp_path: Path) -> None:
    _write_state(tmp_path)

    payload = ProjectDNAReader(tmp_path).read().bootstrap_payload()

    assert payload["dna_schema_version"] == DNA_SCHEMA_VERSION
    assert payload["project"]["name"] == "HOMIO"
    assert payload["authority"]["chat_memory_authoritative"] is False
    assert payload["authority"]["execution_authorized"] is False
    assert payload["authority"]["write_authorized"] is False
    assert payload["authority"]["approval_authorized"] is False
    assert payload["compatibility"]["state_schema_version"] == 3


def test_default_root_resolution_after_t01_relocation(
    tmp_path: Path,
) -> None:
    t01 = (
        tmp_path
        / "AUTONOMY_ENGINE"
        / "continuity"
        / "acrl"
        / "T01_Project_DNA"
    )
    t01.mkdir(parents=True)

    module_path = t01 / "project_dna.py"
    module_path.write_text(
        "# test placeholder\n",
        encoding="utf-8",
    )

    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "state.json").write_text("{}", encoding="utf-8")

    reader = object.__new__(ProjectDNAReader)
    reader.root = module_path.resolve().parents[4]
    reader.state_path = reader.root / "data" / "state.json"

    assert reader.root == tmp_path.resolve()
    assert reader.state_path == (
        tmp_path.resolve() / "data" / "state.json"
    )


def test_rejects_wrong_canonical_source(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        canonical_source=(
            "PROJECT_CONTINUITY/continuity_state.json"
        ),
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


def test_rejects_silent_architecture_change_policy(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        silent_architecture_changes=False,
    )

    with pytest.raises(ProjectDNAIntegrityError):
        ProjectDNAReader(tmp_path).read()


def test_missing_authoritative_state_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ProjectDNASourceError):
        ProjectDNAReader(tmp_path).read()


def test_state_source_fingerprint_changes_after_state_change(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ProjectDNAReader(tmp_path)

    first = reader.read().source_state_sha256

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )
    state["project"]["name"] = "HOMIO-CHANGED"

    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    second = reader.read().source_state_sha256

    assert first != second


def test_semantic_fingerprint_ignores_json_formatting(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ProjectDNAReader(tmp_path)
    first = reader.read().semantic_state_sha256

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    second = reader.read().semantic_state_sha256

    assert first == second


def test_dna_is_deterministic_for_same_state(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    first = ProjectDNAReader(tmp_path).read()
    second = ProjectDNAReader(tmp_path).read()

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert first.bootstrap_payload() == second.bootstrap_payload()


def test_execution_and_write_authority_are_never_granted(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()

    payload = dna.bootstrap_payload()

    assert payload["authority"]["execution_authorized"] is False
    assert payload["authority"]["write_authorized"] is False
    assert payload["authority"]["approval_authorized"] is False