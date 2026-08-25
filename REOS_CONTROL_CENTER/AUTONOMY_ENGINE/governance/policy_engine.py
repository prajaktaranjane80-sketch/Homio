"""Policy evaluation primitives for AUTONOMY_ENGINE V6.

This module provides deterministic, deny-by-default policy evaluation.
It does not replace the existing AUTONOMY_ENGINE policy layer and must
remain additive until isolated validation and controlled merge approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PolicyRule:
    """A deterministic governance rule."""

    rule_id: str
    action: str
    effect: str
    conditions: Mapping[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True

    def matches(
        self,
        *,
        action: str,
        context: Mapping[str, Any],
    ) -> bool:
        """Return True when the rule applies to the supplied request."""
        if not self.enabled:
            return False

        if self.action != "*" and self.action != action:
            return False

        for key, expected in self.conditions.items():
            if context.get(key) != expected:
                return False

        return True


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating a governance request."""

    allowed: bool
    action: str
    rule_id: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible decision."""
        return {
            "allowed": self.allowed,
            "action": self.action,
            "rule_id": self.rule_id,
            "reason": self.reason,
        }


class PolicyEngine:
    """Evaluate policy rules using deterministic deny precedence.

    Rules with an explicit DENY effect always take precedence over ALLOW
    rules at the same request boundary. If no rule allows an operation,
    the engine fails closed.
    """

    def __init__(
        self,
        rules: list[PolicyRule] | None = None,
    ) -> None:
        self._rules: list[PolicyRule] = list(rules or [])

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a policy rule."""
        if any(existing.rule_id == rule.rule_id for existing in self._rules):
            raise ValueError(f"Duplicate policy rule: {rule.rule_id}")

        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a policy rule by ID."""
        before = len(self._rules)
        self._rules = [
            rule for rule in self._rules
            if rule.rule_id != rule_id
        ]
        return len(self._rules) != before

    def evaluate(
        self,
        *,
        action: str,
        context: Mapping[str, Any] | None = None,
    ) -> PolicyDecision:
        """Evaluate an action against the registered policy rules."""
        request_context = dict(context or {})

        matched = [
            rule
            for rule in self._rules
            if rule.matches(
                action=action,
                context=request_context,
            )
        ]

        if not matched:
            return PolicyDecision(
                allowed=False,
                action=action,
                rule_id=None,
                reason="No matching policy rule; denied by default.",
            )

        denies = [
            rule
            for rule in matched
            if rule.effect.upper() == "DENY"
        ]

        if denies:
            selected = max(
                denies,
                key=lambda rule: rule.priority,
            )
            return PolicyDecision(
                allowed=False,
                action=action,
                rule_id=selected.rule_id,
                reason="Explicit deny policy matched.",
            )

        allows = [
            rule
            for rule in matched
            if rule.effect.upper() == "ALLOW"
        ]

        if allows:
            selected = max(
                allows,
                key=lambda rule: rule.priority,
            )
            return PolicyDecision(
                allowed=True,
                action=action,
                rule_id=selected.rule_id,
                reason="Explicit allow policy matched.",
            )

        return PolicyDecision(
            allowed=False,
            action=action,
            rule_id=None,
            reason="No valid allow policy matched; denied by default.",
        )

    def rules(self) -> tuple[PolicyRule, ...]:
        """Return the current immutable rule view."""
        return tuple(self._rules)