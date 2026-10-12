from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from reos_control_center import calculate_hash
from .state_reader import CanonicalStateReader, StateReadError


def _state() -> dict:
    return {
        "execution": {
            "current_gate": "CORE-008",
            "current_task": "Commission domain",
            "current_subtask": "CORE-008-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        }
    }


def _write(root: Path, state: dict) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def _sealed_state() -> dict:
    state = _state()
    state["integrity"] = {"sha256": None}
    state["integrity"]["sha256"] = calculate_hash(state)
    return state


def test_valid_state_integrity_is_accepted():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, _sealed_state())

        loaded = CanonicalStateReader(root).read()

        assert loaded["execution"]["current_gate"] == "CORE-008"


def test_missing_integrity_metadata_fails_closed():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, _state())

        with pytest.raises(StateReadError, match="integrity metadata missing"):
            CanonicalStateReader(root).read()


def test_missing_sha256_fails_closed():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state = _state()
        state["integrity"] = {"sha256": None}
        _write(root, state)

        with pytest.raises(StateReadError, match="SHA-256 missing"):
            CanonicalStateReader(root).read()


def test_tampered_state_fails_closed():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        state = _sealed_state()
        state["execution"]["current_gate"] = "UNAUTHORIZED-GATE"
        _write(root, state)

        with pytest.raises(StateReadError, match="SHA-256 mismatch"):
            CanonicalStateReader(root).read()