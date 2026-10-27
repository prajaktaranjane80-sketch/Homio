"""Provider-independent, fail-closed HOMIO AI request gateway.

The gateway delegates model selection, authorization, usage accounting,
provider calls and observability to injected ports. Fallback is permitted
only from trusted server configuration and only before a provider request
has been attempted. An ambiguous provider failure is never automatically
retried because the first attempt may already have incurred cost or effects.
"""
from __future__ import annotations

from time import monotonic

from .contracts import (
    AIRequest,
    AIResponse,
    AuthorizationDecision,
    ModelRoute,
    ObservabilityEvent,
    ProviderRequest,
    ProviderResponse,
    RequestContext,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
)
from .errors import (
    AuthorizationDeniedError,
    AuthorizationServiceUnavailableError,
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
from .ports import (
    AuthorizationPort,
    ModelRegistryPort,
    ObservabilityPort,
    ProviderResolverPort,
    UsageControlPort,
)
from .settings import GatewaySettings


class ModelGateway:
    """Coordinate a single request without owning business data or permissions."""

    def __init__(
        self,
        *,
        settings: GatewaySettings,
        model_registry: ModelRegistryPort,
        provider_resolver: ProviderResolverPort,
        authorization: AuthorizationPort,
        usage_control: UsageControlPort,
        observability: ObservabilityPort,
    ) -> None:
        dependencies = {
            "settings": settings,
            "model_registry": model_registry,
            "provider_resolver": provider_resolver,
            "authorization": authorization,
            "usage_control": usage_control,
            "observability": observability,
        }
        missing = [
            name
            for name, value in dependencies.items()
            if value is None
        ]
        if missing:
            raise ValueError("Required AI gateway dependencies are missing")
        if not isinstance(settings, GatewaySettings):
            raise TypeError("settings must be GatewaySettings")

        self._settings = settings
        self._model_registry = model_registry
        self._provider_resolver = provider_resolver
        self._authorization = authorization
        self._usage_control = usage_control
        self._observability = observability

    def complete(self, request: AIRequest) -> AIResponse:
        """Complete one text request or raise a safe, classified platform error."""
        started = monotonic()

        if not self._settings.enabled:
            raise GatewayDisabledError()
        if not isinstance(request, AIRequest):
            raise InvalidRequestError()

        context = request.context
        if not isinstance(context, RequestContext):
            raise RequestContextMissingError()

        if len(request.input_text) > self._settings.max_input_chars:
            raise InvalidRequestError()

        selected_model = request.model_id or self._settings.default_model_id
        if not selected_model:
            raise ModelResolutionError()

        route = self._resolve_route(selected_model)
        output_tokens = self._validate_route_limits(
            request,
            route,
            requested_output_tokens=request.max_output_tokens,
        )

        decision = self._authorize(context, request.operation)
        if not decision.allowed:
            self._emit_best_effort(
                self._event(
                    request,
                    "AUTHORIZATION_DENIED",
                    "DENIED",
                    route=route,
                    error_code="AI_AUTHORIZATION_DENIED",
                    started=started,
                )
            )
            raise AuthorizationDeniedError()

        provider = None
        provider_preselected = False

        # Fallback candidates are a trusted server setting. An explicit
        # per-request model choice is honored as-is and is not silently changed.
        # The resolver is only queried here; no provider generation is attempted.
        if (
            self._settings.fallback_model_ids
            and request.model_id is None
        ):
            route, output_tokens, provider, used_fallback = (
                self._select_available_route(
                    request=request,
                    primary_route=route,
                    primary_output_tokens=output_tokens,
                    started=started,
                )
            )
            provider_preselected = True

            if used_fallback:
                # Required telemetry must succeed before quota reservation and
                # before any provider request is attempted.
                self._emit_required(
                    self._event(
                        request,
                        "MODEL_FALLBACK_SELECTED",
                        "FALLBACK_SELECTED",
                        route=route,
                        error_code="AI_PRIMARY_PROVIDER_UNAVAILABLE",
                        started=started,
                    )
                )

        reservation = self._reserve(
            request,
            context,
            route,
            output_tokens,
        )

        try:
            self._emit_required(
                self._event(
                    request,
                    "REQUEST_ACCEPTED",
                    "STARTED",
                    route=route,
                    started=started,
                )
            )
        except ObservabilityUnavailableError:
            self._release_best_effort(
                reservation,
                "AI_OBSERVABILITY_UNAVAILABLE",
            )
            raise

        if not provider_preselected:
            try:
                provider = self._provider_resolver.get(route.provider_id)
            except Exception:
                self._release_best_effort(
                    reservation,
                    "AI_PROVIDER_UNAVAILABLE",
                )
                self._emit_best_effort(
                    self._event(
                        request,
                        "REQUEST_FAILED",
                        "FAILED",
                        route=route,
                        error_code="AI_PROVIDER_UNAVAILABLE",
                        started=started,
                    )
                )
                raise ProviderUnavailableError() from None

        if provider is None or not callable(
            getattr(provider, "generate", None)
        ):
            self._release_best_effort(
                reservation,
                "AI_PROVIDER_UNAVAILABLE",
            )
            self._emit_best_effort(
                self._event(
                    request,
                    "REQUEST_FAILED",
                    "FAILED",
                    route=route,
                    error_code="AI_PROVIDER_UNAVAILABLE",
                    started=started,
                )
            )
            raise ProviderUnavailableError()

        provider_request = ProviderRequest(
            request_id=request.request_id,
            operation=request.operation,
            prompt=request.input_text,
            model_id=route.model_id,
            max_output_tokens=output_tokens,
            timeout_seconds=self._settings.request_timeout_seconds,
            idempotency_key=request.idempotency_key,
        )

        try:
            provider_response = provider.generate(provider_request)
        except Exception:
            # The request may have reached the provider before a timeout or
            # transport failure. Account as FAILED with unknown usage instead
            # of releasing the reservation or retrying an ambiguous call.
            self._settle_failed(
                reservation,
                route,
                usage=None,
            )
            self._emit_best_effort(
                self._event(
                    request,
                    "REQUEST_FAILED",
                    "FAILED",
                    route=route,
                    error_code="AI_PROVIDER_CALL_FAILED",
                    started=started,
                )
            )
            raise ProviderCallFailedError() from None

        try:
            self._validate_provider_response(
                provider_response,
                route=route,
                max_output_tokens=output_tokens,
            )
        except ProviderResponseInvalidError:
            reported_usage = (
                provider_response.usage
                if isinstance(provider_response, ProviderResponse)
                and provider_response.provider_id == route.provider_id
                and provider_response.model_id == route.model_id
                else None
            )
            self._settle_failed(
                reservation,
                route,
                usage=reported_usage,
            )
            self._emit_best_effort(
                self._event(
                    request,
                    "REQUEST_FAILED",
                    "FAILED",
                    route=route,
                    error_code="AI_PROVIDER_RESPONSE_INVALID",
                    started=started,
                )
            )
            raise

        try:
            self._usage_control.settle(
                reservation,
                outcome=UsageOutcome.SUCCEEDED,
                usage=provider_response.usage,
                provider_id=route.provider_id,
                model_id=route.model_id,
            )
        except Exception:
            # Settlement outcome may be ambiguous. Do not also release the
            # same reservation; the durable owner must reconcile it idempotently.
            self._emit_best_effort(
                self._event(
                    request,
                    "USAGE_SETTLEMENT_FAILED",
                    "UNKNOWN",
                    route=route,
                    error_code="AI_USAGE_CONTROL_UNAVAILABLE",
                    started=started,
                )
            )
            raise UsageControlUnavailableError() from None

        self._emit_best_effort(
            self._event(
                request,
                "REQUEST_COMPLETED",
                "SUCCEEDED",
                route=route,
                started=started,
            )
        )
        return AIResponse(
            request_id=request.request_id,
            correlation_id=context.correlation_id,
            text=provider_response.text,
            provider_id=route.provider_id,
            model_id=route.model_id,
            finish_reason=provider_response.finish_reason,
            usage=provider_response.usage,
        )

    def _select_available_route(
        self,
        *,
        request: AIRequest,
        primary_route: ModelRoute,
        primary_output_tokens: int,
        started: float,
    ) -> tuple[ModelRoute, int, object | None, bool]:
        """Preflight configured routes without attempting a provider request."""
        primary_provider = self._get_provider_if_available(primary_route)
        if primary_provider is not None:
            return (
                primary_route,
                primary_output_tokens,
                primary_provider,
                False,
            )

        for fallback_model_id in self._settings.fallback_model_ids:
            try:
                candidate = self._resolve_route(fallback_model_id)
            except ModelResolutionError:
                # A stale or disabled candidate is not allowed to block
                # other explicitly configured candidates.
                continue

            if candidate.model_id == primary_route.model_id:
                continue

            try:
                candidate_output_tokens = self._validate_route_limits(
                    request,
                    candidate,
                    requested_output_tokens=request.max_output_tokens,
                )
            except InvalidRequestError:
                # Do not silently lower a caller-specified output limit.
                continue

            candidate_provider = self._get_provider_if_available(candidate)
            if candidate_provider is None:
                continue

            return (
                candidate,
                candidate_output_tokens,
                candidate_provider,
                True,
            )

        self._emit_best_effort(
            self._event(
                request,
                "REQUEST_FAILED",
                "FAILED",
                route=primary_route,
                error_code="AI_PROVIDER_UNAVAILABLE",
                started=started,
            )
        )
        raise ProviderUnavailableError()

    def _get_provider_if_available(self, route: ModelRoute) -> object | None:
        """Resolve an injected provider without generating a request."""
        try:
            provider = self._provider_resolver.get(route.provider_id)
        except Exception:
            return None

        if provider is None or not callable(
            getattr(provider, "generate", None)
        ):
            return None
        return provider

    def _validate_route_limits(
        self,
        request: AIRequest,
        route: ModelRoute,
        *,
        requested_output_tokens: int | None,
    ) -> int:
        if len(request.input_text) > min(
            self._settings.max_input_chars,
            route.max_input_chars,
        ):
            raise InvalidRequestError()

        output_limit = min(
            self._settings.max_output_tokens,
            route.max_output_tokens,
        )
        output_tokens = requested_output_tokens or output_limit
        if output_tokens > output_limit:
            raise InvalidRequestError()
        return output_tokens

    def _resolve_route(self, model_id: str) -> ModelRoute:
        try:
            route = self._model_registry.resolve(model_id)
        except ModelResolutionError:
            raise
        except Exception:
            raise ModelResolutionError() from None

        if not isinstance(route, ModelRoute) or not route.enabled:
            raise ModelResolutionError()
        return route

    def _authorize(
        self,
        context: RequestContext,
        operation: str,
    ) -> AuthorizationDecision:
        try:
            decision = self._authorization.authorize_request(
                context,
                operation=operation,
            )
        except AuthorizationDeniedError:
            raise
        except Exception:
            raise AuthorizationServiceUnavailableError() from None

        if not isinstance(decision, AuthorizationDecision):
            raise AuthorizationServiceUnavailableError()
        return decision

    def _reserve(
        self,
        request: AIRequest,
        context: RequestContext,
        route: ModelRoute,
        output_tokens: int,
    ) -> UsageReservation:
        reservation_request = UsageReservationRequest(
            request_id=request.request_id,
            tenant_id=context.tenant_id,
            model_id=route.model_id,
            prompt_chars=len(request.input_text),
            max_output_tokens=output_tokens,
            idempotency_key=request.idempotency_key,
        )

        try:
            reservation = self._usage_control.reserve(reservation_request)
        except UsageLimitExceededError:
            raise
        except Exception:
            raise UsageControlUnavailableError() from None

        if (
            not isinstance(reservation, UsageReservation)
            or reservation.request_id != request.request_id
            or reservation.tenant_id != context.tenant_id
            or reservation.model_id != route.model_id
        ):
            if isinstance(reservation, UsageReservation):
                self._release_best_effort(
                    reservation,
                    "AI_USAGE_CONTROL_UNAVAILABLE",
                )
            raise UsageControlUnavailableError()

        return reservation

    def _validate_provider_response(
        self,
        response: object,
        *,
        route: ModelRoute,
        max_output_tokens: int,
    ) -> None:
        if not isinstance(response, ProviderResponse):
            raise ProviderResponseInvalidError()

        if (
            response.provider_id != route.provider_id
            or response.model_id != route.model_id
        ):
            raise ProviderResponseInvalidError()

        if len(response.text) > self._settings.max_output_chars:
            raise ProviderResponseInvalidError()

        if (
            response.usage is not None
            and response.usage.output_tokens is not None
            and response.usage.output_tokens > max_output_tokens
        ):
            raise ProviderResponseInvalidError()

    def _settle_failed(
        self,
        reservation: UsageReservation,
        route: ModelRoute,
        *,
        usage,
    ) -> None:
        try:
            self._usage_control.settle(
                reservation,
                outcome=UsageOutcome.FAILED,
                usage=usage,
                provider_id=route.provider_id,
                model_id=route.model_id,
            )
        except Exception:
            # The provider may have incurred cost. Keep the reservation for
            # owner-controlled reconciliation; never release it on ambiguity.
            raise UsageControlUnavailableError() from None

    def _release_best_effort(
        self,
        reservation: UsageReservation,
        reason_code: str,
    ) -> None:
        try:
            self._usage_control.release(
                reservation,
                reason_code=reason_code,
            )
        except Exception:
            # Keep the original safe error primary. Unresolved usage must be
            # reconciled through the existing durable accounting contract.
            pass

    def _event(
        self,
        request: AIRequest,
        event_name: str,
        outcome: str,
        *,
        route: ModelRoute | None = None,
        error_code: str | None = None,
        started: float,
    ) -> ObservabilityEvent:
        context = request.context
        correlation_id = (
            context.correlation_id
            if isinstance(context, RequestContext)
            else request.request_id
        )
        duration_ms = max(
            0,
            int((monotonic() - started) * 1000),
        )

        return ObservabilityEvent(
            event_name=event_name,
            request_id=request.request_id,
            correlation_id=correlation_id,
            outcome=outcome,
            provider_id=route.provider_id if route else None,
            model_id=route.model_id if route else None,
            duration_ms=duration_ms,
            error_code=error_code,
        )

    def _emit_required(self, event: ObservabilityEvent) -> None:
        try:
            self._observability.emit(event)
        except Exception:
            raise ObservabilityUnavailableError() from None

    def _emit_best_effort(self, event: ObservabilityEvent) -> None:
        try:
            self._observability.emit(event)
        except Exception:
            # Never expose sink exceptions or sensitive internal details.
            pass
