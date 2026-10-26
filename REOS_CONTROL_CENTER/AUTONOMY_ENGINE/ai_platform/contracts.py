"""Stable, provider-independent contracts for the HOMIO AI platform.

These types describe requests and evidence. They do not establish identity,
authorize an action, or prove that a caller is trusted; those decisions belong
to the server authentication and existing HOMIO authorization boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
import re

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}$")
_OPERATION = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
_EVENT_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def _text(
    value: object,
    field_name: str,
    maximum: int,
    *,
    allow_multiline: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")

    permitted_controls = {"\t", "\n", "\r"} if allow_multiline else set()
    if any(
        ord(char) < 32 and char not in permitted_controls
        for char in normalized
    ):
        raise ValueError(
            f"{field_name} contains a forbidden control character"
        )
    return normalized


def _identifier(value: object, field_name: str) -> str:
    normalized = _text(value, field_name, 256)
    if not _IDENTIFIER.fullmatch(normalized):
        raise ValueError(
            f"{field_name} has an invalid identifier format"
        )
    return normalized


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _nonnegative_optional_int(
    value: object,
    field_name: str,
) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"{field_name} must be a non-negative integer or None"
        )
    return value


class UsageOutcome(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Server-derived identity references required at the AI boundary.

    Construct this only from a trusted server authentication/tenant context.
    The presence of these strings is not itself proof of authentication or
    authorization; the injected authorization port must verify the context.
    """

    principal_id: str
    tenant_id: str
    authentication_context_ref: str
    correlation_id: str
    organization_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "principal_id",
            "tenant_id",
            "authentication_context_ref",
            "correlation_id",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        if self.organization_id is not None:
            object.__setattr__(
                self,
                "organization_id",
                _identifier(self.organization_id, "organization_id"),
            )


@dataclass(frozen=True, slots=True)
class AIRequest:
    """A bounded, user-facing request to the provider-independent gateway."""

    request_id: str
    operation: str
    input_text: str
    context: RequestContext | None
    model_id: str | None = None
    max_output_tokens: int | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _identifier(self.request_id, "request_id"),
        )

        if (
            not isinstance(self.operation, str)
            or not _OPERATION.fullmatch(self.operation)
        ):
            raise ValueError(
                "operation must be a lowercase operation identifier"
            )

        object.__setattr__(
            self,
            "input_text",
            _text(
                self.input_text,
                "input_text",
                1_000_000,
                allow_multiline=True,
            ),
        )

        if self.context is not None and not isinstance(
            self.context,
            RequestContext,
        ):
            raise TypeError("context must be RequestContext or None")

        if self.model_id is not None:
            object.__setattr__(
                self,
                "model_id",
                _identifier(self.model_id, "model_id"),
            )

        if self.max_output_tokens is not None:
            _positive_int(self.max_output_tokens, "max_output_tokens")

        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _identifier(self.idempotency_key, "idempotency_key"),
            )


@dataclass(frozen=True, slots=True)
class ModelRoute:
    """A registry-approved route, not an authorization decision."""

    provider_id: str
    model_id: str
    max_input_chars: int
    max_output_tokens: int
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_id",
            _identifier(self.provider_id, "provider_id"),
        )
        object.__setattr__(
            self,
            "model_id",
            _identifier(self.model_id, "model_id"),
        )
        _positive_int(self.max_input_chars, "max_input_chars")
        _positive_int(self.max_output_tokens, "max_output_tokens")

        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean")


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """Minimal model-facing request; tenant and auth IDs are not forwarded."""

    request_id: str
    operation: str
    prompt: str
    model_id: str
    max_output_tokens: int
    timeout_seconds: float
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _identifier(self.request_id, "request_id"),
        )

        if (
            not isinstance(self.operation, str)
            or not _OPERATION.fullmatch(self.operation)
        ):
            raise ValueError(
                "operation must be a lowercase operation identifier"
            )

        object.__setattr__(
            self,
            "prompt",
            _text(
                self.prompt,
                "prompt",
                1_000_000,
                allow_multiline=True,
            ),
        )
        object.__setattr__(
            self,
            "model_id",
            _identifier(self.model_id, "model_id"),
        )
        _positive_int(self.max_output_tokens, "max_output_tokens")

        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
        ):
            raise TypeError(
                "timeout_seconds must be a finite positive number"
            )

        if (
            not isfinite(float(self.timeout_seconds))
            or self.timeout_seconds <= 0
            or self.timeout_seconds > 120
        ):
            raise ValueError(
                "timeout_seconds must be > 0 and <= 120 seconds"
            )

        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _identifier(self.idempotency_key, "idempotency_key"),
            )


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Provider-reported usage; None means the provider did not report it."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        input_tokens = _nonnegative_optional_int(
            self.input_tokens,
            "input_tokens",
        )
        output_tokens = _nonnegative_optional_int(
            self.output_tokens,
            "output_tokens",
        )
        total_tokens = _nonnegative_optional_int(
            self.total_tokens,
            "total_tokens",
        )

        known_minimum = (input_tokens or 0) + (output_tokens or 0)
        if (
            total_tokens is not None
            and total_tokens < known_minimum
        ):
            raise ValueError(
                "total_tokens cannot be less than the known token counts"
            )


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    text: str
    provider_id: str
    model_id: str
    finish_reason: str | None = None
    usage: ProviderUsage | None = None
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "text",
            _text(
                self.text,
                "text",
                1_000_000,
                allow_multiline=True,
            ),
        )
        object.__setattr__(
            self,
            "provider_id",
            _identifier(self.provider_id, "provider_id"),
        )
        object.__setattr__(
            self,
            "model_id",
            _identifier(self.model_id, "model_id"),
        )

        if self.finish_reason is not None:
            object.__setattr__(
                self,
                "finish_reason",
                _text(self.finish_reason, "finish_reason", 128),
            )

        if self.usage is not None and not isinstance(
            self.usage,
            ProviderUsage,
        ):
            raise TypeError("usage must be ProviderUsage or None")

        if self.provider_request_id is not None:
            object.__setattr__(
                self,
                "provider_request_id",
                _identifier(self.provider_request_id, "provider_request_id"),
            )


