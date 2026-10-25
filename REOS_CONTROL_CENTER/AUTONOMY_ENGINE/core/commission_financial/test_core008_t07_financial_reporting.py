
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from .commission_financial_audit import (
    CommissionFinancialAuditAction,
    CommissionFinancialAuditTrail,
)
from .commission_financial_reporting import (
    CommissionFinancialReportFormat,
    CommissionFinancialReportingError,
    build_commission_statement_report,
)
from .commission_statement import (
    CommissionStatement,
    CommissionStatementState,
)
from .financial_domain import Currency, FinancialTenantScopeError, MonetaryAmount


UTC = timezone.utc
T0 = datetime(2026, 10, 25, 10, 0, tzinfo=UTC)


def _statement(
    *,
    tenant_id: str = "tenant-a",
    commission_id: str = "commission-001",
    statement_id: str = "statement-001",
) -> CommissionStatement:
    currency = Currency("INR", 2)
    zero = MonetaryAmount.zero(currency)

    return CommissionStatement(
        statement_id=statement_id,
        tenant_id=tenant_id,
        commission_id=commission_id,
        statement_version=1,
        gross_commission=zero,
        total_adjustments=zero,
        invoiced_amount=zero,
        settled_amount=zero,
        reconciled_amount=zero,
        total_tax=zero,
        total_withholding=zero,
        outstanding_amount=zero,
        unresolved_variance=zero,
        source_invoice_ids=("invoice-001",),
        source_settlement_ids=("settlement-001",),
        source_reconciliation_ids=("reconciliation-001",),
        source_adjustment_ids=("adjustment-001",),
        source_tax_assessment_ids=("tax-001",),
        generated_at=T0,
        provenance_reference="statement-provenance-001",
        authorization_reference="statement-authorization-001",
        state=CommissionStatementState.DRAFT,
        metadata={"source": "test"},
    )


def _export(
    statement: CommissionStatement | None = None,
    *,
    report_format: CommissionFinancialReportFormat = (
        CommissionFinancialReportFormat.JSON
    ),
    audit_trail: CommissionFinancialAuditTrail | None = None,
    report_id: str = "report-001",
    audit_id: str = "audit-report-001",
):
    selected = statement or _statement()
    trail = audit_trail or CommissionFinancialAuditTrail(
        selected.tenant_id,
        selected.commission_id,
    )

    return build_commission_statement_report(
        selected,
        report_format=report_format,
        tenant_id=selected.tenant_id,
        actor_reference="operator-001",
        authorization_reference="report-approval-001",
        provenance_reference="report-provenance-001",
        occurred_at=T0,
        report_id=report_id,
        audit_id=audit_id,
        audit_trail=trail,
    )


def test_json_report_is_canonical_and_matches_statement_fingerprint():
    statement = _statement()
    result = _export(statement)

    payload = json.loads(result.report.content)

    assert payload["statement_id"] == statement.statement_id
    assert payload["tenant_id"] == statement.tenant_id
    assert payload["commission_id"] == statement.commission_id
    assert (
        result.report.statement_fingerprint
        == statement.immutable_fingerprint
    )
    assert result.report.content_type == "application/json; charset=utf-8"


def test_csv_report_contains_fixed_precision_amounts_and_source_ids():
    result = _export(
        report_format=CommissionFinancialReportFormat.CSV
    )

    rows = list(csv.DictReader(io.StringIO(result.report.content)))
    assert len(rows) == 1

    row = rows[0]
    assert row["statement_id"] == "statement-001"
    assert row["currency_code"] == "INR"
    assert row["gross_commission"] == "0.00"
    assert row["outstanding_amount"] == "0.00"
    assert json.loads(row["source_invoice_ids"]) == ["invoice-001"]
    assert result.report.content_type == "text/csv; charset=utf-8"


def test_successful_export_is_recorded_in_existing_audit_chain():
    result = _export()

    assert result.audit_entry.action is (
        CommissionFinancialAuditAction.REPORT_EXPORTED
    )
    assert result.audit_entry.authorization_reference == (
        "report-approval-001"
    )
    assert result.audit_entry.subject_fingerprint == (
        result.report.statement_fingerprint
    )
    assert len(result.audit_trail.records) == 1
    assert result.audit_trail.verify_integrity() is True


def test_report_fingerprint_is_stable_for_identical_export_inputs():
    first = _export()
    second = _export()

    assert first.report.report_fingerprint == second.report.report_fingerprint
    assert first.report.content == second.report.content


def test_exact_audit_replay_is_idempotent():
    first = _export()
    replay = _export(audit_trail=first.audit_trail)

    assert replay.audit_trail is first.audit_trail
    assert len(replay.audit_trail.records) == 1


def test_cross_tenant_export_is_rejected():
    statement = _statement()

    with pytest.raises(FinancialTenantScopeError):
        build_commission_statement_report(
            statement,
            report_format=CommissionFinancialReportFormat.JSON,
            tenant_id="tenant-b",
            actor_reference="operator-001",
            authorization_reference="report-approval-001",
            provenance_reference="report-provenance-001",
            occurred_at=T0,
            report_id="report-001",
            audit_id="audit-report-001",
            audit_trail=CommissionFinancialAuditTrail(
                statement.tenant_id,
                statement.commission_id,
            ),
        )


def test_mismatched_audit_trail_scope_is_rejected():
    statement = _statement()
    wrong_trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-other",
    )

    with pytest.raises(
        CommissionFinancialReportingError,
        match="does not match statement tenant/commission scope",
    ):
        _export(statement, audit_trail=wrong_trail)


def test_export_requires_authorization_reference():
    statement = _statement()

    with pytest.raises(
        CommissionFinancialReportingError,
        match="authorization_reference must be non-empty text",
    ):
        build_commission_statement_report(
            statement,
            report_format=CommissionFinancialReportFormat.JSON,
            tenant_id=statement.tenant_id,
            actor_reference="operator-001",
            authorization_reference=" ",
            provenance_reference="report-provenance-001",
            occurred_at=T0,
            report_id="report-001",
            audit_id="audit-report-001",
            audit_trail=CommissionFinancialAuditTrail(
                statement.tenant_id,
                statement.commission_id,
            ),
        )


def test_csv_text_fields_are_safe_from_spreadsheet_formulas():
    statement = _statement(tenant_id="=tenant-a")
    result = _export(
        statement,
        report_format=CommissionFinancialReportFormat.CSV,
    )

    row = next(csv.DictReader(io.StringIO(result.report.content)))
    assert row["tenant_id"] == "'=tenant-a"


def test_unsupported_report_format_is_rejected():
    with pytest.raises(CommissionFinancialReportingError):
        _export(report_format="PDF")  # type: ignore[arg-type]
