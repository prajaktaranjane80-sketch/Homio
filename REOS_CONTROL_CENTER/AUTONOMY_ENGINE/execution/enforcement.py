"""Deterministic preflight/postflight enforcement boundary for AUTONOMY_ENGINE.

This module is an additive enforcement layer.

Design invariants:
- Never executes mutations itself.
- Never bypasses REOS_CONTROL_CENTER authority.
- Fails closed on malformed or incomplete inputs.
- Preflight must pass before a mutation adapter may be called.
- Postflight success requires explicit evidence of successful completion.
- Exceptions are converted into deterministic failure decisions.
- Existing AUTONOMY_ENGINE modules remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from protocols.action_protocol import ActionProposal, validate_proposal


@dataclass(frozen=True)
class EnforcementDecision:
    """Immutable result of an enforcement stage."""

    allowed: bool
    stage: str
    reason: str
    checks: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "allowed": self.allowed,
            "stage": self.stage,
            "reason": self.reason,
            "checks": list(self.checks),
            "failures": list(self.failures),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EnforcementResult:
    """Complete preflight/execution/postflight result."""

    preflight: EnforcementDecision
    execution_attempted: bool
    execution_succeeded: bool
    postflight: EnforcementDecision

    @property
    def allowed(self) -> bool:
        """Return whether the complete operation completed safely."""
        return (
            self.preflight.allowed
            and self.execution_attempted
            and self.execution_succeeded
            and self.postflight.allowed
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "preflight": self.preflight.to_dict(),
            "execution_attempted": self.execution_attempted,
            "execution_succeeded": self.execution_succeeded,
            "postflight": self.postflight.to_dict(),
            "allowed": self.allowed,
        }


class EnforcementEngine:
    """Fail-closed preflight/postflight enforcement boundary.

    The engine evaluates supplied guards and optionally invokes a caller-owned
    mutation adapter only after preflight succeeds.

    The mutation adapter remains outside this module's authority.
    """

    def preflight(
        self,
        proposal: ActionProposal,
        *,
        checks: Mapping[str, Callable[[], bool]] | None = None,
    ) -> EnforcementDecision:
        """Validate an action proposal and all supplied preflight checks."""

        failures: list[str] = []
        executed_checks: list[str] = []

        if not isinstance(proposal, ActionProposal):
            return EnforcementDecision(
                allowed=False,
                stage="PREFLIGHT",
                reason="Invalid action proposal type.",
                failures=("proposal_type",),
            )

        protocol_decision = validate_proposal(proposal)

        executed_checks.append("action_protocol")

        if not protocol_decision.valid:
            failures.extend(
                f"action_protocol:{error}"
                for error in protocol_decision.errors
            )

        for name, check in (checks or {}).items():
            executed_checks.append(name)

            if not isinstance(name, str) or not name.strip():
                failures.append("invalid_check_name")
                continue

            if not callable(check):
                failures.append(f"{name}:check_not_callable")
                continue

            try:
                result = check()
            except Exception as exc:  # defensive boundary
                failures.append(
                    f"{name}:exception:{type(exc).__name__}"
                )
                continue

            if result is not True:
                failures.append(f"{name}:failed")

        allowed = not failures

        return EnforcementDecision(
            allowed=allowed,
            stage="PREFLIGHT",
            reason=(
                "All preflight checks passed."
                if allowed
                else "Preflight rejected the operation."
            ),
            checks=tuple(executed_checks),
            failures=tuple(failures),
        )

    def postflight(
        self,
        *,
        execution_succeeded: bool,
        evidence_complete: bool,
        provenance_valid: bool,
        state_consistent: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> EnforcementDecision:
        """Validate the observable result after a mutation attempt."""

        failures: list[str] = []

        if execution_succeeded is not True:
            failures.append("execution_failed")

        if evidence_complete is not True:
            failures.append("evidence_incomplete")

        if provenance_valid is not True:
            failures.append("provenance_invalid")

        if state_consistent is not True:
            failures.append("state_inconsistent")

        allowed = not failures

        return EnforcementDecision(
            allowed=allowed,
            stage="POSTFLIGHT",
            reason=(
                "Postflight verification passed."
                if allowed
                else "Postflight verification rejected completion."
            ),
            checks=(
                "execution_result",
                "evidence",
                "provenance",
                "state_consistency",
            ),
            failures=tuple(failures),
            metadata=dict(metadata or {}),
        )

    def enforce(
        self,
        proposal: ActionProposal,
        *,
        preflight_checks: Mapping[str, Callable[[], bool]] | None = None,
        mutation_adapter: Callable[[ActionProposal], Any] | None = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> EnforcementResult:
        """Run the complete fail-closed enforcement lifecycle.

        This method does not select or discover a mutation adapter. The caller
        must explicitly provide one. No adapter means no mutation attempt.
        """

        preflight = self.preflight(
            proposal,
            checks=preflight_checks,
        )

        if not preflight.allowed:
            blocked_postflight = EnforcementDecision(
                allowed=False,
                stage="POSTFLIGHT",
                reason="Postflight skipped because preflight failed.",
                failures=("preflight_failed",),
            )

            return EnforcementResult(
                preflight=preflight,
                execution_attempted=False,
                execution_succeeded=False,
                postflight=blocked_postflight,
            )

        if mutation_adapter is None:
            blocked_postflight = EnforcementDecision(
                allowed=False,
                stage="POSTFLIGHT",
                reason="No explicit mutation adapter was supplied.",
                failures=("mutation_adapter_missing",),
            )

            return EnforcementResult(
                preflight=preflight,
                execution_attempted=False,
                execution_succeeded=False,
                postflight=blocked_postflight,
            )

        if not callable(mutation_adapter):
            blocked_postflight = EnforcementDecision(
                allowed=False,
                stage="POSTFLIGHT",
                reason="Mutation adapter is not callable.",
                failures=("mutation_adapter_invalid",),
            )

            return EnforcementResult(
                preflight=preflight,
                execution_attempted=False,
                execution_succeeded=False,
                postflight=blocked_postflight,
            )

        execution_attempted = True
        execution_succeeded = False
        execution_metadata: dict[str, Any] = {}

        try:
            result = mutation_adapter(proposal)

            if isinstance(result, Mapping):
                execution_succeeded = (
                    result.get("success") is True
                )
                execution_metadata.update(result)
            else:
                execution_succeeded = result is True

        except Exception as exc:  # defensive execution boundary
            execution_metadata["exception_type"] = type(exc).__name__
            execution_succeeded = False

        postflight_data = dict(postflight or {})

        postflight_result = self.postflight(
            execution_succeeded=execution_succeeded,
            evidence_complete=(
                postflight_data.get("evidence_complete") is True
            ),
            provenance_valid=(
                postflight_data.get("provenance_valid") is True
            ),
            state_consistent=(
                postflight_data.get("state_consistent") is True
            ),
            metadata=execution_metadata,
        )

        return EnforcementResult(
            preflight=preflight,
            execution_attempted=execution_attempted,
            execution_succeeded=execution_succeeded,
            postflight=postflight_result,
        )