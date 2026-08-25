
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.constants import MUTATING_ACTIONS, SENSITIVE_ACTIONS

@dataclass(frozen=True)
class ToolRequest:
    action: str
    arguments: dict[str, Any]
    actor: str = "agent"
    reason: str | None = None

@dataclass(frozen=True)
class ToolDecision:
    allowed: bool
    reason: str

class ToolGateway:
    """
    Policy gateway. By default this class is non-mutating.
    A future Control Center adapter must be explicitly registered.
    """

    def __init__(self) -> None:
        self.adapters: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(self, action: str, fn: Callable[[dict[str, Any]], Any]) -> None:
        self.adapters[action] = fn

    def authorize(self, request: ToolRequest, preflight_ok: bool, evidence_ok: bool) -> ToolDecision:
        if not preflight_ok:
            return ToolDecision(False, "Preflight failed; fail closed.")
        if not evidence_ok:
            return ToolDecision(False, "Required evidence is not established; fail closed.")
        if request.action in SENSITIVE_ACTIONS and not request.reason:
            return ToolDecision(False, "Sensitive action requires an explicit reason.")
        if request.action in MUTATING_ACTIONS and request.action not in self.adapters:
            return ToolDecision(False, "No registered execution adapter exists for this mutation.")
        return ToolDecision(True, "Authorized by local policy; adapter is required for mutation.")

    def execute(self, request: ToolRequest, preflight_ok: bool, evidence_ok: bool) -> Any:
        decision = self.authorize(request, preflight_ok, evidence_ok)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        fn = self.adapters[request.action]
        return fn(request.arguments)
