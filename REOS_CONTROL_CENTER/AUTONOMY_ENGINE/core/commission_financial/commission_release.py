from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_closeout import CommissionCloseout
from .commission_invoice import CommissionInvoice
from .commission_reconciliation import CommissionReconciliation
from .commission_statement import CommissionStatement
from .commission_tax import CommissionTaxAssessment
from .commission_settlement import CommissionSettlement
from .financial_domain import (
    FinancialTenantScopeError,
)


CORE008_COMMISSION_RELEASE_SCHEMA_VERSION = 1


class CommissionReleaseError(ValueError):
    """Base financial release error."""


class CommissionReleaseValidationError(
    CommissionReleaseError
):
    """Invalid financial release record."""


class CommissionReleaseState(str, Enum):
    BLOCKED = "BLOCKED"
    READY = "READY"
    AUTHORIZATION_PENDING = "AUTHORIZATION_PENDING"
    RELEASED = "RELEASED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class CommissionReleaseCheck:
    """One deterministic release prerequisite."""

    code: str
    passed: bool
    description: str
    reference: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.code, str)
            or not self.code.strip()
        ):
            raise CommissionReleaseValidationError(
                "check code is required."
            )

        if not isinstance(
            self.passed,
            bool,
        ):
            raise CommissionReleaseValidationError(
                "check passed must be boolean."
            )

        if (
            not isinstance(
                self.description,
                str,
            )
            or not self.description.strip()
        ):
            raise CommissionReleaseValidationError(
                "check description is required."
            )

        object.__setattr__(
            self,
            "code",
            self.code.strip(),
        )

        object.__setattr__(
            self,
            "description",
            self.description.strip(),
        )

        if self.reference is not None:
            if (
                not isinstance(
                    self.reference,
                    str,
                )
                or not self.reference.strip()
            ):
                raise CommissionReleaseValidationError(
                    "reference must be non-empty when supplied."
                )

            object.__setattr__(
                self,
                "reference",
                self.reference.strip(),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "passed": self.passed,
            "description": self.description,
            "reference": self.reference,
        }


