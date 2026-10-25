
"""CORE-008 Commission & Financial Core public API."""

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

from .commission_protection import (
    CommissionProtection,
    CommissionProtectionError,
    CommissionProtectionState,
    CommissionProtectionValidationError,
    ProtectionEvidenceReference,
)

from .financial_ledger_boundary import (
    CORE008_FINANCIAL_LEDGER_SCHEMA_VERSION,
    FinancialLedgerBoundary,
    FinancialLedgerBoundaryError,
    FinancialLedgerEntry,
    FinancialLedgerValidationError,
    LedgerAccountReference,
    compare_ledger_entries,
)

from .commission_concurrency import (
    CommissionConcurrencyError,
    CommissionDuplicateCommandError,
    CommissionStaleVersionError,
    FinancialConcurrencyBoundary,
    FinancialIdempotencyRecord,
    FinancialTransitionContract,
    FinancialVersionToken,
)

from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationDecision,
    FinancialAuthorizationError,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
    FinancialSecurityError,
    FinancialTenantBoundaryError,
)

from .commission_reos_contract import (
    CORE008_CANONICAL_STATE,
    CORE008_REOS_AUTHORITY,
    CommissionREOSBoundary,
    CommissionREOSContractError,
    CommissionREOSExecutionReference,
    CommissionREOSIntegrationContract,
    validate_reos_contract,
)

from .commission_attribution import (
    CORE008_COMMISSION_ATTRIBUTION_SCHEMA_VERSION,
    CommissionAttributionBinding,
    CommissionAttributionError,
    CommissionAttributionValidationError,
)

from .commission_participant_split import (
    CORE008_COMMISSION_PARTICIPANT_SPLIT_SCHEMA_VERSION,
    CommissionParticipantSplit,
    CommissionParticipantSplitError,
    CommissionParticipantSplitLine,
    CommissionParticipantSplitValidationError,
)

# CORE-008 T04: settlement domain
from .commission_settlement import (
    CORE008_COMMISSION_SETTLEMENT_SCHEMA_VERSION,
    CommissionSettlement,
    CommissionSettlementError,
    CommissionSettlementMode,
    CommissionSettlementState,
    CommissionSettlementValidationError,
)

from .commission_settlement_history import (
    CommissionSettlementHistory,
    CommissionSettlementHistoryEntry,
    CommissionSettlementHistoryError,
)

from .commission_settlement_snapshot import (
    CommissionSettlementSnapshot,
)

from .commission_settlement_integrity import (
    CommissionSettlementIntegrityError as
    CommissionSettlementSnapshotIntegrityError,
    CommissionSettlementIntegrityReport,
    assert_integrity as assert_settlement_integrity,
    inspect_integrity as inspect_settlement_integrity,
)

from .commission_settlement_validation import (
    settlement_validation_report,
    validate_settlement,
)

# CORE-008 T04: reconciliation domain
from .commission_reconciliation import (
    CORE008_COMMISSION_RECONCILIATION_SCHEMA_VERSION,
    CommissionExternalSettlementEvidence,
    CommissionReconciliation,
    CommissionReconciliationError,
    CommissionReconciliationMatchType,
    CommissionReconciliationState,
    CommissionReconciliationValidationError,
)

from .commission_reconciliation_history import (
    CommissionReconciliationHistory,
    CommissionReconciliationHistoryEntry,
    CommissionReconciliationHistoryError,
)

from .commission_reconciliation_snapshot import (
    CommissionReconciliationSnapshot,
)

from .commission_reconciliation_integrity import (
    CommissionReconciliationIntegrityError,
    CommissionReconciliationIntegrityReport,
    assert_integrity as assert_reconciliation_integrity,
    inspect_integrity as inspect_reconciliation_integrity,
)

from .commission_reconciliation_validation import (
    reconciliation_validation_report,
    validate_reconciliation,
)

# CORE-008 T04: lifecycle orchestration
from .commission_settlement_lifecycle import (
    CommissionSettlementConcurrencyError,
    CommissionSettlementEvidenceError,
    CommissionSettlementIntegrityError,
    CommissionSettlementLifecycle,
    CommissionSettlementLifecycleError,
    CommissionSettlementLifecycleEvent,
    CommissionSettlementLifecycleValidationError,
    CommissionSettlementReconciliationResult,
    CommissionSettlementTransitionError,
    SettlementLifecycleRecord,
)

# CORE-008 T06: financial audit chain and external evidence references
from .commission_financial_audit import (
    CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION,
    CommissionFinancialAuditAction,
    CommissionFinancialAuditConflictError,
    CommissionFinancialAuditEntry,
    CommissionFinancialAuditError,
    CommissionFinancialAuditIntegrityError,
    CommissionFinancialAuditIntegrityReport,
    CommissionFinancialAuditOutcome,
    CommissionFinancialAuditRecord,
    CommissionFinancialAuditTrail,
    CommissionFinancialAuditValidationError,
    CommissionFinancialEvidenceLink,
    assert_financial_audit_trail_integrity,
    inspect_financial_audit_trail,
)

