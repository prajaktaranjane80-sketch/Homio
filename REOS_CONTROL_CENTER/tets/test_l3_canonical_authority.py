from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from context.control_plane import CanonicalAuthorityVerifier
from context.phase_projection import (
    expected_phase_for_gate,
    is_phase_coherent,
    synchronize_current_phase,
)
import reos_control_center as control_center
from reos_control_center import (
    calculate_hash,
    cmd_complete_subtask,
    cmd_verify_state,
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


def test_l3_verification_blocks_phase_gate_mismatch_with_valid_integrity():
    state = load_canonical_state()
    broken = copy.deepcopy(state)
    broken["phases"]["current"] = "__INCOHERENT_PHASE__"
    broken["integrity"]["sha256"] = calculate_hash(broken)

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=broken,
    )

    result = verifier.verify()

    assert result.allowed is False
    assert result.reason == "AUTHORITATIVE_PHASE_GATE_COHERENCE_FAILURE"
    assert result.current_gate == broken["execution"]["current_gate"]


def test_verify_state_command_reports_phase_gate_coherence(capsys):
    state = load_canonical_state()

    cmd_verify_state(state)

    output = capsys.readouterr().out
    assert "INTEGRITY: PASS" in output
    assert "PHASE/GATE COHERENCE: PASS" in output


def test_verify_state_command_fails_on_phase_mismatch_with_valid_hash(capsys):
    state = load_canonical_state()
    broken = copy.deepcopy(state)
    broken["phases"]["current"] = "__INCOHERENT_PHASE__"
    broken["integrity"]["sha256"] = calculate_hash(broken)

    with pytest.raises(SystemExit) as result:
        cmd_verify_state(broken)

    assert result.value.code == 1
    output = capsys.readouterr().out
    assert "INTEGRITY: PASS" in output
    assert "PHASE/GATE COHERENCE: MISMATCH" in output


def test_complete_subtask_persists_integrity_after_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    state = copy.deepcopy(load_canonical_state())
    gate = state["gate_plans"]["CORE-008"]

    # Build an isolated T04-current fixture without mutating canonical state.
    for item in gate["subtasks"]:
        if item["id"] == "CORE-008-T04":
            item["status"] = "CURRENT"
        elif item["id"] == "CORE-008-T05":
            item["status"] = "PENDING"

    gate["current_subtask"] = "CORE-008-T04"
    state["execution"]["current_subtask"] = "CORE-008-T04"
    state["execution"]["current_task"] = (
        "CORE-008-T04: Implement settlement and reconciliation lifecycle."
    )

    control_center.synchronize_execution_projection(state)
    state["integrity"]["sha256"] = calculate_hash(state)

    root = tmp_path / "REOS_CONTROL_CENTER"
    state_path = root / "data" / "state.json"
    packets = root / "packets"
    snapshots = root / "snapshots"
    logs = root / "logs"

    for folder in (
        state_path.parent,
        packets,
        snapshots,
        logs,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(control_center, "ROOT", root)
    monkeypatch.setattr(control_center, "STATE", state_path)
    monkeypatch.setattr(control_center, "PACKETS", packets)
    monkeypatch.setattr(control_center, "SNAPSHOTS", snapshots)
    monkeypatch.setattr(control_center, "LOGS", logs)

    cmd_complete_subtask(
        state,
        "CORE-008-T04",
        note="test evidence for controller completion handoff integrity",
    )

    persisted = json.loads(
        state_path.read_text(encoding="utf-8")
    )
    persisted_gate = persisted["gate_plans"]["CORE-008"]
    persisted_statuses = {
        item["id"]: item["status"]
        for item in persisted_gate["subtasks"]
    }

    assert persisted["integrity"]["sha256"] == calculate_hash(
        persisted
    )
    assert persisted["session"]["last_handoff"] == str(
        packets / "NEW_CHAT_PACKET.txt"
    )
    assert persisted_statuses["CORE-008-T04"] == "DONE"
    assert persisted_statuses["CORE-008-T05"] == "CURRENT"
    assert persisted_gate["current_subtask"] == "CORE-008-T05"
    assert persisted["execution"]["current_subtask"] == "CORE-008-T05"

    packet = (packets / "NEW_CHAT_PACKET.txt").read_text(
        encoding="utf-8"
    )
    assert "CORE-008-T04|DONE|" in packet
    assert "CORE-008-T05|CURRENT|" in packet
    assert (root / "REOS_NEXT_CHAT.txt").read_text(
        encoding="utf-8"
    ) == packet
