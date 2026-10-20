from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from .commission_reconciliation_history import (
    CommissionReconciliationHistory,
)
from .commission_settlement import CommissionSettlementState
from .commission_settlement_lifecycle import (
    CommissionSettlementIntegrityError,
)
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    _create,
    _evidence,
    _lifecycle,
    _reconcile,
    _submit,
    _transition,
)


def _confirmed_record():
    lifecycle = _lifecycle()
    submitted = _submit(lifecycle)
    evidence = _evidence(submitted)

    result = _reconcile(
        lifecycle,
        submitted,
        evidence,
    )

    return lifecycle, result.settlement_record


def _rechain(events):
    """Rebuild event fingerprints and predecessor links in sequence."""
    rebuilt = []
    previous_fingerprint = None

    for event in events:
        rebuilt_event = replace(
            event,
            previous_event_fingerprint=previous_fingerprint,
            event_fingerprint="",
        )
        rebuilt.append(rebuilt_event)
        previous_fingerprint = (
            rebuilt_event.event_fingerprint
        )

    return tuple(rebuilt)


def _verify(lifecycle, record):
    return lifecycle.verify(
        record,
        at=NOW + timedelta(hours=8),
    )


def test_confirmed_settlement_requires_reconciliation_history():
    lifecycle, record = _confirmed_record()

    record_without_reconciliation_history = replace(
        record,
        reconciliation_history=CommissionReconciliationHistory(),
    )

    with pytest.raises(CommissionSettlementIntegrityError):
        _verify(
            lifecycle,
            record_without_reconciliation_history,
        )


def test_matched_event_must_reference_exact_reconciliation_fingerprint():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[-1] = replace(
        events[-1],
        reconciliation_fingerprint="tampered-reconciliation-fingerprint",
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(CommissionSettlementIntegrityError):
        _verify(lifecycle, tampered_record)


def test_matched_event_evidence_fingerprint_must_match_history():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[-1] = replace(
        events[-1],
        evidence_fingerprint="tampered-evidence-fingerprint",
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(CommissionSettlementIntegrityError):
        _verify(lifecycle, tampered_record)


def test_lifecycle_event_settlement_fingerprint_must_exist_in_history():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[-1] = replace(
        events[-1],
        settlement_fingerprint="unknown-settlement-fingerprint",
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(CommissionSettlementIntegrityError):
        _verify(lifecycle, tampered_record)


def test_event_from_state_must_equal_previous_event_to_state():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[1] = replace(
        events[1],
        from_state="CANCELLED",
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="state continuity",
    ):
        _verify(lifecycle, tampered_record)


def test_lifecycle_event_timestamps_must_not_move_backwards():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[-1] = replace(
        events[-1],
        occurred_at=(
            events[-2].occurred_at - timedelta(seconds=1)
        ),
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="timestamps move backwards",
    ):
        _verify(lifecycle, tampered_record)


def test_settlement_history_order_must_follow_lifecycle_events():
    lifecycle, record = _confirmed_record()
    entries = list(record.settlement_history.entries)
    assert len(entries) >= 5

    entries[1], entries[2] = entries[2], entries[1]
    reordered_history = replace(
        record.settlement_history,
        entries=tuple(entries),
    )

    tampered_record = replace(
        record,
        settlement_history=reordered_history,
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="history order",
    ):
        _verify(lifecycle, tampered_record)


def test_authorized_transition_requires_matching_authorization_reference():
    lifecycle, record = _confirmed_record()
    events = list(record.lifecycle_events)

    index = next(
        i
        for i, event in enumerate(events)
        if (
            event.event_type == "SETTLEMENT_STATE_TRANSITION"
            and event.to_state
            == CommissionSettlementState.AUTHORIZED.value
        )
    )

    events[index] = replace(
        events[index],
        authorization_reference=None,
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="authorization reference",
    ):
        _verify(lifecycle, tampered_record)


def test_cancelled_transition_requires_authorization_reference():
    lifecycle = _lifecycle()
    created = _create(lifecycle)

    cancelled = _transition(
        lifecycle,
        created,
        CommissionSettlementState.CANCELLED,
        at=NOW + timedelta(hours=4),
    )

    events = list(cancelled.lifecycle_events)
    events[-1] = replace(
        events[-1],
        authorization_reference=None,
        event_fingerprint="",
    )

    tampered_record = replace(
        cancelled,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="authorization reference",
    ):
        _verify(lifecycle, tampered_record)


def test_reconciliation_event_requires_authorization_reference():
    lifecycle, record = _confirmed_record()

    events = list(record.lifecycle_events)
    events[-1] = replace(
        events[-1],
        authorization_reference=None,
        event_fingerprint="",
    )

    tampered_record = replace(
        record,
        lifecycle_events=_rechain(events),
    )

    with pytest.raises(
        CommissionSettlementIntegrityError,
        match="authorization reference",
    ):
        _verify(lifecycle, tampered_record)
