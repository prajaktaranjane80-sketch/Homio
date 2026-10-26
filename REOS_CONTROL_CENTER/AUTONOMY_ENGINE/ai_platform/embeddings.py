"""Registry-bound embedding adaptation for the HOMIO AI platform.

No provider SDK, credential lookup, index write, or network client is created
here. Provider calls are made only through an injected, explicitly configured
embedding-capable adapter.
"""
from __future__ import annotations

from .contracts import (
    EmbeddingRequest,
    EmbeddingResult,
    ProviderEmbeddingRequest,
    ProviderEmbeddingResponse,
)
from .errors import (
    AIPlatformError,
    EmbeddingCompatibilityError,
    EmbeddingPolicyDeniedError,
    EmbeddingPolicyUnavailableError,
    InvalidRequestError,
    ModelResolutionError,
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    ProviderUnavailableError,
)
from .model_registry import ModelRegistry
from .ports import EmbeddingDataPolicyPort, EmbeddingProviderResolverPort


class EmbeddingService:
    """Create model-version-bound vectors after policy and compatibility checks."""

    def __init__(
        self,
        *,
        model_registry: ModelRegistry,
        provider_resolver: EmbeddingProviderResolverPort,
        data_policy: EmbeddingDataPolicyPort,
        max_text_chars: int = 16_000,
    ) -> None:
        if (
            model_registry is None
            or provider_resolver is None
            or data_policy is None
        ):
            raise ValueError(
                "model registry, provider resolver, and data policy are required"
            )

        if (
            isinstance(max_text_chars, bool)
            or not isinstance(max_text_chars, int)
            or not 1 <= max_text_chars <= 1_000_000
        ):
            raise ValueError(
                "max_text_chars must be between 1 and 1000000"
            )

        if not callable(getattr(model_registry, "resolve_definition", None)):
            raise TypeError("model_registry must expose resolve_definition")
        if not callable(getattr(provider_resolver, "get", None)):
            raise TypeError("provider_resolver must expose get")
        if not callable(getattr(data_policy, "allow_embedding", None)):
            raise TypeError("data_policy must expose allow_embedding")

        self._model_registry = model_registry
        self._provider_resolver = provider_resolver
        self._data_policy = data_policy
        self._max_text_chars = max_text_chars

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Return a validated vector or raise a safe, classified platform error."""
        if not isinstance(request, EmbeddingRequest):
            raise InvalidRequestError()

        if len(request.text) > self._max_text_chars:
            raise InvalidRequestError()

        try:
            definition = self._model_registry.resolve_definition(
                request.model_id,
                required_capability="embeddings",
            )
        except ModelResolutionError:
            raise
        except Exception:
            raise ModelResolutionError() from None

        if len(request.text) > definition.route.max_input_chars:
            raise InvalidRequestError()

        dimension = getattr(definition, "embedding_dimension", None)
        if (
            isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension < 1
        ):
            raise EmbeddingCompatibilityError()

        try:
            allowed = self._data_policy.allow_embedding(request)
        except Exception:
            raise EmbeddingPolicyUnavailableError() from None

        if not isinstance(allowed, bool):
            raise EmbeddingPolicyUnavailableError()
        if not allowed:
            raise EmbeddingPolicyDeniedError()

        try:
            provider = self._provider_resolver.get(
                definition.route.provider_id
            )
        except Exception:
            raise ProviderUnavailableError() from None

        if provider is None or not callable(getattr(provider, "embed", None)):
            raise ProviderUnavailableError()

        provider_request = ProviderEmbeddingRequest(
            request_id=request.request_id,
            model_id=definition.route.model_id,
            text=request.text,
        )

        try:
            provider_response = provider.embed(provider_request)
        except AIPlatformError:
            raise
        except Exception:
            raise ProviderCallFailedError() from None

        if not isinstance(provider_response, ProviderEmbeddingResponse):
            raise ProviderResponseInvalidError()

        if (
            provider_response.model_id != definition.route.model_id
            or provider_response.model_version != definition.model_version
        ):
            raise EmbeddingCompatibilityError()

        if len(provider_response.vector) != dimension:
            raise EmbeddingCompatibilityError()

        try:
            return EmbeddingResult(
                request_id=request.request_id,
                tenant_id=request.tenant_id,
                model_id=definition.route.model_id,
                model_version=definition.model_version,
                provider_id=definition.route.provider_id,
                provider_version=definition.provider_version,
                dimension=dimension,
                vector=provider_response.vector,
                classification=request.classification,
                purpose=request.purpose,
                source_reference=request.source_reference,
                record_id=request.record_id,
                source_version=request.source_version,
                provider_request_id=provider_response.provider_request_id,
            )
        except (TypeError, ValueError):
            raise ProviderResponseInvalidError() from None


__all__ = ["EmbeddingService"]
