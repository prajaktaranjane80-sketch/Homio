"""CORE-008 Commission & Financial Core package.

Boundaries
----------
- REOS Control Center remains project-state authority.
- CORE-001 remains identity/tenant/authorization authority.
- CORE-002 remains event infrastructure authority.
- CORE-003 remains lead/customer ownership authority.
- CORE-006 remains deal/transaction authority.
- CORE-007 remains trust/fraud/governance authority.
- ACRL remains continuity/reconstruction/recovery authority.

This package owns the financial/commission domain itself and must not
create duplicate versions of those existing authorities.
"""

from .financial_domain import (
    CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION,
    CORE008_FINANCIAL_DOMAIN_SOURCE,
    Currency,
    FinancialCurrencyMismatchError,
    FinancialDomainError,
    FinancialDomainRecord,
    FinancialIdentity,
    FinancialPrecisionError,
    FinancialState,
    FinancialSubject,
    FinancialSubjectType,
    FinancialTenantScopeError,
    FinancialValidationError,
    MonetaryAmount,
    RoundingMode,
    new_financial_identity,
)

__all__ = [
    "CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION",
    "CORE008_FINANCIAL_DOMAIN_SOURCE",
    "Currency",
    "FinancialCurrencyMismatchError",
    "FinancialDomainError",
    "FinancialDomainRecord",
    "FinancialIdentity",
    "FinancialPrecisionError",
    "FinancialState",
    "FinancialSubject",
    "FinancialSubjectType",
    "FinancialTenantScopeError",
    "FinancialValidationError",
    "MonetaryAmount",
    "RoundingMode",
    "new_financial_identity",
]