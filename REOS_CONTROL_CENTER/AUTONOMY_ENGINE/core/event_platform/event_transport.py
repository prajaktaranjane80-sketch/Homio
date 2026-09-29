from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Mapping, Any
from uuid import UUID

from .event_domain import EventEnvelope


class TransportAdapterError(ValueError):
    """Base transport adapter error."""


class TransportSerializationError(
    TransportAdapterError
):
    """Transport conversion failed."""


@dataclass(frozen=True, slots=True)
class TransportMessage:
    """
    Broker-neutral transport representation.

    No Kafka-specific type appears in the domain contract.
    """

    message_id: UUID
    tenant_id: UUID
    body: bytes
    headers: Mapping[str, str]


class EventTransportAdapter(Protocol):
    """
    Runtime transport adapter protocol.

    Kafka and future transports implement this protocol.
    """

    name: str

    def encode(
        self,
        event: EventEnvelope,
    ) -> TransportMessage:
        ...

    def decode(
        self,
        message: TransportMessage,
    ) -> EventEnvelope:
        ...

    def publish(
        self,
        message: TransportMessage,
    ) -> None:
        ...


class TransportRegistry:
    """
    Adapter registry.

    Domain code resolves adapters through this boundary.
    """

    def __init__(self) -> None:
        self._adapters: dict[
            str,
            EventTransportAdapter,
        ] = {}

    def register(
        self,
        adapter: EventTransportAdapter,
    ) -> None:
        name = getattr(
            adapter,
            "name",
            None,
        )

        if not isinstance(
            name,
            str,
        ) or not name.strip():
            raise ValueError(
                "transport adapter requires name"
            )

        if name in self._adapters:
            raise TransportAdapterError(
                f"transport adapter already registered: {name}"
            )

        self._adapters[name] = adapter

    def resolve(
        self,
        name: str,
    ) -> EventTransportAdapter:
        try:
            return self._adapters[name]
        except KeyError as exc:
            raise TransportAdapterError(
                f"unsupported transport: {name}"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(
            sorted(self._adapters)
        )


__all__ = [
    "TransportAdapterError",
    "TransportSerializationError",
    "TransportMessage",
    "EventTransportAdapter",
    "TransportRegistry",
]
