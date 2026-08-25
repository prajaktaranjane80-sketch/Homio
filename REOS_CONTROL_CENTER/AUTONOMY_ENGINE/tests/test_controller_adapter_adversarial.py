"""
Adversarial tests for the controller adapter boundary.

These tests verify that AUTONOMY_ENGINE can observe the authoritative
REOS_CONTROL_CENTER only through explicitly allow-listed read-only commands.

The adapter must:
- allow only approved read-only commands;
- reject mutation commands;
- reject unknown commands;
- fail closed when the controller entrypoint is missing;
- preserve controller process results;
- never provide an AUTONOMY_ENGINE-side mutation bypass.

These tests are additive and do not modify controller state.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from adapter.controller_adapter import ControllerAdapter  # noqa: E402


READ_ONLY_COMMANDS = (
    "status",
    "plan",
    "gate",
    "verify-state",
    "verify-all",
    "context",
    "doctor",
)

MUTATING_COMMANDS = (
    "complete-subtask",
    "verify-criterion",
    "validate-gate",
    "approve-gate",
    "repair",
    "transition",
    "reset",
)


class FakeCompletedProcess:
    """Minimal subprocess result used to test adapter behavior."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_adapter(tmp_path: Path) -> ControllerAdapter:
    """Create an adapter rooted at a temporary controller workspace."""
    entrypoint = tmp_path / "reos_control_center.py"
    entrypoint.write_text(
        "print('controller-test')\n",
        encoding="utf-8",
    )
    return ControllerAdapter(tmp_path)


def test_read_only_commands_are_allow_listed() -> None:
    """Every declared read-only command must be explicitly allow-listed."""
    assert set(READ_ONLY_COMMANDS).issubset(
        ControllerAdapter.READ_ONLY_COMMANDS
    )


@pytest.mark.parametrize("command", MUTATING_COMMANDS)
def test_mutating_commands_are_not_read_only(command: str) -> None:
    """Known controller mutations must never become read-only commands."""
    assert command not in ControllerAdapter.READ_ONLY_COMMANDS


@pytest.mark.parametrize("command", MUTATING_COMMANDS)
def test_mutating_commands_are_blocked_by_default(
    tmp_path: Path,
    command: str,
) -> None:
    """Mutation commands must fail closed through the adapter."""
    adapter = make_adapter(tmp_path)

    with pytest.raises(PermissionError):
        adapter.run(command)


@pytest.mark.parametrize(
    "command",
    (
        "",
        "unknown",
        "execute",
        "write-state",
        "shell",
        "python",
        "rm",
    ),
)
def test_unknown_commands_are_blocked(
    tmp_path: Path,
    command: str,
) -> None:
    """Commands outside the explicit allowlist must be rejected."""
    adapter = make_adapter(tmp_path)

    with pytest.raises((PermissionError, ValueError)):
        adapter.run(command)


def test_missing_controller_entrypoint_fails_closed(
    tmp_path: Path,
) -> None:
    """A missing authoritative controller must prevent execution."""
    adapter = ControllerAdapter(tmp_path)

    with pytest.raises(FileNotFoundError):
        adapter.run("status")


def test_base_command_points_to_authoritative_controller(
    tmp_path: Path,
) -> None:
    """The adapter must resolve the expected controller entrypoint."""
    adapter = make_adapter(tmp_path)

    command = adapter._base()

    assert command[0] == sys.executable
    assert command[1] == str(
        tmp_path.resolve() / "reos_control_center.py"
    )


def test_successful_read_only_command_preserves_process_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful observation must preserve stdout/stderr/returncode."""
    adapter = make_adapter(tmp_path)

    captured: list[list[str]] = []

    def fake_run(*args, **kwargs):
        captured.append(list(args[0]))
        return FakeCompletedProcess(
            returncode=0,
            stdout="STATUS OK",
            stderr="",
        )

    monkeypatch.setattr(
        "adapter.controller_adapter.subprocess.run",
        fake_run,
    )

    result = adapter.run("status")

    assert result.ok is True
    assert result.returncode == 0
    assert result.stdout == "STATUS OK"
    assert result.stderr == ""
    assert captured

    assert captured[0][-1] == "status"


def test_nonzero_controller_exit_is_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Controller failure must not be converted into adapter success."""
    adapter = make_adapter(tmp_path)

    def fake_run(*args, **kwargs):
        return FakeCompletedProcess(
            returncode=7,
            stdout="",
            stderr="controller failure",
        )

    monkeypatch.setattr(
        "adapter.controller_adapter.subprocess.run",
        fake_run,
    )

    result = adapter.run("verify-state")

    assert result.ok is False
    assert result.returncode == 7
    assert result.stderr == "controller failure"


