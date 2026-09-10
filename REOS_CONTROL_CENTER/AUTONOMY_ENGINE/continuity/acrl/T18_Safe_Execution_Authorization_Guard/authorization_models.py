from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..T15_AI_Operator_Autonomy.operator_policy import (
    OperatorActionType,
    OperatorRisk,
)
from ..T15_AI_Operator_Autonomy.operator_autonomy import (
    OperatorReport,
)
from ..T17_Change_Impact_Dependency_Analysis.impact_models import (
    ChangeImpactReport,
)

from .authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)


@dataclass(frozen=True, slots=True)
class HumanApproval:
    """Immutable explicit approval evidence."""

    approval_id: str
    authority: str
    approved: bool
    scope_fingerprint: str
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "authority": self.authority,
            "approved": self.approved,
            "scope_fingerprint": self.scope_fingerprint,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    """Immutable T18 authorization request."""

    operator_report: OperatorReport
    impact_report: ChangeImpactReport
    approval: HumanApproval | None
    nonce: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_report": self.operator_report.to_dict(),
            "impact_report": self.impact_report.to_dict(),
            "approval": (
                self.approval.to_dict()
                if self.approval is not None
                else None
            ),
            "nonce": self.nonce,
        }


@dataclass(frozen=True, slots=True)
class ExecutionAuthorization:
    """Immutable bounded authorization artifact."""

    schema_version: str
    decision: AuthorizationDecision
    reason: AuthorizationReason
    authorization_fingerprint: str
    request_fingerprint: str
    operator_request_fingerprint: str
    impact_fingerprint: str
    action_type: OperatorActionType | None
    risk: OperatorRisk | None
    execution_authorized: bool
    state_mutated: bool
    requires_external_executor: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "authorization_fingerprint": self.authorization_fingerprint,
            "request_fingerprint": self.request_fingerprint,
            "operator_request_fingerprint": self.operator_request_fingerprint,
            "impact_fingerprint": self.impact_fingerprint,
            "action_type": (
                self.action_type.value
                if self.action_type is not None
                else None
            ),
            "risk": (
                self.risk.value
                if self.risk is not None
                else None
            ),
            "execution_authorized": self.execution_authorized,
            "state_mutated": self.state_mutated,
            "requires_external_executor": self.requires_external_executor,
        }


__all__ = [
    "AuthorizationRequest",
    "ExecutionAuthorization",
    "HumanApproval",
]
