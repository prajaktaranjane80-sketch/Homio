
"""Governed bridge from typed AI tool proposals to the existing HOMIO gateway.

This module does not create tool executors or grant business authority. It only
uses explicitly configured, read-only actions already registered with the
existing AUTONOMY_ENGINE execution ToolGateway. The bridge is disabled by
default and requires server-owned preflight/evidence checks and a timeout
runner before it can be enabled.
"""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
import json
import re
from types import MappingProxyType, SimpleNamespace
from typing import Any, Protocol

from .contracts import RequestContext, _identifier, _text
from .errors import RequestContextMissingError

_ACTION_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_ARGUMENT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_SECRET_KEY = re.compile(
    r"(?:password|passwd|secret|token|credential|api[_-]?key|access[_-]?key|"
    r"authorization|cookie|private[_-]?key)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?i)(?:\bBearer\s+\S+|\b(?:api[_-]?key|access[_-]?token|password|"
    r"client_secret)\s*[:=]\s*\S+)"
)
_FORBIDDEN_ACTION_FRAGMENTS = (
    "shell",
    "command_exec",
    "run_command",
    "sql",
    "database",
    "repository",
    "repo_",
    "git_",
    "filesystem",
    "read_file",
    "write_file",
    "file_read",
    "file_write",
)


class ToolBridgeError(RuntimeError):
    """A safe, non-sensitive tool-boundary failure."""

    def __init__(
        self,
        message: str = "The requested tool operation was blocked.",
    ) -> None:
        super().__init__(message)


class ToolBridgeConfigurationError(ToolBridgeError):
    """Invalid or incomplete trusted tool-bridge configuration."""

    def __init__(self) -> None:
        super().__init__(
            "The tool execution boundary is not safely configured."
        )


class ToolExecutionBlockedError(ToolBridgeError):
    """A proposal was refused before execution or its result was withheld."""

    def __init__(self) -> None:
        super().__init__(
            "The requested tool operation was blocked by policy."
        )


def _normalise_json(
    value: object,
    *,
    depth: int = 0,
    strict_keys: bool = True,
) -> Any:
    """Copy only small, finite, bounded JSON data."""
    if depth > 8:
        raise ValueError("JSON nesting is too deep")

    if value is None or isinstance(value, bool):
        return value

    if isinstance(value, str):
        if len(value) > 4096:
            raise ValueError("JSON string is too large")
        if any(
            ord(char) < 32 and char not in "\t\n\r"
            for char in value
        ):
            raise ValueError("JSON string contains control characters")
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > 2**53:
            raise ValueError("JSON integer is outside the safe range")
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("JSON number must be finite")
        return value

    if isinstance(value, Mapping):
        if len(value) > 64:
            raise ValueError("JSON object has too many members")

        copied: dict[str, Any] = {}
        for key, item in value.items():
            if (
                not isinstance(key, str)
                or not key
                or len(key) > 128
                or any(ord(char) < 32 for char in key)
                or (
                    strict_keys
                    and not _ARGUMENT_NAME.fullmatch(key)
                )
            ):
                raise ValueError("JSON object has an invalid key")

            copied[key] = _normalise_json(
                item,
                depth=depth + 1,
                strict_keys=strict_keys,
            )
        return copied

    if isinstance(value, (list, tuple)):
        if len(value) > 100:
            raise ValueError("JSON array has too many members")

        return [
            _normalise_json(
                item,
                depth=depth + 1,
                strict_keys=strict_keys,
            )
            for item in value
        ]

    raise ValueError(
        "Tool arguments and results must contain JSON values only"
    )


