
import json
from pathlib import Path

from adapter.targeted_state import compact_state
from integration.preflight import run_preflight
from integration.safe_next import next_safe_action


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "REOS_CONTROL_CENTER"
    (root / "data").mkdir(parents=True)
    state = {
        "execution": {
            "current_gate": "CORE-X",
            "current_task": "CORE-X-T01: Test",
            "current_subtask": "CORE-X-T01",
            "status": "CONTROL_CENTER_DRIVEN"
        },
        "execution_plan": {
            "authoritative_sequence": [
                {"gate": "CORE-X", "status": "CURRENT", "name": "Test"}
            ]
        },
        "gate_plans": {
            "CORE-X": {
                "status": "CURRENT",
                "subtasks": [
                    {"id": "CORE-X-T01", "status": "CURRENT", "title": "Test"}
                ],
                "criteria_state": [
                    {"id": "CORE-X-AC01", "status": "PENDING"}
                ]
            }
        }
    }
    (root / "data" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (root / "reos_control_center.py").write_text("print('stub')", encoding="utf-8")
    return root


def test_compact_state(tmp_path):
    root = make_root(tmp_path)
    c = compact_state(root)
    assert c["current_gate"] == "CORE-X"
    assert c["criteria"]["pending"] == ["CORE-X-AC01"]


def test_preflight_passes_consistent_state(tmp_path):
    root = make_root(tmp_path)
    p = run_preflight(root)
    assert p.safe


def test_next_action_is_criteria_verification(tmp_path):
    root = make_root(tmp_path)
    a = next_safe_action(root)
    assert a.status == "READY"
    assert a.action == "VERIFY_REMAINING_CRITERIA"
