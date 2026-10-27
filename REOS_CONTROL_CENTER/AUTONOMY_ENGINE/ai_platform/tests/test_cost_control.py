from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import threading

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    ProviderUsage,
    UsageOutcome,
    UsageReservationRequest,
)
from AUTONOMY_ENGINE.ai_platform.cost_control import (
    ModelPricing,
    SQLiteUsageControl,
    microusd_to_usd,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    InvalidRequestError,
    UsageControlUnavailableError,
    UsageLimitExceededError,
)


def make_control(
    path: Path,
    *,
    budget: int = 100_000,
    tenant_budgets: dict[str, int] | None = None,
    clock=None,
) -> SQLiteUsageControl:
    kwargs = {}
    if clock is not None:
        kwargs["clock"] = clock

    return SQLiteUsageControl(
        database_path=path,
        pricing={"model-a": ModelPricing(2_000, 4_000)},
        default_tenant_budget_microusd=budget,
        tenant_budgets_microusd=tenant_budgets,
        chars_per_input_token=4,
        **kwargs,
    )


def make_request(
    request_id: str = "request-1",
    *,
    tenant_id: str = "tenant-a",
    prompt_chars: int = 40,
    output_tokens: int = 10,
    idempotency_key: str | None = None,
) -> UsageReservationRequest:
    return UsageReservationRequest(
        request_id=request_id,
        tenant_id=tenant_id,
        model_id="model-a",
        prompt_chars=prompt_chars,
        max_output_tokens=output_tokens,
        idempotency_key=idempotency_key,
    )


def test_reservation_is_durable_and_counts_against_tenant_budget(
    tmp_path: Path,
) -> None:
    db = tmp_path / "usage.sqlite3"
    usage = make_control(db, budget=100)
    reservation = usage.reserve(
        make_request(prompt_chars=40, output_tokens=10)
    )

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.reserved_microusd == 60
    assert snapshot.settled_microusd == 0
    assert snapshot.remaining_microusd == 40

    reopened = make_control(db, budget=100)
    persisted = reopened.snapshot("tenant-a")
    assert persisted.reserved_microusd == 60
    assert persisted.period_start == snapshot.period_start
    assert reservation.tenant_id == "tenant-a"


def test_settlement_uses_provider_usage_and_is_idempotent(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=100)
    reservation = usage.reserve(make_request())
    actual_usage = ProviderUsage(
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
    )

    usage.settle(
        reservation,
        outcome=UsageOutcome.SUCCEEDED,
        usage=actual_usage,
        provider_id="provider-a",
        model_id="model-a",
    )
    usage.settle(
        reservation,
        outcome=UsageOutcome.SUCCEEDED,
        usage=actual_usage,
        provider_id="provider-a",
        model_id="model-a",
    )

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.settled_microusd == 40
    assert snapshot.reserved_microusd == 0
    assert snapshot.remaining_microusd == 60


def test_unknown_provider_usage_is_charged_conservatively_not_released(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=100)
    reservation = usage.reserve(make_request())
    held = usage.snapshot("tenant-a").reserved_microusd

    usage.settle(
        reservation,
        outcome=UsageOutcome.FAILED,
        usage=None,
        provider_id="provider-a",
        model_id="model-a",
    )

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.settled_microusd == held
    assert snapshot.reserved_microusd == 0


def test_partial_provider_usage_estimates_missing_side(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=100)
    reservation = usage.reserve(
        make_request(prompt_chars=40, output_tokens=10)
    )

    usage.settle(
        reservation,
        outcome=UsageOutcome.SUCCEEDED,
        usage=ProviderUsage(
            input_tokens=10,
            output_tokens=None,
            total_tokens=None,
        ),
        provider_id="provider-a",
        model_id="model-a",
    )

    assert usage.snapshot("tenant-a").settled_microusd == 60


def test_tenant_budgets_are_isolated_and_override_default(
    tmp_path: Path,
) -> None:
    usage = make_control(
        tmp_path / "usage.sqlite3",
        budget=1_000,
        tenant_budgets={"tenant-a": 60},
    )

    usage.reserve(make_request("a-1", tenant_id="tenant-a"))
    with pytest.raises(UsageLimitExceededError):
        usage.reserve(make_request("a-2", tenant_id="tenant-a"))

    other = usage.reserve(make_request("b-1", tenant_id="tenant-b"))
    assert other.tenant_id == "tenant-b"
    assert usage.snapshot("tenant-a").reserved_microusd == 60
    assert usage.snapshot("tenant-b").reserved_microusd == 60


def test_quota_rejection_does_not_create_a_reservation(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=59)

    with pytest.raises(UsageLimitExceededError):
        usage.reserve(make_request())

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.reserved_microusd == 0
    assert snapshot.settled_microusd == 0


