"""ACRL T08 — Context Budget.

Provides deterministic safety limits for compressed context.

Boundary:
    Budget validation and accounting only.
    No mutation of source context.
    No authority escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


class ContextBudgetError(ValueError):
    """Base context-budget error."""


class ContextBudgetExceededError(ContextBudgetError):
    """Raised when a context exceeds a configured budget."""


class ContextBudgetInsufficientError(ContextBudgetError):
    """Raised when the budget cannot preserve mandatory information."""


@dataclass(frozen=True)
class ContextBudget:
    """Immutable deterministic T08 context budget."""

    max_output_bytes: int = 64_000
    max_output_fields: int = 256
    max_section_bytes: int = 32_000
    compression_level: int = 1

    MIN_OUTPUT_BYTES: Final[int] = 1_024
    MAX_OUTPUT_BYTES: Final[int] = 10_000_000
    MIN_OUTPUT_FIELDS: Final[int] = 1
    MAX_OUTPUT_FIELDS: Final[int] = 100_000
    MIN_SECTION_BYTES: Final[int] = 256
    MAX_SECTION_BYTES: Final[int] = 10_000_000
    MIN_COMPRESSION_LEVEL: Final[int] = 0
    MAX_COMPRESSION_LEVEL: Final[int] = 3

    def __post_init__(self) -> None:
        if not (
            self.MIN_OUTPUT_BYTES
            <= self.max_output_bytes
            <= self.MAX_OUTPUT_BYTES
        ):
            raise ContextBudgetError(
                "max_output_bytes is outside the supported range."
            )

        if not (
            self.MIN_OUTPUT_FIELDS
            <= self.max_output_fields
            <= self.MAX_OUTPUT_FIELDS
        ):
            raise ContextBudgetError(
                "max_output_fields is outside the supported range."
            )

        if not (
            self.MIN_SECTION_BYTES
            <= self.max_section_bytes
            <= self.MAX_SECTION_BYTES
        ):
            raise ContextBudgetError(
                "max_section_bytes is outside the supported range."
            )

        if not (
            self.MIN_COMPRESSION_LEVEL
            <= self.compression_level
            <= self.MAX_COMPRESSION_LEVEL
        ):
            raise ContextBudgetError(
                "compression_level is outside the supported range."
            )

    def validate_output(
        self,
        output_bytes: int,
        output_fields: int,
    ) -> None:
        """Validate final compressed-context size."""

        if output_bytes < 0:
            raise ContextBudgetError(
                "output_bytes cannot be negative."
            )

        if output_fields < 0:
            raise ContextBudgetError(
                "output_fields cannot be negative."
            )

        if output_bytes > self.max_output_bytes:
            raise ContextBudgetExceededError(
                "Compressed context exceeds the configured byte budget."
            )

        if output_fields > self.max_output_fields:
            raise ContextBudgetExceededError(
                "Compressed context exceeds the configured field budget."
            )

    def validate_section(
        self,
        section_bytes: int,
    ) -> None:
        """Validate an individual preserved section."""

        if section_bytes < 0:
            raise ContextBudgetError(
                "section_bytes cannot be negative."
            )

        if section_bytes > self.max_section_bytes:
            raise ContextBudgetExceededError(
                "Context section exceeds the configured section budget."
            )

    def require_mandatory_capacity(
        self,
        mandatory_bytes: int,
    ) -> None:
        """Ensure mandatory information can fit without truncation."""

        if mandatory_bytes < 0:
            raise ContextBudgetError(
                "mandatory_bytes cannot be negative."
            )

        if mandatory_bytes > self.max_output_bytes:
            raise ContextBudgetInsufficientError(
                "Budget cannot preserve all mandatory information."
            )

    def can_fit(
        self,
        output_bytes: int,
        output_fields: int,
    ) -> bool:
        """Return whether a projected output fits the budget."""

        return (
            output_bytes <= self.max_output_bytes
            and output_fields <= self.max_output_fields
        )

    def to_dict(self) -> dict[str, int]:
        """Return deterministic machine-readable budget metadata."""

        return {
            "max_output_bytes": self.max_output_bytes,
            "max_output_fields": self.max_output_fields,
            "max_section_bytes": self.max_section_bytes,
            "compression_level": self.compression_level,
        }


DEFAULT_CONTEXT_BUDGET = ContextBudget()


__all__ = [
    "ContextBudget",
    "ContextBudgetError",
    "ContextBudgetExceededError",
    "ContextBudgetInsufficientError",
    "DEFAULT_CONTEXT_BUDGET",
]
