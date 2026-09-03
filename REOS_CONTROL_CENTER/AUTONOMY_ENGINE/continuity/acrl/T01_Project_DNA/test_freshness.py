"""Tests for T01 state freshness classification."""

from __future__ import annotations

from datetime import datetime, timezone

from .freshness import (
    FreshnessPolicy,
    StateFreshness,
    classify_state_freshness,
)


def _state(updated_at: str) -> dict[str, object]:
    return {
        "meta": {
            "updated_at": updated_at,
        }
    }


def test_current_state_is_current() -> None:
    observed = datetime(
        2026,
        8,
        30,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = classify_state_freshness(
        _state("2026-08-30T11:59:00+00:00"),
        observed_at=observed,
        policy=FreshnessPolicy(max_age_seconds=3600),
    )

    assert result.status == StateFreshness.CURRENT
    assert result.age_seconds == 60


def test_old_state_is_stale() -> None:
    observed = datetime(
        2026,
        8,
        30,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = classify_state_freshness(
        _state("2026-08-29T12:00:00+00:00"),
        observed_at=observed,
        policy=FreshnessPolicy(max_age_seconds=3600),
    )

    assert result.status == StateFreshness.STALE


def test_future_state_is_blocked() -> None:
    observed = datetime(
        2026,
        8,
        30,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = classify_state_freshness(
        _state("2026-08-30T13:00:00+00:00"),
        observed_at=observed,
    )

    assert result.status == StateFreshness.FUTURE


def test_invalid_timestamp_is_unknown() -> None:
    result = classify_state_freshness(
        _state("not-a-timestamp")
    )

    assert result.status == StateFreshness.UNKNOWN