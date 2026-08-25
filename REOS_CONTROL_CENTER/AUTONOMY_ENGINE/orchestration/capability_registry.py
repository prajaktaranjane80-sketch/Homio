"""Capability registry for AUTONOMY_ENGINE V6 additions.

Provides deterministic registration and lookup of capabilities while
keeping business execution and controller state outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Capability:
    """Immutable description of an autonomous capability."""

    capability_id: str
    name: str
    description: str = ""
    enabled: bool = True
    risk_class: str = "standard"
    metadata: dict[str, object] | None = None


class CapabilityRegistry:
    """Deterministic in-memory capability registry."""

    def __init__(self, capabilities: Iterable[Capability] | None = None) -> None:
        self._capabilities: dict[str, Capability] = {}

        if capabilities is not None:
            for capability in capabilities:
                self.register(capability)

    def register(self, capability: Capability) -> None:
        """Register a capability, rejecting duplicate identifiers."""

        capability_id = capability.capability_id.strip()

        if not capability_id:
            raise ValueError("capability_id must not be empty")

        if capability_id in self._capabilities:
            raise ValueError(f"capability already registered: {capability_id}")

        self._capabilities[capability_id] = capability

    def get(self, capability_id: str) -> Capability | None:
        """Return a capability by identifier."""

        return self._capabilities.get(capability_id.strip())

    def require(self, capability_id: str) -> Capability:
        """Return a capability or raise a deterministic lookup error."""

        capability = self.get(capability_id)

        if capability is None:
            raise KeyError(f"unknown capability: {capability_id}")

        return capability

    def is_enabled(self, capability_id: str) -> bool:
        """Return whether a registered capability is enabled."""

        capability = self.get(capability_id)
        return capability is not None and capability.enabled

    def ids(self) -> tuple[str, ...]:
        """Return registered capability identifiers in deterministic order."""

        return tuple(sorted(self._capabilities))

    def all(self) -> tuple[Capability, ...]:
        """Return all registered capabilities in deterministic order."""

        return tuple(
            self._capabilities[capability_id]
            for capability_id in self.ids()
        )

    def clear(self) -> None:
        """Clear only this registry's in-memory state."""

        self._capabilities.clear()