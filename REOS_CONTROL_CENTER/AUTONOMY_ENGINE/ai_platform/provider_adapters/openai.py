"""Managed OpenAI provider adapter.

The API key must be injected from the approved server-side secret provider.
This module does not read environment variables or access credentials itself.
"""

from __future__ import annotations

from .base import OpenAICompatibleProvider

OPENAI_API_BASE_URL = "https://api.openai.com/v1"


class OpenAIChatProvider(OpenAICompatibleProvider):
    """OpenAI chat and embedding adapter for explicit registry injection."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = OPENAI_API_BASE_URL,
        provider_id: str = "openai",
        max_response_bytes: int = 4 * 1024 * 1024,
    ) -> None:
        super().__init__(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            api_key_required=True,
            allow_insecure_http=False,
            max_output_tokens_field="max_completion_tokens",
            max_response_bytes=max_response_bytes,
        )


__all__ = ("OPENAI_API_BASE_URL", "OpenAIChatProvider")