# CORE-008 T07: statement reporting and audited export hooks
from .commission_financial_reporting import (
    CORE008_FINANCIAL_REPORTING_SCHEMA_VERSION,
    CommissionFinancialReport,
    CommissionFinancialReportExport,
    CommissionFinancialReportFormat,
    CommissionFinancialReportingError,
    build_commission_statement_report,
)

__all__ = [
    "CORE008_FINANCIAL_REPORTING_SCHEMA_VERSION",
    "CommissionFinancialReport",
    "CommissionFinancialReportExport",
    "CommissionFinancialReportFormat",
    "CommissionFinancialReportingError",
    "build_commission_statement_report",
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
    "CommissionProtection",
    "CommissionProtectionError",
    "CommissionProtectionState",
    "CommissionProtectionValidationError",
    "ProtectionEvidenceReference",
    "CORE008_FINANCIAL_LEDGER_SCHEMA_VERSION",
    "FinancialLedgerBoundary",
    "FinancialLedgerBoundaryError",
    "FinancialLedgerEntry",
    "FinancialLedgerValidationError",
    "LedgerAccountReference",
    "compare_ledger_entries",
    "CommissionConcurrencyError",
    "CommissionDuplicateCommandError",
    "CommissionStaleVersionError",
    "FinancialConcurrencyBoundary",
    "FinancialIdempotencyRecord",
    "FinancialTransitionContract",
    "FinancialVersionToken",
    "FinancialAuthorizationAction",
    "FinancialAuthorizationDecision",
    "FinancialAuthorizationError",
    "FinancialAuthorizationRequest",
    "FinancialSecurityBoundary",
    "FinancialSecurityError",
    "FinancialTenantBoundaryError",
    "CORE008_CANONICAL_STATE",
    "CORE008_REOS_AUTHORITY",
    "CommissionREOSBoundary",
    "CommissionREOSContractError",
    "CommissionREOSExecutionReference",
    "CommissionREOSIntegrationContract",
    "validate_reos_contract",
    "CORE008_COMMISSION_ATTRIBUTION_SCHEMA_VERSION",
    "CommissionAttributionBinding",
    "CommissionAttributionError",
    "CommissionAttributionValidationError",
    "CORE008_COMMISSION_PARTICIPANT_SPLIT_SCHEMA_VERSION",
    "CommissionParticipantSplit",
    "CommissionParticipantSplitError",
    "CommissionParticipantSplitLine",
    "CommissionParticipantSplitValidationError",
    "CORE008_COMMISSION_SETTLEMENT_SCHEMA_VERSION",
    "CommissionSettlement",
    "CommissionSettlementError",
    "CommissionSettlementMode",
    "CommissionSettlementState",
    "CommissionSettlementValidationError",
    "CommissionSettlementHistory",
    "CommissionSettlementHistoryEntry",
    "CommissionSettlementHistoryError",
    "CommissionSettlementSnapshot",
    "CommissionSettlementSnapshotIntegrityError",
    "CommissionSettlementIntegrityReport",
    "assert_settlement_integrity",
    "inspect_settlement_integrity",
    "settlement_validation_report",
    "validate_settlement",
    "CORE008_COMMISSION_RECONCILIATION_SCHEMA_VERSION",
    "CommissionExternalSettlementEvidence",
    "CommissionReconciliation",
    "CommissionReconciliationError",
    "CommissionReconciliationMatchType",
    "CommissionReconciliationState",
    "CommissionReconciliationValidationError",
    "CommissionReconciliationHistory",
    "CommissionReconciliationHistoryEntry",
    "CommissionReconciliationHistoryError",
    "CommissionReconciliationSnapshot",
    "CommissionReconciliationIntegrityError",
    "CommissionReconciliationIntegrityReport",
    "assert_reconciliation_integrity",
    "inspect_reconciliation_integrity",
    "reconciliation_validation_report",
    "validate_reconciliation",
    "CommissionSettlementConcurrencyError",
    "CommissionSettlementEvidenceError",
    "CommissionSettlementIntegrityError",
    "CommissionSettlementLifecycle",
    "CommissionSettlementLifecycleError",
    "CommissionSettlementLifecycleEvent",
    "CommissionSettlementLifecycleValidationError",
    "CommissionSettlementReconciliationResult",
    "CommissionSettlementTransitionError",
    "SettlementLifecycleRecord",
    "CORE008_FINANCIAL_AUDIT_SCHEMA_VERSION",
    "CommissionFinancialAuditAction",
    "CommissionFinancialAuditConflictError",
    "CommissionFinancialAuditEntry",
    "CommissionFinancialAuditError",
    "CommissionFinancialAuditIntegrityError",
    "CommissionFinancialAuditIntegrityReport",
    "CommissionFinancialAuditOutcome",
    "CommissionFinancialAuditRecord",
    "CommissionFinancialAuditTrail",
    "CommissionFinancialAuditValidationError",
    "CommissionFinancialEvidenceLink",
    "assert_financial_audit_trail_integrity",
    "inspect_financial_audit_trail",
]
