"""Unit tests for shared read-only transition contract helpers."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from transition_contract import (
    EXPECTED_CORE008_CRITERIA,
    require_core008_criteria_baseline,
    state_indexes,
)


def sample_state():
    return {
        "gate_plans": {
            "CORE-008": {
                "status": "CURRENT",
                "subtasks": [
                    {"id": "CORE-008-T05", "status": "DONE"},
                    {"id": "CORE-008-T06", "status": "CURRENT"},
                    {"id": "CORE-008-T07", "status": "PENDING"},
                ],
                "criteria_state": [
                    {"id": key, "status": value}
                    for key, value in EXPECTED_CORE008_CRITERIA.items()
                ],
            }
        }
    }


def test_state_indexes_use_canonical_gate_and_criterion_ids():
    gate, subtasks, criteria = state_indexes(sample_state())

    assert gate["status"] == "CURRENT"
    assert subtasks["CORE-008-T06"]["status"] == "CURRENT"
    assert criteria == EXPECTED_CORE008_CRITERIA


def test_expected_criterion_baseline_is_accepted():
    require_core008_criteria_baseline(sample_state())


def test_criterion_drift_fails_closed():
    state = sample_state()
    state["gate_plans"]["CORE-008"]["criteria_state"][0]["status"] = "VERIFIED"

    with pytest.raises(ValueError, match="baseline changed"):
        require_core008_criteria_baseline(state)
