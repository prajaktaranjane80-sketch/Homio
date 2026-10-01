from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ..event_platform.event_contract import EventContract


CORE008_EVENT_SCHEMA = "CORE008.COMMISSION_FINANCIAL"
CORE008_EVENT_SCHEMA_VERSION = 1
CORE008_EVENT_VERSION = 1


class CommissionEventType(str, Enum):
    COMMISSION_CREATED = "COMMISSION_CREATED"
    ENTITLEMENT_ESTABLISHED = "ENTITLEMENT_ESTABLISHED"
    COMMISSION_CALCULATED = "COMMISSION_CALCULATED"
    COMMISSION_ADJUSTED = "COMMISSION_ADJUSTED"
    SETTLEMENT_CREATED = "SETTLEMENT_CREATED"
    SETTLEMENT_COMPLETED = "SETTLEMENT_COMPLETED"
    RECONCILIATION_DISCREPANCY = "RECONCILIATION_DISCREPANCY"


@dataclass(frozen=True, slots=True)
class CommissionEventDefinition:
    event_type: CommissionEventType
    required_fields: tuple[str, ...]
    field_types: Mapping[str, str]

    def __post_init__(self) -> None:
        required = tuple(
            sorted(
                {
                    field.strip()
                    for field in self.required_fields
                    if isinstance(field, str) and field.strip()
                }
            )
        )

        if not required:
            raise ValueError("required_fields cannot be empty")

        normalized = {
            key.strip(): value.strip()
            for key, value in self.field_types.items()
            if isinstance(key, str)
            and key.strip()
            and isinstance(value, str)
            and value.strip()
        }

        missing = sorted(set(required) - set(normalized))
        if missing:
            raise ValueError(
                "Missing field type definitions: "
                + ", ".join(missing)
            )

        object.__setattr__(self, "required_fields", required)
        object.__setattr__(
            self,
            "field_types",
            MappingProxyType(normalized),
        )

    def contract(self) -> EventContract:
        return EventContract(
            schema_name=CORE008_EVENT_SCHEMA,
            event_type=self.event_type.value,
            schema_version=CORE008_EVENT_SCHEMA_VERSION,
            event_version=CORE008_EVENT_VERSION,
            required_fields=self.required_fields,
            field_types=self.field_types,
            allow_additional_fields=True,
        )


COMMISSION_EVENT_DEFINITIONS: tuple[
    CommissionEventDefinition, ...
] = (
    CommissionEventDefinition(
        event_type=CommissionEventType.COMMISSION_CREATED,
        required_fields=(
            "commission_id",
            "contract_id",
            "deal_id",
        ),
        field_types={
            "commission_id": "string",
            "contract_id": "string",
            "deal_id": "string",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.ENTITLEMENT_ESTABLISHED,
        required_fields=(
            "commission_id",
            "entitlement_id",
            "party_id",
        ),
        field_types={
            "commission_id": "string",
            "entitlement_id": "string",
            "party_id": "string",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.COMMISSION_CALCULATED,
        required_fields=(
            "commission_id",
            "calculation_id",
            "calculation_version",
            "commission_amount",
        ),
        field_types={
            "commission_id": "string",
            "calculation_id": "string",
            "calculation_version": "integer",
            "commission_amount": "object",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.COMMISSION_ADJUSTED,
        required_fields=(
            "commission_id",
            "adjustment_id",
            "adjustment_amount",
            "reason_code",
        ),
        field_types={
            "commission_id": "string",
            "adjustment_id": "string",
            "adjustment_amount": "object",
            "reason_code": "string",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.SETTLEMENT_CREATED,
        required_fields=(
            "commission_id",
            "settlement_id",
            "settlement_reference",
            "amount",
        ),
        field_types={
            "commission_id": "string",
            "settlement_id": "string",
            "settlement_reference": "string",
            "amount": "object",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.SETTLEMENT_COMPLETED,
        required_fields=(
            "commission_id",
            "settlement_id",
            "settlement_reference",
            "amount",
        ),
        field_types={
            "commission_id": "string",
            "settlement_id": "string",
            "settlement_reference": "string",
            "amount": "object",
        },
    ),
    CommissionEventDefinition(
        event_type=CommissionEventType.RECONCILIATION_DISCREPANCY,
        required_fields=(
            "commission_id",
            "reconciliation_id",
            "settlement_id",
            "expected_amount",
            "observed_amount",
            "variance_amount",
            "discrepancy_state",
        ),
        field_types={
            "commission_id": "string",
            "reconciliation_id": "string",
            "settlement_id": "string",
            "expected_amount": "object",
            "observed_amount": "object",
            "variance_amount": "object",
            "discrepancy_state": "string",
        },
    ),
)


def get_event_definition(
    event_type: CommissionEventType,
) -> CommissionEventDefinition:
    if not isinstance(event_type, CommissionEventType):
        raise TypeError(
            "event_type must be CommissionEventType"
        )

    for definition in COMMISSION_EVENT_DEFINITIONS:
        if definition.event_type is event_type:
            return definition

    raise LookupError(
        f"No CORE-008 event definition for {event_type.value}"
    )


__all__ = [
    "CORE008_EVENT_SCHEMA",
    "CORE008_EVENT_SCHEMA_VERSION",
    "CORE008_EVENT_VERSION",
    "CommissionEventType",
    "CommissionEventDefinition",
    "COMMISSION_EVENT_DEFINITIONS",
    "get_event_definition",
]
