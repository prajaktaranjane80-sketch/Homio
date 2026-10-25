from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from .commission_release import (
    CommissionRelease,
    CommissionReleaseCheck,
    CommissionReleaseState,
    CommissionReleaseValidationError,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationError,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
)
from .financial_domain import FinancialTenantScopeError
from .test_core008_t07_financial_reporting import _statement


UTC = timezone.utc
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)


def _pending_release(
    *,
    checks: tuple[CommissionReleaseCheck, ...] | None = None,
) -> CommissionRelease:
    selected_checks = checks or (
        CommissionReleaseCheck(
            code="STATEMENT_READY",
            passed=True,
            description="Statement prerequisites passed.",
            reference="statement-001",
        ),
        CommissionReleaseCheck(
            code="CLOSEOUT_READY",
            passed=True,
            description="Financial closeout is complete.",
            reference="closeout-001",
        ),
    )

    return CommissionRelease(
        release_id="release-001",
        tenant_id="tenant-a",
        commission_id="commission-001",
        release_version=1,
        statement_id="statement-001",
        closeout_id="closeout-001",
        invoice_ids=("invoice-001",),
        settlement_ids=("settlement-001",),
        reconciliation_ids=("reconciliation-001",),
        tax_assessment_ids=("tax-001",),
        checks=selected_checks,
        authorization_reference=None,
        provenance_reference="release-provenance-001",
        evaluated_at=NOW,
        released_at=None,
        state=CommissionReleaseState.AUTHORIZATION_PENDING,
        metadata={"review_scope": "CORE-008-T09"},
    )


def test_evaluate_cannot_release_from_reference_alone() -> None:
    with pytest.raises(
        CommissionReleaseValidationError,
        match="evaluate cannot authorize a release from a reference alone",
    ):
        CommissionRelease.evaluate(
            statement=_statement(),
            closeout=None,
            invoices=(),
            settlements=(),
            reconciliations=(),
            tax_assessments=(),
            evaluated_at=NOW,
            provenance_reference="release-provenance-001",
            authorization_reference="unverified-approval-reference",
        )


def test_direct_released_state_requires_authorization_audit_metadata() -> None:
    pending = _pending_release()

    with pytest.raises(
        CommissionReleaseValidationError,
        match="Only authorize_release\\(\\) can construct a RELEASED record",
    ):
        replace(
            pending,
            authorization_reference="unverified-approval-reference",
            released_at=NOW,
            state=CommissionReleaseState.RELEASED,
        )


def test_denied_release_authorization_does_not_mutate_pending_record() -> None:
    pending = _pending_release()
    before_fingerprint = pending.immutable_fingerprint
    before_payload = pending.to_dict()

    boundary = FinancialSecurityBoundary(lambda _request: False)

    with pytest.raises(FinancialAuthorizationError):
        pending.authorize_release(
            authorization_boundary=boundary,
            actor_reference="finance-operator-001",
            authorization_reference="release-approval-denied",
            authorized_at=NOW + timedelta(minutes=5),
        )

    assert pending.state is CommissionReleaseState.AUTHORIZATION_PENDING
    assert pending.immutable_fingerprint == before_fingerprint
    assert pending.to_dict() == before_payload


def test_fabricated_authorization_metadata_cannot_construct_released_record() -> None:
    pending = _pending_release()
    forged_metadata = dict(pending.metadata)
    forged_metadata.update(
        {
            "release_authorization_source_fingerprint": "a" * 64,
            "release_authorized_actor_reference": "forged-approver",
            "release_authorization_operation": "AUTHORIZE_COMMISSION_RELEASE",
            "release_authorized_at": (NOW + timedelta(minutes=5)).isoformat(),
            "release_authorization_reference": "forged-approval-reference",
        }
    )

    with pytest.raises(
        CommissionReleaseValidationError,
        match="Only authorize_release\\(\\) can construct a RELEASED record",
    ):
        replace(
            pending,
            authorization_reference="forged-approval-reference",
            released_at=NOW + timedelta(minutes=5),
            state=CommissionReleaseState.RELEASED,
            metadata=forged_metadata,
        )


