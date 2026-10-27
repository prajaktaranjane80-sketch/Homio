"""Durable, tenant-scoped AI usage reservations and cost accounting.

This adapter implements the existing UsageControlPort without owning identity,
model selection, or business authorization. It uses a transactional SQLite
file for single-host deployments and tests. A horizontally scaled deployment
must inject a ledger backed by its approved shared transactional datastore;
SQLite on an arbitrary network filesystem is not a distributed-locking design.

Money is stored as integer micro-USD (one millionth of a US dollar). Prices
are explicit per model and must be configured by the server, never by a caller.
No prompts or provider response bodies are persisted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Callable, Mapping
from uuid import uuid4

from .contracts import (
    ProviderUsage,
    UsageOutcome,
    UsageReservation,
    UsageReservationRequest,
    _identifier,
)
from .errors import (
    InvalidRequestError,
    UsageControlUnavailableError,
    UsageLimitExceededError,
)


_MICRO_USD_PER_USD = 1_000_000
_MICRO_USD_PER_1K_TOKENS = 1_000
_SCHEMA_VERSION = 1


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_int_value(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _cost_for_tokens(rate_per_1k: int, tokens: int) -> int:
    """Round fractional micro-USD charges up instead of silently rounding down."""
    if rate_per_1k == 0 or tokens == 0:
        return 0
    return (
        rate_per_1k * tokens + _MICRO_USD_PER_1K_TOKENS - 1
    ) // _MICRO_USD_PER_1K_TOKENS


def _clock_utc(clock: Callable[[], datetime]) -> datetime:
    try:
        current = clock()
    except Exception:
        raise UsageControlUnavailableError() from None

    if (
        not isinstance(current, datetime)
        or current.tzinfo is None
        or current.utcoffset() is None
    ):
        raise UsageControlUnavailableError()

    return current.astimezone(timezone.utc)


def _period_start(current: datetime) -> str:
    """Return the UTC calendar-month key for an already-normalized instant."""
    return f"{current.year:04d}-{current.month:02d}-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Server-owned model prices in micro-USD per 1,000 tokens."""

    input_microusd_per_1k_tokens: int
    output_microusd_per_1k_tokens: int

    def __post_init__(self) -> None:
        _nonnegative_int(
            self.input_microusd_per_1k_tokens,
            "input price",
        )
        _nonnegative_int(
            self.output_microusd_per_1k_tokens,
            "output price",
        )


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    """Tenant usage for one UTC calendar month, measured in micro-USD."""

    tenant_id: str
    period_start: str
    budget_microusd: int
    settled_microusd: int
    reserved_microusd: int

    @property
    def committed_microusd(self) -> int:
        return self.settled_microusd + self.reserved_microusd

    @property
    def remaining_microusd(self) -> int:
        return max(0, self.budget_microusd - self.committed_microusd)

    @property
    def over_budget(self) -> bool:
        # Actual provider charges can exceed an estimate. Preserve that cost
        # and block additional reservations instead of hiding the overrun.
        return self.committed_microusd > self.budget_microusd


