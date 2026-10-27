from __future__ import annotations

import logging

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AIRequest,
    AuthorizationDecision,
    ModelRoute,
    ObservabilityEvent,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    RequestContext,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    ModelResolutionError,
    ObservabilityUnavailableError,
    ProviderCallFailedError,
    ProviderUnavailableError,
)
from AUTONOMY_ENGINE.ai_platform.model_gateway import ModelGateway
from AUTONOMY_ENGINE.ai_platform.observability import (
    StructuredLoggingObservability,
)
from AUTONOMY_ENGINE.ai_platform.settings import GatewaySettings


PRIMARY = ModelRoute(
    "provider-primary",
    "model-primary",
    max_input_chars=200,
    max_output_tokens=64,
)

FALLBACK = ModelRoute(
    "provider-fallback",
    "model-fallback",
    max_input_chars=200,
    max_output_tokens=32,
)


class FakeRegistry:
    def __init__(self) -> None:
        self.routes = {
            PRIMARY.model_id: PRIMARY,
            FALLBACK.model_id: FALLBACK,
        }
        self.calls: list[str] = []

    def resolve(self, model_id: str) -> ModelRoute:
        self.calls.append(model_id)
        try:
            return self.routes[model_id]
        except KeyError:
            raise ModelResolutionError() from None


