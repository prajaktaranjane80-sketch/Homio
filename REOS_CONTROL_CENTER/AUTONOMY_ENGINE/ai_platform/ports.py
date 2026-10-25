"""Dependency-inversion ports used by the AI gateway.

Implementations are supplied by later AI-001 subtasks. A missing or failing
security, usage or provider dependency must never silently become an allow.
"""
from __future__ import annotations

from typing import Protocol

from .contracts import (
    AuthorizationDecision,
    ModelRoute,
    ObservabilityEvent,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    RequestContext,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
)


class ModelRegistryPort(Protocol):
    def resolve(self, model_id: str) -> ModelRoute:
        """Return an enabled, configured route or reject the identifier."""


class ProviderPort(Protocol):
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Perform one bounded provider request; never receive tenant secrets."""


class ProviderResolverPort(Protocol):
    def get(self, provider_id: str) -> ProviderPort | None:
        """Return only a registered provider adapter for this identifier."""


class AuthorizationPort(Protocol):
    def authorize_request(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        """Revalidate trusted identity, tenant and operation access."""


class UsageControlPort(Protocol):
    def reserve(self, request: UsageReservationRequest) -> UsageReservation:
        """Reserve permitted usage atomically before calling the provider."""

    def settle(
        self,
        reservation: UsageReservation,
        *,
        outcome: UsageOutcome,
        usage: ProviderUsage | None,
        provider_id: str,
        model_id: str,
    ) -> None:
        """Settle the reservation idempotently against the actual outcome."""

    def release(
        self,
        reservation: UsageReservation,
        *,
        reason_code: str,
    ) -> None:
        """Release only when the provider call was not attempted.

        After a provider attempt, use settle(FAILED, usage=None) if outcome or
        cost is unknown; ambiguous reservations must remain reconcilable.
        """


class ObservabilityPort(Protocol):
    def emit(self, event: ObservabilityEvent) -> None:
        """Record a redacted event; never persist raw prompts by default."""
