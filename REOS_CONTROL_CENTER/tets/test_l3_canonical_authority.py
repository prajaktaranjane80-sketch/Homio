from __future__ import annotations

import copy
import json
from pathlib import Path

from context.control_plane import CanonicalAuthorityVerifier
from context.phase_projection import (
    expected_phase_for_gate,
    is_phase_coherent,
    synchronize_current_phase,
)


CONTROL_CENTER_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = CONTROL_CENTER_ROOT / "data" / "state.json"


def load_canonical_state() -> dict:
    return json.loads(
        STATE_PATH.read_text(encoding="utf-8")
    )


def test_canonical_state_path_is_data_state_json():
    state = load_canonical_state()

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
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
    tampered["execution"]["current_gate"] = (
        "UNAUTHORIZED-GATE"
    )

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=tampered,
    )

    assert verifier.verify_state_integrity() is False


def test_missing_integrity_hash_is_blocked():
    state = load_canonical_state()

    broken = copy.deepcopy(state)
    broken["integrity"]["sha256"] = None

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    assert verifier.verify_state_integrity() is False


def test_missing_integrity_metadata_is_blocked():
    state = load_canonical_state()

    broken = copy.deepcopy(state)
    broken.pop("integrity")

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    assert verifier.verify_state_integrity() is False



def test_core_gate_phase_mismatch_is_detected_and_projected():
    state = load_canonical_state()
    state["execution"]["current_gate"] = "CORE-008"
    state["phases"]["current"] = "PRE-CODING ARCHITECTURE"

    assert expected_phase_for_gate(state) == state["phases"]["phase_1"]
    assert is_phase_coherent(state) is False

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )
    assert verifier.verify_phase_coherence() is False

    assert synchronize_current_phase(state) is True
    assert state["phases"]["current"] == state["phases"]["phase_1"]
    assert is_phase_coherent(state) is True
    assert verifier.verify_phase_coherence() is True


def test_future_phase_uses_registered_execution_sequence():
    state = load_canonical_state()
    state["execution"]["current_gate"] = "AI-001"
    state["phases"]["current"] = "PRE-CODING ARCHITECTURE"

    assert expected_phase_for_gate(state) == state["phases"]["phase_2"]
    assert synchronize_current_phase(state) is True
    assert is_phase_coherent(state) is True


def test_unknown_gate_does_not_guess_or_rewrite_phase():
    state = load_canonical_state()
    state["execution"]["current_gate"] = "UNKNOWN-999"
    previous_phase = state["phases"]["current"]

    assert expected_phase_for_gate(state) is None
    assert synchronize_current_phase(state) is False
    assert state["phases"]["current"] == previous_phase

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

    broken["execution"] = {
        "current_gate": "",
        "current_task": "",
        "status": "CONTROL_CENTER_DRIVEN",
    }

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    result = verifier.verify()

    assert result.allowed is False
    assert result.reason == "CANONICAL_STATE_INTEGRITY_FAILURE"


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