@dataclass(frozen=True, slots=True)
class CommissionRelease:
    """Immutable financial release decision record.

    CORE-008 decides whether the financial package is internally
    complete and records the external authorization reference.

    It never executes payment.
    """

    release_id: str
    tenant_id: str
    commission_id: str
    release_version: int

    statement_id: str
    closeout_id: str | None

    invoice_ids: tuple[str, ...]
    settlement_ids: tuple[str, ...]
    reconciliation_ids: tuple[str, ...]
    tax_assessment_ids: tuple[str, ...]

    checks: tuple[CommissionReleaseCheck, ...]
    authorization_reference: str | None
    provenance_reference: str

    evaluated_at: datetime
    released_at: datetime | None

    state: CommissionReleaseState
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "release_id",
            "tenant_id",
            "commission_id",
            "statement_id",
            "provenance_reference",
        ):
            value = getattr(
                self,
                field,
            )

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise CommissionReleaseValidationError(
                    f"{field} must be non-empty text."
                )

            object.__setattr__(
                self,
                field,
                value.strip(),
            )

        if self.closeout_id is not None:
            if (
                not isinstance(
                    self.closeout_id,
                    str,
                )
                or not self.closeout_id.strip()
            ):
                raise CommissionReleaseValidationError(
                    "closeout_id must be non-empty when supplied."
                )

            object.__setattr__(
                self,
                "closeout_id",
                self.closeout_id.strip(),
            )

        if (
            isinstance(
                self.release_version,
                bool,
            )
            or not isinstance(
                self.release_version,
                int,
            )
            or self.release_version < 1
        ):
            raise CommissionReleaseValidationError(
                "release_version must be positive."
            )

        object.__setattr__(
            self,
            "invoice_ids",
            self._ids(
                self.invoice_ids,
                "invoice_ids",
            ),
        )

        object.__setattr__(
            self,
            "settlement_ids",
            self._ids(
                self.settlement_ids,
                "settlement_ids",
            ),
        )

        object.__setattr__(
            self,
            "reconciliation_ids",
            self._ids(
                self.reconciliation_ids,
                "reconciliation_ids",
            ),
        )

        object.__setattr__(
            self,
            "tax_assessment_ids",
            self._ids(
                self.tax_assessment_ids,
                "tax_assessment_ids",
            ),
        )

        checks = tuple(self.checks)

        if not checks:
            raise CommissionReleaseValidationError(
                "At least one release check is required."
            )

        if any(
            not isinstance(
                check,
                CommissionReleaseCheck,
            )
            for check in checks
        ):
            raise CommissionReleaseValidationError(
                "checks contain invalid values."
            )

        check_codes = [
            check.code
            for check in checks
        ]

        if len(check_codes) != len(
            set(check_codes)
        ):
            raise CommissionReleaseValidationError(
                "Duplicate release check codes are not allowed."
            )

        object.__setattr__(
            self,
            "checks",
            checks,
        )

        if self.authorization_reference is not None:
            if (
                not isinstance(
                    self.authorization_reference,
                    str,
                )
                or not self.authorization_reference.strip()
            ):
                raise CommissionReleaseValidationError(
                    "authorization_reference must be "
                    "non-empty when supplied."
                )

            object.__setattr__(
                self,
                "authorization_reference",
                self.authorization_reference.strip(),
            )

        object.__setattr__(
            self,
            "evaluated_at",
            self._aware(
                self.evaluated_at,
                "evaluated_at",
            ),
        )

        if self.released_at is not None:
            released_at = self._aware(
                self.released_at,
                "released_at",
            )

            if released_at < self.evaluated_at:
                raise CommissionReleaseValidationError(
                    "released_at cannot precede evaluated_at."
                )

            object.__setattr__(
                self,
                "released_at",
                released_at,
            )

        try:
            state = CommissionReleaseState(
                self.state
            )
        except ValueError as exc:
            raise CommissionReleaseValidationError(
                "Unsupported release state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        if (
            state is CommissionReleaseState.RELEASED
            and not self.authorization_reference
        ):
            raise CommissionReleaseValidationError(
                "RELEASED state requires authorization reference."
            )

        if (
            state is CommissionReleaseState.RELEASED
            and self.released_at is None
        ):
            raise CommissionReleaseValidationError(
                "RELEASED state requires released_at."
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
            raise CommissionReleaseValidationError(
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

    @staticmethod
    def _ids(
        values: tuple[str, ...],
        field: str,
    ) -> tuple[str, ...]:
        items = tuple(values)

        if any(
            not isinstance(
                value,
                str,
            )
            or not value.strip()
            for value in items
        ):
            raise CommissionReleaseValidationError(
                f"{field} contains invalid references."
            )

        if len(items) != len(set(items)):
            raise CommissionReleaseValidationError(
                f"{field} contains duplicates."
            )

        return tuple(
            value.strip()
            for value in items
        )

    @staticmethod
    def _aware(
        value: datetime,
        field: str,
    ) -> datetime:
        if (
            not isinstance(
                value,
                datetime,
            )
            or value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise CommissionReleaseValidationError(
                f"{field} must be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.release_id,
            self.release_version,
        )

    @property
    def all_checks_passed(self) -> bool:
        return all(
            check.passed
            for check in self.checks
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
        if not isinstance(
            tenant_id,
            str,
        ) or not tenant_id.strip():
            raise CommissionReleaseValidationError(
                "tenant_id must be non-empty text."
            )

        if tenant_id.strip() != self.tenant_id:
            raise FinancialTenantScopeError(
                "Commission release crossed tenant scope."
            )

    @classmethod
    def evaluate(
        cls,
        *,
        statement: CommissionStatement,
        closeout: CommissionCloseout | None,
        invoices: tuple[CommissionInvoice, ...],
        settlements: tuple[CommissionSettlement, ...],
        reconciliations: tuple[CommissionReconciliation, ...],
        tax_assessments: tuple[CommissionTaxAssessment, ...],
        evaluated_at: datetime,
        provenance_reference: str,
        authorization_reference: str | None = None,
        release_id: str | None = None,
        release_version: int = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionRelease":
        if not isinstance(
            statement,
            CommissionStatement,
        ):
            raise CommissionReleaseValidationError(
                "statement must be CommissionStatement."
            )

        if closeout is not None and not isinstance(
            closeout,
            CommissionCloseout,
        ):
            raise CommissionReleaseValidationError(
                "closeout must be CommissionCloseout or None."
            )

        tenant_id = statement.tenant_id
        commission_id = statement.commission_id

        checks: list[CommissionReleaseCheck] = []

        checks.append(
            CommissionReleaseCheck(
                code="STATEMENT_SCOPE",
                passed=True,
                description=(
                    "Statement exists inside the requested "
                    "tenant and commission scope."
                ),
                reference=statement.statement_id,
            )
        )

        checks.append(
            CommissionReleaseCheck(
                code="OUTSTANDING_ZERO",
                passed=(
                    statement.outstanding_amount.is_zero
                ),
                description=(
                    "Financial statement has no outstanding amount."
                ),
                reference=statement.statement_id,
            )
        )

        checks.append(
            CommissionReleaseCheck(
                code="VARIANCE_ZERO",
                passed=(
                    statement.unresolved_variance.is_zero
                ),
                description=(
                    "Financial statement has no unresolved "
                    "reconciliation variance."
                ),
                reference=statement.statement_id,
            )
        )

        if closeout is None:
            checks.append(
                CommissionReleaseCheck(
                    code="CLOSEOUT_PRESENT",
                    passed=False,
                    description=(
                        "A financial closeout record "
                        "is required before release."
                    ),
                )
            )
        else:
            checks.append(
                CommissionReleaseCheck(
                    code="CLOSEOUT_READY",
                    passed=(
                        closeout.tenant_id == tenant_id
                        and closeout.commission_id
                        == commission_id
                        and closeout.statement_id
                        == statement.statement_id
                        and closeout.state.value == "CLOSED"
                    ),
                    description=(
                        "Closeout must be CLOSED and "
                        "match the statement scope."
                    ),
                    reference=closeout.closeout_id,
                )
            )

        invoice_scope_ok = all(
            isinstance(item, CommissionInvoice)
            and item.tenant_id == tenant_id
            and item.commission_id == commission_id
            for item in invoices
        )

        settlement_scope_ok = all(
            isinstance(item, CommissionSettlement)
            and item.tenant_id == tenant_id
            and item.commission_id == commission_id
            for item in settlements
        )

        reconciliation_scope_ok = all(
            isinstance(item, CommissionReconciliation)
            and item.tenant_id == tenant_id
            and item.commission_id == commission_id
            for item in reconciliations
        )

        tax_scope_ok = all(
            isinstance(item, CommissionTaxAssessment)
            and item.tenant_id == tenant_id
            and item.commission_id == commission_id
            for item in tax_assessments
        )

        checks.extend(
            [
                CommissionReleaseCheck(
                    code="INVOICE_SCOPE",
                    passed=invoice_scope_ok,
                    description=(
                        "All invoice references belong to "
                        "the statement scope."
                    ),
                ),
                CommissionReleaseCheck(
                    code="SETTLEMENT_SCOPE",
                    passed=settlement_scope_ok,
                    description=(
                        "All settlement references belong to "
                        "the statement scope."
                    ),
                ),
                CommissionReleaseCheck(
                    code="RECONCILIATION_SCOPE",
                    passed=reconciliation_scope_ok,
                    description=(
                        "All reconciliation references belong "
                        "to the statement scope."
                    ),
                ),
                CommissionReleaseCheck(
                    code="TAX_SCOPE",
                    passed=tax_scope_ok,
                    description=(
                        "All tax assessment references belong "
                        "to the statement scope."
                    ),
            ]
        )

        all_passed = all(
            check.passed
            for check in checks
        )

        if all_passed:
            if authorization_reference:
                state = CommissionReleaseState.RELEASED
                released_at = evaluated_at
            else:
                state = (
                    CommissionReleaseState.AUTHORIZATION_PENDING
                )
                released_at = None
        else:
            state = CommissionReleaseState.BLOCKED
            released_at = None

        return cls(
            release_id=(
                release_id
                or str(uuid4())
            ),
            tenant_id=tenant_id,
            commission_id=commission_id,
            release_version=release_version,
            statement_id=statement.statement_id,
            closeout_id=(
                closeout.closeout_id
                if closeout is not None
                else None
            ),
            invoice_ids=tuple(
                item.invoice_id
                for item in invoices
                if isinstance(
                    item,
                    CommissionInvoice,
                )
            ),
            settlement_ids=tuple(
                item.settlement_id
                for item in settlements
                if isinstance(
                    item,
                    CommissionSettlement,
                )
            ),
            reconciliation_ids=tuple(
                item.reconciliation_id
                for item in reconciliations
                if isinstance(
                    item,
                    CommissionReconciliation,
                )
            ),
            tax_assessment_ids=tuple(
                item.assessment_id
                for item in tax_assessments
                if isinstance(
                    item,
                    CommissionTaxAssessment,
                )
            ),
            checks=tuple(checks),
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            evaluated_at=evaluated_at,
            released_at=released_at,
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
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_RELEASE"
            ),
            "schema_version": (
                CORE008_COMMISSION_RELEASE_SCHEMA_VERSION
            ),
            "release_id": self.release_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "release_version": (
                self.release_version
            ),
            "statement_id": self.statement_id,
            "closeout_id": self.closeout_id,
            "invoice_ids": list(
                self.invoice_ids
            ),
            "settlement_ids": list(
                self.settlement_ids
            ),
            "reconciliation_ids": list(
                self.reconciliation_ids
            ),
            "tax_assessment_ids": list(
                self.tax_assessment_ids
            ),
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "released_at": (
                self.released_at.isoformat()
                if self.released_at is not None
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
    "CORE008_COMMISSION_RELEASE_SCHEMA_VERSION",
    "CommissionReleaseError",
    "CommissionReleaseValidationError",
    "CommissionReleaseState",
    "CommissionReleaseCheck",
    "CommissionRelease",
]
