from __future__ import annotations

"""
Read-only ACRL operational preflight.

Safety contract:
- Read and validate canonical Control Center state.
- Discover T01-T30 through the canonical ACRLTaskRegistry.
- Collect local Git identity for verification.
- Never execute a checkpoint, mutate state.json, or self-authorize execution.

The legacy run_final_operational_proof name is retained for compatibility,
but the function now performs read-only preflight only.
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

# Use the one canonical T-layer registry. Do not maintain a second
# directory-counting implementation here.
from continuity.acrl.runtime_integration.task_registry import (  # noqa: E402
    ACRLTaskRegistry,
)


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


def _load_state() -> dict[str, Any]:
    """Load the canonical state as a JSON object without modifying it."""

    if not STATE_PATH.is_file():
        raise RuntimeError(f"Canonical state missing: {STATE_PATH}")

    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read valid state.json: {exc}") from exc

    if not isinstance(value, dict):
        raise RuntimeError("Canonical state.json root must be a JSON object")

    return value


def _state_hash(state: dict[str, Any]) -> str:
    """Calculate the Control Center's canonical integrity hash."""

    clone = json.loads(json.dumps(state, ensure_ascii=False))
    integrity = clone.get("integrity")

    if not isinstance(integrity, dict):
        raise RuntimeError("Canonical state integrity object is missing")

    integrity["sha256"] = None

    canonical = json.dumps(
        clone,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def _state_integrity(state: dict[str, Any]) -> bool:
    integrity = state.get("integrity")

    if not isinstance(integrity, dict):
        return False

    stored = integrity.get("sha256")

    return isinstance(stored, str) and stored == _state_hash(state)


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
        message = process.stderr.strip() or "no error detail returned"
        raise RuntimeError(
            f"Read-only Git query failed ({' '.join(args)}): {message}"
        )

    return process.stdout.strip()


def _validate_acrl_spine() -> tuple[str, ...]:
    """
    Validate the existing canonical T01-T30 registry.

    T14 directory compatibility rules belong to ACRLTaskRegistry, not here.
    """

    if not ACRL_ROOT.is_dir():
        raise RuntimeError(f"ACRL root missing: {ACRL_ROOT}")

    descriptors = ACRLTaskRegistry(ACRL_ROOT).validate()

    expected = tuple(f"T{number:02d}" for number in range(1, 31))
    actual = tuple(descriptor.task_id for descriptor in descriptors)

    if actual != expected:
        raise RuntimeError(
            "Canonical ACRL registry returned an unexpected T-layer order: "
            f"{actual}"
        )

    return actual


def _build_context(
    *,
    mission_id: str,
    objective: str,
) -> OperationalContext:
    """Build a read-only context from the current repository and state."""

    if not isinstance(mission_id, str) or not mission_id.strip():
        raise ValueError("mission_id is required")

    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("objective is required")

    mission_id = mission_id.strip()
    objective = objective.strip()

    state = _load_state()

    if not _state_integrity(state):
        raise RuntimeError("Preflight state.json integrity check failed")

    constitution = state.get("constitution")

    if not isinstance(constitution, dict):
        raise RuntimeError("Canonical constitution is missing")

    integrity = state.get("integrity")
    state_sha256 = integrity.get("sha256") if isinstance(integrity, dict) else None

    if not isinstance(state_sha256, str) or not state_sha256:
        raise RuntimeError("Canonical state fingerprint is missing")

    task_ids = _validate_acrl_spine()

    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    clean = _git("status", "--porcelain") == ""

    payload = {
        "mission_id": mission_id,
        "objective": objective,
        "branch": branch,
        "head": head,
        "worktree_clean": clean,
        "state_sha256": state_sha256,
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
    """
    Validate read-only readiness.

    This routine deliberately has no controller, pipeline, checkpoint,
    state-write, or execution-authorization integration.
    """

    if not isinstance(note, str) or not note.strip():
        raise ValueError("note is required")

    state_before_bytes = STATE_PATH.read_bytes()
    state_before = _load_state()

    if not _state_integrity(state_before):
        raise RuntimeError("Preflight state.json integrity check failed")

    context = _build_context(
        mission_id=mission_id,
        objective="Read-only ACRL operational preflight",
    )

    state_after_bytes = STATE_PATH.read_bytes()
    state_after = _load_state()

    if state_before_bytes != state_after_bytes:
        raise RuntimeError(
            "Read-only preflight detected a change to canonical state.json; "
            "result is rejected"
        )

    if not _state_integrity(state_after):
        raise RuntimeError("Canonical state integrity failed after preflight")

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
    """
    Backward-compatible alias.

    Despite the historic name, this entry point is read-only. A mutating
    operational proof must not be performed by this module.
    """

    return validate_operational_readiness(
        mission_id=mission_id,
        note=note,
    )


if __name__ == "__main__":
    result = validate_operational_readiness(
        mission_id="ACRL-READ-ONLY-PREFLIGHT-001",
        note="Read-only registry, Git identity, and state-integrity check",
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
