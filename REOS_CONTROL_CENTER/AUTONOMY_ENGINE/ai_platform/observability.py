"""Structured, allowlisted logging adapter for AI observability events.

The application logging configuration owns the destination and retention
policy. This adapter emits only fields defined by ObservabilityEvent. It never
accepts or logs prompts, model output, credentials, tenant records, or raw
provider exceptions.
"""
from __future__ import annotations

import logging

from .contracts import ObservabilityEvent


class StructuredLoggingObservability:
    """Emit provider-independent AI events as structured log records."""

    __slots__ = ("_logger",)

    def __init__(self, logger: logging.Logger | None = None) -> None:
        selected_logger = logger or logging.getLogger(
            "homio.ai.observability"
        )
        if not callable(getattr(selected_logger, "info", None)):
            raise TypeError("logger must provide a callable info method")
        self._logger = selected_logger

    def emit(self, event: ObservabilityEvent) -> None:
        """Log only the approved event fields; never log request content."""
        if not isinstance(event, ObservabilityEvent):
            raise TypeError("event must be an ObservabilityEvent")

        payload = {
            "event_name": event.event_name,
            "request_id": event.request_id,
            "correlation_id": event.correlation_id,
            "outcome": event.outcome,
            "provider_id": event.provider_id,
            "model_id": event.model_id,
            "duration_ms": event.duration_ms,
            "error_code": event.error_code,
        }

        self._logger.info(
            "homio_ai_event",
            extra={"homio_ai_event": payload},
        )
