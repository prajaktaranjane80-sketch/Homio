"""
ACRL T15 — AI Operator Autonomy Policy.

Defines the immutable policy boundary for autonomous operator
decision-making.

T15 may reason about and propose bounded actions.

T15 must never:
    - mutate authoritative state,
    - execute repository/business operations,
    - bypass REOS_CONTROL_CENTER authority,
    - authorize unrestricted execution,
    - invent architecture,
    - approve its own proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperatorPolicyError(ValueError):
    """Raised when T15 policy constraints are violated."""


class OperatorDecision(str, Enum):
    """Canonical T15 operator decisions."""

    PROPOSE = "PROPOSE"
    BLOCK = "BLOCK"
    FAIL_CLOSED = "FAIL_CLOSED"


class OperatorRisk(str, Enum):
    """Canonical operator risk levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OperatorActionType(str, Enum):
    """Bounded non-executing operator action categories."""

    OBSERVE = "OBSERVE"
    VERIFY = "VERIFY"
    ANALYZE = "ANALYZE"
    TEST = "TEST"
    PROPOSE_CHANGE = "PROPOSE_CHANGE"
    REQUEST_HUMAN_DECISION = "REQUEST_HUMAN_DECISION"


@dataclass(frozen=True)
class OperatorPolicy:
    """Immutable T15 policy configuration."""

    schema_version: str = "1.0"
    authority: str = "REOS_CONTROL_CENTER"
    allow_state_mutation: bool = False
    allow_execution: bool = False
    allow_authority_promotion: bool = False
    allow_architecture_change: bool = False
    allow_self_approval: bool = False
    allow_unbounded_actions: bool = False
    maximum_risk: OperatorRisk = OperatorRisk.MEDIUM

    def validate(self) -> bool:
        """Validate policy invariants."""

        if self.schema_version != "1.0":
            raise OperatorPolicyError(
                "Unsupported T15 policy schema version."
            )

        if self.authority != "REOS_CONTROL_CENTER":
            raise OperatorPolicyError(
                "T15 authority must remain REOS_CONTROL_CENTER."
            )

        if self.allow_state_mutation:
            raise OperatorPolicyError(
                "T15 cannot be permitted to mutate authoritative state."
            )

        if self.allow_execution:
            raise OperatorPolicyError(
                "T15 cannot be permitted to execute operations."
            )

        if self.allow_authority_promotion:
            raise OperatorPolicyError(
                "T15 cannot promote authority."
            )

        if self.allow_architecture_change:
            raise OperatorPolicyError(
                "T15 cannot directly change architecture."
            )

        if self.allow_self_approval:
            raise OperatorPolicyError(
                "T15 cannot self-approve proposals."
            )

        if self.allow_unbounded_actions:
            raise OperatorPolicyError(
                "T15 cannot issue unbounded actions."
            )

        if not isinstance(
            self.maximum_risk,
            OperatorRisk,
        ):
            raise OperatorPolicyError(
                "maximum_risk must be an OperatorRisk."
            )

        return True

    def permits(
        self,
        action_type: OperatorActionType,
        risk: OperatorRisk,
    ) -> bool:
        """Return True only for policy-permitted bounded proposals."""

        if not isinstance(
            action_type,
            OperatorActionType,
        ):
            raise OperatorPolicyError(
                "Invalid operator action type."
            )

        if not isinstance(
            risk,
            OperatorRisk,
        ):
            raise OperatorPolicyError(
                "Invalid operator risk."
            )

        self.validate()

        risk_order = {
            OperatorRisk.LOW: 0,
            OperatorRisk.MEDIUM: 1,
            OperatorRisk.HIGH: 2,
            OperatorRisk.CRITICAL: 3,
        }

        return (
            action_type is not OperatorActionType.PROPOSE_CHANGE
            or risk_order[risk]
            <= risk_order[self.maximum_risk]
        )
