from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    """Immutable result of one controller observation command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Return True only when the controller process succeeded."""
        return self.returncode == 0


class ControllerAdapter:
    """
    Preventive read-only adapter for the existing REOS Control Center.

    Authority boundary
    ------------------
    This adapter is an observation boundary only.

    It:
    - may invoke explicitly allow-listed read-only controller commands
    - never grants mutation authority
    - never approves controller work
    - never transitions controller state
    - never repairs controller state
    - never writes state.json
    - never discovers a mutation executor
    - never invents controller commands
    - never converts a compatibility flag into authorization

    Security model
    --------------
    Default deny.

    A command must be explicitly present in READ_ONLY_COMMANDS.
    Anything else is rejected before subprocess execution.

    `allow_mutation` is retained only as a compatibility parameter for
    existing callers. True mutation authority can never be obtained through
    this adapter. Supplying allow_mutation=True is therefore itself rejected.

    Timeout behavior is fail-closed. A timeout is surfaced as TimeoutError
    rather than being converted into a successful-looking CommandResult.
    """

    # Explicit read-only command allow-list.
    READ_ONLY_COMMANDS = {
        "status",
        "plan",
        "gate",
        "verify-state",
        "verify-all",
        "context",
        "doctor",
    }

    # Explicit documentation of controller mutation boundaries.
    #
    # These commands are NEVER executed by this adapter, regardless of
    # allow_mutation.
    MUTATING_PREFIXES = {
        "complete-subtask",
        "verify-criterion",
        "validate-gate",
        "approve-gate",
        "repair",
        "transition",
        "reset",
    }

    # Deterministic discovery order is part of the observation contract.
    DISCOVERY_COMMANDS = (
        "verify-state",
        "status",
        "plan",
        "gate",
        "verify-all",
        "doctor",
        "context",
    )

    DEFAULT_TIMEOUT = 30

    def __init__(self, root: Path) -> None:
        """
        Create a read-only controller adapter.

        The adapter stores only the resolved controller root. It does not
        inspect or mutate controller state during construction.
        """
        self.root = Path(root).resolve()
        self.entrypoint = self.root / "reos_control_center.py"

    def _base(self) -> list[str]:
        """Return the controller invocation prefix after existence validation."""
        if not self.entrypoint.exists():
            raise FileNotFoundError(
                f"Controller entrypoint not found: {self.entrypoint}"
            )

        if not self.entrypoint.is_file():
            raise FileNotFoundError(
                f"Controller entrypoint is not a file: {self.entrypoint}"
            )

        return [sys.executable, str(self.entrypoint)]

    @classmethod
    def _is_mutating_command(cls, command: str) -> bool:
        """
        Return True when a command is explicitly known as mutating.

        This is informational for the boundary; mutation commands are denied
        regardless of whether they appear in this set.
        """
        return command in cls.MUTATING_PREFIXES

    @classmethod
    def _validate_command(cls, args: tuple[str, ...]) -> str:
        """
        Validate and authorize a controller command.

        No command normalization is performed that could accidentally turn
        an unapproved command into an approved command.
        """
        if not args:
            raise ValueError("A controller command is required.")

        command = args[0]

        if not isinstance(command, str) or not command.strip():
            raise ValueError("Controller command must be a non-empty string.")

        if command not in cls.READ_ONLY_COMMANDS:
            if cls._is_mutating_command(command):
                raise PermissionError(
                    f"Mutation command blocked by safe adapter: '{command}'."
                )

            raise PermissionError(
                f"Command not allow-listed by safe adapter: '{command}'."
            )

        return command

    def run(
        self,
        *args: str,
        timeout: int = DEFAULT_TIMEOUT,
        allow_mutation: bool = False,
    ) -> CommandResult:
        """
        Execute exactly one approved read-only controller command.

        Important:
        `allow_mutation=True` NEVER enables mutation. The parameter exists only
        to preserve compatibility with older callers and is deliberately
        rejected when supplied.
        """
        command = self._validate_command(args)

        # Preventive compatibility boundary:
        # this adapter has no mutation mode.
        if allow_mutation:
            raise PermissionError(
                "Mutation authority cannot be granted through ControllerAdapter."
            )

        if not isinstance(timeout, int):
            raise TypeError("timeout must be an integer.")

        if isinstance(timeout, bool):
            raise TypeError("timeout must be an integer, not boolean.")

        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        base = self._base()
        full_command = base + list(args)

        try:
            process = subprocess.run(
                full_command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            # Never convert a timeout into a normal CommandResult.
            raise TimeoutError(
                f"Controller command '{command}' timed out "
                f"after {timeout} seconds."
            ) from exc

        return CommandResult(
            command=tuple(full_command),
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def discover(self) -> dict[str, Any]:
        """
        Observe the controller's read-only surface.

        Discovery is strictly observational:
        - no mutation command is attempted
        - no state is changed
        - command order is deterministic
        - individual observation failures are recorded
        """
        result: dict[str, Any] = {
            "root": str(self.root),
            "entrypoint_exists": self.entrypoint.is_file(),
            "read_only_commands": [],
            "errors": [],
        }

        if not self.entrypoint.is_file():
            result["errors"].append(
                f"Controller entrypoint not found: {self.entrypoint}"
            )
            return result

        for command in self.DISCOVERY_COMMANDS:
            try:
                observation = self.run(
                    command,
                    timeout=20,
                )

                result["read_only_commands"].append(
                    {
                        "command": command,
                        "available": True,
                        "returncode": observation.returncode,
                        "stdout_preview": observation.stdout[-3000:],
                        "stderr_preview": observation.stderr[-1000:],
                    }
                )

            except Exception as exc:
                result["read_only_commands"].append(
                    {
                        "command": command,
                        "available": False,
                        "error": str(exc),
                    }
                )

        return result

    @classmethod
    def is_read_only_command(cls, command: str) -> bool:
        """Return whether a command belongs to the explicit read-only surface."""
        return command in cls.READ_ONLY_COMMANDS

    @classmethod
    def is_mutating_command(cls, command: str) -> bool:
        """Return whether a command is explicitly known as mutating."""
        return cls._is_mutating_command(command)