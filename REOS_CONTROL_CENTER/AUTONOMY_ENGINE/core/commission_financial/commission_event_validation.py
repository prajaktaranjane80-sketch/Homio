from __future__ import annotations

from uuid import UUID

from ..event_platform.event_domain import (
    EventEnvelope,
    EventTenantViolation,
)

from .commission_event_contract import (
    CORE008_EVENT_SCHEMA,
    CORE008_EVENT_SCHEMA_VERSION,
    CORE008_EVENT_VERSION,
    CommissionEventType,
    get_event_definition,
)
from .commission_event_integration import (
    CommissionEventIntegration,
)


class CommissionFinancialEventValidationError(
    ValueError
):
    """Financial event validation failure."""


def validate_financial_event(
    event: EventEnvelope,
    *,
    tenant_id: UUID | None = None,
    expected_type: CommissionEventType | None = None,
) -> None:
    if not isinstance(
        event,
        EventEnvelope,
    ):
        raise CommissionFinancialEventValidationError(
            "event must be EventEnvelope"
        )

    if event.schema_name != CORE008_EVENT_SCHEMA:
        raise CommissionFinancialEventValidationError(
            "event does not belong to CORE-008"
        )

    if event.schema_version != CORE008_EVENT_SCHEMA_VERSION:
        raise CommissionFinancialEventValidationError(
            "unsupported CORE-008 schema version"
        )

    if event.event_version != CORE008_EVENT_VERSION:
        raise CommissionFinancialEventValidationError(
            "unsupported CORE-008 event version"
        )

    try:
        event_type = CommissionEventType(
            event.event_type
        )
    except ValueError as exc:
        raise CommissionFinancialEventValidationError(
            f"Unknown CORE-008 event type: {event.event_type}"
        ) from exc

    if expected_type is not None:
        if event_type is not expected_type:
            raise CommissionFinancialEventValidationError(
                "unexpected CORE-008 financial event type"
            )

    get_event_definition(event_type)

    if tenant_id is not None:
        try:
            event.assert_tenant(tenant_id)
        except EventTenantViolation as exc:
            raise CommissionFinancialEventValidationError(
                "financial event crossed tenant boundary"
            ) from exc

    commission_id = event.payload.get(
        "commission_id"
    )

    if not isinstance(
        commission_id,
        str,
    ) or not commission_id.strip():
        raise CommissionFinancialEventValidationError(
            "commission_id is required"
        )

    financial_source_id = event.payload.get(
        "financial_source_id"
    )

    financial_source_fingerprint = event.payload.get(
        "financial_source_fingerprint"
    )

    if not isinstance(
        financial_source_id,
        str,
    ) or not financial_source_id.strip():
        raise CommissionFinancialEventValidationError(
            "financial_source_id is required"
        )

    if not isinstance(
        financial_source_fingerprint,
        str,
    ) or not financial_source_fingerprint.strip():
        raise CommissionFinancialEventValidationError(
            "financial_source_fingerprint is required"
        )

    CommissionEventIntegration().validate_event(
        event
    )


def assert_financial_event(
    event: EventEnvelope,
    *,
    tenant_id: UUID | None = None,
    expected_type: CommissionEventType | None = None,
) -> EventEnvelope:
    validate_financial_event(
        event,
        tenant_id=tenant_id,
        expected_type=expected_type,
    )
    return event


__all__ = [
    "CommissionFinancialEventValidationError",
    "validate_financial_event",
    "assert_financial_event",
]