class SQLiteUsageControl:
    """Transactional implementation of the AI gateway's UsageControlPort.

    `default_tenant_budget_microusd` is mandatory; an absent tenant override
    uses that default. Configure one trusted ModelPricing per allowed model.

    The gateway must call `reserve` only after authorization. This adapter
    does not authenticate a tenant ID; it enforces a budget for the supplied ID.

    Reservation checks and inserts run inside BEGIN IMMEDIATE. Concurrent
    writers sharing this local SQLite database therefore serialize quota
    decisions. Pending reservations count against the monthly budget. Settled
    actual/estimated charges remain in the original reservation month.

    This is a single-host persistent adapter, not a distributed database.
    Multi-replica production deployments must use the approved shared
    transactional datastore behind the same UsageControlPort contract.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
        pricing: Mapping[str, ModelPricing],
        default_tenant_budget_microusd: int,
        tenant_budgets_microusd: Mapping[str, int] | None = None,
        chars_per_input_token: int = 4,
        busy_timeout_ms: int = 5_000,
        clock: Callable[[], datetime] = _now_utc,
    ) -> None:
        raw_path = str(database_path).strip()
        if (
            not raw_path
            or raw_path == ":memory:"
            or raw_path.startswith("file:")
        ):
            raise ValueError(
                "database_path must be a persistent SQLite file path"
            )

        _nonnegative_int(
            default_tenant_budget_microusd,
            "default tenant budget",
        )
        _positive_int_value(chars_per_input_token, "chars_per_input_token")
        _positive_int_value(busy_timeout_ms, "busy_timeout_ms")
        if busy_timeout_ms > 120_000:
            raise ValueError("busy_timeout_ms must not exceed 120000")
        if not callable(clock):
            raise TypeError("clock must be callable")
        if not pricing:
            raise ValueError("pricing must include at least one configured model")

        normalized_pricing: dict[str, ModelPricing] = {}
        for model_id, model_pricing in pricing.items():
            normalized_id = _identifier(model_id, "model_id")
            if not isinstance(model_pricing, ModelPricing):
                raise TypeError("each pricing value must be ModelPricing")
            normalized_pricing[normalized_id] = model_pricing

        normalized_budgets: dict[str, int] = {}
        for tenant_id, budget in (tenant_budgets_microusd or {}).items():
            normalized_budgets[_identifier(tenant_id, "tenant_id")] = (
                _nonnegative_int(budget, "tenant budget")
            )

        self._path = Path(raw_path).expanduser().resolve()
        self._pricing = normalized_pricing
        self._default_budget = default_tenant_budget_microusd
        self._tenant_budgets = normalized_budgets
        self._chars_per_input_token = chars_per_input_token
        self._busy_timeout_ms = busy_timeout_ms
        self._clock = clock

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._initialize()
        except UsageControlUnavailableError:
            raise
        except (OSError, sqlite3.Error):
            raise UsageControlUnavailableError() from None

    def reserve(
        self,
        request: UsageReservationRequest,
    ) -> UsageReservation:
        """Atomically reserve estimated pre-call cost before provider access."""
        if not isinstance(request, UsageReservationRequest):
            raise InvalidRequestError()

        pricing = self._pricing.get(request.model_id)
        if pricing is None:
            raise UsageControlUnavailableError()

        estimated_input_tokens = self._estimate_input_tokens(
            request.prompt_chars
        )
        reserved_cost = self._price(
            pricing,
            estimated_input_tokens,
            request.max_output_tokens,
        )

        # Use one clock reading for both the billing month and creation time.
        current = _clock_utc(self._clock)
        period_start = _period_start(current)
        budget = self._budget_for(request.tenant_id)
        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """SELECT reservation_id
                   FROM usage_reservations
                   WHERE tenant_id = ?
                     AND (
                       request_id = ?
                       OR (
                         ? IS NOT NULL
                         AND idempotency_key = ?
                       )
                     )
                   LIMIT 1""",
                (
                    request.tenant_id,
                    request.request_id,
                    request.idempotency_key,
                    request.idempotency_key,
                ),
            ).fetchone()

            if existing is not None:
                connection.rollback()
                # This gateway does not replay a stored AIResponse. A repeated
                # request must not trigger a second provider call or reservation.
                raise InvalidRequestError()

            row = connection.execute(
                """SELECT
                     COALESCE(
                       SUM(
                         CASE
                           WHEN status = 'SETTLED' THEN final_microusd
                           ELSE 0
                         END
                       ), 0
                     ) AS settled,
                     COALESCE(
                       SUM(
                         CASE
                           WHEN status = 'PENDING' THEN reserved_microusd
                           ELSE 0
                         END
                       ), 0
                     ) AS reserved
                   FROM usage_reservations
                   WHERE tenant_id = ? AND period_start = ?""",
                (request.tenant_id, period_start),
            ).fetchone()

            committed = int(row["settled"]) + int(row["reserved"])
            if committed + reserved_cost > budget:
                connection.rollback()
                raise UsageLimitExceededError()

            reservation_id = f"usage-{uuid4().hex}"
            connection.execute(
                """INSERT INTO usage_reservations (
                     reservation_id,
                     tenant_id,
                     request_id,
                     model_id,
                     idempotency_key,
                     period_start,
                     prompt_chars,
                     max_output_tokens,
                     reserved_microusd,
                     status,
                     created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)""",
                (
                    reservation_id,
                    request.tenant_id,
                    request.request_id,
                    request.model_id,
                    request.idempotency_key,
                    period_start,
                    request.prompt_chars,
                    request.max_output_tokens,
                    reserved_cost,
                    current.isoformat(),
                ),
            )
            connection.commit()

            return UsageReservation(
                reservation_id=reservation_id,
                request_id=request.request_id,
                tenant_id=request.tenant_id,
                model_id=request.model_id,
            )

        except (
            InvalidRequestError,
            UsageLimitExceededError,
            UsageControlUnavailableError,
        ):
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error:
            if connection.in_transaction:
                connection.rollback()
            raise UsageControlUnavailableError() from None
        finally:
            connection.close()

    def settle(
        self,
        reservation: UsageReservation,
        *,
        outcome: UsageOutcome,
        usage: ProviderUsage | None,
        provider_id: str,
        model_id: str,
    ) -> None:
        """Persist reported usage or a conservative estimate idempotently.

        Unknown usage is charged as an estimate rather than released because
        the provider may have incurred the reserved cost. Actual charges above
        the reservation are still recorded and can put the tenant over budget.
        """
        if not isinstance(reservation, UsageReservation):
            raise UsageControlUnavailableError()
        if not isinstance(outcome, UsageOutcome):
            raise UsageControlUnavailableError()
        if usage is not None and not isinstance(usage, ProviderUsage):
            raise UsageControlUnavailableError()

        try:
            provider_id = _identifier(provider_id, "provider_id")
            model_id = _identifier(model_id, "model_id")
        except (TypeError, ValueError):
            raise UsageControlUnavailableError() from None

        if model_id != reservation.model_id or model_id not in self._pricing:
            raise UsageControlUnavailableError()

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM usage_reservations WHERE reservation_id = ?",
                (reservation.reservation_id,),
            ).fetchone()
            self._require_matching_reservation(row, reservation)

            calculated = self._calculate_charge(
                row,
                self._pricing[model_id],
                usage,
            )

            if row["status"] == "SETTLED":
                same = (
                    row["outcome"] == outcome.value
                    and row["provider_id"] == provider_id
                    and row["model_id"] == model_id
                    and row["final_microusd"] == calculated[0]
                    and row["input_tokens"] == calculated[1]
                    and row["output_tokens"] == calculated[2]
                    and row["total_tokens"] == calculated[3]
                    and row["accounting_source"] == calculated[4]
                )
                if same:
                    connection.commit()
                    return

                connection.rollback()
                raise UsageControlUnavailableError()

            if row["status"] != "PENDING":
                connection.rollback()
                raise UsageControlUnavailableError()

            cost, input_tokens, output_tokens, total_tokens, source = calculated
            settled_at = _clock_utc(self._clock).isoformat()
            connection.execute(
                """UPDATE usage_reservations
                   SET status = 'SETTLED',
                       outcome = ?,
                       provider_id = ?,
                       input_tokens = ?,
                       output_tokens = ?,
                       total_tokens = ?,
                       accounting_source = ?,
                       final_microusd = ?,
                       settled_at = ?
                   WHERE reservation_id = ? AND status = 'PENDING'""",
                (
                    outcome.value,
                    provider_id,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    source,
                    cost,
                    settled_at,
                    reservation.reservation_id,
                ),
            )
            connection.commit()

        except UsageControlUnavailableError:
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error:
            if connection.in_transaction:
                connection.rollback()
            raise UsageControlUnavailableError() from None
        finally:
            connection.close()

    def release(
        self,
        reservation: UsageReservation,
        *,
        reason_code: str,
    ) -> None:
        """Release a reservation only when the provider was not attempted."""
        if not isinstance(reservation, UsageReservation):
            raise UsageControlUnavailableError()

        try:
            reason_code = _identifier(reason_code, "reason_code")
        except (TypeError, ValueError):
            raise UsageControlUnavailableError() from None

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM usage_reservations WHERE reservation_id = ?",
                (reservation.reservation_id,),
            ).fetchone()
            self._require_matching_reservation(row, reservation)

            if (
                row["status"] == "RELEASED"
                and row["release_reason"] == reason_code
            ):
                connection.commit()
                return

            if row["status"] != "PENDING":
                connection.rollback()
                raise UsageControlUnavailableError()

            connection.execute(
                """UPDATE usage_reservations
                   SET status = 'RELEASED',
                       release_reason = ?,
                       settled_at = ?
                   WHERE reservation_id = ? AND status = 'PENDING'""",
                (
                    reason_code,
                    _clock_utc(self._clock).isoformat(),
                    reservation.reservation_id,
                ),
            )
            connection.commit()

        except UsageControlUnavailableError:
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error:
            if connection.in_transaction:
                connection.rollback()
            raise UsageControlUnavailableError() from None
        finally:
            connection.close()

    def snapshot(self, tenant_id: str) -> UsageSnapshot:
        """Return settled spend and outstanding reservations for this month."""
        try:
            tenant_id = _identifier(tenant_id, "tenant_id")
            period_start = _period_start(_clock_utc(self._clock))
        except (TypeError, ValueError):
            raise InvalidRequestError() from None

        connection = self._connect()
        try:
            row = connection.execute(
                """SELECT
                     COALESCE(
                       SUM(
                         CASE
                           WHEN status = 'SETTLED' THEN final_microusd
                           ELSE 0
                         END
                       ), 0
                     ) AS settled,
                     COALESCE(
                       SUM(
                         CASE
                           WHEN status = 'PENDING' THEN reserved_microusd
                           ELSE 0
                         END
                       ), 0
                     ) AS reserved
                   FROM usage_reservations
                   WHERE tenant_id = ? AND period_start = ?""",
                (tenant_id, period_start),
            ).fetchone()

            return UsageSnapshot(
                tenant_id=tenant_id,
                period_start=period_start,
                budget_microusd=self._budget_for(tenant_id),
                settled_microusd=int(row["settled"]),
                reserved_microusd=int(row["reserved"]),
            )
        except sqlite3.Error:
            raise UsageControlUnavailableError() from None
        finally:
            connection.close()

    def _initialize(self) -> None:
        connection = sqlite3.connect(
            str(self._path),
            timeout=self._busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        try:
            connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")

            connection.execute(
                """CREATE TABLE IF NOT EXISTS usage_ledger_metadata (
                     key TEXT PRIMARY KEY,
                     value TEXT NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS usage_reservations (
                     reservation_id TEXT PRIMARY KEY,
                     tenant_id TEXT NOT NULL,
                     request_id TEXT NOT NULL,
                     model_id TEXT NOT NULL,
                     idempotency_key TEXT,
                     period_start TEXT NOT NULL,
                     prompt_chars INTEGER NOT NULL CHECK(prompt_chars > 0),
                     max_output_tokens INTEGER NOT NULL
                       CHECK(max_output_tokens > 0),
                     reserved_microusd INTEGER NOT NULL
                       CHECK(reserved_microusd >= 0),
                     status TEXT NOT NULL
                       CHECK(status IN ('PENDING', 'SETTLED', 'RELEASED')),
                     outcome TEXT,
                     provider_id TEXT,
                     input_tokens INTEGER,
                     output_tokens INTEGER,
                     total_tokens INTEGER,
                     accounting_source TEXT,
                     final_microusd INTEGER
                       CHECK(final_microusd IS NULL OR final_microusd >= 0),
                     release_reason TEXT,
                     created_at TEXT NOT NULL,
                     settled_at TEXT,
                     UNIQUE(tenant_id, request_id)
                   )"""
            )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS uq_usage_tenant_idempotency
                   ON usage_reservations(tenant_id, idempotency_key)
                   WHERE idempotency_key IS NOT NULL"""
            )
            connection.execute(
                """CREATE INDEX IF NOT EXISTS ix_usage_tenant_period_status
                   ON usage_reservations(tenant_id, period_start, status)"""
            )

            current = connection.execute(
                """SELECT value FROM usage_ledger_metadata
                   WHERE key = 'schema_version'"""
            ).fetchone()

            if current is not None and current[0] != str(_SCHEMA_VERSION):
                raise sqlite3.DatabaseError(
                    "Unsupported AI usage ledger schema version"
                )

            connection.execute(
                """INSERT OR IGNORE INTO usage_ledger_metadata(key, value)
                   VALUES ('schema_version', ?)""",
                (str(_SCHEMA_VERSION),),
            )
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(
                str(self._path),
                timeout=self._busy_timeout_ms / 1_000,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
            connection.execute("PRAGMA synchronous = FULL")
            return connection
        except sqlite3.Error:
            raise UsageControlUnavailableError() from None

    def _estimate_input_tokens(self, prompt_chars: int) -> int:
        # Estimate only: never label this as provider-reported usage.
        return max(
            1,
            (prompt_chars + self._chars_per_input_token - 1)
            // self._chars_per_input_token,
        )

    @staticmethod
    def _price(
        pricing: ModelPricing,
        input_tokens: int,
        output_tokens: int,
    ) -> int:
        return (
            _cost_for_tokens(
                pricing.input_microusd_per_1k_tokens,
                input_tokens,
            )
            + _cost_for_tokens(
                pricing.output_microusd_per_1k_tokens,
                output_tokens,
            )
        )

    def _budget_for(self, tenant_id: str) -> int:
        return self._tenant_budgets.get(
            tenant_id,
            self._default_budget,
        )

    def _calculate_charge(
        self,
        row: sqlite3.Row,
        pricing: ModelPricing,
        usage: ProviderUsage | None,
    ) -> tuple[int, int, int, int, str]:
        if usage is None:
            input_tokens = self._estimate_input_tokens(int(row["prompt_chars"]))
            output_tokens = int(row["max_output_tokens"])
            source = "ESTIMATED_UNKNOWN_PROVIDER_USAGE"
        else:
            input_tokens = (
                usage.input_tokens
                if usage.input_tokens is not None
                else self._estimate_input_tokens(int(row["prompt_chars"]))
            )
            output_tokens = (
                usage.output_tokens
                if usage.output_tokens is not None
                else int(row["max_output_tokens"])
            )
            source = (
                "PROVIDER_REPORTED"
                if (
                    usage.input_tokens is not None
                    and usage.output_tokens is not None
                )
                else "MIXED_PROVIDER_AND_ESTIMATE"
            )

        reported_total = (
            usage.total_tokens
            if usage is not None and usage.total_tokens is not None
            else 0
        )
        # Partial usage may omit one side while still reporting a provider
        # total. Keep the stored total consistent with estimated token counts.
        total_tokens = max(
            reported_total,
            input_tokens + output_tokens,
        )
        cost = self._price(pricing, input_tokens, output_tokens)

        return cost, input_tokens, output_tokens, total_tokens, source

    @staticmethod
    def _require_matching_reservation(
        row: sqlite3.Row | None,
        reservation: UsageReservation,
    ) -> None:
        if row is None or (
            row["reservation_id"] != reservation.reservation_id
            or row["request_id"] != reservation.request_id
            or row["tenant_id"] != reservation.tenant_id
            or row["model_id"] != reservation.model_id
        ):
            raise UsageControlUnavailableError()


def microusd_to_usd(amount_microusd: int) -> str:
    """Format micro-USD without floating-point rounding."""
    _nonnegative_int(amount_microusd, "amount_microusd")
    dollars, micros = divmod(amount_microusd, _MICRO_USD_PER_USD)
    return f"${dollars}.{micros:06d}"
