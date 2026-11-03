from __future__ import annotations

"""
Read-only ACRL operational preflight and canonical execution projection.

Safety contract:
- Read and validate canonical Control Center state.
- Expose one validated, compact execution projection to ACRL consumers.
- Discover T01-T30 through the canonical ACRLTaskRegistry.
- Collect local Git identity for verification.
- Never execute a checkpoint, mutate state.json, or self-authorize execution.

This module is the single runtime owner of canonical state loading and
integrity hashing. Other runtime components must consume its projection
instead of implementing another state reader or hash algorithm.
"""

from dataclasses import dataclass
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


FILE = Path(__file__).resolve()
CONTROL_CENTER_ROOT = FILE.parents[4]
AUTONOMY_ENGINE_ROOT = CONTROL_CENTER_ROOT / "AUTONOMY_ENGINE"
STATE_PATH = CONTROL_CENTER_ROOT / "data" / "state.json"
ACRL_ROOT = AUTONOMY_ENGINE_ROOT / "continuity" / "acrl"


for root in (CONTROL_CENTER_ROOT, AUTONOMY_ENGINE_ROOT):
    value = str(root)

    if value not in sys.path:
        sys.path.insert(0, value)


# Use the one canonical T-layer registry.
from continuity.acrl.runtime_integration.task_registry import (  # noqa: E402
    ACRLTaskRegistry,
)


@dataclass(frozen=True, slots=True)
class CanonicalExecutionProjection:
    """Minimal validated execution state for ACRL consumers."""

    state_integrity_sha256: str

    current_gate: str
    current_gate_status: str

    current_task: str
    current_subtask: str
    current_subtask_status: str

    execution_status: str
    current_acceptance_criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "state_integrity_sha256": self.state_integrity_sha256,
            "current_gate": self.current_gate,
            "current_gate_status": self.current_gate_status,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "current_subtask_status": self.current_subtask_status,
            "execution_status": self.execution_status,
            "current_acceptance_criteria": list(
                self.current_acceptance_criteria
            ),
        }


@dataclass(frozen=True, slots=True)
class OperationalContext:
    mission_id: str
    objective: str
    git_branch: str
    git_head_sha: str
    worktree_clean: bool
    acrl_task_ids: tuple[str, ...]
    context_fingerprint: str


@dataclass(frozen=True, slots=True)
class OperationalResult:
    mission_id: str
    action_id: str
    status: str
    controller_command: tuple[str, ...]
    state_integrity: bool
    state_changed: bool
    stdout: str
    stderr: str
    evidence: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "action_id": self.action_id,
            "status": self.status,
            "controller_command": list(self.controller_command),
            "state_integrity": self.state_integrity,
            "state_changed": self.state_changed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "evidence": dict(self.evidence),
        }


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(
        f"Non-standard JSON constant is not allowed: {value}"
    )


def _load_state(
    state_path: Path | None = None,
) -> dict[str, Any]:
    """Load canonical state as a JSON object without modifying it."""

    target = Path(state_path or STATE_PATH)

    if not target.is_file():
        raise RuntimeError(
            f"Canonical state missing: {target}"
        )

    try:
        raw_text = target.read_text(
            encoding="utf-8-sig"
        )

        value = json.loads(
            raw_text,
            parse_constant=_reject_nonstandard_json_constant,
        )

    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise RuntimeError(
            f"Unable to read valid state.json: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise RuntimeError(
            "Canonical state.json root must be a JSON object"
        )

    return value


def _state_hash(
    state: dict[str, Any],
) -> str:
    """Calculate the existing Control Center canonical integrity hash."""

    clone = json.loads(
        json.dumps(
            state,
            ensure_ascii=False,
            allow_nan=False,
        )
    )

    integrity = clone.get("integrity")

    if not isinstance(integrity, dict):
        raise RuntimeError(
            "Canonical state integrity object is missing"
        )

    integrity["sha256"] = None

    canonical = json.dumps(
        clone,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def _state_integrity(
    state: dict[str, Any],
) -> bool:
    integrity = state.get("integrity")

    if not isinstance(integrity, dict):
        return False

    stored = integrity.get("sha256")

    return (
        isinstance(stored, str)
        and stored == _state_hash(state)
    )


def _required_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"Canonical execution field is missing: {field_name}"
        )

    return value.strip()


