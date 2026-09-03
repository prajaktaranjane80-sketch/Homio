"""ACRL T01 — Authoritative state freshness classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


FRESHNESS_SCHEMA_VERSION = "1.0"


class StateFreshness(str, Enum):
    """Machine-readable state freshness classification."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    FUTURE = "FUTURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FreshnessPolicy:
    """Explicit deterministic freshness policy."""

    max_age_seconds: int = 86_400


@dataclass(frozen=True)
class FreshnessResult:
    """Result of evaluating authoritative state freshness."""

    status: StateFreshness
    updated_at: str | None
    observed_at: str
    age_seconds: int | None
    reason: str
    schema_version: str = FRESHNESS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "updated_at": self.updated_at,
            "observed_at": self.observed_at,
            "age_seconds": self.age_seconds,
            "reason": self.reason,
        }


def classify_state_freshness(
    state: Mapping[str, Any],
    *,
    observed_at: datetime | None = None,
    policy: FreshnessPolicy | None = None,
) -> FreshnessResult:
    """Classify state freshness without mutating authoritative state."""

    current = observed_at or datetime.now(timezone.utc)
    current = current.astimezone(timezone.utc)

    effective_policy = policy or FreshnessPolicy()

    meta = state.get("meta")

    if not isinstance(meta, Mapping):
        return FreshnessResult(
            status=StateFreshness.UNKNOWN,
            updated_at=None,
            observed_at=current.isoformat(),
            age_seconds=None,
            reason="state.meta is missing or invalid.",
        )

    updated_raw = meta.get("updated_at")

    if not isinstance(updated_raw, str) or not updated_raw.strip():
        return FreshnessResult(
            status=StateFreshness.UNKNOWN,
            updated_at=None,
            observed_at=current.isoformat(),
            age_seconds=None,
            reason="meta.updated_at is missing or invalid.",
        )

    try:
        updated = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
    except ValueError:
        return FreshnessResult(
            status=StateFreshness.UNKNOWN,
            updated_at=updated_raw,
            observed_at=current.isoformat(),
            age_seconds=None,
            reason="meta.updated_at is not a valid ISO-8601 timestamp.",
        )

    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    updated = updated.astimezone(timezone.utc)

    age = int((current - updated).total_seconds())

    if age < 0:
        return FreshnessResult(
            status=StateFreshness.FUTURE,
            updated_at=updated.isoformat(),
            observed_at=current.isoformat(),
            age_seconds=age,
            reason="Authoritative state timestamp is in the future.",
        )

    if age > effective_policy.max_age_seconds:
        return FreshnessResult(
            status=StateFreshness.STALE,
            updated_at=updated.isoformat(),
            observed_at=current.isoformat(),
            age_seconds=age,
            reason="Authoritative state exceeds configured freshness window.",
        )

    return FreshnessResult(
        status=StateFreshness.CURRENT,
        updated_at=updated.isoformat(),
        observed_at=current.isoformat(),
        age_seconds=age,
        reason="Authoritative state is within configured freshness window.",
    )


__all__ = [
    "FRESHNESS_SCHEMA_VERSION",
    "FreshnessPolicy",
    "FreshnessResult",
    "StateFreshness",
    "classify_state_freshness",
]