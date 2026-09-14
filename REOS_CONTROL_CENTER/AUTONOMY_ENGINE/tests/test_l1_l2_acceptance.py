"""
L1 Runtime + L2 Diagnostics acceptance tests.

These tests prove the completion boundary for:

L1
--
- runtime construction
- lifecycle
- success path
- blocked path
- failure path
- MissionCycle integration
- ExecutionCoordinator integration
- execution safety boundary

L2
--
- canonical state detection
- runtime/mission/checkpoint/recovery detection
- read-only behavior
- machine-readable output
- human-readable output
- fail-closed behavior

These tests do not modify canonical state.json.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Import boundary
# ---------------------------------------------------------------------------

TEST_FILE = Path(__file__).resolve()
CONTROL_CENTER_ROOT = TEST_FILE.parents[1]
AUTONOMY_ENGINE_ROOT = CONTROL_CENTER_ROOT / "AUTONOMY_ENGINE"

if str(AUTONOMY_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTONOMY_ENGINE_ROOT))

if str(CONTROL_CENTER_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_CENTER_ROOT))


from diagnostics.reos_health import REOSHealth
from orchestration.agent_runtime import (
    AgentRuntime,
    AgentRuntimeContext,
)
from orchestration.agent_runtime_execution_bridge import (
    AgentRuntimeExecutionBridge,
)
from orchestration.execution_coordinator import ExecutionContext
from protocols.action_protocol import ActionProposal
from runtime.mission_cycle import MissionCycleEngine


# ---------------------------------------------------------------------------
# L1 — AgentRuntime lifecycle
# ---------------------------------------------------------------------------


def _runtime() -> AgentRuntime:
    return AgentRuntime(
        AgentRuntimeContext(
            run_id="L1-ACCEPTANCE-RUN",
            agent_id="L1-ACCEPTANCE-AGENT",
            task_id="L1-ACCEPTANCE-TASK",
        )
    )


def test_l1_runtime_success_path() -> None:
    runtime = _runtime()

    assert runtime.status == "PLANNED"

    started = runtime.start()

    assert started.status == "RUNNING"

    completed = runtime.complete(
        output={"acceptance": "success"},
    )

    assert completed.status == "COMPLETED"
    assert completed.output["acceptance"] == "success"


def test_l1_runtime_blocked_path() -> None:
    runtime = _runtime()

    runtime.start()

    blocked = runtime.block(
        "authorization boundary blocked execution",
    )

    assert blocked.status == "BLOCKED"
    assert blocked.errors == (
        "authorization boundary blocked execution",
    )


def test_l1_runtime_failure_path() -> None:
    runtime = _runtime()

    runtime.start()

    failed = runtime.fail(
        "controlled execution failure",
    )

    assert failed.status == "FAILED"
    assert failed.errors == (
        "controlled execution failure",
    )


def test_l1_runtime_rejects_invalid_lifecycle_transition() -> None:
    runtime = _runtime()

    with pytest.raises(RuntimeError):
        runtime.complete()

    runtime.start()

    with pytest.raises(RuntimeError):
        runtime.start()


# ---------------------------------------------------------------------------
# L1 — MissionCycle integration
# ---------------------------------------------------------------------------


def test_l1_mission_cycle_creates_agent_runtime() -> None:
    engine = MissionCycleEngine()

    cycle = engine.prepare(
        mode="HOMIO_BUILDER",
    )

    if cycle.status == "BLOCKED":
        pytest.fail(
            "MissionCycle must be READY for L1 acceptance: "
            f"{cycle.blockers}"
        )

    runtime = engine.create_agent_runtime(
        cycle,
        agent_id="L1-ACCEPTANCE-AGENT",
    )

    assert runtime.status == "PLANNED"
    assert runtime.context.agent_id == "L1-ACCEPTANCE-AGENT"
    assert runtime.context.run_id == cycle.cycle_id
    assert runtime.context.task_id


# ---------------------------------------------------------------------------
# L1 — Execution boundary integration
# ---------------------------------------------------------------------------


def _execution_proposal() -> ActionProposal:
    return ActionProposal.create(
        action="L1_ACCEPTANCE_ACTION",
        target="L1_ACCEPTANCE_TARGET",
        requester="L1_ACCEPTANCE_TEST",
        reason="Controlled L1 execution acceptance.",
    )


def _execution_context() -> ExecutionContext:
    return ExecutionContext(
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        evidence={
            "acceptance": "L1",
            "source": "test_l1_l2_acceptance",
        },
    )


def test_l1_execution_bridge_success_path() -> None:
    runtime = _runtime()

    bridge = AgentRuntimeExecutionBridge(runtime)

    executed: list[str] = []

    def authoritative_executor(proposal: ActionProposal) -> dict[str, str]:
        executed.append(proposal.action_id)

        return {
            "status": "accepted",
            "action_id": proposal.action_id,
        }

    proposal = _execution_proposal()

    result = bridge.execute(
        proposal,
        _execution_context(),
        executor=authoritative_executor,
    )

    assert result.runtime_status == "COMPLETED"
    assert result.coordination_status == "EXECUTED"
    assert result.allowed is True
    assert result.action_id == proposal.action_id
    assert executed == [proposal.action_id]
    assert result.evidence["runtime_execution_attempted"] is True
    assert result.evidence["runtime_terminal"] is True
    assert result.evidence["mutation_executed"] is True


def test_l1_execution_bridge_blocked_path() -> None:
    runtime = _runtime()

    bridge = AgentRuntimeExecutionBridge(runtime)

    proposal = _execution_proposal()

    blocked_context = ExecutionContext(
        authorized=False,
        capability_available=True,
        policy_allowed=True,
        risk_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
        architecture_locked=False,
        evidence={
            "acceptance": "L1-BLOCKED",
        },
    )

    executor_called = False

    def executor(_: ActionProposal) -> None:
        nonlocal executor_called
        executor_called = True

    result = bridge.execute(
        proposal,
        blocked_context,
        executor=executor,
    )

    assert result.runtime_status == "BLOCKED"
    assert result.coordination_status == "BLOCKED"
    assert result.allowed is False
    assert executor_called is False
    assert result.evidence["runtime_execution_attempted"] is True


def test_l1_execution_bridge_executor_failure_path() -> None:
    runtime = _runtime()

    bridge = AgentRuntimeExecutionBridge(runtime)

    proposal = _execution_proposal()

    def failing_executor(_: ActionProposal) -> None:
        raise RuntimeError("simulated authoritative executor failure")

    result = bridge.execute(
        proposal,
        _execution_context(),
        executor=failing_executor,
    )

    assert result.runtime_status == "FAILED"
    assert result.coordination_status == "FAILED"
    assert result.allowed is False
    assert "simulated authoritative executor failure" in result.reason
    assert result.evidence["runtime_execution_attempted"] is True


# ---------------------------------------------------------------------------
# L2 — Diagnostic acceptance
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    return CONTROL_CENTER_ROOT.parent


def test_l2_health_surface_passes() -> None:
    health = REOSHealth(
        project_root=_repo_root(),
    )

    report = health.run()

    assert report.result == "PASS"

    required_checks = {
        "CONTROL_CENTER",
        "STATE",
        "ARCHITECTURE",
        "AUTONOMY_ENGINE",
        "ACRL",
        "RUNTIME",
        "MISSION_CYCLE",
        "CHECKPOINT",
        "RECOVERY",
        "INTEGRATION",
    }

    actual_checks = {
        check.name
        for check in report.checks
    }

    assert required_checks.issubset(actual_checks)

    assert all(
        check.status == "PASS"
        for check in report.checks
    )


def test_l2_health_is_machine_readable() -> None:
    health = REOSHealth(
        project_root=_repo_root(),
    )

    payload = json.loads(
        health.json(),
    )

    assert payload["module"] == "REOS_HEALTH"
    assert payload["schema_version"] == "1.0"
    assert payload["result"] == "PASS"
    assert isinstance(payload["checks"], list)
    assert payload["checks"]


def test_l2_health_is_human_readable() -> None:
    health = REOSHealth(
        project_root=_repo_root(),
    )

    compact = health.compact()

    assert "REOS HEALTH" in compact
    assert "RESULT" in compact
    assert "PASS" in compact
    assert "RUNTIME" in compact
    assert "INTEGRATION" in compact


def test_l2_health_is_read_only() -> None:
    state_path = (
        _repo_root()
        / "REOS_CONTROL_CENTER"
        / "data"
        / "state.json"
    )

    before = state_path.read_bytes()

    health = REOSHealth(
        project_root=_repo_root(),
    )

    report = health.run()

    after = state_path.read_bytes()

    assert report.result == "PASS"
    assert before == after


def test_l2_health_does_not_mutate_loaded_state() -> None:
    state_path = (
        _repo_root()
        / "REOS_CONTROL_CENTER"
        / "data"
        / "state.json"
    )

    original = json.loads(
        state_path.read_text(
            encoding="utf-8",
        )
    )

    snapshot = copy.deepcopy(original)

    health = REOSHealth(
        project_root=_repo_root(),
    )

    health.run()

    current = json.loads(
        state_path.read_text(
            encoding="utf-8",
        )
    )

    assert current == snapshot


def test_l2_missing_state_fails_closed(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"

    control_center = project_root / "REOS_CONTROL_CENTER"
    data = control_center / "data"

    data.mkdir(
        parents=True,
    )

    (control_center / "AUTONOMY_ENGINE").mkdir()

    health = REOSHealth(
        project_root=project_root,
    )

    report = health.run()

    assert report.result == "BLOCKED"

    state_check = next(
        check
        for check in report.checks
        if check.name == "STATE"
    )

    assert state_check.status == "BLOCKED"


def test_l2_missing_runtime_fails_closed(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"

    control_center = project_root / "REOS_CONTROL_CENTER"
    data = control_center / "data"

    data.mkdir(
        parents=True,
    )

    state = {
        "execution": {
            "current_gate": "TEST",
            "current_task": "TEST",
            "current_subtask": "TEST",
        }
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    (control_center / "AUTONOMY_ENGINE").mkdir()

    acrl = (
        control_center
        / "AUTONOMY_ENGINE"
        / "continuity"
        / "acrl"
    )

    acrl.mkdir(
        parents=True,
    )

    health = REOSHealth(
        project_root=project_root,
    )

    report = health.run()

    assert report.result == "BLOCKED"

    runtime_check = next(
        check
        for check in report.checks
        if check.name == "RUNTIME"
    )

    assert runtime_check.status == "BLOCKED"


def test_l2_diagnostics_never_become_authority() -> None:
    health = REOSHealth(
        project_root=_repo_root(),
    )

    report = health.run()

    payload = report.as_dict()

    assert payload["module"] == "REOS_HEALTH"

    serialized = json.dumps(
        payload,
        sort_keys=True,
    )

    assert "canonical-state-json" in serialized or (
        "canonical" in serialized.lower()
    )
