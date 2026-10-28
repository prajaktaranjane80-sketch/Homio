
from __future__ import annotations

from email.message import Message
from io import BytesIO
import json
from urllib.error import HTTPError, URLError

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    ProviderEmbeddingRequest,
    ProviderRequest,
    ProviderResponse,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    ProviderUnavailableError,
)
from AUTONOMY_ENGINE.ai_platform.provider_adapters import (
    OpenAIChatProvider,
    VLLMChatProvider,
)
from AUTONOMY_ENGINE.ai_platform.provider_adapters import base as adapter_base


class FakeHTTPResponse:
    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.closed = False

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def read(self, amount: int = -1) -> bytes:
        if amount < 0:
            return self.body
        return self.body[:amount]

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        self.closed = True


def chat_payload(
    *,
    content: str = "Two bedroom properties are available for review.",
    model: str = "gpt-test-snapshot",
) -> dict:
    return {
        "id": "chatcmpl-test-1",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20,
        },
    }


def make_request() -> ProviderRequest:
    return ProviderRequest(
        request_id="request-1",
        operation="property.search",
        prompt="Find two bedroom apartments in Pune.",
        model_id="gpt-test",
        max_output_tokens=64,
        timeout_seconds=5,
    )


def patch_response(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> dict:
    captured: dict = {}
    response_body = (
        payload if isinstance(payload, bytes) else
        json.dumps(payload).encode("utf-8")
    )

    def fake_open(request, *, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        captured["calls"] = captured.get("calls", 0) + 1
        return FakeHTTPResponse(
            response_body,
            status=status,
            headers=headers,
        )

    monkeypatch.setattr(adapter_base, "_open_url", fake_open)
    return captured


def test_openai_chat_request_and_response_are_mapped_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = patch_response(
        monkeypatch,
        chat_payload(),
        headers={"x-request-id": "req-test-123"},
    )
    provider = OpenAIChatProvider(api_key="test-secret-value")

    response = provider.generate(make_request())

    assert isinstance(response, ProviderResponse)
    assert response.provider_id == "openai"
    assert response.model_id == "gpt-test"
    assert response.text == "Two bedroom properties are available for review."
    assert response.finish_reason == "stop"
    assert response.provider_request_id == "req-test-123"
    assert response.usage is not None
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 8
    assert response.usage.total_tokens == 20

    assert captured["url"] == (
        "https://api.openai.com/v1/chat/completions"
    )
    assert captured["method"] == "POST"
    assert captured["headers"]["Authorization"] == (
        "Bearer test-secret-value"
    )
    assert captured["body"]["model"] == "gpt-test"
    assert captured["body"]["max_completion_tokens"] == 64
    assert captured["body"]["stream"] is False
    assert "tenant_id" not in captured["body"]
    assert captured["calls"] == 1


def test_openai_provider_repr_never_contains_api_key() -> None:
    provider = OpenAIChatProvider(api_key="highly-sensitive-token")

    assert "highly-sensitive-token" not in repr(provider)
    assert "redacted" in repr(provider)


def test_openai_requires_a_nonempty_api_key() -> None:
    with pytest.raises(ValueError, match="API key"):
        OpenAIChatProvider(api_key="")

    with pytest.raises(ValueError, match="API key"):
        OpenAIChatProvider(api_key="   ")


def test_http_is_rejected_without_explicit_operator_opt_in() -> None:
    with pytest.raises(ValueError, match="HTTP is disabled"):
        VLLMChatProvider(
            base_url="http://127.0.0.1:8000/v1",
            api_key="private-key",
        )


def test_vllm_chat_uses_compatible_endpoint_and_explicit_http_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = patch_response(monkeypatch, chat_payload())
    provider = VLLMChatProvider(
        base_url="http://127.0.0.1:8000/v1",
        api_key="private-vllm-key",
        allow_insecure_http=True,
    )

    response = provider.generate(make_request())

    assert response.provider_id == "vllm"
    assert captured["url"] == (
        "http://127.0.0.1:8000/v1/chat/completions"
    )
    assert captured["headers"]["Authorization"] == "Bearer private-vllm-key"
    assert captured["body"]["max_tokens"] == 64
    assert captured["calls"] == 1


def test_vllm_requires_explicit_opt_in_for_missing_api_key() -> None:
    with pytest.raises(ValueError, match="API key is required"):
        VLLMChatProvider(base_url="https://vllm.internal/v1")

    provider = VLLMChatProvider(
        base_url="https://vllm.internal/v1",
        allow_missing_api_key=True,
    )

    assert "credentials='redacted'" in repr(provider)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://user:password@provider.example/v1",
        "https://provider.example/v1?token=secret",
        "https://provider.example/v1#fragment",
        "https://provider.example/v1/chat/completions",
        "ftp://provider.example/v1",
    ],
)
def test_unsafe_or_invalid_base_urls_are_rejected(base_url: str) -> None:
    with pytest.raises(ValueError):
        VLLMChatProvider(
            base_url=base_url,
            api_key="test-key",
            allow_missing_api_key=False,
        )


def test_invalid_json_response_is_classified_without_leaking_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_response(
        monkeypatch,
        b'{"private":"customer-data"',
    )
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError) as caught:
        provider.generate(make_request())

    assert "customer-data" not in str(caught.value)


def test_missing_or_malformed_choices_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_response(
        monkeypatch,
        {
            "model": "gpt-test",
            "choices": [],
        },
    )
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError):
        provider.generate(make_request())


def test_empty_chat_content_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_response(monkeypatch, chat_payload(content="   "))
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError):
        provider.generate(make_request())


