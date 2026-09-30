from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import fingerprint
from .commission_contract import (
    CommissionContract,
    CommissionRateType,
)
from .commission_calculation_basis import (
    CommissionCalculationBasis,
)
from .financial_domain import (
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_CALCULATION_SCHEMA_VERSION = 1


class CommissionCalculationError(ValueError):
    """Base commission calculation error."""


class CommissionCalculationValidationError(
    CommissionCalculationError
):
    """Invalid calculation request or result."""


class CommissionCalculationEligibilityError(
    CommissionCalculationError
):
    """Eligibility was not externally confirmed."""


class CommissionCalculationCurrencyError(
    CommissionCalculationError
):
    """Calculation currency is incompatible with contract semantics."""


class CommissionCalculationState(str, Enum):
    CALCULATED = "CALCULATED"
    VOID = "VOID"
    SUPERSEDED = "SUPERSEDED"


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionCalculationValidationError(
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
        raise CommissionCalculationValidationError(
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
        raise CommissionCalculationValidationError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionCalculation:
    """Immutable deterministic commission calculation result.

    CORE-008 Point 03 owns:
    - calculation identity
    - contract version binding
    - calculation version
    - financial basis reference
    - deterministic commission amount
    - idempotency fingerprint
    - calculation provenance references

    It does NOT own:
    - deal lifecycle
    - ownership
    - authorization
    - governance
    - payment
    - ledger
    - settlement
    - event transport
    - Control Center state
    - ACRL recovery
    """

    calculation_id: str
    tenant_id: str
    commission_id: str
    contract_version: int
    calculation_version: int
    basis_reference: str
    source_reference: str
    formula_code: str
    basis_amount: MonetaryAmount
    commission_amount: MonetaryAmount
    calculated_at: datetime
    eligibility_reference: str
    provenance_reference: str
    idempotency_key: str
    state: CommissionCalculationState = (
        CommissionCalculationState.CALCULATED
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
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
            "calculation_version",
            _positive(
                self.calculation_version,
                "calculation_version",
            ),
        )

        object.__setattr__(
            self,
            "basis_reference",
            _text(
                self.basis_reference,
                "basis_reference",
            ),
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "formula_code",
            _text(
                self.formula_code,
                "formula_code",
            ),
        )

        if not isinstance(
            self.basis_amount,
            MonetaryAmount,
        ):
            raise CommissionCalculationValidationError(
                "basis_amount must be MonetaryAmount."
            )

        if not isinstance(
            self.commission_amount,
            MonetaryAmount,
        ):
            raise CommissionCalculationValidationError(
                "commission_amount must be MonetaryAmount."
            )

        object.__setattr__(
            self,
            "calculated_at",
            _aware(
                self.calculated_at,
                "calculated_at",
            ),
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
            "provenance_reference",
            _text(
                self.provenance_reference,
                "provenance_reference",
            ),
        )

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

        try:
            state = CommissionCalculationState(
                self.state
            )
        except ValueError as exc:
            raise CommissionCalculationValidationError(
                "Unsupported calculation state."
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

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionCalculationValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            dict(metadata),
        )

        if (
            self.basis_amount.currency.identity_key
            != self.commission_amount.currency.identity_key
        ):
            raise CommissionCalculationCurrencyError(
                "Basis and commission amounts must use "
                "identical currency semantics."
            )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, int, int]:
        return (
            self.tenant_id,
            self.commission_id,
            self.contract_version,
            self.calculation_version,
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
                "Commission calculation crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.COMMISSION_CALCULATION"
            ),
            "schema_version": (
                CORE008_COMMISSION_CALCULATION_SCHEMA_VERSION
            ),
            "calculation_id": (
                self.calculation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "contract_version": (
                self.contract_version
            ),
            "calculation_version": (
                self.calculation_version
            ),
            "basis_reference": (
                self.basis_reference
            ),
            "source_reference": (
                self.source_reference
            ),
            "formula_code": (
                self.formula_code
            ),
            "basis_amount": (
                self.basis_amount.to_dict()
            ),
            "commission_amount": (
                self.commission_amount.to_dict()
            ),
            "calculated_at": (
                self.calculated_at.isoformat()
            ),
            "eligibility_reference": (
                self.eligibility_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "idempotency_key": (
                self.idempotency_key
            ),
            "state": self.state.value,
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


def calculate_commission(
    contract: CommissionContract,
    basis: CommissionCalculationBasis,
    *,
    calculated_at: datetime,
    eligibility_confirmed: bool,
    eligibility_reference: str,
    provenance_reference: str,
    calculation_version: int = 1,
    calculation_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CommissionCalculation:
    """Calculate one deterministic commission amount.

    Eligibility is intentionally supplied as an authoritative external
    result. This prevents CORE-008 from becoming a duplicate governance,
    ownership, or authorization engine.
    """

    if not isinstance(
        contract,
        CommissionContract,
    ):
        raise CommissionCalculationValidationError(
            "contract must be CommissionContract."
        )

    if not isinstance(
        basis,
        CommissionCalculationBasis,
    ):
        raise CommissionCalculationValidationError(
            "basis must be CommissionCalculationBasis."
        )

    when = _aware(
        calculated_at,
        "calculated_at",
    )

    if not eligibility_confirmed:
        raise CommissionCalculationEligibilityError(
            "Eligibility must be externally confirmed "
            "before calculation."
        )

    eligibility_reference = _text(
        eligibility_reference,
        "eligibility_reference",
    )

    provenance_reference = _text(
        provenance_reference,
        "provenance_reference",
    )

    if not contract.is_effective_at(
        when
    ):
        raise CommissionCalculationValidationError(
            "Commission contract is not ACTIVE "
            "at calculation time."
        )

    if (
        basis.source_reference
        != contract.basis.source_reference
    ):
        raise CommissionCalculationValidationError(
            "Calculation basis source_reference does "
            "not match the commission contract basis."
        )

    if (
        basis.basis_code
        != contract.basis.basis_type.value
    ):
        raise CommissionCalculationValidationError(
            "Calculation basis code does not match "
            "the commission contract basis type."
        )

    if contract.rate.rate_type is CommissionRateType.PERCENTAGE:
        result_currency = basis.amount.currency

        raw_amount = (
            basis.amount.amount
            * contract.rate.value
            / Decimal("100")
        )

        commission_amount = MonetaryAmount.create(
            raw_amount,
            result_currency,
        )

        formula = "PERCENTAGE_OF_BASIS"

    else:
        if contract.rate.currency is None:
            raise CommissionCalculationCurrencyError(
                "Fixed commission rate requires currency."
            )

        if (
            contract.rate.currency.identity_key
            != basis.amount.currency.identity_key
        ):
            raise CommissionCalculationCurrencyError(
                "Fixed commission currency must match "
                "calculation-basis currency."
            )

        commission_amount = MonetaryAmount.create(
            contract.rate.value,
            contract.rate.currency,
        )

        formula = "FIXED_AMOUNT"

    provisional_payload = {
        "tenant_id": contract.tenant_id,
        "commission_id": contract.commission_id,
        "contract_version": (
            contract.contract_version
        ),
        "calculation_version": (
            calculation_version
        ),
        "basis_reference": (
            basis.basis_reference
        ),
        "source_reference": (
            basis.source_reference
        ),
        "formula_code": formula,
        "basis_amount": (
            basis.amount.to_dict()
        ),
        "commission_amount": (
            commission_amount.to_dict()
        ),
        "calculated_at": (
            when.isoformat()
        ),
        "eligibility_reference": (
            eligibility_reference
        ),
        "provenance_reference": (
            provenance_reference
        ),
    }

    idempotency_key = fingerprint(
        provisional_payload
    )

    return CommissionCalculation(
        calculation_id=(
            calculation_id
            or str(uuid4())
        ),
        tenant_id=contract.tenant_id,
        commission_id=contract.commission_id,
        contract_version=(
            contract.contract_version
        ),
        calculation_version=(
            calculation_version
        ),
        basis_reference=(
            basis.basis_reference
        ),
        source_reference=(
            basis.source_reference
        ),
        formula_code=formula,
        basis_amount=basis.amount,
        commission_amount=commission_amount,
        calculated_at=when,
        eligibility_reference=(
            eligibility_reference
        ),
        provenance_reference=(
            provenance_reference
        ),
        idempotency_key=idempotency_key,
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
    )


__all__ = [
    "CORE008_COMMISSION_CALCULATION_SCHEMA_VERSION",
    "CommissionCalculationError",
    "CommissionCalculationValidationError",
    "CommissionCalculationEligibilityError",
    "CommissionCalculationCurrencyError",
    "CommissionCalculationState",
    "CommissionCalculation",
    "calculate_commission",
]
