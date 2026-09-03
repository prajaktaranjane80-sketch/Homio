"""ACRL T01 — Project DNA health and resume readiness."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .compatibility import CompatibilityStatus
from .freshness import StateFreshness
from .linking import T01LinkedContext


HEALTH_SCHEMA_VERSION = "1.0"


class T01HealthStatus(str, Enum):
    """Machine-readable T01 health classification."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class T01Health:
    """Final T01 health projection."""

    status: T01HealthStatus
    reasons: tuple[str, ...]
    resume_safe: bool
    execution_authorized: bool
    write_authorized: bool
    schema_version: str = HEALTH_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "reasons": list(self.reasons),
            "resume_safe": self.resume_safe,
            "execution_authorized": self.execution_authorized,
            "write_authorized": self.write_authorized,
        }


def evaluate_t01_health(
    context: T01LinkedContext,
) -> T01Health:
    """Evaluate T01 readiness without performing any mutation."""

    reasons: list[str] = []

    if context.freshness.status == StateFreshness.UNKNOWN:
        reasons.append("State freshness is unknown.")

    if context.freshness.status == StateFreshness.STALE:
        reasons.append("Authoritative state is stale.")

    if context.freshness.status == StateFreshness.FUTURE:
        reasons.append("Authoritative state timestamp is in the future.")

    if context.compatibility.status == CompatibilityStatus.MIGRATION_REQUIRED:
        reasons.append("State schema migration is required.")

    if context.compatibility.status == CompatibilityStatus.FUTURE_VERSION:
        reasons.append("State schema is newer than supported.")

    if context.compatibility.status == CompatibilityStatus.UNSUPPORTED:
        reasons.append("State schema is unsupported.")

    if reasons:
        return T01Health(
            status=T01HealthStatus.BLOCKED,
            reasons=tuple(reasons),
            resume_safe=False,
            execution_authorized=False,
            write_authorized=False,
        )

    return T01Health(
        status=T01HealthStatus.READY,
        reasons=(),
        resume_safe=True,
        execution_authorized=False,
        write_authorized=False,
    )


def build_t01_health_payload(
    context: T01LinkedContext,
) -> dict[str, Any]:
    """Return the final machine-readable T01 status payload."""

    health = evaluate_t01_health(context)

    return {
        "t01": context.to_dict(),
        "health": health.to_dict(),
    }


__all__ = [
    "HEALTH_SCHEMA_VERSION",
    "T01Health",
    "T01HealthStatus",
    "build_t01_health_payload",
    "evaluate_t01_health",
]