def load_execution_projection(
    state_path: Path | None = None,
) -> CanonicalExecutionProjection:
    """Read, validate and project one canonical execution position.

    This is the only runtime entry point that ACRL components should use
    when they need current gate/task/subtask information.

    The returned projection is observational context, not authorization.
    """

    target = Path(state_path or STATE_PATH)
    state = _load_state(target)

    if not _state_integrity(state):
        raise RuntimeError(
            "Canonical state integrity check failed"
        )

    constitution = state.get("constitution")

    if not isinstance(constitution, dict):
        raise RuntimeError(
            "Canonical constitution is missing"
        )

    if constitution.get("canonical_source") != "data/state.json":
        raise RuntimeError(
            "Canonical state source declaration is invalid"
        )

    architecture = state.get("architecture")

    if not isinstance(architecture, dict):
        raise RuntimeError(
            "Canonical architecture registry is missing"
        )

    if architecture.get("locked") is not True:
        raise RuntimeError(
            "Approved architecture is not locked"
        )

    approved_architecture = architecture.get("approved")

    if (
        not isinstance(approved_architecture, list)
        or not approved_architecture
    ):
        raise RuntimeError(
            "Approved architecture registry is empty or invalid"
        )

    integrity = state["integrity"]
    state_sha256 = integrity.get("sha256")

    if not isinstance(state_sha256, str) or not state_sha256:
        raise RuntimeError(
            "Canonical state fingerprint is missing"
        )

    execution = state.get("execution")

    if not isinstance(execution, dict):
        raise RuntimeError(
            "Canonical execution object is missing"
        )

    current_gate = _required_text(
        execution.get("current_gate"),
        "execution.current_gate",
    )

    current_task = _required_text(
        execution.get("current_task"),
        "execution.current_task",
    )

    current_subtask = _required_text(
        execution.get("current_subtask"),
        "execution.current_subtask",
    )

    execution_status = _required_text(
        execution.get("status"),
        "execution.status",
    )

    raw_criteria = execution.get(
        "current_acceptance_criteria"
    )

    if (
        not isinstance(raw_criteria, list)
        or not raw_criteria
        or any(
            not isinstance(item, str) or not item.strip()
            for item in raw_criteria
        )
    ):
        raise RuntimeError(
            "Current acceptance criteria are missing or invalid"
        )

    criteria = tuple(
        item.strip()
        for item in raw_criteria
    )

    gate_plans = state.get("gate_plans")

    if not isinstance(gate_plans, dict):
        raise RuntimeError(
            "Canonical gate_plans registry is missing"
        )

    gate_plan = gate_plans.get(current_gate)

    if not isinstance(gate_plan, dict):
        raise RuntimeError(
            "Current execution gate has no matching gate plan"
        )

    gate_status = _required_text(
        gate_plan.get("status"),
        "gate_plans.current_gate.status",
    )

    if gate_status != "CURRENT":
        raise RuntimeError(
            "Current execution gate and gate-plan status disagree"
        )

    gate_current_subtask = _required_text(
        gate_plan.get("current_subtask"),
        "gate_plans.current_gate.current_subtask",
    )

    if gate_current_subtask != current_subtask:
        raise RuntimeError(
            "Current subtask mismatch between execution and gate plan"
        )

    subtasks = gate_plan.get("subtasks")

    if not isinstance(subtasks, list):
        raise RuntimeError(
            "Current gate subtask registry is invalid"
        )

    matches = [
        item
        for item in subtasks
        if isinstance(item, dict)
        and item.get("id") == current_subtask
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Current subtask must resolve to exactly one gate-plan item"
        )

    subtask_status = _required_text(
        matches[0].get("status"),
        "gate_plans.current_subtask.status",
    )

    return CanonicalExecutionProjection(
        state_integrity_sha256=state_sha256,
        current_gate=current_gate,
        current_gate_status=gate_status,
        current_task=current_task,
        current_subtask=current_subtask,
        current_subtask_status=subtask_status,
        execution_status=execution_status,
        current_acceptance_criteria=criteria,
    )


