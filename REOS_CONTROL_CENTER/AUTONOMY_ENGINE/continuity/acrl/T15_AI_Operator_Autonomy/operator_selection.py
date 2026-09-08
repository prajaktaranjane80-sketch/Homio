"""
ACRL T15 — Operator Selection.

Selects only from the registered bounded capability set.
"""

from __future__ import annotations

from .operator_policy import (
    OperatorActionType,
    OperatorRisk,
)
from .operator_registry import (
    OperatorCapability,
    OperatorCapabilityRegistry,
)


class OperatorSelectionEngine:
    """Deterministic action selection helper."""

    @classmethod
    def select(
        cls,
        action_type: OperatorActionType,
    ) -> tuple[OperatorCapability, OperatorRisk]:
        capability = OperatorCapabilityRegistry.get(
            action_type
        )

        if capability.minimum_risk is OperatorRisk.CRITICAL:
            raise ValueError(
                "T15 registry must never expose a critical "
                "autonomous capability."
            )

        return capability, capability.minimum_risk


__all__ = [
    "OperatorSelectionEngine",
]
