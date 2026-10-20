from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from .commission_reconciliation import (
    CommissionExternalSettlementEvidence,
    CommissionReconciliationState,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationError,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
)
from .commission_settlement import CommissionSettlementState
from .commission_settlement_integrity import (
    CommissionSettlementIntegrityError,
)
from .commission_settlement_lifecycle import (
    CommissionSettlementConcurrencyError,
    CommissionSettlementEvidenceError,
    CommissionSettlementLifecycle,
    CommissionSettlementLifecycleValidationError,
    CommissionSettlementTransitionError,
)
from .financial_domain import MonetaryAmount
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t03_allocation_participants import _build_fixture


ACTOR = "finance-operator-001"
SETTLEMENT_AUTH = "settlement-auth-001"
RECONCILIATION_AUTH = "reconciliation-auth-001"
EXTERNAL_REFERENCE = "provider-settlement-001"


def _allocation():
    return _build_fixture()[-1]


def _lifecycle(
    *,
    authorization_allowed: bool = True,
    evidence_allowed: bool = True,
) -> CommissionSettlementLifecycle:
    def verify_authorization(
        request: FinancialAuthorizationRequest,
    ) -> bool:
        return (
            authorization_allowed
            and request.tenant_id == request.resource_tenant_id
            and request.actor_reference == ACTOR
            and request.authorization_reference
            in {SETTLEMENT_AUTH, RECONCILIATION_AUTH}
            and request.action
            in {
                FinancialAuthorizationAction.SETTLE,
                FinancialAuthorizationAction.RECONCILE,
            }
        )

    def verify_evidence(
        evidence: CommissionExternalSettlementEvidence,
        settlement,
    ) -> bool:
        return (
            evidence_allowed
            and evidence.status_code == "SETTLED"
            and bool(evidence.provider_reference)
            and evidence.external_reference
            == settlement.external_reference
            and evidence.tenant_id == settlement.tenant_id
        )

    return CommissionSettlementLifecycle(
        security_boundary=FinancialSecurityBoundary(
            verify_authorization
        ),
        evidence_verifier=verify_evidence,
    )


def _create(lifecycle: CommissionSettlementLifecycle):
    return lifecycle.create_settlement(
        _allocation(),
        settlement_id="settlement-001",
        settlement_version=1,
        authorization_reference=SETTLEMENT_AUTH,
        provenance_reference="settlement-provenance-001",
        actor_reference=ACTOR,
        requested_at=NOW + timedelta(hours=3),
    )


def _transition(
    lifecycle: CommissionSettlementLifecycle,
    record,
    destination: CommissionSettlementState,
    *,
    at,
    **kwargs,
):
    return lifecycle.transition(
        record,
        target_state=destination,
        expected_settlement_version=(
            record.settlement.settlement_version
        ),
        expected_settlement_fingerprint=(
            record.settlement.immutable_fingerprint
        ),
        actor_reference=ACTOR,
        at=at,
        **kwargs,
    )


def _submit(lifecycle: CommissionSettlementLifecycle):
    record = _create(lifecycle)

    record = _transition(
        lifecycle,
        record,
        CommissionSettlementState.AUTHORIZATION_PENDING,
        at=NOW + timedelta(hours=4),
    )

    record = _transition(
        lifecycle,
        record,
        CommissionSettlementState.AUTHORIZED,
        at=NOW + timedelta(hours=5),
    )

    record = _transition(
        lifecycle,
        record,
        CommissionSettlementState.SUBMITTED,
        external_reference=EXTERNAL_REFERENCE,
        at=NOW + timedelta(hours=6),
    )

    return record


