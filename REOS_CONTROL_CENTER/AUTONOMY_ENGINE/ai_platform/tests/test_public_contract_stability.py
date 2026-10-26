from __future__ import annotations

import AUTONOMY_ENGINE.ai_platform as ai_platform


def test_public_exports_are_explicit_and_stable() -> None:
    assert ai_platform.__all__ == (
        "AIErrorCode",
        "AIPlatformError",
        "AIRequest",
        "AIResponse",
        "AuthorizationDecision",
        "AuthorizationDeniedError",
        "AuthorizationServiceUnavailableError",
        "DataClassification",
        "EmbeddingCompatibilityError",
        "EmbeddingPolicyDeniedError",
        "EmbeddingPolicyUnavailableError",
        "EmbeddingPurpose",
        "EmbeddingRequest",
        "EmbeddingResult",
        "GatewayDisabledError",
        "GatewaySettings",
        "InvalidRequestError",
        "ModelDefinition",
        "ModelGateway",
        "ModelRegistry",
        "ModelResolutionError",
        "ModelRoute",
        "ObservabilityEvent",
        "ObservabilityUnavailableError",
        "ProviderCallFailedError",
        "ProviderEmbeddingRequest",
        "ProviderEmbeddingResponse",
        "ProviderRegistry",
        "ProviderRequest",
        "ProviderResponse",
        "ProviderResponseInvalidError",
        "ProviderUnavailableError",
        "ProviderUsage",
        "RequestContext",
        "RequestContextMissingError",
        "RetrievalResultInvalidError",
        "RetrievalSourceStaleError",
        "RetrievalUnavailableError",
        "UsageControlUnavailableError",
        "UsageLimitExceededError",
        "UsageOutcome",
        "UsageReservation",
        "UsageReservationRequest",
    )


def test_public_package_starts_with_live_provider_disabled() -> None:
    assert ai_platform.ModelGateway is not None
    assert ai_platform.ModelRegistry is not None
    assert ai_platform.ProviderRegistry is not None
    assert ai_platform.GatewaySettings().enabled is False