def test_mutation_flag_cannot_bypass_default_boundary(
    tmp_path: Path,
) -> None:
    """
    Existing compatibility parameters, if present, must not be treated as
    authorization to execute controller mutations.
    """
    adapter = make_adapter(tmp_path)

    try:
        adapter.run("approve-gate", allow_mutation=True)
    except PermissionError:
        return

    pytest.fail(
        "controller_adapter exposed a mutation bypass through "
        "allow_mutation=True"
    )


def test_mutating_prefixes_are_defined_for_boundary_documentation() -> None:
    """The adapter must retain an explicit mutation classification."""
    assert hasattr(ControllerAdapter, "MUTATING_PREFIXES")

    for command in MUTATING_COMMANDS:
        assert command in ControllerAdapter.MUTATING_PREFIXES


def test_discover_is_observation_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discovery must use only the adapter's read-only path."""
    adapter = make_adapter(tmp_path)

    calls: list[str] = []

    def fake_run(command: str, timeout: int = 30):
        calls.append(command)
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": f"{command}:ok",
                "stderr": "",
            },
        )()

    monkeypatch.setattr(adapter, "run", fake_run)

    result = adapter.discover()

    assert result["entrypoint_exists"] is True
    assert calls == [
        "verify-state",
        "status",
        "plan",
        "gate",
        "verify-all",
        "doctor",
        "context",
    ]

    assert all(
        command in READ_ONLY_COMMANDS
        for command in calls
    )


def test_adapter_does_not_directly_write_state(tmp_path: Path) -> None:
    """The adapter module must not expose a direct state mutation API."""
    adapter = make_adapter(tmp_path)

    forbidden_methods = (
        "write_state",
        "update_state",
        "mutate_state",
        "approve_gate",
        "complete_subtask",
        "transition",
        "repair",
        "reset_controller",
    )

    for method_name in forbidden_methods:
        assert not hasattr(adapter, method_name)


def test_read_only_command_set_has_no_known_mutations() -> None:
    """The read-only allowlist and mutation denylist must not overlap."""
    assert (
        ControllerAdapter.READ_ONLY_COMMANDS
        .isdisjoint(ControllerAdapter.MUTATING_PREFIXES)
    )


def test_adapter_root_is_resolved(
    tmp_path: Path,
) -> None:
    """Controller root must be normalized before execution."""
    adapter = ControllerAdapter(tmp_path)

    assert adapter.root == tmp_path.resolve()
    assert adapter.entrypoint == (
        tmp_path.resolve() / "reos_control_center.py"
    )


def test_empty_arguments_fail_closed(
    tmp_path: Path,
) -> None:
    """No controller command means no controller execution."""
    adapter = make_adapter(tmp_path)

    with pytest.raises(ValueError):
        adapter.run()


def test_timeout_is_not_swallowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Controller timeout must propagate rather than becoming success."""
    adapter = make_adapter(tmp_path)

    def fake_run(*args, **kwargs):
        raise TimeoutError("controller timeout")

    monkeypatch.setattr(
        "adapter.controller_adapter.subprocess.run",
        fake_run,
    )

    with pytest.raises(TimeoutError, match="controller timeout"):
        adapter.run("status")


def test_discover_fails_closed_per_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Discovery must record command-level failures rather than silently
    converting them into available commands.
    """
    adapter = make_adapter(tmp_path)

    def fake_run(command: str, timeout: int = 30):
        if command == "doctor":
            raise RuntimeError("doctor unavailable")

        return FakeCompletedProcess(
            returncode=0,
            stdout=f"{command}:ok",
            stderr="",
        )

    monkeypatch.setattr(adapter, "run", fake_run)

    result = adapter.discover()

    doctor = next(
        item
        for item in result["read_only_commands"]
        if item["command"] == "doctor"
    )

    assert doctor["available"] is False
    assert "doctor unavailable" in doctor["error"]