def _evidence(
    record,
    *,
    evidence_id: str = "external-evidence-001",
    observed_amount: MonetaryAmount | None = None,
    observed_at=None,
    status_code: str = "SETTLED",
    source_version: int = 1,
    external_reference: str = EXTERNAL_REFERENCE,
):
    if observed_amount is None:
        observed_amount = record.settlement.amount

    if observed_at is None:
        observed_at = NOW + timedelta(hours=7)

    return CommissionExternalSettlementEvidence(
        evidence_id=evidence_id,
        tenant_id=record.settlement.tenant_id,
        external_reference=external_reference,
        provider_reference=f"provider-transaction-{source_version:03d}",
        observed_amount=observed_amount,
        observed_at=observed_at,
        status_code=status_code,
        source_version=source_version,
    )


def _reconcile(
    lifecycle: CommissionSettlementLifecycle,
    record,
    evidence: CommissionExternalSettlementEvidence,
    *,
    version: int = 1,
    at=None,
):
    if at is None:
        at = NOW + timedelta(hours=8)

    return lifecycle.reconcile(
        record,
        evidence,
        reconciliation_id="reconciliation-001",
        reconciliation_version=version,
        reconciliation_reference="reconciliation-reference-001",
        provenance_reference=f"reconciliation-provenance-{version:03d}",
        actor_reference=ACTOR,
        authorization_reference=RECONCILIATION_AUTH,
        reconciled_at=at,
        at=at,
        variance_tolerance=MonetaryAmount.zero(
            record.settlement.amount.currency
        ),
    )


def test_settlement_requires_authorization_before_submission() -> None:
    lifecycle = _lifecycle()
    record = _create(lifecycle)

    assert record.settlement.state is CommissionSettlementState.READY
    assert record.settlement_history.latest is not None
    assert record.settlement_history.latest.state == "READY"

    with pytest.raises(CommissionSettlementTransitionError):
        _transition(
            lifecycle,
            record,
            CommissionSettlementState.SUBMITTED,
            external_reference=EXTERNAL_REFERENCE,
            at=NOW + timedelta(hours=4),
        )

    pending = _transition(
        lifecycle,
        record,
        CommissionSettlementState.AUTHORIZATION_PENDING,
        at=NOW + timedelta(hours=4),
    )

    assert (
        pending.settlement.state
        is CommissionSettlementState.AUTHORIZATION_PENDING
    )


def test_denied_authorization_does_not_advance_settlement() -> None:
    lifecycle = _lifecycle(authorization_allowed=False)
    record = _create(lifecycle)

    pending = _transition(
        lifecycle,
        record,
        CommissionSettlementState.AUTHORIZATION_PENDING,
        at=NOW + timedelta(hours=4),
    )

    before_fingerprint = pending.settlement.immutable_fingerprint
    before_event_count = len(pending.lifecycle_events)

    with pytest.raises(FinancialAuthorizationError):
        _transition(
            lifecycle,
            pending,
            CommissionSettlementState.AUTHORIZED,
            at=NOW + timedelta(hours=5),
        )

    assert (
        pending.settlement.state
        is CommissionSettlementState.AUTHORIZATION_PENDING
    )
    assert pending.settlement.immutable_fingerprint == before_fingerprint
    assert len(pending.lifecycle_events) == before_event_count


def test_stale_fingerprint_is_rejected() -> None:
    lifecycle = _lifecycle()
    created = _create(lifecycle)

    pending = _transition(
        lifecycle,
        created,
        CommissionSettlementState.AUTHORIZATION_PENDING,
        at=NOW + timedelta(hours=4),
    )

    with pytest.raises(CommissionSettlementConcurrencyError):
        lifecycle.transition(
            pending,
            CommissionSettlementState.AUTHORIZED,
            expected_settlement_version=created.settlement.settlement_version,
            expected_settlement_fingerprint=(
                created.settlement.immutable_fingerprint
            ),
            actor_reference=ACTOR,
            at=NOW + timedelta(hours=5),
        )


