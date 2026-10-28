
from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AIRequest,
    AuthorizationDecision,
    ModelRoute,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    RequestContext,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    AuthorizationDeniedError,
    GatewayDisabledError,
    InvalidRequestError,
    ModelResolutionError,
    ObservabilityUnavailableError,
    ProviderCallFailedError,
    ProviderResponseInvalidError,
    ProviderUnavailableError,
    RequestContextMissingError,
    UsageControlUnavailableError,
    UsageLimitExceededError,
)
from AUTONOMY_ENGINE.ai_platform.model_gateway import ModelGateway
from AUTONOMY_ENGINE.ai_platform.settings import GatewaySettings


ROUTE = ModelRoute(
    "provider-a",
    "model-a",
    max_input_chars=100,
    max_output_tokens=200,
)


class FakeRegistry:
    def __init__(
        self,
        route: ModelRoute = ROUTE,
        error: Exception | None = None,
    ) -> None:
        self.route = route
        self.error = error
        self.calls: list[str] = []

    def resolve(self, model_id: str) -> ModelRoute:
        self.calls.append(model_id)
        if self.error:
            raise self.error
        if model_id not in {self.route.model_id, "alias-a"}:
            raise ModelResolutionError()
        return self.route


class FakeProvider:
    def __init__(
        self,
        response: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or ProviderResponse(
            "Matches are available.",
            "provider-a",
            "model-a",
            usage=ProviderUsage(
                input_tokens=8,
                output_tokens=5,
                total_tokens=13,
            ),
        )
        self.error = error
        self.requests: list[ProviderRequest] = []

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response  # type: ignore[return-value]


class FakeProviderResolver:
    def __init__(self, provider: FakeProvider | None) -> None:
        self.provider = provider
        self.calls: list[str] = []

    def get(self, provider_id: str) -> FakeProvider | None:
        self.calls.append(provider_id)
        return self.provider


class FakeAuthorization:
    def __init__(
        self,
        decision: AuthorizationDecision | None = None,
        error: Exception | None = None,
    ) -> None:
        self.decision = decision or AuthorizationDecision(
            True,
            "decision-1",
            "ALLOW",
        )
        self.error = error
        self.calls: list[tuple[RequestContext, str]] = []

    def authorize_request(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        self.calls.append((context, operation))
        if self.error:
            raise self.error
        return self.decision


class FakeUsageControl:
    def __init__(
        self,
        reserve_error: Exception | None = None,
        settle_error: Exception | None = None,
    ) -> None:
        self.reserve_error = reserve_error
        self.settle_error = settle_error
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
        if self.reserve_error:
            raise self.reserve_error

        return UsageReservation(
            "reservation-1",
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
        if self.settle_error:
            raise self.settle_error

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
    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.events = []

    def emit(self, event) -> None:
        if event.event_name == self.fail_on:
            raise RuntimeError("telemetry token=private-value")
        self.events.append(event)


def make_gateway(
    *,
    enabled: bool = True,
    route: ModelRoute = ROUTE,
    provider: FakeProvider | None = None,
    registry_error: Exception | None = None,
    auth_decision: AuthorizationDecision | None = None,
    auth_error: Exception | None = None,
    reserve_error: Exception | None = None,
    settle_error: Exception | None = None,
    observability_fail_on: str | None = None,
):
    registry = FakeRegistry(route, registry_error)
    provider = provider or FakeProvider()
    provider_resolver = FakeProviderResolver(provider)
    authorization = FakeAuthorization(auth_decision, auth_error)
    usage = FakeUsageControl(reserve_error, settle_error)
    observer = FakeObservability(observability_fail_on)

    gateway = ModelGateway(
        settings=GatewaySettings(
            enabled=enabled,
            default_model_id="model-a",
            max_input_chars=100,
            max_output_tokens=100,
            max_output_chars=24_000,
        ),
        model_registry=registry,
        provider_resolver=provider_resolver,
        authorization=authorization,
        usage_control=usage,
        observability=observer,
    )
    return (
        gateway,
        registry,
        provider,
        provider_resolver,
        authorization,
        usage,
        observer,
    )


def make_request(
    *,
    context: RequestContext | None = None,
    **kwargs,
) -> AIRequest:
    return AIRequest(
        request_id="request-1",
        operation="property.search",
        input_text="Find a two bedroom apartment.",
        context=context
        if context is not None
        else RequestContext(
            "user-1",
            "tenant-1",
            "auth-context-1",
            "trace-1",
        ),
        **kwargs,
    )


def test_success_routes_through_policy_usage_provider_and_observability() -> None:
    gateway, registry, provider, resolver, auth, usage, observer = make_gateway()
    result = gateway.complete(make_request())

    assert result.text == "Matches are available."
    assert result.provider_id == "provider-a"
    assert result.model_id == "model-a"
    assert registry.calls == ["model-a"]
    assert resolver.calls == ["provider-a"]
    assert len(auth.calls) == 1
    assert usage.reservations[0].tenant_id == "tenant-1"
    assert usage.settlements[0][1] is UsageOutcome.SUCCEEDED
    assert usage.releases == []
    assert [event.event_name for event in observer.events] == [
        "REQUEST_ACCEPTED",
        "REQUEST_COMPLETED",
    ]

    provider_request = provider.requests[0]
    assert provider_request.prompt == "Find a two bedroom apartment."
    assert not hasattr(provider_request, "tenant_id")


def test_gateway_is_disabled_by_default_and_never_contacts_dependencies() -> None:
    gateway, registry, provider, resolver, auth, usage, observer = make_gateway(
        enabled=False
    )

    with pytest.raises(GatewayDisabledError):
        gateway.complete(make_request())

    assert registry.calls == []
    assert provider.requests == []
    assert auth.calls == []
    assert usage.reservations == []


def test_missing_context_fails_before_authorization_or_provider() -> None:
    gateway, _, provider, _, auth, usage, _ = make_gateway()
    request = AIRequest("request-1", "property.search", "hello", None)

    with pytest.raises(RequestContextMissingError):
        gateway.complete(request)

    assert auth.calls == []
    assert provider.requests == []
    assert usage.reservations == []


def test_authorization_denial_prevents_reservation_and_provider_call() -> None:
    gateway, _, provider, _, _, usage, observer = make_gateway(
        auth_decision=AuthorizationDecision(
            False,
            "decision-2",
            "DENY",
        )
    )

    with pytest.raises(AuthorizationDeniedError):
        gateway.complete(make_request())

    assert usage.reservations == []
    assert provider.requests == []
    assert observer.events[0].event_name == "AUTHORIZATION_DENIED"


def test_authorization_dependency_failure_fails_closed() -> None:
    from AUTONOMY_ENGINE.ai_platform.errors import (
        AuthorizationServiceUnavailableError,
    )

    gateway, _, provider, _, _, usage, _ = make_gateway(
        auth_error=RuntimeError("private details")
    )

    with pytest.raises(AuthorizationServiceUnavailableError) as exc:
        gateway.complete(make_request())

    assert "private details" not in str(exc.value)
    assert usage.reservations == []
    assert provider.requests == []


def test_input_exceeding_route_limit_is_rejected_before_provider() -> None:
    small_route = ModelRoute(
        "provider-a",
        "model-a",
        max_input_chars=5,
        max_output_tokens=100,
    )
    gateway, _, provider, _, _, usage, _ = make_gateway(route=small_route)

    with pytest.raises(InvalidRequestError):
        gateway.complete(make_request())

    assert usage.reservations == []
    assert provider.requests == []


def test_requested_output_limit_cannot_exceed_configured_or_model_limit() -> None:
    gateway, _, provider, _, _, usage, _ = make_gateway()

    with pytest.raises(InvalidRequestError):
        gateway.complete(make_request(max_output_tokens=101))

    assert usage.reservations == []
    assert provider.requests == []


def test_unknown_model_fails_closed_before_auth_and_provider() -> None:
    gateway, _, provider, _, auth, usage, _ = make_gateway()

    with pytest.raises(ModelResolutionError):
        gateway.complete(make_request(model_id="unknown-model"))

    assert auth.calls == []
    assert usage.reservations == []
    assert provider.requests == []


def test_unavailable_provider_releases_reservation() -> None:
    gateway, _, _, resolver, _, usage, _ = make_gateway()
    resolver.provider = None

    with pytest.raises(ProviderUnavailableError):
        gateway.complete(make_request())

    assert usage.releases[0][1] == "AI_PROVIDER_UNAVAILABLE"


def test_provider_exception_is_sanitized_and_failure_is_accounted() -> None:
    provider = FakeProvider(
        error=RuntimeError("api_key=private-value")
    )
    gateway, _, _, _, _, usage, _ = make_gateway(provider=provider)

    with pytest.raises(ProviderCallFailedError) as exc:
        gateway.complete(make_request())

    assert "private-value" not in str(exc.value)
    assert usage.releases == []
    assert usage.settlements[0][1] is UsageOutcome.FAILED
    assert usage.settlements[0][2] is None


def test_provider_must_return_the_configured_provider_and_model() -> None:
    bad_response = ProviderResponse("text", "other-provider", "model-a")
    gateway, _, _, _, _, usage, _ = make_gateway(
        provider=FakeProvider(response=bad_response)
    )

    with pytest.raises(ProviderResponseInvalidError):
        gateway.complete(make_request())

    assert usage.releases == []
    assert usage.settlements[0][1] is UsageOutcome.FAILED
    assert usage.settlements[0][2] is None


def test_provider_output_usage_cannot_exceed_reserved_output_tokens() -> None:
    too_large = ProviderResponse(
        "text",
        "provider-a",
        "model-a",
        usage=ProviderUsage(
            input_tokens=1,
            output_tokens=101,
            total_tokens=102,
        ),
    )
    gateway, _, _, _, _, usage, _ = make_gateway(
        provider=FakeProvider(response=too_large)
    )

    with pytest.raises(ProviderResponseInvalidError):
        gateway.complete(make_request())

    assert usage.releases == []
    assert usage.settlements[0][1] is UsageOutcome.FAILED
    assert usage.settlements[0][2] == too_large.usage


def test_configured_character_output_cap_is_enforced() -> None:
    registry = FakeRegistry()
    provider = FakeProvider(
        response=ProviderResponse(
            "text is too long",
            "provider-a",
            "model-a",
        )
    )
    resolver = FakeProviderResolver(provider)
    authorization = FakeAuthorization()
    usage = FakeUsageControl()
    observer = FakeObservability()

    gateway = ModelGateway(
        settings=GatewaySettings(
            enabled=True,
            default_model_id="model-a",
            max_input_chars=100,
            max_output_tokens=100,
            max_output_chars=5,
        ),
        model_registry=registry,
        provider_resolver=resolver,
        authorization=authorization,
        usage_control=usage,
        observability=observer,
    )

    with pytest.raises(ProviderResponseInvalidError):
        gateway.complete(make_request())

    assert usage.settlements[0][1] is UsageOutcome.FAILED


def test_usage_limit_denial_does_not_call_provider() -> None:
    gateway, _, provider, _, _, usage, _ = make_gateway(
        reserve_error=UsageLimitExceededError()
    )

    with pytest.raises(UsageLimitExceededError):
        gateway.complete(make_request())

    assert provider.requests == []
    assert usage.settlements == []


def test_required_start_event_failure_prevents_provider_and_releases_quota() -> None:
    gateway, _, provider, _, _, usage, _ = make_gateway(
        observability_fail_on="REQUEST_ACCEPTED"
    )

    with pytest.raises(ObservabilityUnavailableError):
        gateway.complete(make_request())

    assert provider.requests == []
    assert usage.releases[0][1] == "AI_OBSERVABILITY_UNAVAILABLE"


@pytest.mark.parametrize(
    ("settle_error", "private_detail"),
    (
        (RuntimeError("db secret"), "db secret"),
        (TimeoutError("settlement timeout secret"), "settlement timeout secret"),
    ),
)
def test_ambiguous_settlement_failure_is_not_followed_by_release(
    settle_error: Exception,
    private_detail: str,
) -> None:
    gateway, _, provider, _, _, usage, _ = make_gateway(
        settle_error=settle_error
    )

    with pytest.raises(UsageControlUnavailableError) as exc:
        gateway.complete(make_request())

    # A possibly committed settlement must never be followed by a release.
    # A timeout is as ambiguous as any other settlement failure.
    assert private_detail not in str(exc.value)
    assert len(provider.requests) == 1
    assert usage.releases == []
    assert usage.settlements == []
