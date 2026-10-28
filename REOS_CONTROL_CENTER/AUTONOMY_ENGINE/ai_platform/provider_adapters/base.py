"""Bounded HTTP adapter for OpenAI-compatible chat and embedding endpoints.

Security properties:
- Credentials are supplied by a trusted composition root, never by a request.
- HTTP is rejected unless the operator explicitly opts into it.
- Redirects are not followed, preventing accidental credential forwarding.
- Responses are size-bounded and schema-validated.
- Provider failures are classified without copying remote error bodies.
- No implicit retry occurs after a provider request has been attempted.
"""

from __future__ import annotations

import json
import re
import socket
from math import isfinite
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..contracts import (
    ProviderEmbeddingRequest,
    ProviderEmbeddingResponse,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    _identifier,
)
from ..errors import (
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    ProviderUnavailableError,
)

_DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_MAX_ALLOWED_RESPONSE_BYTES = 16 * 1024 * 1024
_MAX_URL_LENGTH = 2048
_MAX_API_KEY_LENGTH = 4096
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}$")


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not follow redirects from a credential-bearing inference request."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _open_url(request: Request, *, timeout: float) -> Any:
    """Open one HTTP request without automatically following redirects."""
    opener = build_opener(_NoRedirectHandler())
    return opener.open(request, timeout=timeout)


def _required_text(value: object, *, max_length: int) -> str:
    if not isinstance(value, str):
        raise ProviderResponseInvalidError()

    if not value.strip() or len(value) > max_length:
        raise ProviderResponseInvalidError()

    if any(ord(char) < 32 and char not in "\t\n\r" for char in value):
        raise ProviderResponseInvalidError()

    return value


def _optional_identifier(value: object) -> str | None:
    """Return a safe provider request ID, or omit it if it is malformed."""
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        return None

    return normalized


def _optional_token_count(payload: dict[str, Any], field: str) -> int | None:
    value = payload.get(field)
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderResponseInvalidError()

    return value


def _usage_from_payload(payload: dict[str, Any]) -> ProviderUsage | None:
    raw_usage = payload.get("usage")
    if raw_usage is None:
        return None

    if not isinstance(raw_usage, dict):
        raise ProviderResponseInvalidError()

    try:
        usage = ProviderUsage(
            input_tokens=_optional_token_count(raw_usage, "prompt_tokens"),
            output_tokens=_optional_token_count(
                raw_usage,
                "completion_tokens",
            ),
            total_tokens=_optional_token_count(raw_usage, "total_tokens"),
        )
    except (TypeError, ValueError):
        raise ProviderResponseInvalidError() from None

    # When all three counters are present, the provider's total must match
    # the input/output sum. An inflated total corrupts usage reconciliation;
    # a smaller total could undercount consumption.
    if (
        usage.input_tokens is not None
        and usage.output_tokens is not None
        and usage.total_tokens is not None
        and usage.total_tokens != usage.input_tokens + usage.output_tokens
    ):
        raise ProviderResponseInvalidError()

    return usage