def test_only_matching_reconciliation_confirms_settlement() -> None:
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)
    evidence = _evidence(submitted)

    result = _reconcile(lifecycle, submitted, evidence)

    assert (
        result.reconciliation.state
        is CommissionReconciliationState.MATCHED
    )
    assert (
        result.settlement_record.settlement.state
        is CommissionSettlementState.CONFIRMED
    )
    assert result.reconciliation_snapshot.verify()
    assert lifecycle.verify(
        result.settlement_record,
        at=NOW + timedelta(hours=8),
    )

    history = result.settlement_record.settlement_history
    assert history.latest is not None
    assert history.latest.state == "CONFIRMED"

    events = result.settlement_record.lifecycle_events
    assert events[-1].event_type == "RECONCILIATION_MATCHED"
    assert events[-1].from_state == "SUBMITTED"
    assert events[-1].to_state == "CONFIRMED"
    assert events[-1].previous_event_fingerprint == (
        events[-2].event_fingerprint
    )


def test_variance_stays_submitted_and_can_be_reconciled_again() -> None:
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)

    short_amount = MonetaryAmount.create(
        submitted.settlement.amount.amount - Decimal("0.01"),
        submitted.settlement.amount.currency,
    )
    short_evidence = _evidence(
        submitted,
        evidence_id="external-evidence-001",
        observed_amount=short_amount,
        observed_at=NOW + timedelta(hours=7),
        source_version=1,
    )

    first = _reconcile(
        lifecycle,
        submitted,
        short_evidence,
        version=1,
        at=NOW + timedelta(hours=8),
    )

    assert (
        first.reconciliation.state
        is CommissionReconciliationState.VARIANCE
    )
    assert (
        first.settlement_record.settlement.state
        is CommissionSettlementState.SUBMITTED
    )
    assert len(
        first.settlement_record.reconciliation_history.entries
    ) == 1

    corrected_evidence = _evidence(
        first.settlement_record,
        evidence_id="external-evidence-002",
        observed_amount=first.settlement_record.settlement.amount,
        observed_at=NOW + timedelta(hours=9),
        source_version=2,
    )

    second = _reconcile(
        lifecycle,
        first.settlement_record,
        corrected_evidence,
        version=2,
        at=NOW + timedelta(hours=10),
    )

    assert (
        second.reconciliation.state
        is CommissionReconciliationState.MATCHED
    )
    assert (
        second.settlement_record.settlement.state
        is CommissionSettlementState.CONFIRMED
    )
    assert len(
        second.settlement_record.reconciliation_history.entries
    ) == 2
    assert (
        second.settlement_record.reconciliation_history.latest
        .reconciliation_version
        == 2
    )


def test_unverified_external_evidence_cannot_confirm_settlement() -> None:
    lifecycle = _lifecycle(evidence_allowed=False)
    submitted = _submit(lifecycle)
    evidence = _evidence(
        submitted,
        status_code="PENDING",
    )

    before_fingerprint = submitted.settlement.immutable_fingerprint
    before_event_count = len(submitted.lifecycle_events)

    with pytest.raises(CommissionSettlementEvidenceError):
        _reconcile(lifecycle, submitted, evidence)

    assert submitted.settlement.state is CommissionSettlementState.SUBMITTED
    assert submitted.settlement.immutable_fingerprint == before_fingerprint
    assert len(submitted.lifecycle_events) == before_event_count


def test_wrong_external_reference_is_rejected() -> None:
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)
    evidence = _evidence(
        submitted,
        external_reference="different-provider-settlement",
    )

    with pytest.raises(CommissionSettlementEvidenceError):
        _reconcile(lifecycle, submitted, evidence)


def test_tampered_snapshot_fails_closed() -> None:
    lifecycle = _lifecycle()
    record = _create(lifecycle)

    # Snapshots are checked on every lifecycle command.
    record.snapshot.canonical_payload["state"] = "TAMPERED"

    with pytest.raises(CommissionSettlementIntegrityError):
        lifecycle.verify(
            record,
            at=NOW + timedelta(hours=4),
        )
