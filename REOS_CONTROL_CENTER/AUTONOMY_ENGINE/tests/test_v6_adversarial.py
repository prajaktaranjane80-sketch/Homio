"""Deterministic adversarial/security tests for AUTONOMY_ENGINE V6.

These tests exercise the V6 additions against real engine contracts.
They are intentionally additive and must not mutate REOS_CONTROL_CENTER
authority or production state.
"""

from pathlib import Path
import json

import pytest

from core.idempotency import already_applied
from core.workspace_guard import WorkspaceGuard
from execution.guard import ExecutionGuard
from security.workspace_manifest import WorkspaceManifest
from continuity.provenance import ProvenanceTracker
from orchestration.capability_registry import Capability, CapabilityRegistry
from orchestration.loop_detector import LoopDetector
from budgets.context_budget import ContextBudget
from protocols.action_protocol import ActionProposal, validate_proposal
from governance.policy_engine import PolicyEngine


ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "evaluation" / "adversarial_cases.json"


def _cases():
    payload = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    return {
        case["case_id"]: case
        for case in payload["cases"]
        if case.get("enabled", False)
    }


CASES = _cases()


def test_v6_adv_001_duplicate_action_prevention():
    """V6-ADV-001: repeated event/action must be detectable."""

    case = CASES["V6-ADV-001"]
    request_id = case["input_data"]["request_id"]

    state = {
        "events": [
            {
                "idempotency_key": request_id,
                "action_id": case["input_data"]["action_id"],
            }
        ]
    }

    assert already_applied(state, request_id) is True
    assert case["expected"]["duplicate"] is True
    assert case["expected"]["allow_second_execution"] is False


def test_v6_adv_002_unauthorized_execution_denied():
    """V6-ADV-002: missing authorization must remain denied."""

    case = CASES["V6-ADV-002"]

    guard = ExecutionGuard()

    decision = guard.evaluate(
        integrity_ok=True,
        semantic_status="PASS",
        architecture_locked=True,
        required_evidence_ok=False,
        mutation_requested=True,
    )

    assert decision is not None
    assert case["expected"]["authorized"] is False
    assert case["expected"]["allow_execution"] is False

    # A mutation request without required evidence must not be allowed.
    assert not bool(getattr(decision, "allowed", False))


def test_v6_adv_003_workspace_boundary_violation():
    """V6-ADV-003: writes outside the authorized workspace are blocked."""

    case = CASES["V6-ADV-003"]

    workspace = Path(case["input_data"]["workspace"])
    target = Path(case["input_data"]["target"])

    guard = WorkspaceGuard([workspace])

    assert guard.check(target) is False

    with pytest.raises(Exception):
        guard.require(target)

    assert case["expected"]["within_workspace"] is False
    assert case["expected"]["allow_write"] is False


def test_v6_adv_004_loop_detection():
    """V6-ADV-004: repeated actions trigger loop protection."""

    case = CASES["V6-ADV-004"]

    detector = LoopDetector(
        threshold=case["input_data"]["repeat_threshold"]
    )

    results = []

    for action in case["input_data"]["sequence"]:
        results.append(detector.observe(action))

    assert any(result.repeated for result in results)

    assert detector.count("plan") >= 3
    assert detector.count("validate") >= 3

    assert case["expected"]["loop_detected"] is True
    assert case["expected"]["allow_unbounded_repeat"] is False

def test_v6_adv_005_tampered_provenance():
    """V6-ADV-005: modified content must fail provenance verification."""

    case = CASES["V6-ADV-005"]

    tracker = ProvenanceTracker()

    tracker.record(
        record_id="v6-adv-005-record",
        source_type="adversarial-test",
        source_ref="V6-ADV-005",
        subject_type="decision",
        subject_ref="decision-001",
        content=case["input_data"]["original_content"],
    )

    valid = tracker.verify(
        "v6-adv-005-record",
        case["input_data"]["modified_content"],
    )

    assert valid is False
    assert case["expected"]["provenance_valid"] is False
    assert case["expected"]["tamper_detected"] is True


def test_v6_adv_006_missing_capability_denied():
    """V6-ADV-006: unregistered capability must not be executable."""

    case = CASES["V6-ADV-006"]

    registry = CapabilityRegistry()

    for capability_id in case["input_data"]["registered_capabilities"]:
        registry.register(
            Capability(
                capability_id=capability_id,
                name=capability_id,
            )
        )

    requested = case["input_data"]["requested_capability"]

    assert requested not in registry.ids()

    with pytest.raises(Exception):
        registry.require(requested)

    assert case["expected"]["capability_available"] is False
    assert case["expected"]["allow_execution"] is False


def test_v6_adv_007_context_budget_exhaustion():
    """V6-ADV-007: context consumption cannot exceed configured budget."""

    case = CASES["V6-ADV-007"]

    budget = ContextBudget(case["input_data"]["budget"])
    requested = case["input_data"]["requested"]

    assert budget.can_consume(requested) is False

    with pytest.raises(Exception):
        budget.consume(requested)

    assert case["expected"]["budget_exceeded"] is True
    assert case["expected"]["allow_unbounded_context"] is False


def test_v6_adv_008_invalid_action_proposal():
    """V6-ADV-008: malformed action proposal must fail validation."""

    case = CASES["V6-ADV-008"]

    proposal_data = case["input_data"]["proposal"]

    proposal = ActionProposal(
        action_id="v6-adv-008",
        action=proposal_data["action"],
        target=proposal_data["target"],
    )

    decision = validate_proposal(proposal)

    assert decision is not None
    assert bool(getattr(decision, "valid", False)) is False

    assert case["expected"]["valid"] is False
    assert case["expected"]["allow_execution"] is False