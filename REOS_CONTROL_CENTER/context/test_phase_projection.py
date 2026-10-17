from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from .control_plane import CanonicalAuthorityVerifier
from .phase_projection import (
    PRE_CODING_PHASE,
    expected_phase_for_gate,
    is_phase_coherent,
    synchronize_current_phase,
)


PHASE_ONE = "Core Business & Protection Engines"
PHASE_TWO = "Data, Search, Services, Analytics, Security, DevOps & AI Infrastructure"

REGISTERED_GATES = (
    "ARCH-036",
    "REPO-001",
    "ENG-001",
    "CORE-008",
    "AI-001",
    "APP-001",
    "REL-001",
    "SCALE-001",
)

CONTROL_CENTER_ROOT = Path(__file__).resolve().parents[1]


def make_state(gate: str, current_phase: str) -> dict:
    return {
        "execution": {
            "current_gate": gate,
            "current_task": "test task",
        },
        "execution_plan": {
            "authoritative_sequence": [
                {"gate": registered_gate}
                for registered_gate in REGISTERED_GATES
            ],
        },
        "phases": {
            "phase_1": PHASE_ONE,
            "phase_2": PHASE_TWO,
            "current": current_phase,
        },
    }


@pytest.mark.parametrize(
    ("gate", "expected_phase"),
    [
        ("ARCH-036", PRE_CODING_PHASE),
        ("REPO-001", PRE_CODING_PHASE),
        ("ENG-001", PRE_CODING_PHASE),
        ("CORE-008", PHASE_ONE),
        ("AI-001", PHASE_TWO),
        ("APP-001", PHASE_TWO),
        ("REL-001", PHASE_TWO),
        ("SCALE-001", PHASE_TWO),
    ],
)
def test_registered_gate_maps_to_expected_phase(
    gate: str,
    expected_phase: str,
):
    state = make_state(gate, expected_phase)

    assert expected_phase_for_gate(state) == expected_phase
    assert is_phase_coherent(state)


def test_phase_coherence_requires_an_exact_match():
    state = make_state("CORE-008", PHASE_TWO)

    assert expected_phase_for_gate(state) == PHASE_ONE
    assert not is_phase_coherent(state)


def test_synchronize_updates_only_the_derived_phase_projection():
    state = make_state("CORE-008", "incorrect phase")
    execution_before = copy.deepcopy(state["execution"])
    plan_before = copy.deepcopy(state["execution_plan"])

    assert synchronize_current_phase(state) is True
    assert state["phases"]["current"] == PHASE_ONE
    assert state["execution"] == execution_before
    assert state["execution_plan"] == plan_before

    assert synchronize_current_phase(state) is False


def test_unknown_gate_fails_closed_without_mutating_state():
    state = make_state("UNKNOWN-999", PHASE_ONE)
    before = copy.deepcopy(state)

    assert expected_phase_for_gate(state) is None
    assert not is_phase_coherent(state)
    assert synchronize_current_phase(state) is False
    assert state == before


def test_malformed_state_fails_closed():
    state = {}

    assert expected_phase_for_gate(state) is None
    assert not is_phase_coherent(state)
    assert synchronize_current_phase(state) is False


def test_current_canonical_state_is_phase_coherent():
    state_path = CONTROL_CENTER_ROOT / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert is_phase_coherent(state), (
        "Canonical data/state.json current gate and phase projection disagree."
    )


def test_control_plane_verifier_uses_the_canonical_phase_projection():
    state_path = CONTROL_CENTER_ROOT / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))

    verifier = CanonicalAuthorityVerifier(
        control_center_root=CONTROL_CENTER_ROOT,
        state=state,
    )

    assert verifier.verify_phase_coherence()
