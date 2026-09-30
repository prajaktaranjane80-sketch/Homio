from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from ..contract_primitives import fingerprint
from .commission_calculation import CommissionCalculation
from .commission_contract import CommissionPartyReference
from .financial_domain import (
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_ENTITLEMENT_SCHEMA_VERSION = 1


class CommissionEntitlementError(ValueError):
    """Base entitlement error."""


class CommissionEntitlementValidationError(
    CommissionEntitlementError
):
    """Invalid entitlement."""


class CommissionEntitlementState(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    VOID = "VOID"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionEntitlementValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionEntitlementValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionEntitlementValidationError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionEntitlement:
    """Immutable financial entitlement derived from an approved calculation.

    CORE-003 owns customer/lead ownership.
    CORE-006 owns deal/transaction truth.
    CORE-001 owns authorization and identity.
    CORE-008 records the monetary entitlement established from
    authoritative upstream references.
    """

    entitlement_id: str
    tenant_id: str
    commission_id: str
    contract_version: int
    calculation_id: str
    calculation_version: int
    entitled_party: CommissionPartyReference
    entitled_amount: MonetaryAmount
    eligibility_reference: str
    authorization_reference: str
    provenance_reference: str
    established_at: datetime
    state: CommissionEntitlementState = (
        CommissionEntitlementState.PENDING
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entitlement_id",
            _text(
                self.entitlement_id,
                "entitlement_id",
            ),
        )
        object.__setattr__(
            self,
            "tenant_id",
            _text(
                self.tenant_id,
                "tenant_id",
            ),
        )
        object.__setattr__(
            self,
            "commission_id",
            _text(
                self.commission_id,
                "commission_id",
            ),
        )
        object.__setattr__(
            self,
            "contract_version",
            _positive(
                self.contract_version,
                "contract_version",
            ),
        )
        object.__setattr__(
            self,
            "calculation_id",
            _text(
                self.calculation_id,
                "calculation_id",
            ),
        )
        object.__setattr__(
            self,
            "calculation_version",
            _positive(
                self.calculation_version,
                "calculation_version",
            ),
        )

        if not isinstance(
            self.entitled_party,
            CommissionPartyReference,
        ):
            raise CommissionEntitlementValidationError(
                "entitled_party must be "
                "CommissionPartyReference."
            )

        if not isinstance(
            self.entitled_amount,
            MonetaryAmount,
        ):
            raise CommissionEntitlementValidationError(
                "entitled_amount must be MonetaryAmount."
            )

        if self.entitled_amount.amount < 0:
            raise CommissionEntitlementValidationError(
                "entitled_amount cannot be negative."
            )

        object.__setattr__(
            self,
            "eligibility_reference",
            _text(
                self.eligibility_reference,
                "eligibility_reference",
            ),
        )
        object.__setattr__(
            self,
            "authorization_reference",
            _text(
                self.authorization_reference,
                "authorization_reference",
            ),
        )
        object.__setattr__(
            self,
            "provenance_reference",
            _text(
                self.provenance_reference,
                "provenance_reference",
            ),
        )
        object.__setattr__(
            self,
            "established_at",
            _aware(
                self.established_at,
                "established_at",
            ),
        )

        try:
            state = CommissionEntitlementState(
                self.state
            )
        except ValueError as exc:
            raise CommissionEntitlementValidationError(
                "Unsupported entitlement state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(metadata, Mapping):
            raise CommissionEntitlementValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            dict(metadata),
        )

    @classmethod
    def from_calculation(
        cls,
        calculation: CommissionCalculation,
        *,
        entitlement_id: str,
        entitled_party: CommissionPartyReference,
        eligibility_reference: str,
        authorization_reference: str,
        provenance_reference: str,
        established_at: datetime,
        entitled_amount: MonetaryAmount | None = None,
        state: CommissionEntitlementState = (
            CommissionEntitlementState.PENDING
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionEntitlement":
        if not isinstance(
            calculation,
            CommissionCalculation,
        ):
            raise CommissionEntitlementValidationError(
                "calculation must be CommissionCalculation."
            )

        amount = (
            calculation.commission_amount
            if entitled_amount is None
            else entitled_amount
        )

        if (
            amount.currency.identity_key
            != calculation.commission_amount.currency.identity_key
        ):
            raise CommissionEntitlementValidationError(
                "Entitlement currency must match "
                "calculation currency."
            )

        if (
            amount.amount
            > calculation.commission_amount.amount
        ):
            raise CommissionEntitlementValidationError(
                "Entitlement cannot exceed calculated "
                "commission amount."
            )

        return cls(
            entitlement_id=entitlement_id,
            tenant_id=calculation.tenant_id,
            commission_id=calculation.commission_id,
            contract_version=(
                calculation.contract_version
            ),
            calculation_id=(
                calculation.calculation_id
            ),
            calculation_version=(
                calculation.calculation_version
            ),
            entitled_party=entitled_party,
            entitled_amount=amount,
            eligibility_reference=eligibility_reference,
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            established_at=established_at,
            state=state,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.tenant_id,
            self.entitlement_id,
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
                "Commission entitlement crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.COMMISSION_ENTITLEMENT"
            ),
            "schema_version": (
                CORE008_COMMISSION_ENTITLEMENT_SCHEMA_VERSION
            ),
            "entitlement_id": (
                self.entitlement_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "contract_version": (
                self.contract_version
            ),
            "calculation_id": (
                self.calculation_id
            ),
            "calculation_version": (
                self.calculation_version
            ),
            "entitled_party": (
                self.entitled_party.to_dict()
            ),
            "entitled_amount": (
                self.entitled_amount.to_dict()
            ),
            "eligibility_reference": (
                self.eligibility_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "established_at": (
                self.established_at.isoformat()
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
    "CORE008_COMMISSION_ENTITLEMENT_SCHEMA_VERSION",
    "CommissionEntitlementError",
    "CommissionEntitlementValidationError",
    "CommissionEntitlementState",
    "CommissionEntitlement",
]
