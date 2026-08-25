"""Defensive live read-only REOS_CONTROL_CENTER bridge tests.

Design principles
-----------------
1. Never invent or require fields that the authoritative controller schema
   does not explicitly guarantee.
2. Never mutate controller state.
3. Never use approval/mutation commands as part of a read-only test.
4. Verify the controller through its actual authoritative integrity command.
5. Treat optional/derived controller information as optional.
6. Fail closed on integrity violations.
7. Preserve the existing REOS_CONTROL_CENTER architecture and state schema.

This module tests the observation boundary only.

It does NOT:
- approve gates
- complete subtasks
- verify criteria
- create checkpoints
- synchronize gates
- mutate controller state
- modify AUTONOMY_ENGINE state
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ENGINE_ROOT = Path(__file__).resolve().parents[1]
CONTROL_CENTER_ROOT = ENGINE_ROOT.parent

CONTROLLER = CONTROL_CENTER_ROOT / "reos_control_center.py"
STATE_FILE = CONTROL_CENTER_ROOT / "data" / "state.json"


READ_ONLY_COMMANDS = frozenset(
    {
        "verify-state",
    }
)

FORBIDDEN_MUTATION_COMMANDS = frozenset(
    {
        "approve-gate",
        "complete-subtask",
        "verify-criterion",
        "checkpoint",
        "sync-gate",
    }
)


def _sha256_file(path: Path) -> str:
    """Calculate a file digest without modifying the file."""
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _load_state() -> dict:
    """Load the live controller state defensively."""
    assert STATE_FILE.is_file(), (
        f"Authoritative state file missing: {STATE_FILE}"
    )

    with STATE_FILE.open("r", encoding="utf-8") as handle:
        state = json.load(handle)

    assert isinstance(state, dict), (
        "Authoritative controller state must be a JSON object."
    )

    return state


def _run_read_only_controller_command(
    command: str,
) -> subprocess.CompletedProcess[str]:
    """Execute only commands explicitly classified as read-only."""
    if command not in READ_ONLY_COMMANDS:
        raise ValueError(
            f"Command is not permitted by read-only bridge: {command!r}"
        )

    assert CONTROLLER.is_file(), (
        f"Controller entrypoint missing: {CONTROLLER}"
    )

    return subprocess.run(
        [
            sys.executable,
            str(CONTROLLER),
            command,
        ],
        cwd=str(CONTROL_CENTER_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_controller_entrypoint_exists() -> None:
    """The authoritative REOS controller entrypoint must exist."""
    assert CONTROLLER.is_file()


def test_authoritative_state_is_present_and_valid() -> None:
    """The controller state must exist and remain valid JSON."""
    state = _load_state()

    assert state


def test_controller_integrity_verification_passes() -> None:
    """The controller's own integrity verification must pass."""
    result = _run_read_only_controller_command("verify-state")

    assert result.returncode == 0, (
        "REOS_CONTROL_CENTER verify-state failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    output = result.stdout.upper()

    assert "STATE HASH STORED:" in output
    assert "STATE HASH CALCULATED:" in output
    assert "INTEGRITY: PASS" in output


def test_read_only_integrity_check_does_not_mutate_state() -> None:
    """verify-state must leave authoritative state byte-for-byte unchanged."""
    before = _sha256_file(STATE_FILE)

    result = _run_read_only_controller_command("verify-state")

    after = _sha256_file(STATE_FILE)

    assert result.returncode == 0
    assert before == after, (
        "READ-ONLY BRIDGE VIOLATION: "
        "verify-state changed the authoritative state."
    )


def test_authoritative_execution_plan_is_observable() -> None:
    """The controller state must expose its execution-plan object."""
    state = _load_state()

    execution_plan = state.get("execution_plan")

    assert isinstance(
        execution_plan,
        dict,
    ), "execution_plan must be an object when present."

    authoritative_sequence = execution_plan.get(
        "authoritative_sequence"
    )

    assert isinstance(
        authoritative_sequence,
        list,
    ), (
        "execution_plan.authoritative_sequence must be a list."
    )


def test_controller_metadata_is_structurally_valid() -> None:
    """Validate only metadata fields actually guaranteed by current state."""
    state = _load_state()

    meta = state.get("meta")

    assert isinstance(
        meta,
        dict,
    ), "Controller meta must be an object."

    # These fields are part of the observed authoritative state schema.
    for field_name in (
        "product",
        "version",
        "schema_version",
    ):
        assert field_name in meta, (
            f"Required controller metadata missing: {field_name}"
        )

    assert isinstance(meta["product"], str)
    assert isinstance(meta["version"], str)
    assert isinstance(meta["schema_version"], int)


def test_read_only_boundary_contains_no_mutation_command() -> None:
    """The read-only boundary must remain disjoint from mutation commands."""
    assert READ_ONLY_COMMANDS.isdisjoint(
        FORBIDDEN_MUTATION_COMMANDS
    )


def test_read_only_boundary_is_explicitly_allowlisted() -> None:
    """Unknown commands must never become implicitly read-only."""
    assert "status" not in READ_ONLY_COMMANDS
    assert "gate" not in READ_ONLY_COMMANDS
    assert "plan" not in READ_ONLY_COMMANDS

    # These commands may derive/materialize controller information and
    # therefore are intentionally excluded until their true side effects
    # are independently proven to be read-only.
    assert "sync-gate" in FORBIDDEN_MUTATION_COMMANDS
    assert "checkpoint" in FORBIDDEN_MUTATION_COMMANDS