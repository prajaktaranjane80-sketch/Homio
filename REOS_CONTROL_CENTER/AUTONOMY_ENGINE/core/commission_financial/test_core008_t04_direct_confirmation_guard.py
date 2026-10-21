from __future__ import annotations

from datetime import timedelta

import pytest

from .commission_settlement import CommissionSettlementState
from .commission_settlement_lifecycle import (
    CommissionSettlementTransitionError,
)
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    ACTOR,
    _lifecycle,
    _submit,
)


def test_submitted_settlement_cannot_be_confirmed_by_direct_transition():
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)

    assert (
        submitted.settlement.state
        is CommissionSettlementState.SUBMITTED
    )

    original_fingerprint = (
        submitted.settlement.immutable_fingerprint
    )
    original_events = submitted.lifecycle_events
    original_settlement_history = (
        submitted.settlement_history.entries
    )
    original_reconciliation_history = (
        submitted.reconciliation_history.entries
    )

    verification_time = NOW + timedelta(hours=7)

    with pytest.raises(
        CommissionSettlementTransitionError,
        match="only by a MATCHED reconciliation",
    ):
        lifecycle.transition(
            submitted,
            target_state=CommissionSettlementState.CONFIRMED,
            expected_settlement_version=(
                submitted.settlement.settlement_version
            ),
            expected_settlement_fingerprint=(
                submitted.settlement.immutable_fingerprint
            ),
            actor_reference=ACTOR,
            at=verification_time,
        )

    # A rejected direct confirmation must not mutate the input record.
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
        submitted.settlement_history.entries
        == original_settlement_history
    )
    assert (
        submitted.reconciliation_history.entries
        == original_reconciliation_history
    )

    assert lifecycle.verify(
        submitted,
        at=verification_time,
    )
