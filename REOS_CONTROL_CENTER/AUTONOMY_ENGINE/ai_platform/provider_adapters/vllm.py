"""Self-hosted vLLM adapter using its OpenAI-compatible API.

Production deployments should use an authenticated private endpoint, normally
over HTTPS. Missing API-key mode is explicit and must only be selected when
another trusted network boundary provides equivalent access control.
"""

from __future__ import annotations

from .base import OpenAICompatibleProvider


class VLLMChatProvider(OpenAICompatibleProvider):
    """vLLM chat and embedding adapter for explicit registry injection."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        provider_id: str = "vllm",
        allow_missing_api_key: bool = False,
        allow_insecure_http: bool = False,
        max_response_bytes: int = 4 * 1024 * 1024,
    ) -> None:
        if not isinstance(allow_missing_api_key, bool):
            raise ValueError("allow_missing_api_key must be a boolean")

        if api_key is None and not allow_missing_api_key:
            raise ValueError(
                "vLLM API key is required unless the operator explicitly "
                "approves a separately authenticated private endpoint"
            )

        super().__init__(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            api_key_required=not allow_missing_api_key,
            allow_insecure_http=allow_insecure_http,
            # `max_tokens` is used for wider compatibility with vLLM releases.
            max_output_tokens_field="max_tokens",
            max_response_bytes=max_response_bytes,
        )


__all__ = ("VLLMChatProvider",)
