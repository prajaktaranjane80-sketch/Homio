"""Safe, stable error classifications for the HOMIO AI platform."""
from __future__ import annotations

from enum import StrEnum


class AIErrorCode(StrEnum):
    GATEWAY_DISABLED = "AI_GATEWAY_DISABLED"
    INVALID_REQUEST = "AI_INVALID_REQUEST"
    REQUEST_CONTEXT_MISSING = "AI_REQUEST_CONTEXT_MISSING"
    AUTHORIZATION_DENIED = "AI_AUTHORIZATION_DENIED"
    AUTHORIZATION_UNAVAILABLE = "AI_AUTHORIZATION_UNAVAILABLE"
    MODEL_NOT_ALLOWED = "AI_MODEL_NOT_ALLOWED"
    PROVIDER_UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"
    PROVIDER_CALL_FAILED = "AI_PROVIDER_CALL_FAILED"
    PROVIDER_RESPONSE_INVALID = "AI_PROVIDER_RESPONSE_INVALID"
    USAGE_LIMIT_EXCEEDED = "AI_USAGE_LIMIT_EXCEEDED"
    USAGE_CONTROL_UNAVAILABLE = "AI_USAGE_CONTROL_UNAVAILABLE"
    OBSERVABILITY_UNAVAILABLE = "AI_OBSERVABILITY_UNAVAILABLE"
    EMBEDDING_POLICY_DENIED = "AI_EMBEDDING_POLICY_DENIED"
    EMBEDDING_POLICY_UNAVAILABLE = "AI_EMBEDDING_POLICY_UNAVAILABLE"
    EMBEDDING_INCOMPATIBLE = "AI_EMBEDDING_INCOMPATIBLE"
    RETRIEVAL_UNAVAILABLE = "AI_RETRIEVAL_UNAVAILABLE"
    RETRIEVAL_RESULT_INVALID = "AI_RETRIEVAL_RESULT_INVALID"
    RETRIEVAL_SOURCE_STALE = "AI_RETRIEVAL_SOURCE_STALE"


class AIPlatformError(RuntimeError):
    """Base error whose message is safe to return beyond the provider boundary."""

    code = AIErrorCode.INVALID_REQUEST
    public_message = "The AI request could not be completed."

    def __init__(self) -> None:
        super().__init__(self.public_message)


class GatewayDisabledError(AIPlatformError):
    code = AIErrorCode.GATEWAY_DISABLED
    public_message = "The AI service is not enabled."


class InvalidRequestError(AIPlatformError):
    code = AIErrorCode.INVALID_REQUEST
    public_message = "The AI request is invalid or exceeds the allowed limits."


class RequestContextMissingError(AIPlatformError):
    code = AIErrorCode.REQUEST_CONTEXT_MISSING
    public_message = "A trusted request context is required."


class AuthorizationDeniedError(AIPlatformError):
    code = AIErrorCode.AUTHORIZATION_DENIED
    public_message = "The request is not authorized."


class AuthorizationServiceUnavailableError(AIPlatformError):
    code = AIErrorCode.AUTHORIZATION_UNAVAILABLE
    public_message = "Authorization could not be verified."


class ModelResolutionError(AIPlatformError):
    code = AIErrorCode.MODEL_NOT_ALLOWED
    public_message = "The requested model is not configured or permitted."


class ProviderUnavailableError(AIPlatformError):
    code = AIErrorCode.PROVIDER_UNAVAILABLE
    public_message = "The configured AI provider is unavailable."


class ProviderCallFailedError(AIPlatformError):
    code = AIErrorCode.PROVIDER_CALL_FAILED
    public_message = "The AI provider did not complete the request."


class ProviderResponseInvalidError(AIPlatformError):
    code = AIErrorCode.PROVIDER_RESPONSE_INVALID
    public_message = "The AI provider returned an invalid response."


class UsageLimitExceededError(AIPlatformError):
    code = AIErrorCode.USAGE_LIMIT_EXCEEDED
    public_message = "The AI usage limit has been reached."


class UsageControlUnavailableError(AIPlatformError):
    code = AIErrorCode.USAGE_CONTROL_UNAVAILABLE
    public_message = "AI usage controls could not be verified."


class ObservabilityUnavailableError(AIPlatformError):
    code = AIErrorCode.OBSERVABILITY_UNAVAILABLE
    public_message = "The AI request could not be safely recorded."


class EmbeddingPolicyDeniedError(AIPlatformError):
    code = AIErrorCode.EMBEDDING_POLICY_DENIED
    public_message = "The data policy does not permit this text to be embedded."


class EmbeddingPolicyUnavailableError(AIPlatformError):
    code = AIErrorCode.EMBEDDING_POLICY_UNAVAILABLE
    public_message = "Embedding data policy could not be verified."


class EmbeddingCompatibilityError(AIPlatformError):
    code = AIErrorCode.EMBEDDING_INCOMPATIBLE
    public_message = (
        "The embedding model or vector is incompatible with the configured index."
    )


class RetrievalUnavailableError(AIPlatformError):
    code = AIErrorCode.RETRIEVAL_UNAVAILABLE
    public_message = "The configured retrieval service is unavailable."


class RetrievalResultInvalidError(AIPlatformError):
    code = AIErrorCode.RETRIEVAL_RESULT_INVALID
    public_message = (
        "The retrieval service returned invalid or out-of-scope data."
    )


class RetrievalSourceStaleError(AIPlatformError):
    code = AIErrorCode.RETRIEVAL_SOURCE_STALE
    public_message = "A retrieved source is missing or out of date."
