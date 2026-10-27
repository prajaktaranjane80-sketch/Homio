"""Validated, non-secret configuration for the AI gateway."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .contracts import _identifier, _positive_int


@dataclass(frozen=True, slots=True)
class GatewaySettings:
    """Safe-by-default settings; live service use requires explicit enablement."""

    enabled: bool = False
    default_model_id: str | None = None
    max_input_chars: int = 12_000
    max_output_tokens: int = 512
    max_output_chars: int = 24_000
    request_timeout_seconds: float = 30.0
    fallback_model_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean")

        if self.default_model_id is not None:
            object.__setattr__(
                self,
                "default_model_id",
                _identifier(self.default_model_id, "default_model_id"),
            )

        _positive_int(self.max_input_chars, "max_input_chars")
        _positive_int(self.max_output_tokens, "max_output_tokens")
        _positive_int(self.max_output_chars, "max_output_chars")

        timeout = self.request_timeout_seconds
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
        ):
            raise TypeError(
                "request_timeout_seconds must be a finite positive number"
            )

        if (
            not isfinite(float(timeout))
            or timeout <= 0
            or timeout > 120
        ):
            raise ValueError(
                "request_timeout_seconds must be > 0 and <= 120 seconds"
            )

        object.__setattr__(
            self,
            "request_timeout_seconds",
            float(timeout),
        )

        raw_fallbacks = self.fallback_model_ids
        if isinstance(raw_fallbacks, (str, bytes)):
            raise TypeError(
                "fallback_model_ids must be a sequence of model identifiers"
            )

        try:
            fallbacks = tuple(
                _identifier(value, "fallback_model_id")
                for value in raw_fallbacks
            )
        except TypeError as exc:
            raise TypeError(
                "fallback_model_ids must be an iterable of model identifiers"
            ) from exc

        if len(set(fallbacks)) != len(fallbacks):
            raise ValueError(
                "duplicate fallback model identifiers are not allowed"
            )

        if self.default_model_id is not None:
            if self.default_model_id in fallbacks:
                raise ValueError(
                    "the default model cannot also be a fallback model"
                )

        object.__setattr__(self, "fallback_model_ids", fallbacks)
