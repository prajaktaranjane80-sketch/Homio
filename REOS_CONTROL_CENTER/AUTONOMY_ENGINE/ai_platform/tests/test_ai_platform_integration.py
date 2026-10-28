from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AIRequest,
    AuthorizationDecision,
    ObservabilityEvent,
    ProviderUsage,
    RequestContext,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    AuthorizationDeniedError,
    GatewayDisabledError,
    ProviderCallFailedError,
)
from AUTONOMY_ENGINE.ai_platform.provider_adapters import (
    OpenAIChatProvider,
    VLLMChatProvider,
)
from AUTONOMY_ENGINE.ai_platform.provider_adapters import base as adapter_base
from AUTONOMY_ENGINE.ai_platform.server_composition import (
    AICompositionConfigurationError,
    build_model_gateway_from_environment,
)


class FakeHTTPResponse:
    """Deterministic HTTP response for provider integration tests."""

    def __init__(
        self,
        payload: dict[str, object],
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status
        self.headers = headers or {}
        self.closed = False

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def read(self, amount: int = -1) -> bytes:
        if amount < 0:
            return self._body
        return self._body[:amount]

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        self.closed = True


class FakeAuthorization:
    """Injected server-owned authorization boundary."""

    def __init__(
        self,
        *,
        allowed: bool = True,
        sequence: list[str] | None = None,
    ) -> None:
        self.allowed = allowed
        self.sequence = sequence
        self.calls: list[tuple[RequestContext, str]] = []

    def authorize_request(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        self.calls.append((context, operation))

        if self.sequence is not None:
            self.sequence.append("authorize")

        return AuthorizationDecision(
            allowed=self.allowed,
            decision_id="decision-1",
            reason_code="ALLOW" if self.allowed else "DENY",
        )


class FakeUsageControl:
    """Recording usage-control port for testing gateway wiring."""

    def __init__(
        self,
        *,
        sequence: list[str] | None = None,
    ) -> None:
        self.sequence = sequence
        self.reservations: list[UsageReservationRequest] = []
        self.settlements: list[
            tuple[
                UsageReservation,
                UsageOutcome,
                ProviderUsage | None,
                str,
                str,
            ]
        ] = []
        self.releases: list[tuple[UsageReservation, str]] = []

    def reserve(
        self,
        request: UsageReservationRequest,
    ) -> UsageReservation:
        if self.sequence is not None:
            self.sequence.append("reserve")

        self.reservations.append(request)

        return UsageReservation(
            reservation_id=f"reservation-{len(self.reservations)}",
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            model_id=request.model_id,
        )

    def settle(
        self,
        reservation: UsageReservation,
        *,
        outcome: UsageOutcome,
        usage: ProviderUsage | None,
        provider_id: str,
        model_id: str,
    ) -> None:
        if self.sequence is not None:
            self.sequence.append(f"settle:{outcome.value}")

        self.settlements.append(
            (reservation, outcome, usage, provider_id, model_id)
        )

    def release(
        self,
        reservation: UsageReservation,
        *,
        reason_code: str,
    ) -> None:
        if self.sequence is not None:
            self.sequence.append(f"release:{reason_code}")

        self.releases.append((reservation, reason_code))


class FakeObservability:
    """Recording redacted-event sink for testing gateway wiring."""

    def __init__(
        self,
        *,
        sequence: list[str] | None = None,
    ) -> None:
        self.sequence = sequence
        self.events: list[ObservabilityEvent] = []

    def emit(self, event: ObservabilityEvent) -> None:
        self.events.append(event)

        if self.sequence is not None:
            self.sequence.append(f"observe:{event.event_name}")


def dependencies(
    *,
    allowed: bool = True,
    sequence: list[str] | None = None,
) -> dict[str, object]:
    return {
        "authorization": FakeAuthorization(
            allowed=allowed,
            sequence=sequence,
        ),
        "usage_control": FakeUsageControl(sequence=sequence),
        "observability": FakeObservability(sequence=sequence),
    }


def openai_environment() -> dict[str, str]:
    return {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "gpt-test-model",
        "HOMIO_AI_OPENAI_API_KEY": "test-secret-do-not-log",
        "HOMIO_AI_OPENAI_MODEL_ID": "gpt-test-model",
    }


def build(environ: dict[str, str]):
    return build_model_gateway_from_environment(
        **dependencies(),
        environ=environ,
    )


def make_ai_request() -> AIRequest:
    """Build a request using a server-derived test identity context."""

    return AIRequest(
        request_id="request-1",
        operation="property.search",
        input_text="Find two bedroom apartments in Pune.",
        context=RequestContext(
            principal_id="user-1",
            tenant_id="tenant-pune",
            authentication_context_ref="auth-context-1",
            correlation_id="correlation-1",
        ),
        max_output_tokens=32,
        idempotency_key="idem-1",
    )


def provider_success_payload() -> dict[str, object]:
    return {
        "id": "chatcmpl-integration-test",
        "model": "gpt-test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Property search completed safely.",
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


def test_ai_gateway_stays_disabled_without_explicit_opt_in() -> None:
    with pytest.raises(GatewayDisabledError):
        build({})


def test_ai_gateway_stays_disabled_when_explicitly_false() -> None:
    with pytest.raises(GatewayDisabledError):
        build({"HOMIO_AI_ENABLED": "false"})


def test_openai_provider_is_registered_without_network_activity() -> None:
    gateway = build(openai_environment())

    assert gateway._settings.enabled is True
    assert gateway._settings.default_model_id == "gpt-test-model"
    assert gateway._model_registry.model_ids == ("gpt-test-model",)
    assert (
        gateway._model_registry.resolve("gpt-test-model").provider_id
        == "openai"
    )

    provider = gateway._provider_resolver.get("openai")

    assert isinstance(provider, OpenAIChatProvider)
    assert "test-secret-do-not-log" not in repr(provider)


def test_provider_key_without_model_id_is_rejected() -> None:
    environ = openai_environment()
    environ.pop("HOMIO_AI_OPENAI_MODEL_ID")

    with pytest.raises(
        AICompositionConfigurationError,
        match="both its server API key and model ID",
    ):
        build(environ)


def test_model_id_without_provider_key_is_rejected() -> None:
    environ = openai_environment()
    environ.pop("HOMIO_AI_OPENAI_API_KEY")

    with pytest.raises(
        AICompositionConfigurationError,
        match="both its server API key and model ID",
    ):
        build(environ)


def test_unknown_default_model_is_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_DEFAULT_MODEL_ID"] = "unconfigured-model"

    with pytest.raises(
        AICompositionConfigurationError,
        match="must match a configured model ID",
    ):
        build(environ)


def test_unknown_fallback_model_is_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = "not-configured"

    with pytest.raises(
        AICompositionConfigurationError,
        match="Every fallback model must be explicitly configured",
    ):
        build(environ)


def test_duplicate_fallback_models_are_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = (
        "gpt-test-model,gpt-test-model"
    )

    with pytest.raises(
        AICompositionConfigurationError,
        match="contains duplicates",
    ):
        build(environ)


def test_default_model_cannot_also_be_fallback() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = "gpt-test-model"

    with pytest.raises(
        AICompositionConfigurationError,
        match="default model cannot also be a fallback",
    ):
        build(environ)


def test_invalid_enable_flag_fails_closed() -> None:
    with pytest.raises(
        AICompositionConfigurationError,
        match="must be explicitly set",
    ):
        build({"HOMIO_AI_ENABLED": "yes"})


def test_provider_credentials_are_not_enough_to_enable_ai() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_ENABLED"] = "false"

    with pytest.raises(GatewayDisabledError):
        build(environ)


def test_incomplete_vllm_configuration_is_rejected() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "https://vllm.internal/v1",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    with pytest.raises(
        AICompositionConfigurationError,
        match="endpoint, API key and model ID",
    ):
        build(environ)


def test_vllm_http_endpoint_is_rejected() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "http://vllm.internal/v1",
        "HOMIO_AI_VLLM_API_KEY": "test-vllm-secret",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    with pytest.raises(
        AICompositionConfigurationError,
        match="vLLM provider configuration is invalid",
    ):
        build(environ)


def test_vllm_provider_is_registered_without_network_activity() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "https://vllm.internal/v1",
        "HOMIO_AI_VLLM_API_KEY": "test-vllm-secret",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    gateway = build(environ)

    assert gateway._model_registry.model_ids == ("local-test-model",)
    assert (
        gateway._model_registry.resolve("local-test-model").provider_id
        == "vllm"
    )

    provider = gateway._provider_resolver.get("vllm")

    assert isinstance(provider, VLLMChatProvider)
    assert "test-vllm-secret" not in repr(provider)


def test_missing_authorization_dependency_fails_closed() -> None:
    with pytest.raises(
        AICompositionConfigurationError,
        match="authorization dependency",
    ):
        build_model_gateway_from_environment(
            authorization=object(),
            usage_control=FakeUsageControl(),
            observability=FakeObservability(),
            environ=openai_environment(),
        )


def test_invalid_token_limit_fails_closed() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_MAX_OUTPUT_TOKENS"] = "0"

    with pytest.raises(
        AICompositionConfigurationError,
        match="outside its permitted range",
    ):
        build(environ)


def test_composed_gateway_completes_request_and_settles_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise composition -> gateway -> adapter -> usage and telemetry."""

    sequence: list[str] = []
    captured: dict[str, object] = {}

    def fake_open(request, *, timeout):
        sequence.append("provider-call")
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout

        return FakeHTTPResponse(
            provider_success_payload(),
            headers={"x-request-id": "provider-request-1"},
        )

    monkeypatch.setattr(adapter_base, "_open_url", fake_open)

    auth = FakeAuthorization(sequence=sequence)
    usage = FakeUsageControl(sequence=sequence)
    observability = FakeObservability(sequence=sequence)

    gateway = build_model_gateway_from_environment(
        authorization=auth,
        usage_control=usage,
        observability=observability,
        environ=openai_environment(),
    )

    request = make_ai_request()
    response = gateway.complete(request)

    assert response.text == "Property search completed safely."
    assert response.provider_id == "openai"
    assert response.model_id == "gpt-test-model"
    assert response.request_id == request.request_id
    assert response.correlation_id == request.context.correlation_id
    assert response.usage is not None
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 8
    assert response.usage.total_tokens == 20

    assert len(auth.calls) == 1
    assert auth.calls[0] == (request.context, "property.search")

    assert len(usage.reservations) == 1
    reservation_request = usage.reservations[0]
    assert reservation_request.request_id == request.request_id
    assert reservation_request.tenant_id == "tenant-pune"
    assert reservation_request.model_id == "gpt-test-model"
    assert reservation_request.idempotency_key == "idem-1"

    assert len(usage.settlements) == 1
    _, outcome, settled_usage, provider_id, model_id = usage.settlements[0]
    assert outcome is UsageOutcome.SUCCEEDED
    assert settled_usage == response.usage
    assert provider_id == "openai"
    assert model_id == "gpt-test-model"
    assert usage.releases == []

    assert captured["url"] == (
        "https://api.openai.com/v1/chat/completions"
    )
    assert captured["method"] == "POST"
    assert captured["timeout"] == 30.0

    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer test-secret-do-not-log"

    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "gpt-test-model"
    assert body["max_completion_tokens"] == 32
    assert body["stream"] is False
    assert body["messages"] == [
        {
            "role": "user",
            "content": "Find two bedroom apartments in Pune.",
        }
    ]

    # Identity and tenant context must remain inside HOMIO's trusted boundary.
    assert "tenant_id" not in body
    assert "principal_id" not in body
    assert "authentication_context_ref" not in body
    assert "correlation_id" not in body

    assert [
        event.event_name for event in observability.events
    ] == [
        "REQUEST_ACCEPTED",
        "REQUEST_COMPLETED",
    ]

    # Verify security and accounting controls run before provider execution.
    assert sequence == [
        "authorize",
        "reserve",
        "observe:REQUEST_ACCEPTED",
        "provider-call",
        "settle:SUCCEEDED",
        "observe:REQUEST_COMPLETED",
    ]


def test_composed_gateway_denial_prevents_provider_call_and_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A denied business operation must never reach the provider."""

    provider_calls: list[str] = []
    sequence: list[str] = []

    def unexpected_provider_call(request, *, timeout):
        provider_calls.append(request.full_url)
        raise AssertionError("Denied requests must not reach the provider")

    monkeypatch.setattr(
        adapter_base,
        "_open_url",
        unexpected_provider_call,
    )

    auth = FakeAuthorization(
        allowed=False,
        sequence=sequence,
    )
    usage = FakeUsageControl(sequence=sequence)
    observability = FakeObservability(sequence=sequence)

    gateway = build_model_gateway_from_environment(
        authorization=auth,
        usage_control=usage,
        observability=observability,
        environ=openai_environment(),
    )

    with pytest.raises(AuthorizationDeniedError):
        gateway.complete(make_ai_request())

    assert len(auth.calls) == 1
    assert usage.reservations == []
    assert usage.settlements == []
    assert usage.releases == []
    assert provider_calls == []

    assert [
        event.event_name for event in observability.events
    ] == ["AUTHORIZATION_DENIED"]

    assert sequence == [
        "authorize",
        "observe:AUTHORIZATION_DENIED",
    ]


def test_composed_gateway_accounts_for_ambiguous_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An uncertain provider outcome is settled as failed, never retried."""

    sequence: list[str] = []
    provider_calls: list[str] = []

    def failed_provider_call(request, *, timeout):
        provider_calls.append(request.full_url)
        sequence.append("provider-call")
        raise URLError("simulated private transport detail")

    monkeypatch.setattr(
        adapter_base,
        "_open_url",
        failed_provider_call,
    )

    auth = FakeAuthorization(sequence=sequence)
    usage = FakeUsageControl(sequence=sequence)
    observability = FakeObservability(sequence=sequence)

    gateway = build_model_gateway_from_environment(
        authorization=auth,
        usage_control=usage,
        observability=observability,
        environ=openai_environment(),
    )

    with pytest.raises(ProviderCallFailedError) as caught:
        gateway.complete(make_ai_request())

    assert "simulated private transport detail" not in str(caught.value)

    # One attempted request only: no hidden retry after an uncertain outcome.
    assert len(provider_calls) == 1

    assert len(usage.reservations) == 1
    assert len(usage.settlements) == 1

    _, outcome, settled_usage, provider_id, model_id = usage.settlements[0]
    assert outcome is UsageOutcome.FAILED
    assert settled_usage is None
    assert provider_id == "openai"
    assert model_id == "gpt-test-model"

    # Once a provider call was attempted, an ambiguous reservation must not
    # be released as if no provider cost could have occurred.
    assert usage.releases == []

    assert [
        event.event_name for event in observability.events
    ] == [
        "REQUEST_ACCEPTED",
        "REQUEST_FAILED",
    ]

    assert sequence == [
        "authorize",
        "reserve",
        "observe:REQUEST_ACCEPTED",
        "provider-call",
        "settle:FAILED",
        "observe:REQUEST_FAILED",
    ]
