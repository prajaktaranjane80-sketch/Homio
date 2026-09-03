"""ACRL T08 — Compression Metrics.

Provides immutable machine-readable compression metrics.

Metrics are observational only. They do not influence authority,
execution, approval, or controller state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CompressionMetricsError(ValueError):
    """Base compression-metrics error."""


@dataclass(frozen=True)
class CompressionMetrics:
    """Immutable T08 compression measurement."""

    input_size: int
    output_size: int
    input_fields: int
    output_fields: int
    preserved_count: int
    summarized_count: int
    omitted_count: int
    compression_version: str
    policy_version: str

    def __post_init__(self) -> None:
        numeric_values = (
            ("input_size", self.input_size),
            ("output_size", self.output_size),
            ("input_fields", self.input_fields),
            ("output_fields", self.output_fields),
            ("preserved_count", self.preserved_count),
            ("summarized_count", self.summarized_count),
            ("omitted_count", self.omitted_count),
        )

        for name, value in numeric_values:
            if not isinstance(value, int):
                raise CompressionMetricsError(
                    f"{name} must be an integer."
                )

            if value < 0:
                raise CompressionMetricsError(
                    f"{name} cannot be negative."
                )

        if not isinstance(
            self.compression_version,
            str,
        ) or not self.compression_version.strip():
            raise CompressionMetricsError(
                "compression_version cannot be empty."
            )

        if not isinstance(
            self.policy_version,
            str,
        ) or not self.policy_version.strip():
            raise CompressionMetricsError(
                "policy_version cannot be empty."
            )

        if self.output_size > self.input_size:
            raise CompressionMetricsError(
                "output_size cannot exceed input_size."
            )

    @property
    def compression_ratio(self) -> float:
        """Return output/input compression ratio."""

        if self.input_size == 0:
            return 1.0

        return self.output_size / self.input_size

    @property
    def reduction_ratio(self) -> float:
        """Return proportion of input removed."""

        if self.input_size == 0:
            return 0.0

        return 1.0 - self.compression_ratio

    @property
    def size_reduction(self) -> int:
        """Return number of bytes removed."""

        return self.input_size - self.output_size

    @property
    def semantic_action_count(self) -> int:
        """Return total semantic decisions."""

        return (
            self.preserved_count
            + self.summarized_count
            + self.omitted_count
        )

    def to_dict(self) -> dict[str, Any]:
        """Return machine-readable metrics."""

        return {
            "input_size": self.input_size,
            "output_size": self.output_size,
            "input_fields": self.input_fields,
            "output_fields": self.output_fields,
            "preserved_count": self.preserved_count,
            "summarized_count": self.summarized_count,
            "omitted_count": self.omitted_count,
            "compression_ratio": self.compression_ratio,
            "reduction_ratio": self.reduction_ratio,
            "size_reduction": self.size_reduction,
            "semantic_action_count": (
                self.semantic_action_count
            ),
            "compression_version": (
                self.compression_version
            ),
            "policy_version": self.policy_version,
        }


def count_mapping_fields(
    value: Any,
) -> int:
    """Count mapping fields recursively and deterministically."""

    if isinstance(value, dict):
        total = len(value)

        for child in value.values():
            total += count_mapping_fields(child)

        return total

    if isinstance(value, (list, tuple)):
        return sum(
            count_mapping_fields(item)
            for item in value
        )

    return 0


def serialized_size(
    value: Any,
) -> int:
    """Return deterministic UTF-8 JSON size."""

    import json

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CompressionMetricsError(
            "Value cannot be deterministically serialized."
        ) from exc

    return len(encoded)


def build_compression_metrics(
    *,
    input_context: Any,
    output_context: Any,
    preserved_count: int,
    summarized_count: int,
    omitted_count: int,
    compression_version: str,
    policy_version: str,
) -> CompressionMetrics:
    """Build immutable metrics for one compression operation."""

    input_size = serialized_size(input_context)
    output_size = serialized_size(output_context)

    input_fields = count_mapping_fields(
        input_context
    )
    output_fields = count_mapping_fields(
        output_context
    )

    return CompressionMetrics(
        input_size=input_size,
        output_size=output_size,
        input_fields=input_fields,
        output_fields=output_fields,
        preserved_count=preserved_count,
        summarized_count=summarized_count,
        omitted_count=omitted_count,
        compression_version=compression_version,
        policy_version=policy_version,
    )


__all__ = [
    "CompressionMetrics",
    "CompressionMetricsError",
    "build_compression_metrics",
    "count_mapping_fields",
    "serialized_size",
]
