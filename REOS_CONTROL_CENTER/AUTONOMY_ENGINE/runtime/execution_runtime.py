from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    action: str
    target: str
    reason: str
    requires_mutation: bool
    risk_level: str


@dataclass(frozen=True, slots=True)
class ExecutionEnvelope:
    intent: ExecutionIntent
    authorized: bool
    capability_available: bool
    policy_allowed: bool
    guard_allowed: bool
    idempotency_clear: bool
    tripwires_clear: bool
    architecture_locked: bool
    evidence: dict[str, Any]


class ExecutionRuntime:
    """
    Prepare a bounded execution envelope.

    This class DOES NOT execute anything. Existing ExecutionPipeline,
    ExecutionCoordinator and ControllerExecutor remain the execution boundary.
    """

    def prepare(
        self,
        intent: ExecutionIntent,
        *,
        evidence: dict[str, Any],
        authorized: bool = False,
        capability_available: bool = False,
        policy_allowed: bool = False,
        guard_allowed: bool = False,
        idempotency_clear: bool = False,
        tripwires_clear: bool = False,
        architecture_locked: bool = False,
    ) -> ExecutionEnvelope:
        if intent.requires_mutation and not authorized:
            raise PermissionError(
                "explicit authorization required"
            )

        return ExecutionEnvelope(
            intent=intent,
            authorized=authorized,
            capability_available=capability_available,
            policy_allowed=policy_allowed,
            guard_allowed=guard_allowed,
            idempotency_clear=idempotency_clear,
            tripwires_clear=tripwires_clear,
            architecture_locked=architecture_locked,
            evidence=dict(evidence),
        )

    @staticmethod
    def ready(
        envelope: ExecutionEnvelope,
    ) -> bool:
        return all(
            (
                envelope.authorized,
                envelope.capability_available,
                envelope.policy_allowed,
                envelope.guard_allowed,
                envelope.idempotency_clear,
                envelope.tripwires_clear,
            )
        )
