from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class DealOperation(str, Enum):
    READ = "DEAL_READ"
    TRANSITION = "DEAL_TRANSITION"
    PARTY = "DEAL_PARTY"
    OFFER = "DEAL_OFFER"
    NEGOTIATE = "DEAL_NEGOTIATE"
    BOOK = "DEAL_BOOK"
    AGREEMENT = "DEAL_AGREEMENT"
    REGISTRATION = "DEAL_REGISTRATION"
    COMPLETE = "DEAL_COMPLETE"
    CANCEL = "DEAL_CANCEL"
    DISPUTE = "DEAL_DISPUTE"
    ATTACH_EVIDENCE = "DEAL_EVIDENCE_ATTACH"


@dataclass(frozen=True)
class DealAuthorizationContext:
    subject_id: str
    tenant_id: str
    permissions: frozenset[str] = frozenset()
    approvals: frozenset[str] = frozenset()
    attributes: Mapping[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class DealAuthorizationDecision:
    allowed: bool
    operation: DealOperation
    reason: str
    required_permission: str
    required_approval: str | None = None


SENSITIVE_APPROVALS = {
    DealOperation.BOOK: "APPROVAL_DEAL_BOOKING",
    DealOperation.AGREEMENT: "APPROVAL_DEAL_AGREEMENT",
    DealOperation.REGISTRATION: "APPROVAL_DEAL_REGISTRATION",
    DealOperation.COMPLETE: "APPROVAL_DEAL_COMPLETION",
    DealOperation.DISPUTE: "APPROVAL_DEAL_DISPUTE",
}

STATE_REQUIREMENTS = {
    DealOperation.BOOK: "BOOKING_PENDING",
    DealOperation.COMPLETE: "COMPLETION_PENDING",
}


def authorize_deal_operation(
    deal: Any,
    context: DealAuthorizationContext,
    operation: DealOperation,
) -> DealAuthorizationDecision:
    operation = DealOperation(operation)
    permission = operation.value

    if context.tenant_id != deal.tenant_id:
        return DealAuthorizationDecision(
            False,
            operation,
            "Tenant mismatch; authorization denied.",
            permission,
        )

    if not isinstance(
        context.subject_id,
        str,
    ) or not context.subject_id.strip():
        return DealAuthorizationDecision(
            False,
            operation,
            "Authenticated subject is required.",
            permission,
        )

    if permission not in context.permissions:
        return DealAuthorizationDecision(
            False,
            operation,
            "Required permission is absent.",
            permission,
        )

    approval = SENSITIVE_APPROVALS.get(operation)

    if (
        approval is not None
        and approval not in context.approvals
    ):
        return DealAuthorizationDecision(
            False,
            operation,
            "Required high-risk approval is absent.",
            permission,
            approval,
        )

    expected_state = STATE_REQUIREMENTS.get(operation)

    current_state = getattr(
        deal.status,
        "value",
        deal.status,
    )

    if (
        expected_state is not None
        and current_state != expected_state
    ):
        return DealAuthorizationDecision(
            False,
            operation,
            (
                f"Operation requires state "
                f"{expected_state}."
            ),
            permission,
            approval,
        )

    return DealAuthorizationDecision(
        True,
        operation,
        "Explicit authorization requirements satisfied.",
        permission,
        approval,
    )
