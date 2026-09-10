from __future__ import annotations

from dataclasses import dataclass

from ..T15_AI_Operator_Autonomy.operator_policy import (
    OperatorActionType,
    OperatorRisk,
)

from .authorization_errors import (
    SafeAuthorizationPolicyError,
)


@dataclass(frozen=True, slots=True)
class SafeAuthorizationPolicy:
    """Immutable T18 authorization policy."""

    schema_version: str = "1.0"
    authority: str = "REOS_CONTROL_CENTER"
    allow_state_mutation: bool = False
    allow_execution_by_guard: bool = False
    allow_authority_promotion: bool = False
    allow_architecture_change: bool = False
    allow_self_approval: bool = False
    require_t17_analyze: bool = True
    reject_unknown_paths: bool = True
    reject_protected_impacts: bool = True
    require_human_approval_for_change: bool = True
    maximum_risk: OperatorRisk = OperatorRisk.MEDIUM

    def validate(self) -> bool:
        if self.schema_version != "1.0":
            raise SafeAuthorizationPolicyError(
                "Unsupported T18 policy schema version."
            )

        if self.authority != "REOS_CONTROL_CENTER":
            raise SafeAuthorizationPolicyError(
                "T18 authority must remain REOS_CONTROL_CENTER."
            )

        if self.allow_state_mutation:
            raise SafeAuthorizationPolicyError(
                "T18 cannot mutate authoritative state."
            )

        if self.allow_execution_by_guard:
            raise SafeAuthorizationPolicyError(
                "T18 guard cannot execute operations."
            )

        if self.allow_authority_promotion:
            raise SafeAuthorizationPolicyError(
                "T18 cannot promote authority."
            )

        if self.allow_architecture_change:
            raise SafeAuthorizationPolicyError(
                "T18 cannot change architecture."
            )

        if self.allow_self_approval:
            raise SafeAuthorizationPolicyError(
                "T18 cannot self-approve."
            )

        if not isinstance(
            self.maximum_risk,
            OperatorRisk,
        ):
            raise SafeAuthorizationPolicyError(
                "maximum_risk must be an OperatorRisk."
            )

        return True

    def permits(
        self,
        action_type: OperatorActionType,
        risk: OperatorRisk,
    ) -> bool:
        self.validate()

        if not isinstance(
            action_type,
            OperatorActionType,
        ):
            raise SafeAuthorizationPolicyError(
                "Invalid operator action type."
            )

        if not isinstance(
            risk,
            OperatorRisk,
        ):
            raise SafeAuthorizationPolicyError(
                "Invalid operator risk."
            )

        if action_type is not OperatorActionType.PROPOSE_CHANGE:
            return False

        risk_order = {
            OperatorRisk.LOW: 0,
            OperatorRisk.MEDIUM: 1,
            OperatorRisk.HIGH: 2,
            OperatorRisk.CRITICAL: 3,
        }

        return (
            risk_order[risk]
            <= risk_order[self.maximum_risk]
        )


__all__ = [
    "SafeAuthorizationPolicy",
]
