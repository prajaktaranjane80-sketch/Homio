from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from .commission_adjustment import (
    CommissionAdjustment,
    CommissionAdjustmentState,
    CommissionAdjustmentType,
    CommissionAdjustmentValidationError,
)
from .commission_dispute import (
    CommissionDispute,
    CommissionDisputeResolution,
    CommissionDisputeState,
    CommissionDisputeType,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationError,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
)
from .commission_settlement import CommissionSettlementState
from .financial_domain import MonetaryAmount
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    _create,
    _evidence,
    _lifecycle,
    _reconcile,
    _submit,
)


def _matched_result():
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)
    evidence = _evidence(submitted)

    return _reconcile(
        lifecycle,
        submitted,
        evidence,
    )


def _new_dispute(
    result,
    *,
    resolve: bool = True,
):
    settlement = result.settlement_record.settlement
    disputed_amount = MonetaryAmount.create(
        Decimal("0.01"),
        settlement.amount.currency,
    )

    dispute = CommissionDispute.open_from_settlement(
        settlement,
        dispute_id="dispute-reversal-001",
        claimant_reference="broker-001",
        dispute_type=CommissionDisputeType.AMOUNT,
        reason_code="APPROVED_PARTIAL_REVERSAL",
        description="Documented partial reversal.",
        evidence_reference="dispute-evidence-001",
        authorization_reference="dispute-opening-auth-001",
        provenance_reference="dispute-provenance-001",
        opened_at=NOW + timedelta(hours=9),
        disputed_amount=disputed_amount,
        reconciliation=result.reconciliation,
    )

    if not resolve:
        return dispute

    return dispute.resolve(
        resolution=CommissionDisputeResolution.PARTIALLY_ACCEPTED,
        resolution_reference="dispute-resolution-001",
        state=CommissionDisputeState.RESOLVED,
    )


def _new_reversal_adjustment(
    result,
    *,
    dispute: CommissionDispute | None = None,
    amount_value: Decimal = Decimal("0.01"),
    reconciliation=None,
):
    settlement = result.settlement_record.settlement
    resolved_dispute = (
        _new_dispute(result)
        if dispute is None
        else dispute
    )

    amount = MonetaryAmount.create(
        amount_value,
        settlement.amount.currency,
    )

    selected_reconciliation = (
        result.reconciliation
        if reconciliation is None
        else reconciliation
    )

    return CommissionAdjustment.create_from_dispute(
        resolved_dispute,
        settlement,
        adjustment_id="adjustment-reversal-001",
        adjustment_type=CommissionAdjustmentType.REVERSAL,
        amount=amount,
        reason_code="APPROVED_PARTIAL_REVERSAL",
        authorization_reference="adjustment-proposal-auth-001",
        provenance_reference="adjustment-provenance-001",
        evidence_reference="adjustment-evidence-001",
        effective_at=NOW + timedelta(hours=10),
        reconciliation=selected_reconciliation,
    )


def _approval_boundary(
    adjustment: CommissionAdjustment,
    *,
    actor_reference: str,
    authorization_reference: str,
    operation: str,
    allowed: bool = True,
):
    requests: list[FinancialAuthorizationRequest] = []

    def verify(request: FinancialAuthorizationRequest) -> bool:
        requests.append(request)
        context = request.context or {}

        return (
            allowed
            and request.action is FinancialAuthorizationAction.ADJUST
            and request.tenant_id == request.resource_tenant_id
            and request.actor_reference == actor_reference
            and request.resource_reference == adjustment.adjustment_id
            and request.authorization_reference == authorization_reference
            and context.get("operation") == operation
            and context.get("adjustment_id") == adjustment.adjustment_id
            and context.get("adjustment_fingerprint")
            == adjustment.immutable_fingerprint
            and context.get("adjustment_type")
            == adjustment.adjustment_type.value
            and context.get("amount") == adjustment.amount.to_dict()
            and context.get("dispute_id") == adjustment.dispute_id
            and context.get("settlement_id") == adjustment.settlement_id
            and context.get("reconciliation_id")
            == adjustment.reconciliation_id
        )

    return FinancialSecurityBoundary(verify), requests


def test_settlement_uses_authoritative_allocation_as_its_source():
    record = _create(_lifecycle())
    settlement = record.settlement
    allocation = record.allocation
    payload = settlement.to_dict()

    assert payload["source_of_truth"] == (
        "CORE-008.COMMISSION_SETTLEMENT"
    )
    assert settlement.commission_id == allocation.commission_id
    assert settlement.tenant_id == allocation.tenant_id
    assert settlement.allocation_set_id == allocation.allocation_set_id
    assert settlement.amount.currency.identity_key == (
        allocation.total_amount.currency.identity_key
    )
    assert settlement.amount.amount <= allocation.total_amount.amount
    assert settlement.immutable_fingerprint


def test_reversal_cannot_be_created_from_an_unresolved_dispute():
    result = _matched_result()
    open_dispute = _new_dispute(result, resolve=False)

    with pytest.raises(
        CommissionAdjustmentValidationError,
        match="resolved, accepted dispute",
    ):
        _new_reversal_adjustment(
            result,
            dispute=open_dispute,
        )


def test_reversal_requires_a_matching_settlement_reconciliation():
    result = _matched_result()
    altered_reconciliation = replace(
        result.reconciliation,
        settlement_id="different-settlement",
    )

    with pytest.raises(
        CommissionAdjustmentValidationError,
        match="does not reference settlement",
    ):
        _new_reversal_adjustment(
            result,
            reconciliation=altered_reconciliation,
        )


