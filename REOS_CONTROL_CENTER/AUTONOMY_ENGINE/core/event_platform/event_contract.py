from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping
import json
import re

from .event_domain import (
    EventEnvelope,
    EventValidationError,
)


class EventContractError(ValueError):
    """Base CORE-002 event contract error."""


class UnknownEventTypeError(EventContractError):
    """Raised when an event type is not registered."""


class UnsupportedEventVersionError(EventContractError):
    """Raised when an event version is unsupported."""


class IncompatibleEventSchemaError(EventContractError):
    """Raised when an event schema is incompatible."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _fingerprint(value: Mapping[str, Any]) -> str:
    return sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class EventContract:
    """
    Immutable schema contract for one event type/version.

    Required fields are explicit.
    Unknown payload fields are controlled by allow_additional_fields.
    """

    schema_name: str
    event_type: str
    schema_version: int
    event_version: int

    required_fields: tuple[str, ...] = ()
    field_types: Mapping[str, str] = ()
    allow_additional_fields: bool = True

    def __post_init__(self) -> None:
        if not isinstance(
            self.schema_name,
            str,
        ) or not self.schema_name.strip():
            raise ValueError(
                "schema_name is required"
            )

        if not isinstance(
            self.event_type,
            str,
        ) or not self.event_type.strip():
            raise ValueError(
                "event_type is required"
            )

        if not re.fullmatch(
            r"[A-Z][A-Z0-9_.-]{1,199}",
            self.event_type,
        ):
            raise ValueError(
                "event_type must use canonical uppercase naming"
            )

        if self.schema_version < 1:
            raise ValueError(
                "schema_version must be >= 1"
            )

        if self.event_version < 1:
            raise ValueError(
                "event_version must be >= 1"
            )

        required = tuple(
            sorted(
                {
                    str(field).strip()
                    for field in self.required_fields
                    if str(field).strip()
                }
            )
        )

        if len(required) != len(
            set(required)
        ):
            raise ValueError(
                "required_fields contain duplicates"
            )

        object.__setattr__(
            self,
            "required_fields",
            required,
        )

        if not isinstance(
            self.field_types,
            Mapping,
        ):
            raise TypeError(
                "field_types must be a mapping"
            )

        normalized_types = {
            str(key): str(value)
            for key, value in self.field_types.items()
        }

        object.__setattr__(
            self,
            "field_types",
            normalized_types,
        )

    @property
    def contract_key(self) -> tuple[
        str,
        str,
        int,
        int,
    ]:
        return (
            self.schema_name,
            self.event_type,
            self.schema_version,
            self.event_version,
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_name": self.schema_name,
                "event_type": self.event_type,
                "schema_version": self.schema_version,
                "event_version": self.event_version,
                "required_fields": list(
                    self.required_fields
                ),
                "field_types": dict(
                    sorted(
                        self.field_types.items()
                    )
                ),
                "allow_additional_fields": (
                    self.allow_additional_fields
                ),
            }
        )

    def validate(
        self,
        event: EventEnvelope,
    ) -> None:
        if not isinstance(
            event,
            EventEnvelope,
        ):
            raise TypeError(
                "event must be EventEnvelope"
            )

        if (
            event.schema_name
            != self.schema_name
            or event.event_type
            != self.event_type
        ):
            raise IncompatibleEventSchemaError(
                "event does not match contract identity"
            )

        if (
            event.schema_version
            != self.schema_version
        ):
            raise UnsupportedEventVersionError(
                "event schema version is not supported"
            )

        if (
            event.event_version
            != self.event_version
        ):
            raise UnsupportedEventVersionError(
                "event version is not supported"
            )

        payload = event.payload

        missing = [
            field
            for field in self.required_fields
            if field not in payload
        ]

        if missing:
            raise EventValidationError(
                "missing required event fields: "
                + ", ".join(missing)
            )

        if not self.allow_additional_fields:
            unknown = set(payload) - set(
                self.field_types
            )

            if unknown:
                raise EventValidationError(
                    "unsupported event fields: "
                    + ", ".join(sorted(unknown))
                )

        for field_name, expected_type in (
            self.field_types.items()
        ):
            if field_name not in payload:
                continue

            value = payload[field_name]

            if not self._matches_type(
                value,
                expected_type,
            ):
                raise EventValidationError(
                    f"field {field_name!r} "
                    f"must be {expected_type}"
                )

    @staticmethod
    def _matches_type(
        value: Any,
        expected_type: str,
    ) -> bool:
        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "integer":
            return (
                isinstance(value, int)
                and not isinstance(value, bool)
            )

        if expected_type == "number":
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        if expected_type == "boolean":
            return isinstance(value, bool)

        if expected_type == "object":
            return isinstance(value, Mapping)

        if expected_type == "array":
            return isinstance(value, (list, tuple))

        if expected_type == "null":
            return value is None

        raise EventValidationError(
            f"unsupported contract field type: "
            f"{expected_type}"
        )


class EventContractRegistry:
    """
    Deterministic in-memory CORE-002 contract registry.

    This is a contract authority, not:
    - a transport
    - Kafka
    - a database
    - an outbox
    - a replay engine
    """

    def __init__(self) -> None:
        self._contracts: dict[
            tuple[str, str, int, int],
            EventContract,
        ] = {}

    def register(
        self,
        contract: EventContract,
    ) -> None:
        if not isinstance(
            contract,
            EventContract,
        ):
            raise TypeError(
                "contract must be EventContract"
            )

        existing = self._contracts.get(
            contract.contract_key
        )

        if existing is not None:
            if existing != contract:
                raise EventContractError(
                    "contract key already registered "
                    "with different definition"
                )

            return

        self._contracts[
            contract.contract_key
        ] = contract

    def resolve(
        self,
        *,
        schema_name: str,
        event_type: str,
        schema_version: int,
        event_version: int,
    ) -> EventContract:
        key = (
            schema_name,
            event_type,
            schema_version,
            event_version,
        )

        contract = self._contracts.get(key)

        if contract is None:
            raise UnknownEventTypeError(
                f"unsupported event contract: {key}"
            )

        return contract

    def validate(
        self,
        event: EventEnvelope,
    ) -> None:
        contract = self.resolve(
            schema_name=event.schema_name,
            event_type=event.event_type,
            schema_version=event.schema_version,
            event_version=event.event_version,
        )

        contract.validate(event)

    def fingerprint(
        self,
        *,
        schema_name: str,
        event_type: str,
        schema_version: int,
        event_version: int,
    ) -> str:
        return self.resolve(
            schema_name=schema_name,
            event_type=event_type,
            schema_version=schema_version,
            event_version=event_version,
        ).fingerprint


__all__ = [
    "EventContractError",
    "UnknownEventTypeError",
    "UnsupportedEventVersionError",
    "IncompatibleEventSchemaError",
    "EventContract",
    "EventContractRegistry",
]
