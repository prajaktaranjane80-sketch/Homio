"""
ACRL T15 — Operator Integration Boundary.

Defines the read-only handoff object produced by T15.
It does not execute or authorize the proposed operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .operator_autonomy import OperatorReport


class OperatorIntegrationError(ValueError):
    """T15 integration boundary error."""


@dataclass(frozen=True)
class OperatorHandoff:
    """Immutable proposal handoff to an external authority."""

    schema_version: str
    authority: str
    request_fingerprint: str
    decision: str
    action_type: str | None
    description: str | None
    risk: str
    requires_authorization: bool
    execution_authorized: bool
    state_mutated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "request_fingerprint": self.request_fingerprint,
            "decision": self.decision,
            "action_type": self.action_type,
            "description": self.description,
            "risk": self.risk,
            "requires_authorization": self.requires_authorization,
            "execution_authorized": self.execution_authorized,
            "state_mutated": self.state_mutated,
        }


class OperatorIntegrationEngine:
    """Builds a safe external handoff from a T15 report."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def build_handoff(
        cls,
        report: OperatorReport,
    ) -> OperatorHandoff:
        if not isinstance(report, OperatorReport):
            raise OperatorIntegrationError(
                "Invalid OperatorReport."
            )

        if report.execution_authorized:
            raise OperatorIntegrationError(
                "T15 cannot hand off an execution-authorized result."
            )

        if report.state_mutated:
            raise OperatorIntegrationError(
                "T15 cannot hand off a state-mutating result."
            )

        proposal = report.proposal

        return OperatorHandoff(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            request_fingerprint=report.request_fingerprint,
            decision=report.decision.value,
            action_type=(
                proposal.action_type.value
                if proposal is not None
                else None
            ),
            description=(
                proposal.description
                if proposal is not None
                else None
            ),
            risk=report.risk.value,
            requires_authorization=(
                proposal.requires_authorization
                if proposal is not None
                else True
            ),
            execution_authorized=False,
            state_mutated=False,
        )


__all__ = [
    "OperatorHandoff",
    "OperatorIntegrationEngine",
    "OperatorIntegrationError",
]
