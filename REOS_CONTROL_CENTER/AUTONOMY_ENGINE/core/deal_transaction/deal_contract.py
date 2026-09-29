from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .deal import Deal


DEAL_CONTRACT_SCHEMA_VERSION = "1.0"


class DealStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    MATCHED = "MATCHED"
    VISIT_PENDING = "VISIT_PENDING"
    VISITED = "VISITED"
    OFFERED = "OFFERED"
    NEGOTIATING = "NEGOTIATING"
    BOOKING_PENDING = "BOOKING_PENDING"
    BOOKED = "BOOKED"
    AGREEMENT_PENDING = "AGREEMENT_PENDING"
    AGREED = "AGREED"
    REGISTRATION_PENDING = "REGISTRATION_PENDING"
    REGISTERED = "REGISTERED"
    COMPLETION_PENDING = "COMPLETION_PENDING"
    COMPLETED = "COMPLETED"

    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    FRAUD_BLOCKED = "FRAUD_BLOCKED"


NOMINAL_TRANSITIONS = {
    DealStatus.QUALIFIED: frozenset({DealStatus.MATCHED}),
    DealStatus.MATCHED: frozenset({DealStatus.VISIT_PENDING}),
    DealStatus.VISIT_PENDING: frozenset({DealStatus.VISITED}),
    DealStatus.VISITED: frozenset({DealStatus.OFFERED}),
    DealStatus.OFFERED: frozenset({
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
    }),
    DealStatus.NEGOTIATING: frozenset({
        DealStatus.OFFERED,
        DealStatus.BOOKING_PENDING,
    }),
    DealStatus.BOOKING_PENDING: frozenset({DealStatus.BOOKED}),
    DealStatus.BOOKED: frozenset({DealStatus.AGREEMENT_PENDING}),
    DealStatus.AGREEMENT_PENDING: frozenset({DealStatus.AGREED}),
    DealStatus.AGREED: frozenset({DealStatus.REGISTRATION_PENDING}),
    DealStatus.REGISTRATION_PENDING: frozenset({DealStatus.REGISTERED}),
    DealStatus.REGISTERED: frozenset({DealStatus.COMPLETION_PENDING}),
    DealStatus.COMPLETION_PENDING: frozenset({DealStatus.COMPLETED}),
}

TERMINAL_STATES = frozenset({
    DealStatus.COMPLETED,
    DealStatus.CANCELLED,
    DealStatus.EXPIRED,
    DealStatus.REJECTED,
    DealStatus.DISPUTED,
    DealStatus.FRAUD_BLOCKED,
})

EXPIRY_STATES = frozenset({
    DealStatus.QUALIFIED,
    DealStatus.MATCHED,
    DealStatus.VISIT_PENDING,
    DealStatus.VISITED,
    DealStatus.OFFERED,
    DealStatus.NEGOTIATING,
    DealStatus.BOOKING_PENDING,
    DealStatus.AGREEMENT_PENDING,
})

REJECTION_STATES = EXPIRY_STATES

DISPUTE_STATES = frozenset({
    DealStatus.BOOKED,
    DealStatus.AGREEMENT_PENDING,
    DealStatus.AGREED,
    DealStatus.REGISTRATION_PENDING,
    DealStatus.REGISTERED,
    DealStatus.COMPLETION_PENDING,
})


def require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def utc_datetime(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "Expected a valid ISO-8601 datetime."
            ) from exc

    if not isinstance(value, datetime):
        raise ValueError(
            "Expected datetime, ISO-8601 string, or None."
        )

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def payload_fingerprint(value: Mapping[str, Any]) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class DealHistoryEntry:
    history_id: str
    from_status: DealStatus | None
    to_status: DealStatus
    version: int
    changed_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("history version must be >= 1.")

        object.__setattr__(
            self,
            "to_status",
            DealStatus(self.to_status),
        )

        if self.from_status is not None:
            object.__setattr__(
                self,
                "from_status",
                DealStatus(self.from_status),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "from_status": (
                self.from_status.value
                if self.from_status is not None
                else None
            ),
            "to_status": self.to_status.value,
            "version": self.version,
            "changed_at": self.changed_at.isoformat(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DealContract:
    deal_id: str
    tenant_id: str
    schema_version: str
    contract_fingerprint: str
    status: DealStatus
    version: int
    identity_key: str
    created_at: str
    updated_at: str

    @classmethod
    def from_deal(cls, deal: Deal) -> "DealContract":
        payload = deal.to_dict(include_contract=False)

        return cls(
            deal_id=deal.deal_id,
            tenant_id=deal.tenant_id,
            schema_version=DEAL_CONTRACT_SCHEMA_VERSION,
            contract_fingerprint=payload_fingerprint(payload),
            status=deal.status,
            version=deal.version,
            identity_key=deal.identity_key,
            created_at=deal.created_at.isoformat(),
            updated_at=deal.updated_at.isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "schema_version": self.schema_version,
            "contract_fingerprint": self.contract_fingerprint,
            "status": self.status.value,
            "version": self.version,
            "identity_key": self.identity_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def validate_contract_payload(
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    required = (
        "deal_id",
        "tenant_id",
        "identity_key",
        "status",
        "version",
        "created_at",
        "updated_at",
    )

    errors = tuple(
        f"missing:{name}"
        for name in required
        if name not in payload
    )

    if errors:
        return errors

    if payload["identity_key"] != (
        f'{payload["tenant_id"]}:{payload["deal_id"]}'
    ):
        return ("invalid:identity_key",)

    try:
        version = int(payload["version"])
    except (TypeError, ValueError):
        return ("invalid:version",)

    if version < 1:
        return ("invalid:version",)

    try:
        DealStatus(payload["status"])
    except (TypeError, ValueError):
        return ("invalid:status",)

    return ()
