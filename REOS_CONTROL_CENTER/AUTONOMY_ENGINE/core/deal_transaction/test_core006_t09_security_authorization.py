from __future__ import annotations

import pytest

from .deal import Deal, DealStatus
from .deal_security import (
    DealAuthorizationContext,
    DealAuthorizationDecision,
    DealOperation,
    SENSITIVE_APPROVALS,
    authorize_deal_operation,
)


AT = "2026-09-29T06:00:00+00:00"


def make_deal() -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        deal_id="deal-001",
        at=AT,
    )


def authorized_context(
    operation: DealOperation,
    *,
    tenant_id: str = "tenant-001",
    subject_id: str = "user-001",
    approvals: frozenset[str] | None = None,
    permissions: frozenset[str] | None = None,
) -> DealAuthorizationContext:
    approval_set = (
        approvals
        if approvals is not None
        else frozenset()
    )

    permission_set = (
        permissions
        if permissions is not None
        else frozenset({operation.value})
    )

    return DealAuthorizationContext(
        subject_id=subject_id,
        tenant_id=tenant_id,
        permissions=permission_set,
        approvals=approval_set,
    )


def move_to(
    deal: Deal,
    *states: DealStatus,
) -> Deal:
    current = deal

    for state in states:
        current = current.transition(
            state,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    return current


@pytest.mark.parametrize(
    "operation",
    tuple(DealOperation),
)
def test_every_operation_is_default_deny(
    operation: DealOperation,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
        ),
        operation,
    )

    assert decision.allowed is False
    assert decision.operation is operation
    assert decision.required_permission == operation.value


@pytest.mark.parametrize(
    "operation",
    tuple(DealOperation),
)
def test_every_operation_requires_its_exact_permission(
    operation: DealOperation,
) -> None:
    other_permissions = frozenset(
        item.value
        for item in DealOperation
        if item is not operation
    )

    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
            permissions=other_permissions,
        ),
        operation,
    )

    assert decision.allowed is False
    assert decision.required_permission == operation.value


@pytest.mark.parametrize(
    "operation",
    tuple(DealOperation),
)
def test_wildcard_permission_cannot_escalate(
    operation: DealOperation,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
            permissions=frozenset({"*"}),
        ),
        operation,
    )

    assert decision.allowed is False
    assert decision.required_permission == operation.value


def test_cross_tenant_is_denied_even_with_permission() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.TRANSITION,
            tenant_id="tenant-999",
        ),
        DealOperation.TRANSITION,
    )

    assert decision.allowed is False
    assert "Tenant mismatch" in decision.reason


def test_cross_tenant_is_denied_even_with_high_risk_approval() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.BOOK,
            tenant_id="tenant-999",
            approvals=frozenset(
                {"APPROVAL_DEAL_BOOKING"}
            ),
        ),
        DealOperation.BOOK,
    )

    assert decision.allowed is False
    assert "Tenant mismatch" in decision.reason


@pytest.mark.parametrize(
    "subject_id",
    (
        "",
        " ",
        "   ",
    ),
)
def test_blank_subject_is_denied(
    subject_id: str,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.READ,
            subject_id=subject_id,
        ),
        DealOperation.READ,
    )

    assert decision.allowed is False
    assert "Authenticated subject is required" in decision.reason


def test_non_string_subject_is_denied() -> None:
    context = DealAuthorizationContext(
        subject_id=123,  # type: ignore[arg-type]
        tenant_id="tenant-001",
        permissions=frozenset(
            {"DEAL_READ"}
        ),
    )

    decision = authorize_deal_operation(
        make_deal(),
        context,
        DealOperation.READ,
    )

    assert decision.allowed is False
    assert "Authenticated subject is required" in decision.reason


@pytest.mark.parametrize(
    ("operation", "approval"),
    tuple(
        (
            operation,
            approval,
        )
        for operation, approval
        in SENSITIVE_APPROVALS.items()
    ),
)
def test_high_risk_operation_requires_explicit_approval(
    operation: DealOperation,
    approval: str,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(operation),
        operation,
    )

    assert decision.allowed is False
    assert decision.required_approval == approval
    assert "high-risk approval" in decision.reason


@pytest.mark.parametrize(
    ("operation", "approval"),
    tuple(
        (
            operation,
            approval,
        )
        for operation, approval
        in SENSITIVE_APPROVALS.items()
    ),
)
def test_wrong_approval_does_not_authorize_sensitive_operation(
    operation: DealOperation,
    approval: str,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            operation,
            approvals=frozenset(
                {"WRONG_APPROVAL"}
            ),
        ),
        operation,
    )

    assert decision.allowed is False
    assert decision.required_approval == approval


@pytest.mark.parametrize(
    ("operation", "approval"),
    tuple(
        (
            operation,
            approval,
        )
        for operation, approval
        in SENSITIVE_APPROVALS.items()
    ),
)
def test_approval_without_permission_does_not_authorize(
    operation: DealOperation,
    approval: str,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
            approvals=frozenset({approval}),
        ),
        operation,
    )

    assert decision.allowed is False
    assert decision.required_permission == operation.value


def test_booking_requires_booking_pending_state() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.BOOK,
            approvals=frozenset(
                {"APPROVAL_DEAL_BOOKING"}
            ),
        ),
        DealOperation.BOOK,
    )

    assert decision.allowed is False
    assert "BOOKING_PENDING" in decision.reason


