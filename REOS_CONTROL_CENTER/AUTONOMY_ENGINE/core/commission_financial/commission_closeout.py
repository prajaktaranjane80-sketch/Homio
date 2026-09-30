from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_statement import CommissionStatement


CORE008_COMMISSION_CLOSEOUT_SCHEMA_VERSION = 1


class CommissionCloseoutError(ValueError):
    """Base closeout error."""


class CommissionCloseoutValidationError(
    CommissionCloseoutError
):
    """Invalid financial closeout."""


class CommissionCloseoutState(str, Enum):
    OPEN = "OPEN"
    READY = "READY"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    VOID = "VOID"


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionCloseoutValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionCloseoutValidationError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _positive(
    value: int,
    field: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionCloseoutValidationError(
            f"{field} must be a positive integer."
        )
    return value


@dataclass(frozen=True, slots=True)
class CommissionCloseout:
    """Immutable financial closeout decision record.

    Closeout certifies the condition of the financial
    record. It does not perform ledger posting or payment.
    """

    closeout_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    closeout_version: int
    outstanding_amount_reference: str
    unresolved_variance_reference: str
    closeout_reason: str
    closeout_authorization_reference: str
    provenance_reference: str
    closed_at: datetime | None
    state: CommissionCloseoutState
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "closeout_id",
            "tenant_id",
            "commission_id",
            "statement_id",
            "outstanding_amount_reference",
            "unresolved_variance_reference",
            "closeout_reason",
            "closeout_authorization_reference",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        object.__setattr__(
            self,
            "closeout_version",
            _positive(
                self.closeout_version,
                "closeout_version",
            ),
        )

        try:
            state = CommissionCloseoutState(
                self.state
            )
        except ValueError as exc:
            raise CommissionCloseoutValidationError(
                "Unsupported closeout state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        if self.closed_at is not None:
            object.__setattr__(
                self,
                "closed_at",
                _aware(
                    self.closed_at,
                    "closed_at",
                ),
            )

        if (
            state is CommissionCloseoutState.CLOSED
            and self.closed_at is None
        ):
            raise CommissionCloseoutValidationError(
                "CLOSED closeout requires closed_at."
            )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionCloseoutValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            deep_freeze(
                dict(metadata),
                field_name="metadata",
            ),
        )

    @classmethod
    def evaluate(
        cls,
        statement: CommissionStatement,
        *,
        closeout_id: str | None = None,
        closeout_version: int = 1,
        closeout_reason: str,
        closeout_authorization_reference: str,
        provenance_reference: str,
        closed_at: datetime | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionCloseout":
        if not isinstance(
            statement,
            CommissionStatement,
        ):
            raise CommissionCloseoutValidationError(
                "statement must be CommissionStatement."
            )

        if (
            statement.outstanding_amount.is_zero
            and statement.unresolved_variance.is_zero
        ):
            state = CommissionCloseoutState.READY
        else:
            state = CommissionCloseoutState.OPEN

        if state is CommissionCloseoutState.READY:
            if closed_at is not None:
                state = CommissionCloseoutState.CLOSED

        return cls(
            closeout_id=(
                closeout_id
                or str(uuid4())
            ),
            tenant_id=statement.tenant_id,
            commission_id=statement.commission_id,
            statement_id=statement.statement_id,
            closeout_version=closeout_version,
            outstanding_amount_reference=(
                statement.outstanding_amount.immutable_fingerprint
                if hasattr(
                    statement.outstanding_amount,
                    "immutable_fingerprint",
                )
                else statement.immutable_fingerprint
            ),
            unresolved_variance_reference=(
                statement.immutable_fingerprint
            ),
            closeout_reason=closeout_reason,
            closeout_authorization_reference=(
                closeout_authorization_reference
            ),
            provenance_reference=provenance_reference,
            closed_at=closed_at,
            state=state,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.closeout_id,
            self.closeout_version,
        )

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise CommissionCloseoutError(
                "Closeout crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_CLOSEOUT"
            ),
            "schema_version": (
                CORE008_COMMISSION_CLOSEOUT_SCHEMA_VERSION
            ),
            "closeout_id": self.closeout_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_id": self.statement_id,
            "closeout_version": (
                self.closeout_version
            ),
            "outstanding_amount_reference": (
                self.outstanding_amount_reference
            ),
            "unresolved_variance_reference": (
                self.unresolved_variance_reference
            ),
            "closeout_reason": (
                self.closeout_reason
            ),
            "closeout_authorization_reference": (
                self.closeout_authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "closed_at": (
                self.closed_at.isoformat()
                if self.closed_at is not None
                else None
            ),
            "state": self.state.value,
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_CLOSEOUT_SCHEMA_VERSION",
    "CommissionCloseoutError",
    "CommissionCloseoutValidationError",
    "CommissionCloseoutState",
    "CommissionCloseout",
]
