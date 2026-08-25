"""
REOS Control Center authoritative executor for AUTONOMY_ENGINE R3.

ARCHITECTURE
------------
AUTONOMY_ENGINE
    |
    v
ExecutionPipeline
    |
    v
ExecutionCoordinator
    |
    v
ControlledMutationAdapter
    |
    v
ControllerExecutor
    |
    v
REOS_CONTROL_CENTER
    |
    v
reos_control_center.py

AUTHORITY RULE
--------------
REOS_CONTROL_CENTER remains the sole authoritative controller.

This module is an EXECUTOR ONLY.

It MUST NOT:
- authorize an action
- approve a gate
- evaluate policy
- evaluate risk
- grant capability
- bypass enforcement
- mutate state.json directly
- discover arbitrary controller commands
- invent controller commands
- retry failed mutations
- transition controller state independently
- repair controller state
- silently modify the requested command

The caller must provide an explicit, validated controller command.

The executor exists to make the final AUTONOMY_ENGINE -> REOS_CONTROL_CENTER
execution boundary deterministic, observable, and fail-closed.

R3 OBJECTIVE
------------
Convert an already-authorized ActionProposal into exactly one explicitly
supplied REOS Control Center command.

No authorization is created here.

No safety decision is created here.

No retry is performed here.

No implicit executor discovery is performed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from protocols.action_protocol import ActionProposal


class ControllerExecutorError(RuntimeError):
    """Base exception for authoritative controller execution failures."""


class ControllerExecutorConfigurationError(ControllerExecutorError):
    """Raised when the executor is incorrectly configured."""


class ControllerCommandRejected(ControllerExecutorError):
    """Raised when a command is not explicitly permitted."""


class ControllerExecutionFailed(ControllerExecutorError):
    """Raised when the authoritative controller returns failure."""


@dataclass(frozen=True)
class ControllerExecutionRequest:
    """
    Immutable explicit execution request.

    The command is supplied by the upstream execution layer.

    This object does not contain authorization. Authorization belongs to the
    upstream governance/enforcement layers.
    """

    proposal: ActionProposal
    command: tuple[str, ...]
    timeout: int = 30
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.command, tuple):
            raise TypeError("command must be a tuple[str, ...]")

        if not self.command:
            raise ValueError("command must not be empty")

        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")


@dataclass(frozen=True)
class ControllerExecutionResult:
    """
    Immutable evidence returned from one controller execution attempt.
    """

    action_id: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    attempted: bool
    succeeded: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.succeeded

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "attempted": self.attempted,
            "succeeded": self.succeeded,
            "evidence": dict(self.evidence),
        }


class ControllerExecutor:
    """
    Explicit authoritative REOS Control Center executor.

    IMPORTANT
    ---------
    This class does not decide whether an operation SHOULD execute.

    It only executes a command that has already crossed all upstream
    authorization and enforcement boundaries.

    The command must be explicitly supplied by the caller.

    No command discovery is performed.
    """

    # ------------------------------------------------------------------
    # Mutation commands intentionally require explicit registration.
    #
    # This set is deliberately empty by default.
    #
    # R3 must not guess the production mutation API of the controller.
    # Once the exact authoritative controller mutation contract is locked,
    # commands can be explicitly registered here or supplied through an
    # immutable executor configuration.
    # ------------------------------------------------------------------

    DEFAULT_ALLOWED_MUTATIONS: frozenset[str] = frozenset()

    # Commands that must NEVER cross this executor boundary.
    #
    # Read-only commands belong to ControllerAdapter /
    # ReadOnlyControllerBridge, not production mutation execution.
    READ_ONLY_COMMANDS: frozenset[str] = frozenset(
        {
            "status",
            "plan",
            "gate",
            "verify-state",
            "verify-all",
            "context",
            "doctor",
        }
    )

    FORBIDDEN_MUTATIONS: frozenset[str] = frozenset(
        {
            "repair",
            "reset",
        }
    )

    def __init__(
        self,
        control_root: Path,
        *,
        allowed_mutations: Sequence[str] | None = None,
        default_timeout: int = 30,
    ) -> None:
        self.control_root = Path(control_root).resolve()
        self.controller = self.control_root / "reos_control_center.py"

        if default_timeout <= 0:
            raise ValueError("default_timeout must be greater than zero")

        configured = (
            self.DEFAULT_ALLOWED_MUTATIONS
            if allowed_mutations is None
            else frozenset(allowed_mutations)
        )

        self._allowed_mutations = frozenset(configured)
        self._default_timeout = default_timeout

        self._validate_configuration()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def allowed_mutations(self) -> frozenset[str]:
        """Return the immutable production mutation allow-list."""

        return self._allowed_mutations

    @property
    def available(self) -> bool:
        """Return whether the authoritative controller entrypoint exists."""

        return self.controller.is_file()

    def execute(
        self,
        proposal: ActionProposal,
        *,
        command: Sequence[str],
        timeout: int | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> ControllerExecutionResult:
        """
        Execute exactly one explicitly supplied controller mutation.

        This method intentionally does not accept:
        - authorization flags
        - policy overrides
        - risk overrides
        - capability grants
        - retry configuration

        Those decisions belong upstream.

        Parameters
        ----------
        proposal:
            Already validated ActionProposal.

        command:
            Explicit controller command, e.g. ("complete-subtask", "...").

        timeout:
            Optional execution timeout.

        evidence:
            Caller-supplied provenance/evidence. It is preserved but not
            interpreted as authorization.
        """

        request = ControllerExecutionRequest(
            proposal=proposal,
            command=tuple(command),
            timeout=(
                self._default_timeout
                if timeout is None
                else timeout
            ),
            evidence=dict(evidence or {}),
        )

        self._validate_request(request)

        action_id = proposal.action_id

        completed_command = self._build_command(request.command)

        try:
            process = subprocess.run(
                completed_command,
                cwd=self.control_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=request.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ControllerExecutionFailed(
                "Authoritative REOS Control Center execution timed out."
            ) from exc
        except OSError as exc:
            raise ControllerExecutionFailed(
                "Unable to start the authoritative REOS Control Center."
            ) from exc

        succeeded = process.returncode == 0

        result = ControllerExecutionResult(
            action_id=action_id,
            command=tuple(request.command),
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            attempted=True,
            succeeded=succeeded,
            evidence={
                **dict(request.evidence),
                "executor": "ControllerExecutor",
                "controller_authoritative": True,
                "execution_attempted": True,
                "execution_succeeded": succeeded,
                "controller_returncode": process.returncode,
            },
        )

        if not succeeded:
            raise ControllerExecutionFailed(
                self._failure_message(result)
            )

        return result

    def __call__(
        self,
        proposal: ActionProposal,
    ) -> ControllerExecutionResult:
        """
        Callable compatibility entrypoint.

        IMPORTANT:
        A production mutation command cannot be inferred from an
        ActionProposal.

        Therefore this callable form intentionally fails closed.

        Production callers must use execute(..., command=...).
        """

        raise ControllerExecutorConfigurationError(
            "ControllerExecutor requires an explicit controller command; "
            "no command may be inferred from ActionProposal."
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_command(
        self,
        command: Sequence[str],
    ) -> tuple[str, ...]:
        """
        Validate an explicitly supplied controller command.

        Returns the normalized immutable command tuple.

        No process is started.
        """

        normalized = tuple(command)

        if not normalized:
            raise ControllerCommandRejected(
                "Controller command cannot be empty."
            )

        command_name = normalized[0]

        if not isinstance(command_name, str):
            raise ControllerCommandRejected(
                "Controller command name must be a string."
            )

        if not command_name.strip():
            raise ControllerCommandRejected(
                "Controller command name cannot be empty."
            )

        if command_name in self.READ_ONLY_COMMANDS:
            raise ControllerCommandRejected(
                f"Read-only controller command '{command_name}' "
                "cannot cross the production mutation executor."
            )

        if command_name in self.FORBIDDEN_MUTATIONS:
            raise ControllerCommandRejected(
                f"Controller mutation '{command_name}' is permanently "
                "blocked by the production executor."
            )

        if command_name not in self._allowed_mutations:
            raise ControllerCommandRejected(
                f"Controller mutation '{command_name}' is not explicitly "
                "registered in the production executor allow-list."
            )

        for argument in normalized:
            if not isinstance(argument, str):
                raise ControllerCommandRejected(
                    "Every controller command argument must be a string."
                )

        return normalized

    # ------------------------------------------------------------------
    # Configuration validation
    # ------------------------------------------------------------------

    def _validate_configuration(self) -> None:
        """
        Validate executor configuration without executing anything.
        """

        if not self.control_root.exists():
            raise ControllerExecutorConfigurationError(
                f"Control Center root does not exist: {self.control_root}"
            )

        if self._default_timeout <= 0:
            raise ControllerExecutorConfigurationError(
                "Production executor timeout must be positive."
            )

        overlap = (
            self._allowed_mutations
            & self.READ_ONLY_COMMANDS
        )

        if overlap:
            raise ControllerExecutorConfigurationError(
                "Mutation allow-list contains read-only commands: "
                + ", ".join(sorted(overlap))
            )

        forbidden_overlap = (
            self._allowed_mutations
            & self.FORBIDDEN_MUTATIONS
        )

        if forbidden_overlap:
            raise ControllerExecutorConfigurationError(
                "Mutation allow-list contains permanently forbidden "
                "commands: "
                + ", ".join(sorted(forbidden_overlap))
            )

    def _validate_request(
        self,
        request: ControllerExecutionRequest,
    ) -> None:
        """
        Validate the complete execution request before process creation.
        """

        if not isinstance(request.proposal, ActionProposal):
            raise ControllerCommandRejected(
                "Controller execution requires an ActionProposal."
            )

        valid, errors = request.proposal.validate()

        if not valid:
            raise ControllerCommandRejected(
                "ActionProposal failed validation: "
                + "; ".join(errors)
            )

        if not self.controller.is_file():
            raise ControllerExecutorConfigurationError(
                f"Authoritative controller entrypoint not found: "
                f"{self.controller}"
            )

        if request.timeout <= 0:
            raise ControllerCommandRejected(
                "Controller execution timeout must be positive."
            )

        self.validate_command(request.command)

    # ------------------------------------------------------------------
    # Process construction
    # ------------------------------------------------------------------

    def _build_command(
        self,
        command: Sequence[str],
    ) -> list[str]:
        """
        Build the final subprocess command.

        The Python interpreter and controller entrypoint are owned by this
        executor. The mutation command itself must come from the explicit
        caller-supplied allow-listed command.
        """

        normalized = self.validate_command(command)

        return [
            sys.executable,
            str(self.controller),
            *normalized,
        ]

    # ------------------------------------------------------------------
    # Failure evidence
    # ------------------------------------------------------------------

    @staticmethod
    def _failure_message(
        result: ControllerExecutionResult,
    ) -> str:
        stderr = result.stderr.strip()

        if stderr:
            return (
                "Authoritative REOS Control Center returned "
                f"exit code {result.returncode}: {stderr}"
            )

        return (
            "Authoritative REOS Control Center returned "
            f"exit code {result.returncode}."
        )


__all__ = [
    "ControllerExecutor",
    "ControllerExecutionRequest",
    "ControllerExecutionResult",
    "ControllerExecutorError",
    "ControllerExecutorConfigurationError",
    "ControllerCommandRejected",
    "ControllerExecutionFailed",
]