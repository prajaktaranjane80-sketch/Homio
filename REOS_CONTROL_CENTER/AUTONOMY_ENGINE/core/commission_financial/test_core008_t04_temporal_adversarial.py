
from __future__ import annotations

from datetime import timedelta

import pytest

from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationRequest,
)
from .commission_settlement import CommissionSettlementState
from .commission_settlement_lifecycle import (
    CommissionSettlementLifecycleValidationError,
)
from .financial_domain import MonetaryAmount
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    ACTOR,
    RECONCILIATION_AUTH,
    _evidence,
    _lifecycle,
    _submit,
)


def _capture_record(record):
    return (
        record.settlement.immutable_fingerprint,
        record.lifecycle_events,
        record.settlement_history.entries,
        record.reconciliation_history.entries,
    )


def _assert_record_unchanged(lifecycle, record, snapshot, at):
    assert record.settlement.state is CommissionSettlementState.SUBMITTED
    assert record.settlement.immutable_fingerprint == snapshot[0]
    assert record.lifecycle_events == snapshot[1]
    assert record.settlement_history.entries == snapshot[2]
    assert record.reconciliation_history.entries == snapshot[3]
    assert lifecycle.verify(record, at=at)


def _reconcile_with_times(
    lifecycle,
    record,
    evidence,
    *,
    reconciled_at,
    at,
):
    return lifecycle.reconcile(
        record,
        evidence,
        reconciliation_id="reconciliation-temporal-001",
        reconciliation_version=1,
        reconciliation_reference="reconciliation-temporal-reference-001",
        provenance_reference="reconciliation-temporal-provenance-001",
        actor_reference=ACTOR,
        authorization_reference=RECONCILIATION_AUTH,
        reconciled_at=reconciled_at,
        at=at,
        variance_tolerance=MonetaryAmount.zero(
            record.settlement.amount.currency
        ),
    )


def _reconciliation_request_count(requests):
    return sum(
        request.action is FinancialAuthorizationAction.RECONCILE
        for request in requests
    )


def test_external_evidence_cannot_predate_settlement_request() -> None:
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)

    evidence = _evidence(
        submitted,
        observed_at=NOW + timedelta(hours=2),
    )
    snapshot = _capture_record(submitted)
    validation_time = NOW + timedelta(hours=8)

    with pytest.raises(
        CommissionSettlementLifecycleValidationError,
        match="External settlement evidence cannot precede "
        "the settlement request",
    ):
        _reconcile_with_times(
            lifecycle,
            submitted,
            evidence,
            reconciled_at=NOW + timedelta(hours=8),
            at=validation_time,
        )

    _assert_record_unchanged(
        lifecycle,
        submitted,
        snapshot,
        validation_time,
    )


def test_reconciliation_cannot_predate_external_evidence() -> None:
    requests: list[FinancialAuthorizationRequest] = []
    lifecycle = _lifecycle(authorization_requests=requests)
    submitted = _submit(lifecycle)

    evidence = _evidence(
        submitted,
        observed_at=NOW + timedelta(hours=7),
    )
    snapshot = _capture_record(submitted)
    validation_time = NOW + timedelta(hours=8)
    requests_before = _reconciliation_request_count(requests)

    with pytest.raises(
        CommissionSettlementLifecycleValidationError,
        match="Reconciliation cannot predate the external evidence",
    ):
        _reconcile_with_times(
            lifecycle,
            submitted,
            evidence,
            reconciled_at=NOW + timedelta(hours=6),
            at=validation_time,
        )

    assert _reconciliation_request_count(requests) == requests_before
    _assert_record_unchanged(
        lifecycle,
        submitted,
        snapshot,
        validation_time,
    )


def test_external_evidence_cannot_be_observed_after_validation_time() -> None:
    requests: list[FinancialAuthorizationRequest] = []
    lifecycle = _lifecycle(authorization_requests=requests)
    submitted = _submit(lifecycle)

    evidence = _evidence(
        submitted,
        observed_at=NOW + timedelta(hours=9),
    )
    snapshot = _capture_record(submitted)
    validation_time = NOW + timedelta(hours=8)
    requests_before = _reconciliation_request_count(requests)

    with pytest.raises(
        CommissionSettlementLifecycleValidationError,
        match="External evidence cannot be observed after validation time",
    ):
        _reconcile_with_times(
            lifecycle,
            submitted,
            evidence,
            reconciled_at=NOW + timedelta(hours=9),
            at=validation_time,
        )

    assert _reconciliation_request_count(requests) == requests_before
    _assert_record_unchanged(
        lifecycle,
        submitted,
        snapshot,
        validation_time,
    )


def test_reconciliation_cannot_occur_after_validation_time() -> None:
    requests: list[FinancialAuthorizationRequest] = []
    lifecycle = _lifecycle(authorization_requests=requests)
    submitted = _submit(lifecycle)

    evidence = _evidence(
        submitted,
        observed_at=NOW + timedelta(hours=7),
    )
    snapshot = _capture_record(submitted)
    validation_time = NOW + timedelta(hours=8)
    requests_before = _reconciliation_request_count(requests)

    with pytest.raises(
        CommissionSettlementLifecycleValidationError,
        match="Reconciliation cannot occur after validation time",
    ):
        _reconcile_with_times(
            lifecycle,
            submitted,
            evidence,
            reconciled_at=NOW + timedelta(hours=9),
            at=validation_time,
        )

    assert _reconciliation_request_count(requests) == requests_before
    _assert_record_unchanged(
        lifecycle,
        submitted,
        snapshot,
        validation_time,
    )
