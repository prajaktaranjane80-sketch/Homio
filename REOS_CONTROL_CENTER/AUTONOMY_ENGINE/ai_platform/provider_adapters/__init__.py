"""Approved concrete adapters for OpenAI-compatible inference APIs.

The existing ProviderPort and EmbeddingProviderPort remain the canonical
contracts. Adapter construction, credentials, endpoint selection and
registration belong to the trusted server-side composition root.
"""

from .base import OpenAICompatibleProvider
from .openai import OpenAIChatProvider
from .vllm import VLLMChatProvider

__all__ = (
    "OpenAIChatProvider",
    "OpenAICompatibleProvider",
    "VLLMChatProvider",
)
