from __future__ import annotations

from uuid import UUID

import pytest

from ..event_platform.event_contract import (
    EventContract,
    EventContractRegistry,
    UnsupportedEventVersionError,
)
from ..event_platform.event_domain import (
    EventEnvelope,
    EventTenantViolation,
)
from .commission_event_contract import (
    CORE008_EVENT_SCHEMA,
    CORE008_EVENT_SCHEMA_VERSION,
    CORE008_EVENT_VERSION,
    COMMISSION_EVENT_DEFINITIONS,
    CommissionEventType,
)
from .commission_event_integration import (
    CommissionEventIntegration,
    build_core008_event_registry,
)
from .commission_event_validation import (
    CommissionFinancialEventValidationError,
    validate_financial_event,
)


TENANT_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)

PRODUCER_ID = UUID(
    "00000000-0000-0000-0000-000000000002"
)


@pytest.fixture
def integration() -> CommissionEventIntegration:
    return CommissionEventIntegration()


def _payload(
    event_type: CommissionEventType,
) -> dict:
    base = {
        "commission_id": "commission-001",
    }

    if event_type is CommissionEventType.COMMISSION_CREATED:
        base.update(
            {
                "contract_id": "contract-001",
                "deal_id": "deal-001",
            }
        )

    elif event_type is CommissionEventType.ENTITLEMENT_ESTABLISHED:
        base.update(
            {
                "entitlement_id": "entitlement-001",
                "party_id": "broker-001",
            }
        )

    elif event_type is CommissionEventType.COMMISSION_CALCULATED:
        base.update(
            {
                "calculation_id": "calculation-001",
                "calculation_version": 1,
                "commission_amount": {
                    "amount": "25000.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
            }
        )

    elif event_type is CommissionEventType.COMMISSION_ADJUSTED:
        base.update(
            {
                "adjustment_id": "adjustment-001",
                "adjustment_amount": {
                    "amount": "500.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
                "reason_code": "CORRECTION",
            }
        )

    elif event_type is CommissionEventType.SETTLEMENT_CREATED:
        base.update(
            {
                "settlement_id": "settlement-001",
                "settlement_reference": "settlement-ref-001",
                "amount": {
                    "amount": "24500.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
            }
        )

    elif event_type is CommissionEventType.SETTLEMENT_COMPLETED:
        base.update(
            {
                "settlement_id": "settlement-001",
                "settlement_reference": "settlement-ref-001",
                "amount": {
                    "amount": "24500.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
            }
        )

    elif (
        event_type
        is CommissionEventType.RECONCILIATION_DISCREPANCY
    ):
        base.update(
            {
                "reconciliation_id": "reconciliation-001",
                "settlement_id": "settlement-001",
                "expected_amount": {
                    "amount": "24500.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
                "observed_amount": {
                    "amount": "24000.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
                "variance_amount": {
                    "amount": "-500.00",
                    "currency": {
                        "code": "INR",
                        "minor_unit": 2,
                    },
                },
                "discrepancy_state": "VARIANCE",
            }
        )

    return base


@pytest.mark.parametrize(
    "event_type",
    list(CommissionEventType),
)
def test_all_required_financial_events_are_contract_valid(
    integration: CommissionEventIntegration,
    event_type: CommissionEventType,
) -> None:
    event = integration.create_event(
        event_type=event_type,
        tenant_id=TENANT_ID,
        producer_id=PRODUCER_ID,
        tenant_reference="tenant-a",
        source_id=f"{event_type.value}-001",
        source_fingerprint=f"{event_type.value}-fingerprint",
        payload=_payload(event_type),
    )

    validate_financial_event(
        event,
        tenant_id=TENANT_ID,
        expected_type=event_type,
    )


def test_core008_registry_contains_exact_required_event_set() -> None:
    registry = build_core008_event_registry()

    assert isinstance(
        registry,
        EventContractRegistry,
    )

    assert {
        definition.event_type
        for definition in COMMISSION_EVENT_DEFINITIONS
    } == set(CommissionEventType)

    for definition in COMMISSION_EVENT_DEFINITIONS:
        contract = registry.resolve(
            schema_name=CORE008_EVENT_SCHEMA,
            event_type=definition.event_type.value,
            schema_version=CORE008_EVENT_SCHEMA_VERSION,
            event_version=CORE008_EVENT_VERSION,
        )

        assert isinstance(
            contract,
            EventContract,
        )


def test_unknown_financial_event_version_is_rejected(
    integration: CommissionEventIntegration,
) -> None:
    event = EventEnvelope.create(
        event_type=CommissionEventType.COMMISSION_CREATED.value,
        schema_name=CORE008_EVENT_SCHEMA,
        schema_version=CORE008_EVENT_SCHEMA_VERSION,
        event_version=99,
        tenant_id=TENANT_ID,
        producer_id=PRODUCER_ID,
        payload={
            "commission_id": "commission-001",
            "contract_id": "contract-001",
            "deal_id": "deal-001",
        },
    )

    with pytest.raises(
        UnsupportedEventVersionError
    ):
        integration.validate_event(event)


def test_cross_tenant_event_validation_is_rejected(
    integration: CommissionEventIntegration,
) -> None:
    event = integration.create_event(
        event_type=CommissionEventType.COMMISSION_CREATED,
        tenant_id=TENANT_ID,
        producer_id=PRODUCER_ID,
        tenant_reference="tenant-a",
        source_id="commission-001",
        source_fingerprint="fingerprint-001",
        payload=_payload(
            CommissionEventType.COMMISSION_CREATED
        ),
    )

    with pytest.raises(
        CommissionFinancialEventValidationError
    ):
        validate_financial_event(
            event,
            tenant_id=UUID(
                "00000000-0000-0000-0000-000000000009"
            ),
        )


def test_core002_itself_rejects_cross_tenant_assertion(
    integration: CommissionEventIntegration,
) -> None:
    event = integration.create_event(
        event_type=CommissionEventType.COMMISSION_CREATED,
        tenant_id=TENANT_ID,
        producer_id=PRODUCER_ID,
        tenant_reference="tenant-a",
        source_id="commission-001",
        source_fingerprint="fingerprint-001",
        payload=_payload(
            CommissionEventType.COMMISSION_CREATED
        ),
    )

    with pytest.raises(
        EventTenantViolation
    ):
        event.assert_tenant(
            UUID(
                "00000000-0000-0000-0000-000000000009"
            )
        )
