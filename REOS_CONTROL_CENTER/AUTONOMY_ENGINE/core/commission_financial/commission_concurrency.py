from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping


class CommissionConcurrencyError(RuntimeError):
    """Financial concurrency error."""


class CommissionStaleVersionError(
    CommissionConcurrencyError
):
    """Expected financial version is stale."""


class CommissionDuplicateCommandError(
    CommissionConcurrencyError
):
    """Same financial command has conflicting content."""


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field} must be non-empty text."
        )
    return value.strip()


@dataclass(frozen=True, slots=True)
class FinancialVersionToken:
    tenant_id: str
    aggregate_type: str
    aggregate_id: str
    version: int

    def __post_init__(self) -> None:
        for field in (
            "tenant_id",
            "aggregate_type",
            "aggregate_id",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        if (
            isinstance(self.version, bool)
            or not isinstance(self.version, int)
            or self.version < 0
        ):
            raise ValueError(
                "version must be a non-negative integer."
            )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.aggregate_type,
            self.aggregate_id,
        )


@dataclass(frozen=True, slots=True)
class FinancialIdempotencyRecord:
    tenant_id: str
    operation: str
    idempotency_key: str
    command_fingerprint: str
    first_seen_at: datetime
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "tenant_id",
            "operation",
            "idempotency_key",
            "command_fingerprint",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        if (
            not isinstance(
                self.first_seen_at,
                datetime,
            )
            or self.first_seen_at.tzinfo is None
            or self.first_seen_at.utcoffset() is None
        ):
            raise ValueError(
                "first_seen_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "first_seen_at",
            self.first_seen_at.astimezone(
                timezone.utc
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(
                    {}
                    if self.metadata == ()
                    else self.metadata
                )
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        return (
            self.tenant_id,
            self.operation,
            self.idempotency_key,
        )

    def compare(
        self,
        command_fingerprint: str,
    ) -> bool:
        return (
            self.command_fingerprint
            == _text(
                command_fingerprint,
                "command_fingerprint",
            )
        )


@dataclass(frozen=True, slots=True)
class FinancialTransitionContract:
    aggregate_type: str
    aggregate_id: str
    expected_version: int
    new_version: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "aggregate_type",
            _text(
                self.aggregate_type,
                "aggregate_type",
            ),
        )

        object.__setattr__(
            self,
            "aggregate_id",
            _text(
                self.aggregate_id,
                "aggregate_id",
            ),
        )

        if (
            isinstance(self.expected_version, bool)
            or not isinstance(
                self.expected_version,
                int,
            )
            or self.expected_version < 0
        ):
            raise ValueError(
                "expected_version must be non-negative."
            )

        if (
            self.new_version
            != self.expected_version + 1
        ):
            raise ValueError(
                "new_version must be exactly expected_version + 1."
            )


class FinancialConcurrencyBoundary:
    """
    Deterministic optimistic-concurrency boundary.

    It validates preconditions; it does not own persistence or locking.
    """

    @staticmethod
    def assert_version(
        expected: FinancialVersionToken,
        actual: FinancialVersionToken,
    ) -> None:
        if expected.identity_key != actual.identity_key:
            raise CommissionConcurrencyError(
                "Version tokens refer to different financial aggregates."
            )

        if expected.version != actual.version:
            raise CommissionStaleVersionError(
                "Financial aggregate version is stale."
            )

    @staticmethod
    def next_version(
        token: FinancialVersionToken,
    ) -> FinancialVersionToken:
        return FinancialVersionToken(
            tenant_id=token.tenant_id,
            aggregate_type=token.aggregate_type,
            aggregate_id=token.aggregate_id,
            version=token.version + 1,
        )

    @staticmethod
    def command_fingerprint(
        payload: Mapping[str, Any],
    ) -> str:
        if not isinstance(
            payload,
            Mapping,
        ):
            raise TypeError(
                "payload must be a mapping."
            )

        canonical = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def assert_idempotent(
        record: FinancialIdempotencyRecord,
        command_fingerprint: str,
    ) -> None:
        if record.compare(
            command_fingerprint
        ):
            return

        raise CommissionDuplicateCommandError(
            "Duplicate financial command contains different content."
        )


__all__ = [
    "CommissionConcurrencyError",
    "CommissionDuplicateCommandError",
    "CommissionStaleVersionError",
    "FinancialConcurrencyBoundary",
    "FinancialIdempotencyRecord",
    "FinancialTransitionContract",
    "FinancialVersionToken",
]
