from __future__ import annotations

from datetime import datetime, timezone

import pytest

from .commission_protection import (
    CommissionProtection,
    CommissionProtectionState,
    ProtectionEvidenceReference,
)
from .commission_entitlement import (
    CommissionEntitlementState,
)
from .commission_ledger_boundary import (
    FinancialLedgerEntry,
    LedgerAccountReference,
)
from .financial_ledger_boundary import (
    FinancialLedgerBoundary,
)
from .financial_domain import (
    Currency,
    MonetaryAmount,
)


UTC = timezone.utc


def test_protection_requires_attribution_and_entitlement_evidence() -> None:
    with pytest.raises(Exception):
        CommissionProtection(
            protection_id="protect-001",
            tenant_id="tenant-a",
            commission_id="commission-001",
            entitlement_id="entitlement-001",
            lead_reference="lead-001",
            deal_reference="deal-001",
            ownership_reference="ownership-001",
            attribution_evidence=(),
            entitlement_evidence=(),
            dispute_reference=None,
            protection_version=1,
            state=CommissionProtectionState.PROTECTED,
            captured_at=datetime.now(UTC),
            provenance_reference="proof-001",
        )


def test_protection_identity_is_versioned_and_immutable() -> None:
    evidence = ProtectionEvidenceReference(
        evidence_type="OWNERSHIP_PROOF",
        evidence_id="evidence-001",
        fingerprint="fp-001",
        source_reference="CORE-003",
    )

    protection = CommissionProtection(
        protection_id="protect-001",
        tenant_id="tenant-a",
        commission_id="commission-001",
        entitlement_id="entitlement-001",
        lead_reference="lead-001",
        deal_reference="deal-001",
        ownership_reference="ownership-001",
        attribution_evidence=(evidence,),
        entitlement_evidence=(evidence,),
        dispute_reference=None,
        protection_version=1,
        state=CommissionProtectionState.PROTECTED,
        captured_at=datetime.now(UTC),
        provenance_reference="proof-001",
    )

    assert protection.identity_key == (
        "tenant-a",
        "protect-001",
        1,
    )
    assert protection.verify_integrity()


def test_ledger_entry_is_immutable_and_balanced() -> None:
    entry = FinancialLedgerBoundary.create_entry(
        entry_id="entry-001",
        tenant_id="tenant-a",
        commission_id="commission-001",
        entry_version=1,
        transaction_reference="txn-001",
        debit=LedgerAccountReference(
            account_id="commission-expense",
            account_type="EXPENSE",
        ),
        credit=LedgerAccountReference(
            account_id="broker-payable",
            account_type="LIABILITY",
        ),
        amount=MonetaryAmount.create(
            "25000.00",
            Currency("INR", 2),
        ),
        entry_timestamp=datetime.now(UTC),
        source_reference="settlement-001",
        provenance_reference="proof-001",
    )

    entry.assert_balanced()
    assert entry.verify_integrity()


def test_ledger_rejects_self_debit() -> None:
    with pytest.raises(Exception):
        FinancialLedgerEntry(
            entry_id="entry-001",
            tenant_id="tenant-a",
            commission_id="commission-001",
            entry_version=1,
            transaction_reference="txn-001",
            debit=LedgerAccountReference(
                account_id="same",
                account_type="A",
            ),
            credit=LedgerAccountReference(
                account_id="same",
                account_type="A",
            ),
            amount=MonetaryAmount.create(
                "100.00",
                Currency("INR", 2),
            ),
            entry_timestamp=datetime.now(UTC),
            source_reference="source-001",
            provenance_reference="proof-001",
        )