@dataclass(frozen=True, slots=True)
class AIResponse:
    request_id: str
    correlation_id: str
    text: str
    provider_id: str
    model_id: str
    finish_reason: str | None = None
    usage: ProviderUsage | None = None

    def __post_init__(self) -> None:
        for name in ("request_id", "correlation_id", "provider_id", "model_id"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        object.__setattr__(
            self,
            "text",
            _text(self.text, "text", 1_000_000, allow_multiline=True),
        )

        if self.finish_reason is not None:
            object.__setattr__(
                self,
                "finish_reason",
                _text(self.finish_reason, "finish_reason", 128),
            )

        if self.usage is not None and not isinstance(
            self.usage,
            ProviderUsage,
        ):
            raise TypeError("usage must be ProviderUsage or None")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    decision_id: str
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be a boolean")

        object.__setattr__(
            self,
            "decision_id",
            _identifier(self.decision_id, "decision_id"),
        )
        object.__setattr__(
            self,
            "reason_code",
            _identifier(self.reason_code, "reason_code"),
        )


@dataclass(frozen=True, slots=True)
class UsageReservationRequest:
    request_id: str
    tenant_id: str
    model_id: str
    prompt_chars: int
    max_output_tokens: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        for name in ("request_id", "tenant_id", "model_id"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        if (
            isinstance(self.prompt_chars, bool)
            or not isinstance(self.prompt_chars, int)
            or self.prompt_chars < 1
        ):
            raise ValueError("prompt_chars must be a positive integer")

        _positive_int(self.max_output_tokens, "max_output_tokens")

        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _identifier(self.idempotency_key, "idempotency_key"),
            )


@dataclass(frozen=True, slots=True)
class UsageReservation:
    reservation_id: str
    request_id: str
    tenant_id: str
    model_id: str

    def __post_init__(self) -> None:
        for name in (
            "reservation_id",
            "request_id",
            "tenant_id",
            "model_id",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )


@dataclass(frozen=True, slots=True)
class ObservabilityEvent:
    event_name: str
    request_id: str
    correlation_id: str
    outcome: str
    provider_id: str | None = None
    model_id: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.event_name, str)
            or not _EVENT_NAME.fullmatch(self.event_name)
        ):
            raise ValueError(
                "event_name must be an uppercase event identifier"
            )

        for name in ("request_id", "correlation_id", "outcome"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        for name in ("provider_id", "model_id", "error_code"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _identifier(value, name),
                )

        if self.duration_ms is not None:
            if (
                isinstance(self.duration_ms, bool)
                or not isinstance(self.duration_ms, int)
                or self.duration_ms < 0
            ):
                raise ValueError(
                    "duration_ms must be a non-negative integer or None"
                )


class DataClassification(StrEnum):
    """Sensitivity label checked against trusted source/policy metadata."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class EmbeddingPurpose(StrEnum):
    """Distinguish query vectors from rebuildable document vectors."""

    QUERY = "QUERY"
    DOCUMENT = "DOCUMENT"


def _finite_vector(
    value: object,
    field_name: str = "vector",
) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be a numeric sequence")

    try:
        raw_values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(
            f"{field_name} must be a numeric sequence"
        ) from exc

    if not raw_values:
        raise ValueError(f"{field_name} cannot be empty")
    if len(raw_values) > 65536:
        raise ValueError(
            f"{field_name} exceeds the maximum supported dimension"
        )

    normalized: list[float] = []
    for item in raw_values:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field_name} values must be finite numbers")
        try:
            number = float(item)
        except (OverflowError, ValueError) as exc:
            raise ValueError(
                f"{field_name} values must be finite numbers"
            ) from exc
        if not isfinite(number):
            raise ValueError(f"{field_name} values must be finite numbers")
        normalized.append(number)

    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class ProviderEmbeddingRequest:
    """Provider-facing embedding input without tenant/business metadata."""

    request_id: str
    model_id: str
    text: str

    def __post_init__(self) -> None:
        for name in ("request_id", "model_id"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )
        object.__setattr__(
            self,
            "text",
            _text(self.text, "text", 1_000_000, allow_multiline=True),
        )


@dataclass(frozen=True, slots=True)
class ProviderEmbeddingResponse:
    """Untrusted provider output; validation against registry metadata is required."""

    model_id: str
    model_version: str
    vector: tuple[float, ...]
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("model_id", "model_version"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )
        object.__setattr__(self, "vector", _finite_vector(self.vector))

        if self.provider_request_id is not None:
            object.__setattr__(
                self,
                "provider_request_id",
                _identifier(self.provider_request_id, "provider_request_id"),
            )


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    """Tenant-bound embedding intent with source provenance for documents."""

    request_id: str
    tenant_id: str
    model_id: str
    text: str
    classification: DataClassification
    purpose: EmbeddingPurpose = EmbeddingPurpose.QUERY
    source_reference: str | None = None
    record_id: str | None = None
    source_version: int | None = None

    def __post_init__(self) -> None:
        for name in ("request_id", "tenant_id", "model_id"):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        object.__setattr__(
            self,
            "text",
            _text(self.text, "text", 1_000_000, allow_multiline=True),
        )

        try:
            classification = DataClassification(self.classification)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "classification must be a supported DataClassification"
            ) from exc

        try:
            purpose = EmbeddingPurpose(self.purpose)
        except (TypeError, ValueError) as exc:
            raise ValueError("purpose must be QUERY or DOCUMENT") from exc

        object.__setattr__(self, "classification", classification)
        object.__setattr__(self, "purpose", purpose)

        source_values = (
            self.source_reference,
            self.record_id,
            self.source_version,
        )

        if purpose is EmbeddingPurpose.DOCUMENT:
            if (
                self.source_reference is None
                or self.record_id is None
                or self.source_version is None
            ):
                raise ValueError(
                    "document embeddings require source_reference, "
                    "record_id, and source_version"
                )

            object.__setattr__(
                self,
                "source_reference",
                _identifier(self.source_reference, "source_reference"),
            )
            object.__setattr__(
                self,
                "record_id",
                _identifier(self.record_id, "record_id"),
            )
            _positive_int(self.source_version, "source_version")

        elif any(value is not None for value in source_values):
            raise ValueError(
                "query embeddings must not claim document source identity"
            )


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Validated vector bound to an exact model version and source identity."""

    request_id: str
    tenant_id: str
    model_id: str
    model_version: str
    provider_id: str
    provider_version: str
    dimension: int
    vector: tuple[float, ...]
    classification: DataClassification
    purpose: EmbeddingPurpose
    source_reference: str | None = None
    record_id: str | None = None
    source_version: int | None = None
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "tenant_id",
            "model_id",
            "model_version",
            "provider_id",
            "provider_version",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name),
            )

        _positive_int(self.dimension, "dimension")
        normalized_vector = _finite_vector(self.vector)

        if len(normalized_vector) != self.dimension:
            raise ValueError("vector length does not match dimension")

        object.__setattr__(self, "vector", normalized_vector)

        try:
            classification = DataClassification(self.classification)
            purpose = EmbeddingPurpose(self.purpose)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "embedding classification or purpose is invalid"
            ) from exc

        object.__setattr__(self, "classification", classification)
        object.__setattr__(self, "purpose", purpose)

        if purpose is EmbeddingPurpose.DOCUMENT:
            if (
                self.source_reference is None
                or self.record_id is None
                or self.source_version is None
            ):
                raise ValueError(
                    "document embedding results require source provenance"
                )

            object.__setattr__(
                self,
                "source_reference",
                _identifier(self.source_reference, "source_reference"),
            )
            object.__setattr__(
                self,
                "record_id",
                _identifier(self.record_id, "record_id"),
            )
            _positive_int(self.source_version, "source_version")

        elif any(
            value is not None
            for value in (
                self.source_reference,
                self.record_id,
                self.source_version,
            )
        ):
            raise ValueError(
                "query embedding results must not claim document source identity"
            )

        if self.provider_request_id is not None:
            object.__setattr__(
                self,
                "provider_request_id",
                _identifier(self.provider_request_id, "provider_request_id"),
            )