def test_release_authorization_binds_actor_action_tenant_and_fingerprint() -> None:
    pending = _pending_release()
    source_fingerprint = pending.immutable_fingerprint
    requests: list[FinancialAuthorizationRequest] = []

    def verify(request: FinancialAuthorizationRequest) -> bool:
        requests.append(request)
        context = request.context or {}

        return (
            request.action is FinancialAuthorizationAction.RELEASE
            and request.tenant_id == "tenant-a"
            and request.resource_tenant_id == "tenant-a"
            and request.actor_reference == "finance-approver-001"
            and request.resource_reference == "release-001"
            and request.authorization_reference == "release-approval-001"
            and request.sensitive is True
            and context.get("operation") == "AUTHORIZE_COMMISSION_RELEASE"
            and context.get("release_id") == "release-001"
            and context.get("release_version") == 1
            and context.get("release_fingerprint") == source_fingerprint
            and context.get("statement_id") == "statement-001"
            and context.get("closeout_id") == "closeout-001"
        )

    boundary = FinancialSecurityBoundary(verify)

    released = pending.authorize_release(
        authorization_boundary=boundary,
        actor_reference="finance-approver-001",
        authorization_reference="release-approval-001",
        authorized_at=NOW + timedelta(minutes=5),
    )

    assert len(requests) == 1
    assert requests[0].action is FinancialAuthorizationAction.RELEASE
    assert requests[0].context is not None
    assert requests[0].context["release_fingerprint"] == source_fingerprint

    assert pending.state is CommissionReleaseState.AUTHORIZATION_PENDING
    assert pending.immutable_fingerprint == source_fingerprint

    assert released.state is CommissionReleaseState.RELEASED
    assert released.release_version == pending.release_version + 1
    assert released.authorization_reference == "release-approval-001"
    assert released.released_at == NOW + timedelta(minutes=5)
    assert (
        released.metadata["release_authorization_source_fingerprint"]
        == source_fingerprint
    )
    assert (
        released.metadata["release_authorized_actor_reference"]
        == "finance-approver-001"
    )
    assert (
        released.metadata["release_authorization_operation"]
        == "AUTHORIZE_COMMISSION_RELEASE"
    )
    assert (
        released.metadata["release_authorization_reference"]
        == "release-approval-001"
    )
    assert released.immutable_fingerprint != source_fingerprint


def test_release_cannot_be_authorized_when_any_check_fails() -> None:
    pending = _pending_release(
        checks=(
            CommissionReleaseCheck(
                code="CLOSEOUT_READY",
                passed=False,
                description="Closeout is not complete.",
                reference="closeout-001",
            ),
        )
    )
    requests: list[FinancialAuthorizationRequest] = []
    boundary = FinancialSecurityBoundary(
        lambda request: (requests.append(request) is None)
    )

    with pytest.raises(
        CommissionReleaseValidationError,
        match="All release checks must pass",
    ):
        pending.authorize_release(
            authorization_boundary=boundary,
            actor_reference="finance-approver-001",
            authorization_reference="release-approval-002",
            authorized_at=NOW + timedelta(minutes=5),
        )

    assert requests == []
    assert pending.state is CommissionReleaseState.AUTHORIZATION_PENDING


def test_release_authorization_cannot_predate_readiness_evaluation() -> None:
    pending = _pending_release()
    requests: list[FinancialAuthorizationRequest] = []
    boundary = FinancialSecurityBoundary(
        lambda request: (requests.append(request) is None)
    )

    with pytest.raises(
        CommissionReleaseValidationError,
        match="authorized_at cannot precede evaluated_at",
    ):
        pending.authorize_release(
            authorization_boundary=boundary,
            actor_reference="finance-approver-001",
            authorization_reference="release-approval-003",
            authorized_at=NOW - timedelta(seconds=1),
        )

    assert requests == []
    assert pending.state is CommissionReleaseState.AUTHORIZATION_PENDING


def test_release_tenant_scope_is_enforced() -> None:
    pending = _pending_release()

    with pytest.raises(
        FinancialTenantScopeError,
        match="crossed tenant scope",
    ):
        pending.assert_tenant("tenant-b")