def _git(*args: str) -> str:
    """Run a read-only Git query and fail closed on command errors."""

    process = subprocess.run(
        ["git", *args],
        cwd=CONTROL_CENTER_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if process.returncode != 0:
        message = (
            process.stderr.strip()
            or "no error detail returned"
        )

        raise RuntimeError(
            f"Read-only Git query failed "
            f"({' '.join(args)}): {message}"
        )

    return process.stdout.strip()


def _validate_acrl_spine() -> tuple[str, ...]:
    """Validate the existing canonical T01-T30 registry."""

    if not ACRL_ROOT.is_dir():
        raise RuntimeError(
            f"ACRL root missing: {ACRL_ROOT}"
        )

    descriptors = ACRLTaskRegistry(
        ACRL_ROOT
    ).validate()

    expected = tuple(
        f"T{number:02d}"
        for number in range(1, 31)
    )

    actual = tuple(
        descriptor.task_id
        for descriptor in descriptors
    )

    if actual != expected:
        raise RuntimeError(
            "Canonical ACRL registry returned an unexpected "
            f"T-layer order: {actual}"
        )

    return actual


def _build_context(
    *,
    mission_id: str,
    objective: str,
) -> OperationalContext:
    """Build a read-only context from current repository and state."""

    if not isinstance(mission_id, str) or not mission_id.strip():
        raise ValueError("mission_id is required")

    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("objective is required")

    mission_id = mission_id.strip()
    objective = objective.strip()

    projection = load_execution_projection()

    task_ids = _validate_acrl_spine()

    branch = _git(
        "branch",
        "--show-current",
    )

    head = _git(
        "rev-parse",
        "HEAD",
    )

    clean = (
        _git("status", "--porcelain") == ""
    )

    payload = {
        "mission_id": mission_id,
        "objective": objective,
        "branch": branch,
        "head": head,
        "worktree_clean": clean,
        "state_sha256": (
            projection.state_integrity_sha256
        ),
        "execution": projection.to_dict(),
        "task_ids": task_ids,
        "state_path": str(STATE_PATH.resolve()),
    }

    fingerprint = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return OperationalContext(
        mission_id=mission_id,
        objective=objective,
        git_branch=branch,
        git_head_sha=head,
        worktree_clean=clean,
        acrl_task_ids=task_ids,
        context_fingerprint=fingerprint,
    )


def validate_operational_readiness(
    *,
    mission_id: str,
    note: str,
) -> OperationalResult:
    """Validate read-only operational readiness.

    This routine deliberately has no controller, pipeline, checkpoint,
    state-write, or execution-authorization integration.
    """

    if not isinstance(note, str) or not note.strip():
        raise ValueError("note is required")

    state_before_bytes = STATE_PATH.read_bytes()
    state_before = _load_state()

    if not _state_integrity(state_before):
        raise RuntimeError(
            "Preflight state.json integrity check failed"
        )

    context = _build_context(
        mission_id=mission_id,
        objective="Read-only ACRL operational preflight",
    )

    state_after_bytes = STATE_PATH.read_bytes()
    state_after = _load_state()

    if state_before_bytes != state_after_bytes:
        raise RuntimeError(
            "Read-only preflight detected a change to canonical "
            "state.json; result is rejected"
        )

    if not _state_integrity(state_after):
        raise RuntimeError(
            "Canonical state integrity failed after preflight"
        )

    return OperationalResult(
        mission_id=context.mission_id,
        action_id=f"{context.mission_id}:READ_ONLY_PREFLIGHT",
        status="READ_ONLY_PREFLIGHT_PASS",
        controller_command=(),
        state_integrity=True,
        state_changed=False,
        stdout="",
        stderr="",
        evidence={
            "mode": "READ_ONLY_PREFLIGHT",
            "note": note.strip(),
            "canonical_registry_used": True,
            "acrl_task_count": len(context.acrl_task_ids),
            "acrl_task_ids": list(context.acrl_task_ids),
            "git_branch": context.git_branch,
            "git_head_sha": context.git_head_sha,
            "worktree_clean": context.worktree_clean,
            "context_fingerprint": context.context_fingerprint,
            "state_sha256": state_after["integrity"]["sha256"],
            "state_bytes_unchanged": True,
            "mutation_attempted": False,
            "self_authorized_execution": False,
        },
    )


def run_final_operational_proof(
    *,
    mission_id: str,
    note: str,
) -> OperationalResult:
    """Backward-compatible alias for read-only operational preflight."""

    return validate_operational_readiness(
        mission_id=mission_id,
        note=note,
    )


if __name__ == "__main__":
    result = validate_operational_readiness(
        mission_id="ACRL-READ-ONLY-PREFLIGHT-001",
        note=(
            "Read-only registry, Git identity, "
            "and state-integrity check"
        ),
    )

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
            ensure_ascii=False,
        )
    )


__all__ = [
    "CanonicalExecutionProjection",
    "OperationalContext",
    "OperationalResult",
    "load_execution_projection",
    "run_final_operational_proof",
    "validate_operational_readiness",
]
