from __future__ import annotations

from datetime import timedelta

import pytest

from .commission_settlement import CommissionSettlementState
from .commission_settlement_lifecycle import (
    CommissionSettlementLifecycleValidationError,
)
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    _evidence,
    _lifecycle,
    _reconcile,
    _submit,
)


def test_external_evidence_cannot_predate_settlement_request() -> None:
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)

    # The settlement request was created at NOW + 3 hours.
    # This external observation deliberately predates that request.
    evidence = _evidence(
        submitted,
        observed_at=NOW + timedelta(hours=2),
    )

    original_fingerprint = (
        submitted.settlement.immutable_fingerprint
    )
    original_events = submitted.lifecycle_events
    original_reconciliation_history = (
        submitted.reconciliation_history.entries
    )

    with pytest.raises(
        CommissionSettlementLifecycleValidationError,
        match=(
            "External settlement evidence cannot precede "
            "the settlement request"
        ),
    ):
        _reconcile(
            lifecycle,
            submitted,
            evidence,
        )

    # A rejected reconciliation must not mutate the input record.
    assert (
        submitted.settlement.state
        is CommissionSettlementState.SUBMITTED
    )
    assert (
        submitted.settlement.immutable_fingerprint
        == original_fingerprint
    )
    assert submitted.lifecycle_events == original_events
    assert (
        submitted.reconciliation_history.entries
        == original_reconciliation_history
    )

    assert lifecycle.verify(
        submitted,
        at=NOW + timedelta(hours=8),
    )