def test_concurrent_reservations_cannot_oversubscribe_budget(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=600)
    barrier = threading.Barrier(20)

    def reserve(index: int) -> str:
        barrier.wait()
        try:
            usage.reserve(make_request(f"parallel-{index}"))
            return "reserved"
        except UsageLimitExceededError:
            return "limited"

    with ThreadPoolExecutor(max_workers=20) as pool:
        outcomes = list(pool.map(reserve, range(20)))

    assert outcomes.count("reserved") == 10
    assert outcomes.count("limited") == 10

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.reserved_microusd == 600
    assert snapshot.committed_microusd <= snapshot.budget_microusd


def test_request_or_idempotency_replay_is_rejected_before_second_provider_call(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3")
    usage.reserve(
        make_request("same-request", idempotency_key="retry-key")
    )

    with pytest.raises(InvalidRequestError):
        usage.reserve(
            make_request("same-request", idempotency_key="retry-key")
        )

    with pytest.raises(InvalidRequestError):
        usage.reserve(
            make_request("different-request", idempotency_key="retry-key")
        )

    assert usage.snapshot("tenant-a").reserved_microusd == 60


def test_release_is_repeat_safe_and_returns_reserved_capacity(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3")
    reservation = usage.reserve(make_request())

    usage.release(
        reservation,
        reason_code="AI_PROVIDER_UNAVAILABLE",
    )
    usage.release(
        reservation,
        reason_code="AI_PROVIDER_UNAVAILABLE",
    )

    assert usage.snapshot("tenant-a").reserved_microusd == 0


def test_released_reservation_cannot_be_settled(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3")
    reservation = usage.reserve(make_request())
    usage.release(
        reservation,
        reason_code="AI_PROVIDER_UNAVAILABLE",
    )

    with pytest.raises(UsageControlUnavailableError):
        usage.settle(
            reservation,
            outcome=UsageOutcome.FAILED,
            usage=None,
            provider_id="provider-a",
            model_id="model-a",
        )


def test_conflicting_duplicate_settlement_fails_closed(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3")
    reservation = usage.reserve(make_request())

    usage.settle(
        reservation,
        outcome=UsageOutcome.SUCCEEDED,
        usage=ProviderUsage(input_tokens=10, output_tokens=5),
        provider_id="provider-a",
        model_id="model-a",
    )

    with pytest.raises(UsageControlUnavailableError):
        usage.settle(
            reservation,
            outcome=UsageOutcome.FAILED,
            usage=ProviderUsage(input_tokens=10, output_tokens=5),
            provider_id="provider-a",
            model_id="model-a",
        )


def test_actual_overrun_is_recorded_and_blocks_future_reservations(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3", budget=70)
    reservation = usage.reserve(make_request())

    usage.settle(
        reservation,
        outcome=UsageOutcome.SUCCEEDED,
        usage=ProviderUsage(
            input_tokens=10_000,
            output_tokens=10_000,
        ),
        provider_id="provider-a",
        model_id="model-a",
    )

    snapshot = usage.snapshot("tenant-a")
    assert snapshot.over_budget is True
    assert snapshot.settled_microusd > snapshot.budget_microusd

    with pytest.raises(UsageLimitExceededError):
        usage.reserve(make_request("after-overrun"))


def test_monthly_window_is_utc_and_new_month_starts_a_new_quota(
    tmp_path: Path,
) -> None:
    current = [
        datetime(2026, 10, 31, 23, 59, tzinfo=timezone.utc)
    ]
    usage = make_control(
        tmp_path / "usage.sqlite3",
        budget=60,
        clock=lambda: current[0],
    )

    usage.reserve(make_request("october"))
    assert (
        usage.snapshot("tenant-a").period_start
        == "2026-10-01T00:00:00+00:00"
    )

    current[0] = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)
    assert usage.snapshot("tenant-a").reserved_microusd == 0

    usage.reserve(make_request("november"))
    assert usage.snapshot("tenant-a").reserved_microusd == 60


def test_missing_pricing_fails_closed_and_does_not_persist_reservation(
    tmp_path: Path,
) -> None:
    usage = make_control(tmp_path / "usage.sqlite3")
    request = UsageReservationRequest(
        request_id="request-unknown-model",
        tenant_id="tenant-a",
        model_id="not-priced",
        prompt_chars=20,
        max_output_tokens=10,
    )

    with pytest.raises(UsageControlUnavailableError):
        usage.reserve(request)

    assert usage.snapshot("tenant-a").reserved_microusd == 0


def test_non_durable_in_memory_database_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        make_control(Path(":memory:"))


def test_micro_usd_format_has_no_float_rounding() -> None:
    assert microusd_to_usd(0) == "$0.000000"
    assert microusd_to_usd(1_234_567) == "$1.234567"
