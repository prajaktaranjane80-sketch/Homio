from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from ..contract_primitives import fingerprint
from .commission_calculation import CommissionCalculation
from .commission_contract import CommissionPartyReference
from .commission_entitlement import (
    CommissionEntitlement,
)
from .financial_domain import (
    FinancialCurrencyMismatchError,
    MonetaryAmount,
)


CORE008_COMMISSION_ALLOCATION_SCHEMA_VERSION = 1


class CommissionAllocationError(ValueError):
    """Base allocation error."""


class CommissionAllocationValidationError(
    CommissionAllocationError
):
    """Invalid allocation."""


@dataclass(frozen=True, slots=True)
class CommissionAllocationLine:
    """One deterministic allocation line."""

    allocation_id: str
    entitlement_id: str
    party: CommissionPartyReference
    amount: MonetaryAmount
    allocation_ratio: Decimal
    rank: int
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.allocation_id,
            str,
        ) or not self.allocation_id.strip():
            raise CommissionAllocationValidationError(
                "allocation_id is required."
            )

        if not isinstance(
            self.entitlement_id,
            str,
        ) or not self.entitlement_id.strip():
            raise CommissionAllocationValidationError(
                "entitlement_id is required."
            )

        if not isinstance(
            self.party,
            CommissionPartyReference,
        ):
            raise CommissionAllocationValidationError(
                "party must be CommissionPartyReference."
            )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionAllocationValidationError(
                "amount must be MonetaryAmount."
            )

        if self.amount.amount < 0:
            raise CommissionAllocationValidationError(
                "allocation amount cannot be negative."
            )

        if isinstance(
            self.allocation_ratio,
            bool,
        ):
            raise CommissionAllocationValidationError(
                "allocation_ratio cannot be boolean."
            )

        try:
            ratio = Decimal(
                str(self.allocation_ratio)
            )
        except Exception as exc:
            raise CommissionAllocationValidationError(
                "allocation_ratio must be decimal."
            ) from exc

        if ratio < 0 or ratio > 100:
            raise CommissionAllocationValidationError(
                "allocation_ratio must be between 0 and 100."
            )

        object.__setattr__(
            self,
            "allocation_ratio",
            ratio,
        )

        if (
            isinstance(self.rank, bool)
            or not isinstance(self.rank, int)
            or self.rank < 1
        ):
            raise CommissionAllocationValidationError(
                "rank must be positive integer."
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
            raise CommissionAllocationValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "allocation_id",
            self.allocation_id.strip(),
        )
        object.__setattr__(
            self,
            "entitlement_id",
            self.entitlement_id.strip(),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allocation_id": (
                self.allocation_id
            ),
            "entitlement_id": (
                self.entitlement_id
            ),
            "party": self.party.to_dict(),
            "amount": self.amount.to_dict(),
            "allocation_ratio": format(
                self.allocation_ratio,
                "f",
            ),
            "rank": self.rank,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CommissionAllocation:
    """Immutable complete allocation of one calculation.

    Allocation only distributes a financially established amount.
    It does not establish ownership or authorization.
    """

    allocation_set_id: str
    tenant_id: str
    commission_id: str
    calculation_id: str
    calculation_version: int
    total_amount: MonetaryAmount
    lines: tuple[
        CommissionAllocationLine,
        ...
    ]
    eligibility_reference: str
    authorization_reference: str
    provenance_reference: str
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        if not self.allocation_set_id.strip():
            raise CommissionAllocationValidationError(
                "allocation_set_id is required."
            )

        if not self.tenant_id.strip():
            raise CommissionAllocationValidationError(
                "tenant_id is required."
            )

        if not self.commission_id.strip():
            raise CommissionAllocationValidationError(
                "commission_id is required."
            )

        if not self.calculation_id.strip():
            raise CommissionAllocationValidationError(
                "calculation_id is required."
            )

        if (
            isinstance(
                self.calculation_version,
                bool,
            )
            or not isinstance(
                self.calculation_version,
                int,
            )
            or self.calculation_version < 1
        ):
            raise CommissionAllocationValidationError(
                "calculation_version must be positive."
            )

        if not isinstance(
            self.total_amount,
            MonetaryAmount,
        ):
            raise CommissionAllocationValidationError(
                "total_amount must be MonetaryAmount."
            )

        lines = tuple(self.lines)

        if not lines:
            raise CommissionAllocationValidationError(
                "allocation must contain at least one line."
            )

        if any(
            not isinstance(
                line,
                CommissionAllocationLine,
            )
            for line in lines
        ):
            raise CommissionAllocationValidationError(
                "lines contain invalid values."
            )

        currencies = {
            line.amount.currency.identity_key
            for line in lines
        }

        if (
            len(currencies) != 1
            or next(iter(currencies))
            != self.total_amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "All allocation lines must use the "
                "total allocation currency."
            )

        amount_sum = sum(
            (
                line.amount.amount
                for line in lines
            ),
            Decimal("0"),
        )

        if amount_sum != self.total_amount.amount:
            raise CommissionAllocationValidationError(
                "Allocation line amounts must equal "
                "total_amount exactly."
            )

        ratio_sum = sum(
            (
                line.allocation_ratio
                for line in lines
            ),
            Decimal("0"),
        )

        if ratio_sum != Decimal("100"):
            raise CommissionAllocationValidationError(
                "Allocation ratios must total exactly 100."
            )

        allocation_ids = [
            line.allocation_id
            for line in lines
        ]

        if len(allocation_ids) != len(
            set(allocation_ids)
        ):
            raise CommissionAllocationValidationError(
                "Duplicate allocation_id is not allowed."
            )

        party_ids = [
            line.party.identity_key
            for line in lines
        ]

        if len(party_ids) != len(
            set(party_ids)
        ):
            raise CommissionAllocationValidationError(
                "A party cannot receive multiple allocation lines."
            )

        entitlement_ids = {
            line.entitlement_id
            for line in lines
        }

        if not entitlement_ids:
            raise CommissionAllocationValidationError(
                "Entitlement reference is required."
            )

        object.__setattr__(
            self,
            "lines",
            lines,
        )

        for field in (
            "allocation_set_id",
            "tenant_id",
            "commission_id",
            "calculation_id",
            "eligibility_reference",
            "authorization_reference",
            "provenance_reference",
        ):
            value = getattr(self, field)

            if not isinstance(
                value,
                str,
            ) or not value.strip():
                raise CommissionAllocationValidationError(
                    f"{field} is required."
                )

            object.__setattr__(
                self,
                field,
                value.strip(),
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
            raise CommissionAllocationValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            dict(metadata),
        )

    @classmethod
    def from_entitlements(
        cls,
        calculation: CommissionCalculation,
        entitlements: tuple[
            CommissionEntitlement,
            ...,
        ],
        *,
        allocation_set_id: str,
        eligibility_reference: str,
        authorization_reference: str,
        provenance_reference: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionAllocation":
        if not isinstance(
            calculation,
            CommissionCalculation,
        ):
            raise CommissionAllocationValidationError(
                "calculation must be CommissionCalculation."
            )

        items = tuple(entitlements)

        if not items:
            raise CommissionAllocationValidationError(
                "At least one entitlement is required."
            )

        total = calculation.commission_amount

        amount_sum = sum(
            (
                item.entitled_amount.amount
                for item in items
            ),
            Decimal("0"),
        )

        if amount_sum != total.amount:
            raise CommissionAllocationValidationError(
                "Entitlements must consume the "
                "calculated commission exactly."
            )

        lines: list[CommissionAllocationLine] = []

        for index, entitlement in enumerate(
            items,
            start=1,
        ):
            if not isinstance(
                entitlement,
                CommissionEntitlement,
            ):
                raise CommissionAllocationValidationError(
                    "Invalid entitlement value."
                )

            if (
                entitlement.tenant_id
                != calculation.tenant_id
            ):
                raise CommissionAllocationValidationError(
                    "Entitlement tenant differs from "
                    "calculation tenant."
                )

            if (
                entitlement.commission_id
                != calculation.commission_id
            ):
                raise CommissionAllocationValidationError(
                    "Entitlement commission differs from "
                    "calculation commission."
                )

            if (
                entitlement.calculation_id
                != calculation.calculation_id
            ):
                raise CommissionAllocationValidationError(
                    "Entitlement calculation reference mismatch."
                )

            ratio = (
                Decimal("0")
                if total.amount == 0
                else (
                    entitlement.entitled_amount.amount
                    * Decimal("100")
                    / total.amount
                )
            )

            ratio = ratio.quantize(
                Decimal("0.00000001")
            )

            lines.append(
                CommissionAllocationLine(
                    allocation_id=(
                        f"{allocation_set_id}:{index}"
                    ),
                    entitlement_id=(
                        entitlement.entitlement_id
                    ),
                    party=(
                        entitlement.entitled_party
                    ),
                    amount=(
                        entitlement.entitled_amount
                    ),
                    allocation_ratio=ratio,
                    rank=index,
                )
            )

        ratio_sum = sum(
            (
                line.allocation_ratio
                for line in lines
            ),
            Decimal("0"),
        )

        if (
            ratio_sum != Decimal("100")
            and total.amount != 0
        ):
            raise CommissionAllocationValidationError(
                "Entitlement-derived ratios must "
                "resolve to exactly 100."
            )

        return cls(
            allocation_set_id=allocation_set_id,
            tenant_id=calculation.tenant_id,
            commission_id=calculation.commission_id,
            calculation_id=calculation.calculation_id,
            calculation_version=(
                calculation.calculation_version
            ),
            total_amount=total,
            lines=tuple(lines),
            eligibility_reference=eligibility_reference,
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.COMMISSION_ALLOCATION"
            ),
            "schema_version": (
                CORE008_COMMISSION_ALLOCATION_SCHEMA_VERSION
            ),
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "calculation_id": self.calculation_id,
            "calculation_version": (
                self.calculation_version
            ),
            "total_amount": (
                self.total_amount.to_dict()
            ),
            "lines": [
                line.to_dict()
                for line in self.lines
            ],
            "eligibility_reference": (
                self.eligibility_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_ALLOCATION_SCHEMA_VERSION",
    "CommissionAllocationError",
    "CommissionAllocationValidationError",
    "CommissionAllocationLine",
    "CommissionAllocation",
]
