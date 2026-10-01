from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from ..event_platform.event_domain import EventEnvelope
from .commission_contract import (
    CommissionBasis,
    CommissionBasisType,
    CommissionContract,
    CommissionContractConflictError,
    CommissionContractState,
    CommissionEligibilityRule,
    CommissionEntitlementReference,
    CommissionPartyReference,
    CommissionPartyType,
    CommissionProvenance,
    CommissionRate,
    CommissionRateType,
    EligibilityOperator,
)
from .commission_event_conflict import (
    CommissionFinancialEventConflictError,
    assert_no_event_conflict,
)
from .commission_event_integration import (
    CommissionEventIntegration,
)
from .commission_event_contract import (
    CommissionEventType,
)


UTC = timezone.utc

START = datetime(
    2026,
    9,
    1,
    tzinfo=UTC,
)


def _contract(
    rate: str = "2.5",
) -> CommissionContract:
    return CommissionContract(
        commission_id="commission-001",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="entitlement-001",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-001",
            ),
            deal_reference="deal-001",
            ownership_reference="ownership-001",
            provenance_reference="proof-001",
        ),
        basis=CommissionBasis(
            basis_type=(
                CommissionBasisType.GROSS_TRANSACTION_VALUE
            ),
            source_reference="deal.gross_value",
        ),
        rate=CommissionRate(
            rate_type=CommissionRateType.PERCENTAGE,
            value=rate,
        ),
        eligibility_rules=(
            CommissionEligibilityRule(
                rule_code="ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="TRUE",
            ),
        ),
        effective_from=START,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-001",
            captured_at=START - timedelta(days=1),
            evidence_reference="evidence-001",
        ),
        state=CommissionContractState.ACTIVE,
    )


def _event(
    integration: CommissionEventIntegration,
) -> EventEnvelope:
    return integration.create_event(
        event_type=CommissionEventType.COMMISSION_CREATED,
        tenant_id=UUID(
            "00000000-0000-0000-0000-000000000001"
        ),
        producer_id=UUID(
            "00000000-0000-0000-0000-000000000002"
        ),
        tenant_reference="tenant-a",
        source_id="commission-001",
        source_fingerprint="source-fp-001",
        payload={
            "commission_id": "commission-001",
            "contract_id": "contract-001",
            "deal_id": "deal-001",
        },
    )


def test_same_contract_identity_with_changed_terms_is_conflict() -> None:
    first = _contract()
    second = _contract("3.0")

    with pytest.raises(
        CommissionContractConflictError
    ):
        first.assert_compatible(second)


def test_same_source_command_has_deterministic_idempotency_key() -> None:
    integration = CommissionEventIntegration()

    first = integration.idempotency_key(
        event_type=CommissionEventType.COMMISSION_CALCULATED,
        tenant_reference="tenant-a",
        source_id="calc-001",
        source_fingerprint="fingerprint-001",
    )

    second = integration.idempotency_key(
        event_type=CommissionEventType.COMMISSION_CALCULATED,
        tenant_reference="tenant-a",
        source_id="calc-001",
        source_fingerprint="fingerprint-001",
    )

    assert first == second


def test_different_source_content_changes_idempotency_key() -> None:
    integration = CommissionEventIntegration()

    first = integration.idempotency_key(
        event_type=CommissionEventType.COMMISSION_CALCULATED,
        tenant_reference="tenant-a",
        source_id="calc-001",
        source_fingerprint="fingerprint-001",
    )

    second = integration.idempotency_key(
        event_type=CommissionEventType.COMMISSION_CALCULATED,
        tenant_reference="tenant-a",
        source_id="calc-001",
        source_fingerprint="fingerprint-002",
    )

    assert first != second


def test_same_event_identity_with_mutated_content_is_rejected() -> None:
    integration = CommissionEventIntegration()

    first = _event(integration)

    second = replace(
        first,
        payload={
            "commission_id": "commission-001",
            "contract_id": "contract-999",
            "deal_id": "deal-001",
            "financial_source_id": "commission-001",
            "financial_source_fingerprint": "source-fp-001",
            "financial_tenant_reference": "tenant-a",
        },
    )

    with pytest.raises(
        CommissionFinancialEventConflictError
    ):
        assert_no_event_conflict(
            first,
            second,
        )


def test_identical_event_observation_is_not_a_conflict() -> None:
    integration = CommissionEventIntegration()

    first = _event(integration)
    second = replace(first)

    assert_no_event_conflict(
        first,
        second,
    )


def test_event_ordering_key_is_commission_scoped() -> None:
    integration = CommissionEventIntegration()

    event = _event(integration)

    assert event.ordering_key == (
        "commission:commission-001"
    )