class FakeProvider:
    def __init__(
        self,
        response: ProviderResponse,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.requests: list[ProviderRequest] = []

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class FakeProviderResolver:
    def __init__(self, providers: dict[str, object]) -> None:
        self.providers = providers
        self.calls: list[str] = []

    def get(self, provider_id: str):
        self.calls.append(provider_id)
        return self.providers.get(provider_id)


class FakeAuthorization:
    def __init__(self) -> None:
        self.calls: list[tuple[RequestContext, str]] = []

    def authorize_request(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        self.calls.append((context, operation))
        return AuthorizationDecision(True, "decision-1", "ALLOW")


class FakeUsageControl:
    def __init__(self) -> None:
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
        self.reservations.append(request)
        return UsageReservation(
            f"reservation-{len(self.reservations)}",
            request.request_id,
            request.tenant_id,
            request.model_id,
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
        self.settlements.append(
            (reservation, outcome, usage, provider_id, model_id)
        )

    def release(
        self,
        reservation: UsageReservation,
        *,
        reason_code: str,
    ) -> None:
        self.releases.append((reservation, reason_code))


class FakeObservability:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.events: list[ObservabilityEvent] = []
        self.fail_on = fail_on

    def emit(self, event: ObservabilityEvent) -> None:
        if event.event_name == self.fail_on:
            raise RuntimeError("logging sink contains private details")
        self.events.append(event)


def make_request(*, model_id: str | None = None) -> AIRequest:
    return AIRequest(
        request_id="request-1",
        operation="property.search",
        input_text="Find a two bedroom apartment.",
        context=RequestContext(
            "user-1",
            "tenant-1",
            "auth-context-1",
            "correlation-1",
        ),
        model_id=model_id,
    )


def make_gateway(
    *,
    providers: dict[str, object],
    observer: FakeObservability | None = None,
):
    registry = FakeRegistry()
    resolver = FakeProviderResolver(providers)
    authorization = FakeAuthorization()
    usage = FakeUsageControl()
    observability = observer or FakeObservability()

    gateway = ModelGateway(
        settings=GatewaySettings(
            enabled=True,
            default_model_id=PRIMARY.model_id,
            max_input_chars=200,
            max_output_tokens=64,
            max_output_chars=1000,
            fallback_model_ids=(FALLBACK.model_id,),
        ),
        model_registry=registry,
        provider_resolver=resolver,
        authorization=authorization,
        usage_control=usage,
        observability=observability,
    )

    return gateway, resolver, authorization, usage, observability


def fallback_provider() -> FakeProvider:
    return FakeProvider(
        ProviderResponse(
            "Safe fallback result.",
            FALLBACK.provider_id,
            FALLBACK.model_id,
            usage=ProviderUsage(
                input_tokens=8,
                output_tokens=5,
                total_tokens=13,
            ),
        )
    )


def test_configured_fallback_is_used_when_primary_is_unavailable() -> None:
    secondary = fallback_provider()
    gateway, resolver, auth, usage, observer = make_gateway(
        providers={FALLBACK.provider_id: secondary}
    )

    result = gateway.complete(make_request())

    assert result.text == "Safe fallback result."
    assert result.model_id == FALLBACK.model_id
    assert result.provider_id == FALLBACK.provider_id
    assert len(auth.calls) == 1

    assert resolver.calls == [
        PRIMARY.provider_id,
        FALLBACK.provider_id,
    ]
    assert len(usage.reservations) == 1
    assert usage.reservations[0].model_id == FALLBACK.model_id
    assert usage.reservations[0].max_output_tokens == FALLBACK.max_output_tokens
    assert usage.settlements[0][1] is UsageOutcome.SUCCEEDED
    assert usage.releases == []

    assert [event.event_name for event in observer.events] == [
        "MODEL_FALLBACK_SELECTED",
        "REQUEST_ACCEPTED",
        "REQUEST_COMPLETED",
    ]


def test_explicit_model_choice_is_not_silently_changed() -> None:
    secondary = fallback_provider()
    gateway, resolver, _, usage, observer = make_gateway(
        providers={FALLBACK.provider_id: secondary}
    )

    with pytest.raises(ProviderUnavailableError):
        gateway.complete(make_request(model_id=PRIMARY.model_id))

    assert secondary.requests == []
    assert resolver.calls == [PRIMARY.provider_id]
    assert len(usage.reservations) == 1
    assert usage.reservations[0].model_id == PRIMARY.model_id
    assert usage.releases[0][1] == "AI_PROVIDER_UNAVAILABLE"
    assert all(
        event.event_name != "MODEL_FALLBACK_SELECTED"
        for event in observer.events
    )


def test_fallback_telemetry_failure_blocks_reservation_and_provider_call() -> None:
    secondary = fallback_provider()
    observer = FakeObservability(fail_on="MODEL_FALLBACK_SELECTED")
    gateway, _, _, usage, _ = make_gateway(
        providers={FALLBACK.provider_id: secondary},
        observer=observer,
    )

    with pytest.raises(ObservabilityUnavailableError):
        gateway.complete(make_request())

    assert usage.reservations == []
    assert usage.settlements == []
    assert usage.releases == []
    assert secondary.requests == []


def test_ambiguous_primary_provider_failure_is_not_retried() -> None:
    primary = FakeProvider(
        ProviderResponse(
            "Not used",
            PRIMARY.provider_id,
            PRIMARY.model_id,
        ),
        error=RuntimeError("provider timeout; api_key=private-value"),
    )
    secondary = fallback_provider()
    gateway, _, _, usage, _ = make_gateway(
        providers={
            PRIMARY.provider_id: primary,
            FALLBACK.provider_id: secondary,
        }
    )

    with pytest.raises(ProviderCallFailedError) as exc:
        gateway.complete(make_request())

    assert "private-value" not in str(exc.value)
    assert len(primary.requests) == 1
    assert secondary.requests == []
    assert usage.releases == []
    assert usage.settlements[0][1] is UsageOutcome.FAILED
    assert usage.settlements[0][2] is None


def test_structured_logging_adapter_emits_only_allowlisted_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("homio.test.observability")
    adapter = StructuredLoggingObservability(logger)

    event = ObservabilityEvent(
        event_name="REQUEST_COMPLETED",
        request_id="request-1",
        correlation_id="correlation-1",
        outcome="SUCCEEDED",
        provider_id=PRIMARY.provider_id,
        model_id=PRIMARY.model_id,
        duration_ms=12,
    )

    with caplog.at_level(logging.INFO, logger="homio.test.observability"):
        adapter.emit(event)

    record = next(
        record
        for record in reversed(caplog.records)
        if record.name == "homio.test.observability"
    )

    assert record.getMessage() == "homio_ai_event"
    assert record.homio_ai_event == {
        "event_name": "REQUEST_COMPLETED",
        "request_id": "request-1",
        "correlation_id": "correlation-1",
        "outcome": "SUCCEEDED",
        "provider_id": PRIMARY.provider_id,
        "model_id": PRIMARY.model_id,
        "duration_ms": 12,
        "error_code": None,
    }
    assert "prompt" not in record.homio_ai_event
    assert "api_key" not in record.homio_ai_event


def test_structured_logging_adapter_rejects_untyped_events() -> None:
    adapter = StructuredLoggingObservability()

    with pytest.raises(TypeError):
        adapter.emit("not-an-event")  # type: ignore[arg-type]
