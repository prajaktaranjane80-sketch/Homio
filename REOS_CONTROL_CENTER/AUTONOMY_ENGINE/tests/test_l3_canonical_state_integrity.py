from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import reos_control_center as control_center


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _valid_state() -> dict:
    state = {
        "meta": {
            "project": "HOMIO / REOS",
            "updated_at": "2026-01-01T00:00:00+00:00",
        },
        "execution": {
            "current_gate": "CORE-005",
            "current_task": "CORE-005-T01",
            "current_subtask": "CORE-005-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "events": [],
        "checkpoints": [],
        "gate_plans": {},
        "session": {},
        "architecture": {
            "approved": [],
            "pending": [],
        },
        "integrity": {
            "sha256": None,
        },
    }

    state["integrity"]["sha256"] = control_center.calculate_hash(state)
    return state


def test_canonical_state_path_is_authoritative():
    expected = (
        Path(control_center.ROOT)
        / "data"
        / "state.json"
    )

    assert control_center.STATE.resolve() == expected.resolve()
    assert control_center.STATE.name == "state.json"
    assert control_center.STATE.parent.name == "data"


def test_load_state_accepts_valid_canonical_state(monkeypatch, tmp_path):
    state_path = tmp_path / "data" / "state.json"
    state = _valid_state()
    _write_state(state_path, state)

    monkeypatch.setattr(control_center, "STATE", state_path)

    loaded = control_center.load_state()

    assert loaded["execution"]["current_gate"] == "CORE-005"
    assert loaded["integrity"]["sha256"] == control_center.calculate_hash(loaded)


def test_load_state_fails_closed_when_state_is_tampered(monkeypatch, tmp_path):
    state_path = tmp_path / "data" / "state.json"
    state = _valid_state()

    _write_state(state_path, state)

    tampered = copy.deepcopy(state)
    tampered["execution"]["current_gate"] = "UNAUTHORIZED-GATE"
    _write_state(state_path, tampered)

    monkeypatch.setattr(control_center, "STATE", state_path)

    with pytest.raises(SystemExit, match="CANONICAL STATE INTEGRITY FAILURE"):
        control_center.load_state()


def test_load_state_fails_closed_when_hash_is_missing(monkeypatch, tmp_path):
    state_path = tmp_path / "data" / "state.json"
    state = _valid_state()
    state["integrity"]["sha256"] = None

    _write_state(state_path, state)

    monkeypatch.setattr(control_center, "STATE", state_path)

    with pytest.raises(SystemExit, match="SHA-256 missing"):
        control_center.load_state()


def test_load_state_fails_closed_when_integrity_metadata_is_missing(
    monkeypatch,
    tmp_path,
):
    state_path = tmp_path / "data" / "state.json"
    state = _valid_state()
    state.pop("integrity")

    _write_state(state_path, state)

    monkeypatch.setattr(control_center, "STATE", state_path)

    with pytest.raises(SystemExit, match="integrity metadata missing"):
        control_center.load_state()


def test_load_state_fails_closed_on_invalid_json(monkeypatch, tmp_path):
    state_path = tmp_path / "data" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        '{"execution": ',
        encoding="utf-8",
    )

    monkeypatch.setattr(control_center, "STATE", state_path)

    with pytest.raises(SystemExit, match="Invalid state.json"):
        control_center.load_state()


def test_verify_state_hash_matches_canonical_state(monkeypatch, tmp_path, capsys):
    state_path = tmp_path / "data" / "state.json"
    state = _valid_state()
    _write_state(state_path, state)

    monkeypatch.setattr(control_center, "STATE", state_path)

    loaded = control_center.load_state()
    control_center.cmd_verify_state(loaded)

    output = capsys.readouterr().out

    assert "INTEGRITY: PASS" in output