class OpenAICompatibleProvider:
    """Concrete provider adapter for compatible chat and embedding APIs.

    `base_url` is the API root, generally ending in `/v1`. It must come from
    trusted server configuration. The caller must register this adapter in
    the existing ProviderRegistry; this class never mutates a registry.

    `api_key_required=False` is intended only for explicitly approved private
    service deployments where authentication is enforced by another trusted
    boundary. It must not be used for an exposed unauthenticated endpoint.
    """

    __slots__ = (
        "_provider_id",
        "_base_url",
        "_api_key",
        "_max_output_tokens_field",
        "_embedding_timeout_seconds",
        "_max_response_bytes",
    )

    def __init__(
        self,
        *,
        provider_id: str,
        base_url: str,
        api_key: str | None,
        api_key_required: bool = True,
        allow_insecure_http: bool = False,
        max_output_tokens_field: str = "max_completion_tokens",
        embedding_timeout_seconds: float = 30.0,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        try:
            normalized_provider_id = _identifier(
                provider_id,
                "provider_id",
            )
        except (TypeError, ValueError):
            raise ValueError("provider_id is invalid") from None

        if not isinstance(api_key_required, bool):
            raise ValueError("api_key_required must be a boolean")

        if not isinstance(allow_insecure_http, bool):
            raise ValueError("allow_insecure_http must be a boolean")

        if max_output_tokens_field not in {
            "max_completion_tokens",
            "max_tokens",
        }:
            raise ValueError("Unsupported output-token parameter")

        if (
            isinstance(embedding_timeout_seconds, bool)
            or not isinstance(embedding_timeout_seconds, (int, float))
            or not isfinite(float(embedding_timeout_seconds))
            or not 0 < embedding_timeout_seconds <= 120
        ):
            raise ValueError(
                "embedding_timeout_seconds must be greater than 0 "
                "and no greater than 120"
            )

        if (
            isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or not 1024 <= max_response_bytes <= _MAX_ALLOWED_RESPONSE_BYTES
        ):
            raise ValueError(
                "max_response_bytes must be between 1024 and 16777216"
            )

        normalized_url = self._validate_base_url(
            base_url,
            allow_insecure_http=allow_insecure_http,
        )
        normalized_key = self._validate_api_key(api_key)

        if api_key_required and normalized_key is None:
            raise ValueError("Provider API key is required")

        self._provider_id = normalized_provider_id
        self._base_url = normalized_url
        self._api_key = normalized_key
        self._max_output_tokens_field = max_output_tokens_field
        self._embedding_timeout_seconds = float(embedding_timeout_seconds)
        self._max_response_bytes = max_response_bytes

    @staticmethod
    def _validate_base_url(
        base_url: str,
        *,
        allow_insecure_http: bool,
    ) -> str:
        if not isinstance(base_url, str):
            raise ValueError("Provider base URL must be a string")

        raw = base_url.strip()
        if not raw or len(raw) > _MAX_URL_LENGTH:
            raise ValueError("Provider base URL is invalid")

        if any(ord(char) < 32 for char in raw):
            raise ValueError("Provider base URL contains control characters")

        try:
            parsed = urlsplit(raw)
            hostname = parsed.hostname
            # Accessing .port validates the configured port syntax.
            _ = parsed.port
        except ValueError:
            raise ValueError("Provider base URL is invalid") from None

        if parsed.scheme not in {"https", "http"} or not hostname:
            raise ValueError("Provider base URL must use HTTPS and include a host")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Provider base URL must not contain credentials")

        if parsed.query or parsed.fragment:
            raise ValueError(
                "Provider base URL must not contain a query or fragment"
            )

        if parsed.scheme == "http" and not allow_insecure_http:
            raise ValueError(
                "HTTP is disabled; explicitly approve it only for a "
                "trusted private inference endpoint"
            )

        if any(segment in {".", ".."} for segment in parsed.path.split("/")):
            raise ValueError("Provider base URL contains an unsafe path")

        if parsed.path.endswith(("/chat/completions", "/embeddings")):
            raise ValueError(
                "Provide the API root, not a full inference endpoint URL"
            )

        return raw.rstrip("/")

    @staticmethod
    def _validate_api_key(api_key: str | None) -> str | None:
        if api_key is None:
            return None

        if not isinstance(api_key, str):
            raise ValueError("Provider API key must be a string")

        normalized = api_key.strip()
        if (
            not normalized
            or len(normalized) > _MAX_API_KEY_LENGTH
            or any(ord(char) < 32 or ord(char) == 127 for char in normalized)
        ):
            raise ValueError("Provider API key is invalid")

        return normalized

    def __repr__(self) -> str:
        # Do not include credentials or endpoint paths in repr/log messages.
        return (
            f"{type(self).__name__}("
            f"provider_id={self._provider_id!r}, "
            "credentials='redacted')"
        )

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Perform one bounded chat-completion request."""
        if not isinstance(request, ProviderRequest):
            raise ProviderCallFailedError()

        body = {
            "model": request.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
            self._max_output_tokens_field: request.max_output_tokens,
            "stream": False,
        }

        payload, response_request_id = self._post_json(
            endpoint="chat/completions",
            body=body,
            timeout=float(request.timeout_seconds),
        )

        try:
            _required_text(payload.get("model"), max_length=256)

            choices = payload.get("choices")
            if not isinstance(choices, list) or len(choices) != 1:
                raise ProviderResponseInvalidError()

            choice = choices[0]
            if not isinstance(choice, dict):
                raise ProviderResponseInvalidError()

            message = choice.get("message")
            if not isinstance(message, dict):
                raise ProviderResponseInvalidError()

            text = _required_text(
                message.get("content"),
                max_length=1_000_000,
            )

            finish_reason = choice.get("finish_reason")
            if finish_reason is not None and not isinstance(
                finish_reason,
                str,
            ):
                raise ProviderResponseInvalidError()

            return ProviderResponse(
                text=text,
                provider_id=self._provider_id,
                # Keep the configured registry route identity stable. Provider
                # snapshots/version policy remain configuration-owned.
                model_id=request.model_id,
                finish_reason=finish_reason,
                usage=_usage_from_payload(payload),
                provider_request_id=response_request_id,
            )
        except ProviderResponseInvalidError:
            raise
        except (TypeError, ValueError, KeyError):
            raise ProviderResponseInvalidError() from None

    def embed(
        self,
        request: ProviderEmbeddingRequest,
    ) -> ProviderEmbeddingResponse:
        """Create one embedding vector through the configured provider."""
        if not isinstance(request, ProviderEmbeddingRequest):
            raise ProviderCallFailedError()

        payload, response_request_id = self._post_json(
            endpoint="embeddings",
            body={
                "model": request.model_id,
                "input": request.text,
                "encoding_format": "float",
            },
            timeout=self._embedding_timeout_seconds,
        )

        try:
            model_version = _required_text(
                payload.get("model"),
                max_length=256,
            )

            data = payload.get("data")
            if not isinstance(data, list) or len(data) != 1:
                raise ProviderResponseInvalidError()

            first = data[0]
            if not isinstance(first, dict):
                raise ProviderResponseInvalidError()

            index = first.get("index")
            if isinstance(index, bool) or not isinstance(index, int) or index != 0:
                raise ProviderResponseInvalidError()

            vector = first.get("embedding")
            if isinstance(vector, (str, bytes)) or not isinstance(
                vector,
                (list, tuple),
            ):
                raise ProviderResponseInvalidError()

            return ProviderEmbeddingResponse(
                model_id=request.model_id,
                model_version=model_version,
                vector=tuple(vector),
                provider_request_id=response_request_id,
            )
        except ProviderResponseInvalidError:
            raise
        except (TypeError, ValueError, KeyError, OverflowError):
            raise ProviderResponseInvalidError() from None

    def _post_json(
        self,
        *,
        endpoint: str,
        body: dict[str, Any],
        timeout: float,
    ) -> tuple[dict[str, Any], str | None]:
        """Post JSON once; never retry and never expose remote response bodies."""
        try:
            serialized_body = json.dumps(
                body,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError):
            raise ProviderCallFailedError() from None

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._api_key is not None:
            headers["Authorization"] = f"Bearer {self._api_key}"

        request = Request(
            url=f"{self._base_url}/{endpoint}",
            data=serialized_body,
            headers=headers,
            method="POST",
        )

        try:
            with _open_url(request, timeout=timeout) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()

                if (
                    isinstance(status, bool)
                    or not isinstance(status, int)
                    or not 200 <= status < 300
                ):
                    self._raise_for_status(status)

                raw_response = response.read(self._max_response_bytes + 1)
                if (
                    not isinstance(raw_response, bytes)
                    or len(raw_response) > self._max_response_bytes
                ):
                    raise ProviderResponseInvalidError()

                headers_object = getattr(response, "headers", None)
                response_request_id = None
                if headers_object is not None:
                    getter = getattr(headers_object, "get", None)
                    if callable(getter):
                        response_request_id = _optional_identifier(
                            getter("x-request-id")
                        )
        except HTTPError as exc:
            status = exc.code
            try:
                exc.close()
            except Exception:
                pass
            self._raise_for_status(status)
        except ProviderResponseInvalidError:
            raise
        except (URLError, TimeoutError, socket.timeout, OSError):
            raise ProviderUnavailableError() from None

        try:
            decoded = raw_response.decode("utf-8")
            parsed = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderResponseInvalidError() from None

        if not isinstance(parsed, dict):
            raise ProviderResponseInvalidError()

        if response_request_id is None:
            response_request_id = _optional_identifier(parsed.get("id"))

        return parsed, response_request_id

    @staticmethod
    def _raise_for_status(status: object) -> None:
        # Do not return or log upstream error text. It may contain request data,
        # operational details, or sensitive values.
        if (
            isinstance(status, int)
            and not isinstance(status, bool)
            and (status in {408, 425, 429} or status >= 500)
        ):
            raise ProviderUnavailableError() from None

        raise ProviderCallFailedError() from None


__all__ = ("OpenAICompatibleProvider",)
