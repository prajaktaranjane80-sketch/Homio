"""
ACRL T15 — Operator Registry.

Registry of bounded operator capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .operator_policy import (
    OperatorActionType,
    OperatorRisk,
)


class OperatorRegistryError(ValueError):
    """Registry validation error."""


@dataclass(frozen=True)
class OperatorCapability:
    """Immutable capability definition."""

    action_type: OperatorActionType
    minimum_risk: OperatorRisk
    execution_allowed: bool
    state_mutation_allowed: bool
    external_authorization_required: bool


class OperatorCapabilityRegistry:
    """Canonical bounded T15 capabilities."""

    VERSION = "T15-REGISTRY-1.0"

    _CAPABILITIES = {
        OperatorActionType.OBSERVE: OperatorCapability(
            action_type=OperatorActionType.OBSERVE,
            minimum_risk=OperatorRisk.LOW,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
        OperatorActionType.VERIFY: OperatorCapability(
            action_type=OperatorActionType.VERIFY,
            minimum_risk=OperatorRisk.LOW,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
        OperatorActionType.ANALYZE: OperatorCapability(
            action_type=OperatorActionType.ANALYZE,
            minimum_risk=OperatorRisk.LOW,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
        OperatorActionType.TEST: OperatorCapability(
            action_type=OperatorActionType.TEST,
            minimum_risk=OperatorRisk.LOW,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
        OperatorActionType.PROPOSE_CHANGE: OperatorCapability(
            action_type=OperatorActionType.PROPOSE_CHANGE,
            minimum_risk=OperatorRisk.MEDIUM,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
        OperatorActionType.REQUEST_HUMAN_DECISION: OperatorCapability(
            action_type=OperatorActionType.REQUEST_HUMAN_DECISION,
            minimum_risk=OperatorRisk.MEDIUM,
            execution_allowed=False,
            state_mutation_allowed=False,
            external_authorization_required=True,
        ),
    }

    @classmethod
    def get(
        cls,
        action_type: OperatorActionType,
    ) -> OperatorCapability:
        try:
            return cls._CAPABILITIES[action_type]
        except KeyError as exc:
            raise OperatorRegistryError(
                "Unknown T15 operator capability."
            ) from exc

    @classmethod
    def contains(
        cls,
        action_type: OperatorActionType,
    ) -> bool:
        return action_type in cls._CAPABILITIES

    @classmethod
    def all(
        cls,
    ) -> tuple[OperatorCapability, ...]:
        return tuple(cls._CAPABILITIES.values())


__all__ = [
    "OperatorCapability",
    "OperatorCapabilityRegistry",
    "OperatorRegistryError",
]
