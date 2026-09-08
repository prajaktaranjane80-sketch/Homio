"""
ACRL T15 — Operator Decision Boundary.
"""

from __future__ import annotations

from .operator_policy import (
    OperatorDecision,
)
from .operator_validation import OperatorContext


class OperatorDecisionBoundary:
    """Hard T15 safety boundary."""

    @staticmethod
    def classify(
        context: OperatorContext,
    ) -> OperatorDecision:
        if not context.authority_valid:
            return OperatorDecision.FAIL_CLOSED

        if not context.integrity_valid:
            return OperatorDecision.FAIL_CLOSED

        if not context.architecture_stable:
            return OperatorDecision.FAIL_CLOSED

        if not context.state_available:
            return OperatorDecision.BLOCK

        if not context.state_valid:
            return OperatorDecision.FAIL_CLOSED

        if not context.evidence_available:
            return OperatorDecision.BLOCK

        return OperatorDecision.PROPOSE


__all__ = [
    "OperatorDecisionBoundary",
]
