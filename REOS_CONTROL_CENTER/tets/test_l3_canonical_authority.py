from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from context.control_plane import CanonicalAuthorityVerifier


CONTROL_CENTER_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = CONTROL_CENTER_ROOT / "data" / "state.json"


def load_canonical_state() -> dict:
    return json.loads(
        STATE_PATH.read_text(encoding="utf-8")
    )


def test_canonical_state_path_is_data_state_json():
    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=load_canonical_state(),
    )

    assert verifier.verify_state_path() is True
    assert verifier.state_path == STATE_PATH.resolve()


def test_state_declares_canonical_authority():
    state = load_canonical_state()

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    assert verifier.verify_authority_declaration() is True


def test_current_execution_position_exists():
    state = load_canonical_state()

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    assert verifier.verify_execution_position() is True


def test_canonical_state_integrity_is_valid():
    state = load_canonical_state()

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    assert verifier.verify_state_integrity() is True


def test_tampered_state_is_blocked():
    state = load_canonical_state()

    tampered = copy.deepcopy(state)

    current = tampered.setdefault("current", {})
    current["__l3_tamper_test__"] = True

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=tampered,
    )

    assert verifier.verify_state_integrity() is False


def test_missing_integrity_hash_is_blocked():
    state = load_canonical_state()

    state.setdefault("integrity", {})["sha256"] = None

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    assert verifier.verify_state_integrity() is False


def test_complete_l3_verification():
    state = load_canonical_state()

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    result = verifier.verify()

    assert result.allowed is True
    assert result.reason == "CANONICAL_AUTHORITY_VERIFIED"
    assert result.state_path == STATE_PATH.resolve()
    assert result.current_gate
    assert result.current_task
    assert result.current_subtask


def test_l3_does_not_mutate_state():
    state = load_canonical_state()
    original = copy.deepcopy(state)

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    verifier.verify()

    assert state == original


def test_invalid_execution_position_is_blocked():
    state = load_canonical_state()

    broken = copy.deepcopy(state)
    broken["current"] = {}

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    result = verifier.verify()

    assert result.allowed is False
    assert result.reason == "AUTHORITATIVE_EXECUTION_POSITION_INVALID"


def test_invalid_authority_declaration_is_blocked():
    state = load_canonical_state()

    broken = copy.deepcopy(state)
    broken.setdefault("constitution", {})[
        "canonical_source"
    ] = "somewhere_else.json"

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    result = verifier.verify()

    assert result.allowed is False
    assert result.reason == "CANONICAL_STATE_INTEGRITY_FAILURE"
