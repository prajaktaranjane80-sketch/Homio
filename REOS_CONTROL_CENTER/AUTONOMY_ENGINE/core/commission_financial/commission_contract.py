from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .financial_domain import Currency


CORE008_COMMISSION_CONTRACT_SCHEMA_VERSION = 1


class CommissionContractError(ValueError):
    """Base CORE-008 commission-contract error."""


class CommissionContractValidationError(CommissionContractError):
    """Invalid commission-contract value."""


class CommissionContractTenantScopeError(CommissionContractError):
    """Commission contract crossed tenant scope."""


class CommissionContractConflictError(CommissionContractError):
    """Same contract identity was supplied with conflicting terms."""


class CommissionContractVersionError(CommissionContractError):
    """Invalid or conflicting commission-contract version."""


class CommissionContractState(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class CommissionBasisType(str, Enum):
    GROSS_TRANSACTION_VALUE = "GROSS_TRANSACTION_VALUE"
    NET_TRANSACTION_VALUE = "NET_TRANSACTION_VALUE"
    FIXED_TRANSACTION_AMOUNT = "FIXED_TRANSACTION_AMOUNT"
    REFERENCE_AMOUNT = "REFERENCE_AMOUNT"


class CommissionRateType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class CommissionPartyType(str, Enum):
    BROKER = "BROKER"
    AGENT = "AGENT"
    PARTNER = "PARTNER"
    BROKERAGE = "BROKERAGE"
    REFERRAL_PARTY = "REFERRAL_PARTY"


class EligibilityOperator(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    IN = "IN"
    EXISTS = "EXISTS"


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionContractValidationError(
            f"{field} must be non-empty text."
        )

    return value.strip()


def _positive_int(
    value: int,
    field: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionContractValidationError(
            f"{field} must be a positive integer."
        )

    return value


def _decimal(
    value: Decimal | int | str,
    field: str,
) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise CommissionContractValidationError(
            f"{field} must use Decimal, integer, or decimal text."
        )

    try:
        result = (
            value
            if isinstance(value, Decimal)
            else Decimal(str(value))
        )
    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ) as exc:
        raise CommissionContractValidationError(
            f"{field} must be a valid decimal."
        ) from exc

    if not result.is_finite():
        raise CommissionContractValidationError(
            f"{field} must be finite."
        )

    return result


def _aware_datetime(
    value: datetime,
    field: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise CommissionContractValidationError(
            f"{field} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise CommissionContractValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class CommissionPartyReference:
    """Reference to entitled party.

    CORE-001 remains the identity/authorization authority.
    This object is only a typed financial reference.
    """

    party_type: CommissionPartyType
    party_id: str

    def __post_init__(self) -> None:
        try:
            party_type = CommissionPartyType(
                self.party_type
            )
        except ValueError as exc:
            raise CommissionContractValidationError(
                "Unsupported commission party type."
            ) from exc

        object.__setattr__(
            self,
            "party_type",
            party_type,
        )

        object.__setattr__(
            self,
            "party_id",
            _text(
                self.party_id,
                "party_id",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "party_type": self.party_type.value,
            "party_id": self.party_id,
        }


@dataclass(frozen=True, slots=True)
class CommissionEntitlementReference:
    """Immutable entitlement and attribution reference.

    Deal and ownership remain references to CORE-006 / CORE-003.
    CORE-008 does not recreate those engines.
    """

    entitlement_id: str
    tenant_id: str
    entitled_party: CommissionPartyReference
    deal_reference: str
    ownership_reference: str
    provenance_reference: str

    def __post_init__(self) -> None:
        for field_name in (
            "entitlement_id",
            "tenant_id",
            "deal_reference",
            "ownership_reference",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(
            self.entitled_party,
            CommissionPartyReference,
        ):
            raise CommissionContractValidationError(
                "entitled_party must be CommissionPartyReference."
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.tenant_id,
            self.entitlement_id,
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        if _text(
            tenant_id,
            "tenant_id",
        ) != self.tenant_id:
            raise CommissionContractTenantScopeError(
                "Commission entitlement crosses tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entitlement_id": self.entitlement_id,
            "tenant_id": self.tenant_id,
            "entitled_party": self.entitled_party.to_dict(),
            "deal_reference": self.deal_reference,
            "ownership_reference": self.ownership_reference,
            "provenance_reference": self.provenance_reference,
        }


@dataclass(frozen=True, slots=True)
class CommissionBasis:
    """Declarative commission basis.

    Point 02 defines the reference.
    Point 03 owns deterministic calculation.
    """

    basis_type: CommissionBasisType
    source_reference: str
    currency: Currency | None = None

    def __post_init__(self) -> None:
        try:
            basis_type = CommissionBasisType(
                self.basis_type
            )
        except ValueError as exc:
            raise CommissionContractValidationError(
                "Unsupported commission basis type."
            ) from exc

        object.__setattr__(
            self,
            "basis_type",
            basis_type,
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        if (
            self.basis_type
            is CommissionBasisType.FIXED_TRANSACTION_AMOUNT
        ):
            if not isinstance(
                self.currency,
                Currency,
            ):
                raise CommissionContractValidationError(
                    "FIXED_TRANSACTION_AMOUNT requires currency."
                )

        elif self.currency is not None and not isinstance(
            self.currency,
            Currency,
        ):
            raise CommissionContractValidationError(
                "currency must be Currency or None."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis_type": self.basis_type.value,
            "source_reference": self.source_reference,
            "currency": (
                self.currency.to_dict()
                if self.currency is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionRate:
    """Immutable commission-rate declaration.

    No commission calculation occurs here.
    Point 03 owns calculation.
    """

    rate_type: CommissionRateType
    value: Decimal
    currency: Currency | None = None

    def __post_init__(self) -> None:
        try:
            rate_type = CommissionRateType(
                self.rate_type
            )
        except ValueError as exc:
            raise CommissionContractValidationError(
                "Unsupported commission rate type."
            ) from exc

        value = _decimal(
            self.value,
            "value",
        )

        if value < 0:
            raise CommissionContractValidationError(
                "Commission rate cannot be negative."
            )

        if rate_type is CommissionRateType.PERCENTAGE:
            if value > 100:
                raise CommissionContractValidationError(
                    "Percentage rate cannot exceed 100."
                )

            if self.currency is not None:
                raise CommissionContractValidationError(
                    "Percentage rate must not carry a currency."
                )

        else:
            if not isinstance(
                self.currency,
                Currency,
            ):
                raise CommissionContractValidationError(
                    "FIXED_AMOUNT rate requires currency."
                )

        object.__setattr__(
            self,
            "rate_type",
            rate_type,
        )

        object.__setattr__(
            self,
            "value",
            value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rate_type": self.rate_type.value,
            "value": format(
                self.value,
                "f",
            ),
            "currency": (
                self.currency.to_dict()
                if self.currency is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionEligibilityRule:
    """Declarative eligibility condition.

    This records eligibility requirements.
    It does not evaluate them.

    Governance and authorization remain outside this contract.
    """

    rule_code: str
    operator: EligibilityOperator
    value: str | None = None
    evidence_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_code",
            _text(
                self.rule_code,
                "rule_code",
            ),
        )

        try:
            operator = EligibilityOperator(
                self.operator
            )
        except ValueError as exc:
            raise CommissionContractValidationError(
                "Unsupported eligibility operator."
            ) from exc

        object.__setattr__(
            self,
            "operator",
            operator,
        )

        if self.value is not None:
            object.__setattr__(
                self,
                "value",
                _text(
                    self.value,
                    "value",
                ),
            )

        if not isinstance(
            self.evidence_required,
            bool,
        ):
            raise CommissionContractValidationError(
                "evidence_required must be boolean."
            )

        if (
            operator is EligibilityOperator.EXISTS
            and self.value is not None
        ):
            raise CommissionContractValidationError(
                "EXISTS rule must not supply value."
            )

        if (
            operator is not EligibilityOperator.EXISTS
            and self.value is None
        ):
            raise CommissionContractValidationError(
                f"{operator.value} rule requires value."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "operator": self.operator.value,
            "value": self.value,
            "evidence_required": self.evidence_required,
        }


@dataclass(frozen=True, slots=True)
class CommissionProvenance:
    """Immutable source/provenance declaration."""

    source_type: str
    source_reference: str
    captured_at: datetime
    evidence_reference: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_type",
            "source_reference",
            "evidence_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "captured_at",
            _aware_datetime(
                self.captured_at,
                "captured_at",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "captured_at": self.captured_at.isoformat(),
            "evidence_reference": self.evidence_reference,
        }


@dataclass(frozen=True, slots=True)
class CommissionContract:
    """Versioned immutable commission terms.

    This is the authoritative contract for commission terms inside CORE-008.

    It does NOT:
    - calculate commission,
    - allocate commission,
    - settle money,
    - reconcile financial entries,
    - own deal lifecycle,
    - own ownership,
    - own authorization,
    - own governance,
    - publish events,
    - own ACRL recovery.
    """

    commission_id: str
    tenant_id: str
    entitlement: CommissionEntitlementReference
    basis: CommissionBasis
    rate: CommissionRate
    eligibility_rules: tuple[
        CommissionEligibilityRule,
        ...,
    ]
    effective_from: datetime
    effective_to: datetime | None
    contract_version: int
    provenance: CommissionProvenance
    state: CommissionContractState = (
        CommissionContractState.DRAFT
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "commission_id",
            "tenant_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        if not isinstance(
            self.entitlement,
            CommissionEntitlementReference,
        ):
            raise CommissionContractValidationError(
                "entitlement must be CommissionEntitlementReference."
            )

        if (
            self.entitlement.tenant_id
            != self.tenant_id
        ):
            raise CommissionContractTenantScopeError(
                "Entitlement tenant does not match commission tenant."
            )

        if not isinstance(
            self.basis,
            CommissionBasis,
        ):
            raise CommissionContractValidationError(
                "basis must be CommissionBasis."
            )

        if not isinstance(
            self.rate,
            CommissionRate,
        ):
            raise CommissionContractValidationError(
                "rate must be CommissionRate."
            )

        rules = tuple(
            self.eligibility_rules
        )

        if len(
            {
                rule.rule_code
                for rule in rules
            }
        ) != len(rules):
            raise CommissionContractValidationError(
                "Duplicate eligibility rule_code is not allowed."
            )

        for rule in rules:
            if not isinstance(
                rule,
                CommissionEligibilityRule,
            ):
                raise CommissionContractValidationError(
                    "eligibility_rules must contain "
                    "CommissionEligibilityRule values."
                )

        object.__setattr__(
            self,
            "eligibility_rules",
            rules,
        )

        effective_from = _aware_datetime(
            self.effective_from,
            "effective_from",
        )

        object.__setattr__(
            self,
            "effective_from",
            effective_from,
        )

        if self.effective_to is not None:
            effective_to = _aware_datetime(
                self.effective_to,
                "effective_to",
            )

            if effective_to <= effective_from:
                raise CommissionContractValidationError(
                    "effective_to must be later than effective_from."
                )

            object.__setattr__(
                self,
                "effective_to",
                effective_to,
            )

        object.__setattr__(
            self,
            "contract_version",
            _positive_int(
                self.contract_version,
                "contract_version",
            ),
        )

        if not isinstance(
            self.provenance,
            CommissionProvenance,
        ):
            raise CommissionContractValidationError(
                "provenance must be CommissionProvenance."
            )

        if (
            self.provenance.captured_at
            > effective_from
        ):
            raise CommissionContractValidationError(
                "provenance.captured_at cannot be later "
                "than effective_from."
            )

        try:
            state = CommissionContractState(
                self.state
            )
        except ValueError as exc:
            raise CommissionContractValidationError(
                "Unsupported commission contract state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        metadata = self.metadata

        if metadata == ():
            metadata = {}

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionContractValidationError(
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
    def create(
        cls,
        *,
        tenant_id: str,
        entitlement: CommissionEntitlementReference,
        basis: CommissionBasis,
        rate: CommissionRate,
        eligibility_rules: tuple[
            CommissionEligibilityRule,
            ...,
        ] = (),
        effective_from: datetime,
        effective_to: datetime | None,
        provenance: CommissionProvenance,
        state: CommissionContractState = (
            CommissionContractState.DRAFT
        ),
        metadata: Mapping[str, Any] | None = None,
        commission_id: str | None = None,
        contract_version: int = 1,
    ) -> "CommissionContract":
        return cls(
            commission_id=(
                commission_id
                or str(uuid4())
            ),
            tenant_id=tenant_id,
            entitlement=entitlement,
            basis=basis,
            rate=rate,
            eligibility_rules=(
                eligibility_rules
            ),
            effective_from=effective_from,
            effective_to=effective_to,
            contract_version=(
                contract_version
            ),
            provenance=provenance,
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
            self.commission_id,
        )

    @property
    def immutable_terms_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        if _text(
            tenant_id,
            "tenant_id",
        ) != self.tenant_id:
            raise CommissionContractTenantScopeError(
                "Commission contract crosses tenant scope."
            )

    def is_effective_at(
        self,
        at: datetime,
    ) -> bool:
        instant = _aware_datetime(
            at,
            "at",
        )

        if instant < self.effective_from:
            return False

        if (
            self.effective_to is not None
            and instant >= self.effective_to
        ):
            return False

        return (
            self.state
            is CommissionContractState.ACTIVE
        )

    def assert_compatible(
        self,
        other: "CommissionContract",
    ) -> None:
        if not isinstance(
            other,
            CommissionContract,
        ):
            raise CommissionContractConflictError(
                "other must be CommissionContract."
            )

        if (
            self.identity_key
            != other.identity_key
        ):
            raise CommissionContractConflictError(
                "Commission identities differ."
            )

        if (
            self.contract_version
            != other.contract_version
        ):
            raise CommissionContractVersionError(
                "Commission contract versions differ."
            )

        if (
            self.immutable_terms_fingerprint
            != other.immutable_terms_fingerprint
        ):
            raise CommissionContractConflictError(
                "Same commission contract identity/version "
                "has conflicting terms."
            )

    def next_version(
        self,
        *,
        basis: CommissionBasis,
        rate: CommissionRate,
        eligibility_rules: tuple[
            CommissionEligibilityRule,
            ...,
        ],
        effective_from: datetime,
        effective_to: datetime | None,
        provenance: CommissionProvenance,
        state: CommissionContractState = (
            CommissionContractState.DRAFT
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionContract":
        """Create a new immutable historical contract version."""

        return CommissionContract(
            commission_id=self.commission_id,
            tenant_id=self.tenant_id,
            entitlement=self.entitlement,
            basis=basis,
            rate=rate,
            eligibility_rules=(
                eligibility_rules
            ),
            effective_from=effective_from,
            effective_to=effective_to,
            contract_version=(
                self.contract_version + 1
            ),
            provenance=provenance,
            state=state,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.COMMISSION_CONTRACT"
            ),
            "schema_version": (
                CORE008_COMMISSION_CONTRACT_SCHEMA_VERSION
            ),
            "commission_id": (
                self.commission_id
            ),
            "tenant_id": (
                self.tenant_id
            ),
            "entitlement": (
                self.entitlement.to_dict()
            ),
            "basis": (
                self.basis.to_dict()
            ),
            "rate": (
                self.rate.to_dict()
            ),
            "eligibility_rules": [
                rule.to_dict()
                for rule in self.eligibility_rules
            ],
            "effective_from": (
                self.effective_from.isoformat()
            ),
            "effective_to": (
                self.effective_to.isoformat()
                if self.effective_to is not None
                else None
            ),
            "contract_version": (
                self.contract_version
            ),
            "provenance": (
                self.provenance.to_dict()
            ),
            "state": (
                self.state.value
            ),
            "metadata": self.metadata,
        }

        if include_fingerprint:
            result["immutable_terms_fingerprint"] = (
                self.immutable_terms_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_CONTRACT_SCHEMA_VERSION",
    "CommissionContractError",
    "CommissionContractValidationError",
    "CommissionContractTenantScopeError",
    "CommissionContractConflictError",
    "CommissionContractVersionError",
    "CommissionContractState",
    "CommissionBasisType",
    "CommissionRateType",
    "CommissionPartyType",
    "EligibilityOperator",
    "CommissionPartyReference",
    "CommissionEntitlementReference",
    "CommissionBasis",
    "CommissionRate",
    "CommissionEligibilityRule",
    "CommissionProvenance",
    "CommissionContract",
]
