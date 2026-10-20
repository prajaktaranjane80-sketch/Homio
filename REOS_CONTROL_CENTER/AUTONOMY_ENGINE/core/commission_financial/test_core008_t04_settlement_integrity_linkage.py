from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from .commission_reconciliation_history import (
    CommissionReconciliationHistory,
)
from .commission_settlement_lifecycle import (
    CommissionSettlementIntegrityError,
)
from .test_core008_t02_attribution_binding import NOW
from .test_core008_t04_settlement_reconciliation_lifecycle import (
    _evidence,
    _lifecycle,
    _reconcile,
    _submit,
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

    # Corrupt a transition while rebuilding the hash chain so that
    # the test checks state continuity, not just a stale fingerprint.
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
