
from __future__ import annotations

from datetime import timedelta

import pytest

from .commission_security import FinancialAuthorizationRequest
from .commission_settlement import CommissionSettlementState
from .commission_settlement_lifecycle import (
    CommissionSettlementConcurrencyError,
)
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    ACTOR,
    _create,
    _lifecycle,
    _transition,
)


def test_stale_settlement_version_is_rejected_when_fingerprint_is_current():
    """A stale version must fail even when the supplied fingerprint matches."""

    authorization_requests: list[FinancialAuthorizationRequest] = []
    lifecycle = _lifecycle(
        authorization_requests=authorization_requests,
    )

    created = _create(lifecycle)

    pending = _transition(
        lifecycle,
        created,
        CommissionSettlementState.AUTHORIZATION_PENDING,
        at=NOW + timedelta(hours=4),
    )

    current_fingerprint = pending.settlement.immutable_fingerprint
    original_events = pending.lifecycle_events
    original_settlement_history = pending.settlement_history.entries
    original_reconciliation_history = (
        pending.reconciliation_history.entries
    )

    assert pending.settlement.state is (
        CommissionSettlementState.AUTHORIZATION_PENDING
    )
    assert authorization_requests == []

    with pytest.raises(
        CommissionSettlementConcurrencyError,
        match="Expected settlement version is stale",
    ):
        lifecycle.transition(
            pending,
            target_state=CommissionSettlementState.AUTHORIZED,
            expected_settlement_version=(
                pending.settlement.settlement_version + 1
            ),
            expected_settlement_fingerprint=current_fingerprint,
            actor_reference=ACTOR,
            at=NOW + timedelta(hours=5),
        )

    # A rejected stale-version request must not authorize or mutate anything.
    assert authorization_requests == []
    assert pending.settlement.state is (
        CommissionSettlementState.AUTHORIZATION_PENDING
    )
    assert pending.settlement.immutable_fingerprint == current_fingerprint
    assert pending.lifecycle_events == original_events
    assert (
        pending.settlement_history.entries
        == original_settlement_history
    )
    assert (
        pending.reconciliation_history.entries
        == original_reconciliation_history
    )

    assert lifecycle.verify(
        pending,
        at=NOW + timedelta(hours=5),
    )
