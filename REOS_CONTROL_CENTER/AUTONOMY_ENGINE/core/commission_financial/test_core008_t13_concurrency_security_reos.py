from __future__ import annotations

import pytest

from .commission_concurrency import (
    CommissionDuplicateCommandError,
    CommissionStaleVersionError,
    FinancialConcurrencyBoundary,
    FinancialIdempotencyRecord,
    FinancialVersionToken,
)
from .commission_reos_contract import (
    CORE008_CANONICAL_STATE,
    CommissionREOSBoundary,
    CommissionREOSIntegrationContract,
    validate_reos_contract,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
    FinancialTenantBoundaryError,
)


def test_stale_financial_version_is_rejected() -> None:
    expected = FinancialVersionToken(
        tenant_id="tenant-a",
        aggregate_type="COMMISSION",
        aggregate_id="commission-001",
        version=2,
    )

    actual = FinancialVersionToken(
        tenant_id="tenant-a",
        aggregate_type="COMMISSION",
        aggregate_id="commission-001",
        version=3,
    )

    with pytest.raises(
        CommissionStaleVersionError
    ):
        FinancialConcurrencyBoundary.assert_version(
            expected,
            actual,
        )


def test_duplicate_command_with_changed_payload_is_rejected() -> None:
    record = FinancialIdempotencyRecord(
        tenant_id="tenant-a",
        operation="SETTLEMENT",
        idempotency_key="command-001",
        command_fingerprint="fingerprint-a",
        first_seen_at=__import__(
            "datetime"
        ).datetime.now(
            __import__(
                "datetime"
            ).timezone.utc
        ),
    )

    with pytest.raises(
        CommissionDuplicateCommandError
    ):
        FinancialConcurrencyBoundary.assert_idempotent(
            record,
            "fingerprint-b",
        )


def test_cross_tenant_financial_authorization_is_rejected() -> None:
    boundary = FinancialSecurityBoundary(
        lambda _: True
    )

    request = FinancialAuthorizationRequest(
        tenant_id="tenant-a",
        resource_tenant_id="tenant-b",
        actor_reference="user-001",
        resource_reference="commission-001",
        action=FinancialAuthorizationAction.READ,
        authorization_reference="auth-001",
    )

    with pytest.raises(
        FinancialTenantBoundaryError
    ):
        boundary.authorize(request)


def test_external_authorization_authority_is_respected() -> None:
    boundary = FinancialSecurityBoundary(
        lambda request: (
            request.actor_reference
            == "authorized-user"
        )
    )

    request = FinancialAuthorizationRequest(
        tenant_id="tenant-a",
        resource_tenant_id="tenant-a",
        actor_reference="authorized-user",
        resource_reference="commission-001",
        action=FinancialAuthorizationAction.SETTLE,
        authorization_reference="auth-001",
    )

    decision = boundary.authorize(request)

    assert decision.allowed is True


def test_reos_contract_cannot_own_state() -> None:
    contract = CommissionREOSIntegrationContract(
        gate_id="CORE-008",
        gate_name="Commission & Financial Core",
        task_name="T10 REOS Integration Contract",
        verification_command="python reos_control_center.py verify-all",
    )

    validate_reos_contract(contract)

    assert contract.canonical_state_path == (
        CORE008_CANONICAL_STATE
    )
    assert (
        contract.canonical_state_owned_externally
        is True
    )
    assert (
        contract.autonomous_project_state_mutation_allowed
        is False
    )


def test_reos_boundary_is_read_verify_only() -> None:
    boundary = CommissionREOSBoundary(
        discover=lambda: {
            "gate": "CORE-008",
            "state_owner": "REOS_CONTROL_CENTER",
        },
        verify=lambda command: command.strip() != "",
    )

    assert boundary.discover_contract()[
        "state_owner"
    ] == "REOS_CONTROL_CENTER"

    assert boundary.verify(
        "python reos_control_center.py verify-all"
    )
