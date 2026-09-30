"""CORE-007 Point 12 — governance event regression."""

from __future__ import annotations

from uuid import uuid4

import pytest

from .governance_event_contract import (
    GovernanceEventScopeError,
    GovernanceEventType,
    build_fraud_signal_event,
    build_trust_signal_event,
)


def _trust_payload():
    return {
        "signal_id": "signal-1",
        "subject_id": "subject-1",
        "signal_type": "BEHAVIORAL",
        "signal_source": "CORE-003",
        "signal_version": 1,
        "provenance": "provenance-1",
        "evidence_reference": "evidence-1",
    }


def test_trust_signal_event_contract():
    event = build_trust_signal_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload=_trust_payload(),
    )

    assert (
        event.event_type
        is GovernanceEventType.TRUST_SIGNAL
    )

    assert (
        event.contract_key
        == (
            "REOS.CORE007.GovernanceEvent:"
            "1:CORE007.TRUST_SIGNAL"
        )
    )


def test_missing_required_event_field_is_rejected():
    payload = _trust_payload()
    del payload["evidence_reference"]

    with pytest.raises(ValueError):
        build_trust_signal_event(
            tenant_id=uuid4(),
            producer_id=uuid4(),
            correlation_id=uuid4(),
            payload=payload,
        )


def test_event_payload_tenant_cannot_cross_event_tenant():
    payload = _trust_payload()
    event_tenant = uuid4()
    payload["tenant_id"] = str(
        uuid4()
    )

    with pytest.raises(
        GovernanceEventScopeError
    ):
        build_trust_signal_event(
            tenant_id=event_tenant,
            producer_id=uuid4(),
            correlation_id=uuid4(),
            payload=payload,
        )


def test_fraud_signal_event_maps_to_core_002_envelope():
    event = build_fraud_signal_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "fraud_signal_id": "fraud-1",
            "subject_id": "subject-1",
            "detection_rule_reference": "rule-1",
            "detection_input_provenance": (
                "provenance-1"
            ),
            "detection_state": "REVIEW",
            "confidence": 90,
        },
    )

    envelope = event.to_event_envelope()

    assert (
        envelope.event_type
        == "CORE007.FRAUD_SIGNAL"
    )

    assert (
        envelope.schema_name
        == "REOS.CORE007.GovernanceEvent"
    )

    assert envelope.idempotency_key == (
        event.payload_fingerprint
    )


def test_event_payload_is_immutable():
    event = build_trust_signal_event(
        tenant_id=uuid4(),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload=_trust_payload(),
    )

    with pytest.raises(
        TypeError
    ):
        event.payload["new"] = "value"