def test_adjustment_amount_cannot_exceed_disputed_amount():
    result = _matched_result()

    with pytest.raises(
        CommissionAdjustmentValidationError,
        match="cannot exceed disputed amount",
    ):
        _new_reversal_adjustment(
            result,
            amount_value=Decimal("0.02"),
        )


def test_denied_reversal_approval_does_not_mutate_proposal():
    result = _matched_result()
    proposal = _new_reversal_adjustment(result)
    original_fingerprint = proposal.immutable_fingerprint
    original_payload = proposal.to_dict()

    boundary = FinancialSecurityBoundary(
        lambda request: False
    )

    with pytest.raises(FinancialAuthorizationError):
        proposal.approve(
            authorization_boundary=boundary,
            actor_reference="finance-approver-001",
            authorization_reference="reversal-approval-denied",
            approved_at=NOW + timedelta(hours=11),
        )

    assert proposal.state is CommissionAdjustmentState.PROPOSED
    assert proposal.immutable_fingerprint == original_fingerprint
    assert proposal.to_dict() == original_payload


def test_approved_reversal_records_bound_authorization_and_source_fingerprint():
    result = _matched_result()
    proposal = _new_reversal_adjustment(result)
    original_fingerprint = proposal.immutable_fingerprint

    boundary, requests = _approval_boundary(
        proposal,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        operation="APPROVE_ADJUSTMENT",
    )

    approved = proposal.approve(
        authorization_boundary=boundary,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        approved_at=NOW + timedelta(hours=11),
    )

    assert len(requests) == 1
    assert requests[0].action is FinancialAuthorizationAction.ADJUST
    assert requests[0].tenant_id == proposal.tenant_id
    assert requests[0].resource_tenant_id == proposal.tenant_id
    assert requests[0].resource_reference == proposal.adjustment_id
    assert requests[0].context["adjustment_fingerprint"] == (
        original_fingerprint
    )

    assert proposal.state is CommissionAdjustmentState.PROPOSED
    assert proposal.immutable_fingerprint == original_fingerprint
    assert approved.state is CommissionAdjustmentState.APPROVED
    assert approved.adjustment_version == proposal.adjustment_version + 1
    assert approved.metadata["approval_source_fingerprint"] == (
        original_fingerprint
    )
    assert approved.metadata["approved_actor_reference"] == (
        "finance-approver-001"
    )
    assert approved.metadata["approval_authorization_reference"] == (
        "reversal-approval-auth-001"
    )
    assert approved.immutable_fingerprint != original_fingerprint


def test_application_reauthorizes_and_chains_the_approved_fingerprint():
    result = _matched_result()
    proposal = _new_reversal_adjustment(result)

    approval_boundary, _ = _approval_boundary(
        proposal,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        operation="APPROVE_ADJUSTMENT",
    )

    approved = proposal.approve(
        authorization_boundary=approval_boundary,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        approved_at=NOW + timedelta(hours=11),
    )

    approved_fingerprint = approved.immutable_fingerprint

    application_boundary, requests = _approval_boundary(
        approved,
        actor_reference="finance-operator-002",
        authorization_reference="reversal-application-auth-001",
        operation="APPLY_ADJUSTMENT",
    )

    applied = approved.mark_applied(
        authorization_boundary=application_boundary,
        actor_reference="finance-operator-002",
        authorization_reference="reversal-application-auth-001",
        applied_at=NOW + timedelta(hours=12),
    )

    assert len(requests) == 1
    assert requests[0].context["approval_authorization_reference"] == (
        "reversal-approval-auth-001"
    )
    assert requests[0].context["approval_source_fingerprint"] == (
        proposal.immutable_fingerprint
    )

    assert proposal.state is CommissionAdjustmentState.PROPOSED
    assert approved.state is CommissionAdjustmentState.APPROVED
    assert applied.state is CommissionAdjustmentState.APPLIED
    assert applied.adjustment_version == approved.adjustment_version + 1
    assert applied.metadata["approval_source_fingerprint"] == (
        proposal.immutable_fingerprint
    )
    assert applied.metadata["application_source_fingerprint"] == (
        approved_fingerprint
    )
    assert applied.metadata["application_authorization_reference"] == (
        "reversal-application-auth-001"
    )
    assert applied.metadata["applied_actor_reference"] == (
        "finance-operator-002"
    )
    assert applied.immutable_fingerprint != approved_fingerprint


def test_reversal_cannot_be_applied_before_approval_time():
    result = _matched_result()
    proposal = _new_reversal_adjustment(result)

    approval_boundary, _ = _approval_boundary(
        proposal,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        operation="APPROVE_ADJUSTMENT",
    )

    approved = proposal.approve(
        authorization_boundary=approval_boundary,
        actor_reference="finance-approver-001",
        authorization_reference="reversal-approval-auth-001",
        approved_at=NOW + timedelta(hours=11),
    )

    application_requests: list[FinancialAuthorizationRequest] = []
    application_boundary = FinancialSecurityBoundary(
        lambda request: (
            application_requests.append(request) is None
        )
    )

    with pytest.raises(
        CommissionAdjustmentValidationError,
        match="before approval",
    ):
        approved.mark_applied(
            authorization_boundary=application_boundary,
            actor_reference="finance-operator-002",
            authorization_reference="reversal-application-auth-001",
            applied_at=NOW + timedelta(hours=10),
        )

    assert not application_requests
    assert approved.state is CommissionAdjustmentState.APPROVED