def test_booking_allowed_only_after_booking_pending() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.BOOKING_PENDING,
    )

    decision = authorize_deal_operation(
        deal,
        authorized_context(
            DealOperation.BOOK,
            approvals=frozenset(
                {"APPROVAL_DEAL_BOOKING"}
            ),
        ),
        DealOperation.BOOK,
    )

    assert decision.allowed is True
    assert decision.required_permission == "DEAL_BOOK"


def test_completion_requires_completion_pending_state() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.COMPLETE,
            approvals=frozenset(
                {"APPROVAL_DEAL_COMPLETION"}
            ),
        ),
        DealOperation.COMPLETE,
    )

    assert decision.allowed is False
    assert "COMPLETION_PENDING" in decision.reason


def test_completion_allowed_only_after_completion_pending() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
    )

    decision = authorize_deal_operation(
        deal,
        authorized_context(
            DealOperation.COMPLETE,
            approvals=frozenset(
                {"APPROVAL_DEAL_COMPLETION"}
            ),
        ),
        DealOperation.COMPLETE,
    )

    assert decision.allowed is True
    assert decision.required_permission == "DEAL_COMPLETE"


@pytest.mark.parametrize(
    "operation",
    (
        DealOperation.READ,
        DealOperation.TRANSITION,
        DealOperation.PARTY,
        DealOperation.OFFER,
        DealOperation.NEGOTIATE,
        DealOperation.CANCEL,
        DealOperation.ATTACH_EVIDENCE,
    ),
)
def test_non_sensitive_operations_need_no_approval(
    operation: DealOperation,
) -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(operation),
        operation,
    )

    assert decision.allowed is True
    assert decision.required_approval is None


def test_authorization_accepts_enum_value_string() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.READ,
        ),
        "DEAL_READ",
    )

    assert decision.allowed is True
    assert decision.operation is DealOperation.READ


def test_invalid_operation_is_rejected() -> None:
    with pytest.raises(ValueError):
        authorize_deal_operation(
            make_deal(),
            authorized_context(
                DealOperation.READ,
            ),
            "DEAL_UNKNOWN",  # type: ignore[arg-type]
        )


def test_attributes_do_not_grant_privilege() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
            attributes={
                "is_admin": True,
                "role": "SUPER_ADMIN",
            },
        ),
        DealOperation.COMPLETE,
    )

    assert decision.allowed is False
    assert decision.required_permission == "DEAL_COMPLETE"


def test_extra_permissions_do_not_bypass_approval() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
            permissions=frozenset(
                {
                    "DEAL_BOOK",
                    "DEAL_COMPLETE",
                    "DEAL_ADMIN",
                }
            ),
        ),
        DealOperation.COMPLETE,
    )

    assert decision.allowed is False
    assert decision.required_approval == (
        "APPROVAL_DEAL_COMPLETION"
    )


def test_decision_is_immutable() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        authorized_context(
            DealOperation.READ,
        ),
        DealOperation.READ,
    )

    assert isinstance(
        decision,
        DealAuthorizationDecision,
    )

    with pytest.raises(Exception):
        decision.allowed = False  # type: ignore[misc]


def test_authorization_does_not_mutate_deal() -> None:
    deal = make_deal()
    before = deal.to_dict()

    decision = authorize_deal_operation(
        deal,
        authorized_context(
            DealOperation.READ,
        ),
        DealOperation.READ,
    )

    after = deal.to_dict()

    assert decision.allowed is True
    assert before == after


def test_required_permission_is_operation_derived() -> None:
    for operation in DealOperation:
        decision = authorize_deal_operation(
            make_deal(),
            DealAuthorizationContext(
                subject_id="user-001",
                tenant_id="tenant-001",
                permissions=frozenset(
                    {operation.value}
                ),
                approvals=frozenset(
                    {
                        SENSITIVE_APPROVALS.get(
                            operation,
                            "",
                        )
                    }
                    if operation in SENSITIVE_APPROVALS
                    else set()
                ),
            ),
            operation,
        )

        if operation is DealOperation.BOOK:
            assert decision.allowed is False
            assert "BOOKING_PENDING" in decision.reason
            continue

        if operation is DealOperation.COMPLETE:
            assert decision.allowed is False
            assert "COMPLETION_PENDING" in decision.reason
            continue

        assert decision.required_permission == operation.value


def test_tenant_boundary_has_priority_over_permission_checks() -> None:
    decision = authorize_deal_operation(
        make_deal(),
        DealAuthorizationContext(
            subject_id="",
            tenant_id="tenant-999",
            permissions=frozenset(
                {"DEAL_READ"}
            ),
        ),
        DealOperation.READ,
    )

    assert decision.allowed is False
    assert "Tenant mismatch" in decision.reason


def test_authorization_context_uses_frozen_permission_and_approval_sets() -> None:
    context = DealAuthorizationContext(
        subject_id="user-001",
        tenant_id="tenant-001",
        permissions=frozenset(
            {"DEAL_READ"}
        ),
        approvals=frozenset(),
    )

    assert isinstance(
        context.permissions,
        frozenset,
    )
    assert isinstance(
        context.approvals,
        frozenset,
    )