def test_nested_secret_in_malformed_provider_content_is_not_leaked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = chat_payload()
    payload["choices"][0]["message"]["content"] = {
        "error": {
            "api_key": "nested-private-secret",
            "customer_record": {"token": "nested-customer-token"},
        }
    }
    patch_response(monkeypatch, payload)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError) as caught:
        provider.generate(make_request())

    assert "nested-private-secret" not in str(caught.value)
    assert "nested-customer-token" not in str(caught.value)


def test_multiple_chat_choices_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = chat_payload()
    payload["choices"].append(payload["choices"][0])
    patch_response(monkeypatch, payload)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError):
        provider.generate(make_request())


def test_oversized_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAIChatProvider(
        api_key="test-key",
        max_response_bytes=1024,
    )
    patch_response(
        monkeypatch,
        b"x" * 2048,
    )

    with pytest.raises(ProviderResponseInvalidError):
        provider.generate(make_request())


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        (400, ProviderCallFailedError),
        (401, ProviderCallFailedError),
        (403, ProviderCallFailedError),
        (408, ProviderUnavailableError),
        (429, ProviderUnavailableError),
        (500, ProviderUnavailableError),
        (503, ProviderUnavailableError),
    ],
)
def test_http_errors_are_sanitized_and_classified(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    expected_error: type[Exception],
) -> None:
    def fake_open(request, *, timeout):
        raise HTTPError(
            request.full_url,
            status,
            "upstream token=private-detail",
            Message(),
            BytesIO(b"secret response body"),
        )

    monkeypatch.setattr(adapter_base, "_open_url", fake_open)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(expected_error) as caught:
        provider.generate(make_request())

    assert "private-detail" not in str(caught.value)
    assert "secret response body" not in str(caught.value)


def test_transport_failure_is_sanitized_and_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_open(request, *, timeout):
        nonlocal calls
        calls += 1
        raise URLError("authorization=private-detail")

    monkeypatch.setattr(adapter_base, "_open_url", fake_open)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderUnavailableError) as caught:
        provider.generate(make_request())

    assert calls == 1
    assert "private-detail" not in str(caught.value)


def test_embedding_response_preserves_configured_model_and_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = patch_response(
        monkeypatch,
        {
            "object": "list",
            "data": [
                {
                    "index": 0,
                    "embedding": [0.1, -0.2, 0.3],
                }
            ],
            "model": "text-embedding-3-small",
            "usage": {
                "prompt_tokens": 5,
                "total_tokens": 5,
            },
        },
        headers={"x-request-id": "req-embedding-1"},
    )
    provider = OpenAIChatProvider(api_key="test-key")
    request = ProviderEmbeddingRequest(
        request_id="embedding-request-1",
        model_id="text-embedding-3-small",
        text="A two-bedroom property in Pune.",
    )

    response = provider.embed(request)

    assert response.model_id == "text-embedding-3-small"
    assert response.model_version == "text-embedding-3-small"
    assert response.vector == (0.1, -0.2, 0.3)
    assert response.provider_request_id == "req-embedding-1"
    assert captured["url"] == "https://api.openai.com/v1/embeddings"
    assert captured["body"]["encoding_format"] == "float"
    assert captured["body"]["input"] == request.text


@pytest.mark.parametrize(
    "invalid_value",
    (float("nan"), float("inf"), float("-inf")),
)
def test_invalid_embedding_vector_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    invalid_value: float,
) -> None:
    patch_response(
        monkeypatch,
        {
            "data": [
                {
                    "index": 0,
                    "embedding": [0.1, invalid_value],
                }
            ],
            "model": "text-embedding-3-small",
        },
    )
    provider = OpenAIChatProvider(api_key="test-key")
    request = ProviderEmbeddingRequest(
        request_id="embedding-request-2",
        model_id="text-embedding-3-small",
        text="A property search query.",
    )

    with pytest.raises(ProviderResponseInvalidError):
        provider.embed(request)


def test_invalid_embedding_response_index_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_response(
        monkeypatch,
        {
            "data": [
                {
                    "index": 1,
                    "embedding": [0.1, 0.2],
                }
            ],
            "model": "text-embedding-3-small",
        },
    )
    provider = OpenAIChatProvider(api_key="test-key")
    request = ProviderEmbeddingRequest(
        request_id="embedding-request-3",
        model_id="text-embedding-3-small",
        text="A property search query.",
    )

    with pytest.raises(ProviderResponseInvalidError):
        provider.embed(request)


def test_missing_usage_metadata_remains_explicitly_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = chat_payload()
    payload.pop("usage", None)
    patch_response(monkeypatch, payload)
    provider = OpenAIChatProvider(api_key="test-key")

    response = provider.generate(make_request())

    assert response.text == "Two bedroom properties are available for review."
    assert response.usage is None


@pytest.mark.parametrize(
    "usage",
    (
        [],
        {"prompt_tokens": True, "completion_tokens": 1},
        {"prompt_tokens": -1, "completion_tokens": 1},
        {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 99,
        },
    ),
)
def test_malformed_or_conflicting_usage_metadata_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    usage: object,
) -> None:
    payload = chat_payload()
    payload["usage"] = usage
    patch_response(monkeypatch, payload)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderResponseInvalidError):
        provider.generate(make_request())


def test_provider_timeout_is_sanitized_and_never_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_open(request, *, timeout):
        nonlocal calls
        calls += 1
        raise TimeoutError("api_key=private-timeout-detail")

    monkeypatch.setattr(adapter_base, "_open_url", fake_open)
    provider = OpenAIChatProvider(api_key="test-key")

    with pytest.raises(ProviderUnavailableError) as caught:
        provider.generate(make_request())

    assert calls == 1
    assert "private-timeout-detail" not in str(caught.value)
