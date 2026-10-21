from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from .commission_reconciliation import (
    CommissionReconciliationState,
)
from .commission_reconciliation_history import (
    CommissionReconciliationHistoryError,
)
from .commission_settlement import (
    CommissionSettlementState,
)
from .financial_domain import MonetaryAmount
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    _evidence,
    _lifecycle,
    _reconcile,
    _submit,
)


def test_replayed_variance_reconciliation_is_rejected_without_corrupting_history():
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)

    short_amount = MonetaryAmount.create(
        submitted.settlement.amount.amount - Decimal("0.01"),
        submitted.settlement.amount.currency,
    )
    evidence = _evidence(
        submitted,
        observed_amount=short_amount,
        source_version=1,
    )

    first = _reconcile(
        lifecycle,
        submitted,
        evidence,
        version=1,
    )

    assert (
        first.reconciliation.state
        is CommissionReconciliationState.VARIANCE
    )
    assert (
        first.settlement_record.settlement.state
        is CommissionSettlementState.SUBMITTED
    )

    history_before = (
        first.settlement_record.reconciliation_history.entries
    )
    events_before = (
        first.settlement_record.lifecycle_events
    )

    assert len(history_before) == 1

    with pytest.raises(
        CommissionReconciliationHistoryError,
        match="Duplicate reconciliation fingerprint",
    ):
        _reconcile(
            lifecycle,
            first.settlement_record,
            evidence,
            version=1,
        )

    # The replay must not alter the original immutable record.
    assert (
        first.settlement_record.reconciliation_history.entries
        == history_before
    )
    assert (
        first.settlement_record.lifecycle_events
        == events_before
    )
    assert lifecycle.verify(
        first.settlement_record,
        at=NOW + timedelta(hours=8),
    )
