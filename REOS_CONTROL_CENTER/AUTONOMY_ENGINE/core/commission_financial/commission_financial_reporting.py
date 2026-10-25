
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..contract_primitives import canonical_json, fingerprint
from .commission_financial_audit import (
    CommissionFinancialAuditAction,
    CommissionFinancialAuditEntry,
    CommissionFinancialAuditOutcome,
    CommissionFinancialAuditTrail,
)
from .commission_statement import CommissionStatement


CORE008_FINANCIAL_REPORTING_SCHEMA_VERSION = 1


class CommissionFinancialReportingError(ValueError):
    """Base error for CORE-008 financial reporting."""


class CommissionFinancialReportFormat(str, Enum):
    JSON = "JSON"
    CSV = "CSV"


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionFinancialReportingError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _csv_safe_text(value: str) -> str:
    """Prevent spreadsheet formula execution for exported text fields."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


@dataclass(frozen=True, slots=True)
class CommissionFinancialReport:
    """Immutable serialized representation of one statement export."""

    report_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    statement_version: int
    report_format: CommissionFinancialReportFormat
    content_type: str
    content: str
    statement_fingerprint: str
    report_fingerprint: str
    generated_at: datetime

    def __post_init__(self) -> None:
        for field in (
            "report_id",
            "tenant_id",
            "commission_id",
            "statement_id",
            "content_type",
            "content",
            "statement_fingerprint",
            "report_fingerprint",
        ):
            object.__setattr__(
                self,
                field,
                _required_text(getattr(self, field), field),
            )

        if (
            isinstance(self.statement_version, bool)
            or not isinstance(self.statement_version, int)
            or self.statement_version < 1
        ):
            raise CommissionFinancialReportingError(
                "statement_version must be a positive integer."
            )

        try:
            report_format = CommissionFinancialReportFormat(
                self.report_format
            )
        except (TypeError, ValueError) as exc:
            raise CommissionFinancialReportingError(
                "Unsupported financial report format."
            ) from exc

        object.__setattr__(self, "report_format", report_format)

        if (
            not isinstance(self.generated_at, datetime)
            or self.generated_at.tzinfo is None
            or self.generated_at.utcoffset() is None
        ):
            raise CommissionFinancialReportingError(
                "generated_at must be timezone-aware."
            )


@dataclass(frozen=True, slots=True)
class CommissionFinancialReportExport:
    """Report plus the updated audit trail; persistence remains caller-owned."""

    report: CommissionFinancialReport
    audit_entry: CommissionFinancialAuditEntry
    audit_trail: CommissionFinancialAuditTrail


def build_commission_statement_report(
    statement: CommissionStatement,
    *,
    report_format: CommissionFinancialReportFormat,
    tenant_id: str,
    actor_reference: str,
    authorization_reference: str,
    provenance_reference: str,
    occurred_at: datetime,
    report_id: str,
    audit_id: str,
    audit_trail: CommissionFinancialAuditTrail,
) -> CommissionFinancialReportExport:
    """Serialize one statement and append a REPORT_EXPORTED audit event.

    This function does not persist the report or audit trail. The caller must
    safely persist the returned trail through the existing governed boundary.
    Stable report_id and audit_id values allow exact retries to be idempotent.
    """
    if not isinstance(statement, CommissionStatement):
        raise CommissionFinancialReportingError(
            "statement must be CommissionStatement."
        )

    if not isinstance(audit_trail, CommissionFinancialAuditTrail):
        raise CommissionFinancialReportingError(
            "audit_trail must be CommissionFinancialAuditTrail."
        )

    tenant_id = _required_text(tenant_id, "tenant_id")
    actor_reference = _required_text(actor_reference, "actor_reference")
    authorization_reference = _required_text(
        authorization_reference, "authorization_reference"
    )
    provenance_reference = _required_text(
        provenance_reference, "provenance_reference"
    )
    report_id = _required_text(report_id, "report_id")
    audit_id = _required_text(audit_id, "audit_id")

    statement.assert_tenant(tenant_id)

    if (
        audit_trail.tenant_id != statement.tenant_id
        or audit_trail.commission_id != statement.commission_id
    ):
        raise CommissionFinancialReportingError(
            "Audit trail does not match statement tenant/commission scope."
        )

    try:
        selected_format = CommissionFinancialReportFormat(report_format)
    except (TypeError, ValueError) as exc:
        raise CommissionFinancialReportingError(
            "Unsupported financial report format."
        ) from exc

    statement_payload = statement.to_dict(include_fingerprint=True)
    statement_fingerprint = statement.immutable_fingerprint

    if selected_format is CommissionFinancialReportFormat.JSON:
        content = canonical_json(statement_payload)
        content_type = "application/json; charset=utf-8"
    else:
        amount_fields = (
            "gross_commission",
            "total_adjustments",
            "invoiced_amount",
            "settled_amount",
            "reconciled_amount",
            "total_tax",
            "total_withholding",
            "outstanding_amount",
            "unresolved_variance",
        )
        row: dict[str, str] = {
            "schema_version": str(
                CORE008_FINANCIAL_REPORTING_SCHEMA_VERSION
            ),
            "report_id": _csv_safe_text(report_id),
            "tenant_id": _csv_safe_text(statement.tenant_id),
            "commission_id": _csv_safe_text(statement.commission_id),
            "statement_id": _csv_safe_text(statement.statement_id),
            "statement_version": str(statement.statement_version),
            "state": statement.state.value,
            "currency_code": statement.gross_commission.currency.code,
            "generated_at": statement.generated_at.isoformat(),
            "statement_fingerprint": statement_fingerprint,
            "source_invoice_ids": canonical_json(
                list(statement.source_invoice_ids)
            ),
            "source_settlement_ids": canonical_json(
                list(statement.source_settlement_ids)
            ),
            "source_reconciliation_ids": canonical_json(
                list(statement.source_reconciliation_ids)
            ),
            "source_adjustment_ids": canonical_json(
                list(statement.source_adjustment_ids)
            ),
            "source_tax_assessment_ids": canonical_json(
                list(statement.source_tax_assessment_ids)
            ),
        }
        for field in amount_fields:
            row[field] = format(
                getattr(statement, field).amount,
                "f",
            )

        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(
            buffer,
            fieldnames=list(row),
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerow(row)
        content = buffer.getvalue()
        content_type = "text/csv; charset=utf-8"

    report_fingerprint = fingerprint(
        {
            "report_id": report_id,
            "report_format": selected_format.value,
            "statement_fingerprint": statement_fingerprint,
            "content": content,
        }
    )

    report = CommissionFinancialReport(
        report_id=report_id,
        tenant_id=statement.tenant_id,
        commission_id=statement.commission_id,
        statement_id=statement.statement_id,
        statement_version=statement.statement_version,
        report_format=selected_format,
        content_type=content_type,
        content=content,
        statement_fingerprint=statement_fingerprint,
        report_fingerprint=report_fingerprint,
        generated_at=occurred_at,
    )

    audit_entry = CommissionFinancialAuditEntry(
        audit_id=audit_id,
        tenant_id=statement.tenant_id,
        commission_id=statement.commission_id,
        subject_type="COMMISSION_STATEMENT",
        subject_id=statement.statement_id,
        subject_version=statement.statement_version,
        action=CommissionFinancialAuditAction.REPORT_EXPORTED,
        outcome=CommissionFinancialAuditOutcome.SUCCEEDED,
        actor_reference=actor_reference,
        occurred_at=occurred_at,
        subject_fingerprint=statement_fingerprint,
        provenance_reference=provenance_reference,
        authorization_reference=authorization_reference,
        metadata={
            "report_id": report.report_id,
            "report_format": report.report_format.value,
            "content_type": report.content_type,
            "report_fingerprint": report.report_fingerprint,
            "statement_fingerprint": report.statement_fingerprint,
        },
    )

    updated_trail = audit_trail.append(audit_entry)

    return CommissionFinancialReportExport(
        report=report,
        audit_entry=audit_entry,
        audit_trail=updated_trail,
    )


__all__ = [
    "CORE008_FINANCIAL_REPORTING_SCHEMA_VERSION",
    "CommissionFinancialReportingError",
    "CommissionFinancialReportFormat",
    "CommissionFinancialReport",
    "CommissionFinancialReportExport",
    "build_commission_statement_report",
]
