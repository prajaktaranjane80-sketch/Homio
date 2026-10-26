"""Unit tests for shared read-only transition contract helpers."""

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
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


def test_ai001_t06_guarded_route_is_connected_and_valid():
    workflows = ROOT / ".github" / "workflows"
    actions = ROOT / ".github" / "actions" / "homio-backend-ci"

    main_path = workflows / "backend-ci.yml"
    reusable_path = workflows / "reusable-ai001-t06-transition.yml"
    action_path = actions / "transitions/ai001-t06/action.yml"
    script_path = actions / "transitions/ai001-t06/scripts/guarded_transition.py"
    request_path = (
        ROOT / "REOS_CONTROL_CENTER/evidence/AI-001/T06-transition-request.md"
    )

    for path in (
        main_path,
        reusable_path,
        action_path,
        script_path,
        request_path,
    ):
        assert path.is_file(), f"Required T06 transition file is missing: {path}"

    main = main_path.read_text(encoding="utf-8")
    reusable = reusable_path.read_text(encoding="utf-8")
    action = action_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")
    request = request_path.read_text(encoding="utf-8")

    # Parse the actual transition script before allowing the guarded job to run.
    ast.parse(script, filename=str(script_path))

    guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-AI-001-T06]') }}"
    )

    assert guard in main
    assert guard in reusable

    assert (
        main.count(
            '".github/workflows/reusable-ai001-t06-transition.yml"'
        ) == 2
    )
    assert "control_center_transition_ai001_t06:" in main
    assert "workflow_call:" in reusable
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/ai001-t06"
        in reusable
    )
    assert "guarded_transition.py" in action

    for required in (
        '"AI-001-T06"',
        '"complete-subtask"',
        "APPROVAL: AUTHORIZE AI-001-T06 COMPLETION",
        "SCOPE: AI-001-T06 only",
        "CURRENT_SUBTASK=AI-001-T07",
        "CANONICAL_BRANCH_HEAD",
        "AI-001-T06 TRANSITION AND CANONICAL READBACK: PASS",
        "test_authorization_tenant_isolation.py",
        "test_agent_tool_boundaries.py",
        "AI-001-AC01",
        "AI-001-AC06",
    ):
        assert required in script, f"T06 guarded script lacks: {required}"

    assert "STATE.write_text" not in script
    assert "STATE_PATH.write_text" not in script
    assert "--force" not in script

    assert "APPROVAL: AUTHORIZE AI-001-T06 COMPLETION" in request
    assert "SCOPE: AI-001-T06 only" in request
