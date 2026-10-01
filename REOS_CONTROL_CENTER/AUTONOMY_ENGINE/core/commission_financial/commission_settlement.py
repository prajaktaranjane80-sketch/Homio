from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_allocation import CommissionAllocation
from .financial_domain import (
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_SETTLEMENT_SCHEMA_VERSION = 1


class CommissionSettlementError(ValueError):
    """Base settlement error."""


class CommissionSettlementValidationError(
    CommissionSettlementError
):
    """Invalid settlement instruction."""


class CommissionSettlementState(str, Enum):
    READY = "READY"
    AUTHORIZATION_PENDING = "AUTHORIZATION_PENDING"
    AUTHORIZED = "AUTHORIZED"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CommissionSettlementMode(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionSettlementValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionSettlementValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionSettlementValidationError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionSettlement:
    """Immutable financial settlement instruction.

    CORE-008 owns the financial settlement obligation/reference.

    It does NOT own:
    - bank/payment gateway execution
    - payment provider state
    - ledger posting
    - ownership
    - deal lifecycle
    - authorization engine
    - event transport
    - Control Center state
    - ACRL state
    """

    settlement_id: str
    tenant_id: str
    commission_id: str
    allocation_set_id: str
    settlement_version: int
    mode: CommissionSettlementMode
    amount: MonetaryAmount
    beneficiary_party_id: str
    beneficiary_party_type: str
    settlement_reference: str
    authorization_reference: str
    provenance_reference: str
    requested_at: datetime
    state: CommissionSettlementState = (
        CommissionSettlementState.READY
    )
    external_reference: str | None = None
    failure_code: str | None = None
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "settlement_id",
            "tenant_id",
            "commission_id",
            "allocation_set_id",
            "beneficiary_party_id",
            "beneficiary_party_type",
            "settlement_reference",
            "authorization_reference",
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
            "settlement_version",
            _positive(
                self.settlement_version,
                "settlement_version",
            ),
        )

        try:
            mode = CommissionSettlementMode(
                self.mode
            )
        except ValueError as exc:
            raise CommissionSettlementValidationError(
                "Unsupported settlement mode."
            ) from exc

        object.__setattr__(
            self,
            "mode",
            mode,
        )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionSettlementValidationError(
                "amount must be MonetaryAmount."
            )

        if self.amount.amount < 0:
            raise CommissionSettlementValidationError(
                "Settlement amount cannot be negative."
            )

        object.__setattr__(
            self,
            "requested_at",
            _aware(
                self.requested_at,
                "requested_at",
            ),
        )

        try:
            state = CommissionSettlementState(
                self.state
            )
        except ValueError as exc:
            raise CommissionSettlementValidationError(
                "Unsupported settlement state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        if self.external_reference is not None:
            object.__setattr__(
                self,
                "external_reference",
                _text(
                    self.external_reference,
                    "external_reference",
                ),
            )

        if self.failure_code is not None:
            object.__setattr__(
                self,
                "failure_code",
                _text(
                    self.failure_code,
                    "failure_code",
                ),
            )

        if (
            state is CommissionSettlementState.FAILED
            and not self.failure_code
        ):
            raise CommissionSettlementValidationError(
                "FAILED settlement requires failure_code."
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
            raise CommissionSettlementValidationError(
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
    def from_allocation(
        cls,
        allocation: CommissionAllocation,
        *,
        settlement_id: str | None = None,
        settlement_version: int = 1,
        amount: MonetaryAmount | None = None,
        authorization_reference: str,
        provenance_reference: str,
        requested_at: datetime,
        mode: CommissionSettlementMode | None = None,
        external_reference: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionSettlement":
        if not isinstance(
            allocation,
            CommissionAllocation,
        ):
            raise CommissionSettlementValidationError(
                "allocation must be CommissionAllocation."
            )

        settlement_amount = (
            allocation.total_amount
            if amount is None
            else amount
        )

        if (
            settlement_amount.currency.identity_key
            != allocation.total_amount.currency.identity_key
        ):
            raise CommissionSettlementValidationError(
                "Settlement currency must match allocation."
            )

        if (
            settlement_amount.amount < 0
            or settlement_amount.amount
            > allocation.total_amount.amount
        ):
            raise CommissionSettlementValidationError(
                "Settlement amount must be within "
                "the allocated amount."
            )

        resolved_mode = (
            CommissionSettlementMode.FULL
            if (
                settlement_amount.amount
                == allocation.total_amount.amount
            )
            else CommissionSettlementMode.PARTIAL
        )

        if mode is not None:
            requested_mode = CommissionSettlementMode(
                mode
            )

            if requested_mode is not resolved_mode:
                raise CommissionSettlementValidationError(
                    "Settlement mode does not match "
                    "settlement amount."
                )

        first_party = allocation.lines[0].party

        return cls(
            settlement_id=(
                settlement_id
                or str(uuid4())
            ),
            tenant_id=allocation.tenant_id,
            commission_id=allocation.commission_id,
            allocation_set_id=(
                allocation.allocation_set_id
            ),
            settlement_version=settlement_version,
            mode=resolved_mode,
            amount=settlement_amount,
            beneficiary_party_id=(
                first_party.party_id
            ),
            beneficiary_party_type=(
                first_party.party_type.value
            ),
            settlement_reference=(
                f"{allocation.allocation_set_id}:"
                f"{settlement_version}"
            ),
            authorization_reference=(
                authorization_reference
            ),
            provenance_reference=(
                provenance_reference
            ),
            requested_at=requested_at,
            external_reference=external_reference,
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
            self.settlement_id,
            self.settlement_version,
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
            raise FinancialTenantScopeError(
                "Settlement crossed tenant scope."
            )

    def with_state(
        self,
        state: CommissionSettlementState,
        *,
        external_reference: str | None = None,
        failure_code: str | None = None,
    ) -> "CommissionSettlement":
        return CommissionSettlement(
            settlement_id=self.settlement_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            allocation_set_id=self.allocation_set_id,
            settlement_version=self.settlement_version,
            mode=self.mode,
            amount=self.amount,
            beneficiary_party_id=(
                self.beneficiary_party_id
            ),
            beneficiary_party_type=(
                self.beneficiary_party_type
            ),
            settlement_reference=(
                self.settlement_reference
            ),
            authorization_reference=(
                self.authorization_reference
            ),
            provenance_reference=(
                self.provenance_reference
            ),
            requested_at=self.requested_at,
            state=state,
            external_reference=(
                external_reference
                if external_reference is not None
                else self.external_reference
            ),
            failure_code=failure_code,
            metadata=self.metadata,
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.COMMISSION_SETTLEMENT"
            ),
            "schema_version": (
                CORE008_COMMISSION_SETTLEMENT_SCHEMA_VERSION
            ),
            "settlement_id": (
                self.settlement_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "settlement_version": (
                self.settlement_version
            ),
            "mode": self.mode.value,
            "amount": self.amount.to_dict(),
            "beneficiary_party_id": (
                self.beneficiary_party_id
            ),
            "beneficiary_party_type": (
                self.beneficiary_party_type
            ),
            "settlement_reference": (
                self.settlement_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "requested_at": (
                self.requested_at.isoformat()
            ),
            "state": self.state.value,
            "external_reference": (
                self.external_reference
            ),
            "failure_code": self.failure_code,
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_SETTLEMENT_SCHEMA_VERSION",
    "CommissionSettlementError",
    "CommissionSettlementValidationError",
    "CommissionSettlementState",
    "CommissionSettlementMode",
    "CommissionSettlement",
]