def _freeze_json(value: Any) -> Any:
    """Prevent callers from mutating a proposal after validation."""
    if isinstance(value, dict):
        return MappingProxyType(
            {
                key: _freeze_json(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _plain_json(value: Any) -> Any:
    """Return a detached JSON-compatible representation."""
    if isinstance(value, Mapping):
        return {
            key: _plain_json(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_plain_json(item) for item in value]
    return value


def _redact_result(value: Any) -> Any:
    """Redact common secret-bearing fields before exposing tool results."""
    if isinstance(value, Mapping):
        return {
            key: (
                "[REDACTED]"
                if _SECRET_KEY.search(key)
                else _redact_result(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_redact_result(item) for item in value]

    if isinstance(value, str):
        return _SECRET_VALUE.sub("[REDACTED]", value)

    return value


def _canonical_action_policy() -> tuple[frozenset[str], frozenset[str]]:
    """Load canonical action classifications; never use a permissive fallback."""
    try:
        from AUTONOMY_ENGINE.core.constants import (
            MUTATING_ACTIONS,
            SENSITIVE_ACTIONS,
        )
    except ImportError:
        try:
            from core.constants import MUTATING_ACTIONS, SENSITIVE_ACTIONS
        except ImportError:
            raise ToolBridgeConfigurationError() from None

    return frozenset(MUTATING_ACTIONS), frozenset(SENSITIVE_ACTIONS)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Trusted server configuration for one explicitly allowlisted tool."""

    name: str
    action_name: str
    description: str
    allowed_arguments: tuple[str, ...] = ()
    required_arguments: tuple[str, ...] = ()
    read_only: bool = True
    max_calls_per_run: int = 1
    timeout_seconds: float = 3.0

    def __post_init__(self) -> None:
        if not _ACTION_NAME.fullmatch(self.name):
            raise ValueError(
                "tool name must be a lowercase identifier"
            )
        if not _ACTION_NAME.fullmatch(self.action_name):
            raise ValueError(
                "tool action must be a lowercase identifier"
            )

        object.__setattr__(
            self,
            "description",
            _text(self.description, "description", 512),
        )

        if (
            isinstance(self.allowed_arguments, (str, bytes))
            or not isinstance(self.allowed_arguments, (tuple, list))
        ):
            raise ValueError(
                "allowed_arguments must be a sequence of names"
            )
        if (
            isinstance(self.required_arguments, (str, bytes))
            or not isinstance(self.required_arguments, (tuple, list))
        ):
            raise ValueError(
                "required_arguments must be a sequence of names"
            )

        allowed = tuple(self.allowed_arguments)
        required = tuple(self.required_arguments)

        if len(set(allowed)) != len(allowed):
            raise ValueError(
                "allowed argument names must not contain duplicates"
            )
        if len(set(required)) != len(required):
            raise ValueError(
                "required argument names must not contain duplicates"
            )

        if any(
            not isinstance(key, str)
            or not _ARGUMENT_NAME.fullmatch(key)
            for key in allowed + required
        ):
            raise ValueError(
                "tool argument names must be identifiers"
            )
        if not set(required).issubset(set(allowed)):
            raise ValueError(
                "required arguments must be in the allowed argument list"
            )

        object.__setattr__(self, "allowed_arguments", allowed)
        object.__setattr__(self, "required_arguments", required)

        if not isinstance(self.read_only, bool) or not self.read_only:
            raise ValueError(
                "T05 only permits explicitly read-only tools"
            )

        if (
            isinstance(self.max_calls_per_run, bool)
            or not isinstance(self.max_calls_per_run, int)
            or not 1 <= self.max_calls_per_run <= 8
        ):
            raise ValueError(
                "max_calls_per_run must be between 1 and 8"
            )

        timeout = self.timeout_seconds
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not isfinite(float(timeout))
            or not 0 < timeout <= 30
        ):
            raise ValueError(
                "timeout_seconds must be greater than 0 and at most 30"
            )

        object.__setattr__(
            self,
            "timeout_seconds",
            float(timeout),
        )


@dataclass(frozen=True, slots=True)
class ToolProposal:
    """Untrusted model proposal normalized to a typed, JSON-only shape."""

    call_id: str
    tool_name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    reason: str = "Read-only tool request"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "call_id",
            _identifier(self.call_id, "call_id"),
        )

        if not _ACTION_NAME.fullmatch(self.tool_name):
            raise ValueError(
                "tool_name must be a lowercase identifier"
            )

        if not isinstance(self.arguments, Mapping):
            raise TypeError("tool arguments must be a mapping")

        copied = _normalise_json(self.arguments)
        object.__setattr__(
            self,
            "arguments",
            _freeze_json(copied),
        )
        object.__setattr__(
            self,
            "reason",
            _text(self.reason, "reason", 512),
        )

    def fingerprint(self) -> str:
        """Stable fingerprint used for circular-call/replay detection."""
        return json.dumps(
            {
                "tool": self.tool_name,
                "arguments": _plain_json(self.arguments),
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )


@dataclass(frozen=True, slots=True)
class ToolExecutionResult:
    """Successful, redacted result suitable for bounded model context."""

    call_id: str
    tool_name: str
    output_json: str


class TimeoutRunner(Protocol):
    def __call__(
        self,
        operation: Callable[[], Any],
        timeout_seconds: float,
    ) -> Any:
        """Invoke an operation with a real, enforced deadline."""


@dataclass(slots=True)
class _RunState:
    call_ids: set[str] = field(default_factory=set)
    fingerprints: set[str] = field(default_factory=set)
    call_counts: dict[str, int] = field(default_factory=dict)
    total_calls: int = 0


class ToolBridge:
    """Fail-closed bridge over an injected existing execution ToolGateway.

    This bridge never registers or replaces gateway adapters. Real execution
    requires a pre-existing read-only adapter, trusted preflight/evidence
    callbacks, and a timeout runner that enforces its deadline.

    The bridge is disabled by default. Its in-memory replay guard is not a
    durable idempotency ledger.
    """

    def __init__(
        self,
        *,
        gateway: object | None = None,
        tools: Sequence[ToolDefinition] = (),
        enabled: bool = False,
        preflight: Callable[
            [ToolProposal, RequestContext], bool
        ] | None = None,
        evidence_check: Callable[
            [ToolProposal, RequestContext], bool
        ] | None = None,
        timeout_runner: TimeoutRunner | None = None,
        max_output_chars: int = 3000,
        max_total_calls: int = 8,
        max_sessions: int = 128,
    ) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean")

        if (
            isinstance(max_output_chars, bool)
            or not isinstance(max_output_chars, int)
            or not 128 <= max_output_chars <= 12000
        ):
            raise ValueError(
                "max_output_chars must be between 128 and 12000"
            )
        if (
            isinstance(max_total_calls, bool)
            or not isinstance(max_total_calls, int)
            or not 1 <= max_total_calls <= 16
        ):
            raise ValueError(
                "max_total_calls must be between 1 and 16"
            )
        if (
            isinstance(max_sessions, bool)
            or not isinstance(max_sessions, int)
            or not 1 <= max_sessions <= 1024
        ):
            raise ValueError(
                "max_sessions must be between 1 and 1024"
            )

        definitions = tuple(tools)
        if any(
            not isinstance(item, ToolDefinition)
            for item in definitions
        ):
            raise TypeError(
                "tools must contain ToolDefinition values"
            )
        if len({item.name for item in definitions}) != len(definitions):
            raise ValueError("tool names must be unique")

        self._enabled = enabled
        self._gateway = gateway
        self._tools = {item.name: item for item in definitions}
        self._preflight = preflight
        self._evidence_check = evidence_check
        self._timeout_runner = timeout_runner
        self._max_output_chars = max_output_chars
        self._max_total_calls = max_total_calls
        self._max_sessions = max_sessions
        self._runs: OrderedDict[str, _RunState] = OrderedDict()
        self._mutating_actions: frozenset[str] = frozenset()
        self._sensitive_actions: frozenset[str] = frozenset()

        if enabled:
            if (
                gateway is None
                or not callable(getattr(gateway, "authorize", None))
                or not callable(getattr(gateway, "execute", None))
                or not isinstance(
                    getattr(gateway, "adapters", None),
                    Mapping,
                )
                or not definitions
                or not callable(preflight)
                or not callable(evidence_check)
                or not callable(timeout_runner)
            ):
                raise ToolBridgeConfigurationError()

            (
                self._mutating_actions,
                self._sensitive_actions,
            ) = _canonical_action_policy()

            adapters = getattr(gateway, "adapters")
            for tool in definitions:
                combined = f"{tool.name} {tool.action_name}".lower()
                if any(
                    fragment in combined
                    for fragment in _FORBIDDEN_ACTION_FRAGMENTS
                ):
                    raise ToolBridgeConfigurationError()

                if (
                    not tool.read_only
                    or tool.action_name in self._mutating_actions
                    or tool.action_name in self._sensitive_actions
                    or tool.action_name not in adapters
                ):
                    raise ToolBridgeConfigurationError()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def available_tools(self) -> tuple[ToolDefinition, ...]:
        if not self._enabled:
            return ()
        return tuple(self._tools.values())

    def describe_available_tools(self) -> tuple[dict[str, Any], ...]:
        """Expose only the server-configured allowlist to the planner."""
        return tuple(
            {
                "name": tool.name,
                "description": tool.description,
                "required_arguments": list(tool.required_arguments),
                "allowed_arguments": list(tool.allowed_arguments),
            }
            for tool in self.available_tools
        )

    def _run_state(self, run_id: str) -> _RunState:
        state = self._runs.get(run_id)
        if state is not None:
            self._runs.move_to_end(run_id)
            return state

        state = _RunState()
        self._runs[run_id] = state
        while len(self._runs) > self._max_sessions:
            self._runs.popitem(last=False)
        return state

    def execute(
        self,
        proposal: ToolProposal,
        context: RequestContext | None,
        *,
        run_id: str,
    ) -> ToolExecutionResult:
        """Validate and run one authorized read-only proposal."""
        if not self._enabled:
            raise ToolExecutionBlockedError()
        if not isinstance(proposal, ToolProposal):
            raise ToolExecutionBlockedError()
        if not isinstance(context, RequestContext):
            raise RequestContextMissingError()

        try:
            normalized_run_id = _identifier(run_id, "run_id")
        except (TypeError, ValueError):
            raise ToolExecutionBlockedError() from None

        tool = self._tools.get(proposal.tool_name)
        if tool is None:
            raise ToolExecutionBlockedError()

        arguments = _plain_json(proposal.arguments)
        argument_names = set(arguments)
        if (
            not set(tool.required_arguments).issubset(argument_names)
            or not argument_names.issubset(
                set(tool.allowed_arguments)
            )
        ):
            raise ToolExecutionBlockedError()

        combined = f"{tool.name} {tool.action_name}".lower()
        if (
            not tool.read_only
            or any(
                fragment in combined
                for fragment in _FORBIDDEN_ACTION_FRAGMENTS
            )
            or tool.action_name in self._mutating_actions
            or tool.action_name in self._sensitive_actions
        ):
            raise ToolExecutionBlockedError()

        adapters = getattr(self._gateway, "adapters", None)
        if (
            not isinstance(adapters, Mapping)
            or tool.action_name not in adapters
        ):
            raise ToolExecutionBlockedError()

        state = self._run_state(normalized_run_id)
        fingerprint = proposal.fingerprint()
        if (
            proposal.call_id in state.call_ids
            or fingerprint in state.fingerprints
            or state.call_counts.get(tool.name, 0)
            >= tool.max_calls_per_run
            or state.total_calls >= self._max_total_calls
        ):
            raise ToolExecutionBlockedError()

        # Claim an attempt before policy/downstream calls. A repeated proposal
        # must not retry after an ambiguous result.
        state.call_ids.add(proposal.call_id)
        state.fingerprints.add(fingerprint)
        state.call_counts[tool.name] = (
            state.call_counts.get(tool.name, 0) + 1
        )
        state.total_calls += 1

        try:
            preflight_ok = self._preflight(proposal, context) is True
            evidence_ok = self._evidence_check(proposal, context) is True
        except Exception:
            raise ToolExecutionBlockedError() from None

        if not preflight_ok or not evidence_ok:
            raise ToolExecutionBlockedError()

        # The existing gateway accepts an attribute-based ToolRequest shape.
        # The bridge does not register or invent a downstream executor.
        gateway_request = SimpleNamespace(
            action=tool.action_name,
            arguments=arguments,
            actor=context.principal_id,
            reason=proposal.reason,
        )

        try:
            decision = self._gateway.authorize(
                gateway_request,
                preflight_ok=preflight_ok,
                evidence_ok=evidence_ok,
            )
        except Exception:
            raise ToolExecutionBlockedError() from None

        if getattr(decision, "allowed", None) is not True:
            raise ToolExecutionBlockedError()

        try:
            raw_result = self._timeout_runner(
                lambda: self._gateway.execute(
                    gateway_request,
                    preflight_ok=preflight_ok,
                    evidence_ok=evidence_ok,
                ),
                tool.timeout_seconds,
            )
            safe_result = _redact_result(
                _normalise_json(raw_result, strict_keys=False)
            )
            output_json = json.dumps(
                safe_result,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except Exception:
            raise ToolExecutionBlockedError() from None

        if len(output_json) > self._max_output_chars:
            raise ToolExecutionBlockedError()

        return ToolExecutionResult(
            call_id=proposal.call_id,
            tool_name=tool.name,
            output_json=output_json,
        )
