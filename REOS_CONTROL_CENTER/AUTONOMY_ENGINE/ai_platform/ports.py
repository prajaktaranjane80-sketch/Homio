"""Dependency-inversion ports used by the AI gateway and retrieval boundary.

Implementations are injected by authorized runtime owners. Missing or failing
security, policy, usage, or provider dependencies must never silently allow.
"""
from __future__ import annotations

from typing import Protocol

from .contracts import (
    AuthorizationDecision,
    EmbeddingRequest,
    ModelRoute,
    ObservabilityEvent,
    ProviderEmbeddingRequest,
    ProviderEmbeddingResponse,
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
        """Revalidate trusted identity, tenant, and operation access."""


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
        """Settle a reservation idempotently against the actual outcome."""

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


class EmbeddingProviderPort(Protocol):
    def embed(
        self,
        request: ProviderEmbeddingRequest,
    ) -> ProviderEmbeddingResponse:
        """Embed text using exactly the model requested."""


class EmbeddingProviderResolverPort(Protocol):
    def get(self, provider_id: str) -> EmbeddingProviderPort | None:
        """Return an explicitly configured embedding-capable adapter."""


class EmbeddingDataPolicyPort(Protocol):
    def allow_embedding(self, request: EmbeddingRequest) -> bool:
        """Check trusted classification, privacy, tenant, and provider policy.

        Implementations must compare the requested classification with
        authoritative source/request metadata. A supplied label is not proof.
        """


class RetrievalAccessPort(Protocol):
    def authorize_search(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        """Authorize this tenant-scoped retrieval operation."""

    def authorize_inventory(
        self,
        context: RequestContext,
        *,
        inventory_id: str,
    ) -> AuthorizationDecision:
        """Authorize access to a candidate before releasing its fields."""


class InventoryVersionPort(Protocol):
    def current_inventory_version(
        self,
        *,
        tenant_id: str,
        inventory_id: str,
    ) -> int | None:
        """Return the canonical source version, or None if the source is absent."""
