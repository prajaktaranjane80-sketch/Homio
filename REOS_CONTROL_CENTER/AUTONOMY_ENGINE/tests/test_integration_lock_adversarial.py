"""
Adversarial tests for the REOS_CONTROL_CENTER <-> AUTONOMY_ENGINE
integration lock.

These tests verify that the integration contract:

- remains fail-closed,
- preserves REOS_CONTROL_CENTER authority,
- rejects direct state mutation,
- rejects executor discovery,
- requires architecture lock,
- requires an explicit controller contract version,
- rejects incompatible integration contracts,
- accepts the canonical locked contract,
- remains deterministic,
- performs no execution or mutation.

The integration lock is a contract boundary only.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from integration.integration_lock import (
    AUTHORITATIVE_CONTROLLER,
    AUTONOMY_ENGINE_NAME,
    INTEGRATION_CONTRACT_VERSION,
    IntegrationBlockReason,
    IntegrationCapabilities,
    IntegrationContract,
    IntegrationLockStatus,
    integration_contract,
    validate_integration,
    verify_integration_lock,
)


def test_canonical_integration_contract_is_locked() -> None:
    contract = integration_contract()

    assert contract.controller_name == AUTHORITATIVE_CONTROLLER
    assert contract.autonomy_engine_name == AUTONOMY_ENGINE_NAME
    assert contract.integration_contract_version == INTEGRATION_CONTRACT_VERSION
    assert contract.controller_authoritative is True
    assert contract.architecture_locked is True


def test_canonical_integration_lock_is_accepted() -> None:
    result = verify_integration_lock()

    assert result.allowed is True
    assert result.status is IntegrationLockStatus.LOCKED
    assert result.block_reason is None
    assert result.errors == ()


def test_wrong_controller_cannot_become_authority() -> None:
    contract = replace(
        integration_contract(),
        controller_name="UNTRUSTED_CONTROLLER",
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.status is IntegrationLockStatus.INCOMPATIBLE
    assert "CONTROLLER_NAME_INVALID" in result.errors


def test_autonomy_engine_cannot_replace_controller_identity() -> None:
    contract = replace(
        integration_contract(),
        autonomy_engine_name="FAKE_CONTROLLER",
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert "AUTONOMY_ENGINE_NAME_INVALID" in result.errors


def test_missing_controller_contract_version_fails_closed() -> None:
    contract = replace(
        integration_contract(),
        controller_contract_version="",
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.block_reason is IntegrationBlockReason.CONTRACT_VERSION_MISSING


def test_architecture_unlock_is_rejected() -> None:
    contract = replace(
        integration_contract(),
        architecture_locked=False,
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.block_reason is IntegrationBlockReason.ARCHITECTURE_NOT_LOCKED
    assert "ARCHITECTURE_NOT_LOCKED" in result.errors


def test_controller_must_remain_authoritative() -> None:
    contract = replace(
        integration_contract(),
        controller_authoritative=False,
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.block_reason is IntegrationBlockReason.CONTROLLER_NOT_AUTHORITATIVE


def test_direct_state_mutation_is_forbidden() -> None:
    capabilities = replace(
        integration_contract().capabilities,
        mutate_state_directly=True,
    )

    contract = replace(
        integration_contract(),
        capabilities=capabilities,
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.block_reason is IntegrationBlockReason.CAPABILITY_CONTRACT_INVALID
    assert "DIRECT_STATE_MUTATION_FORBIDDEN" in result.errors


def test_executor_discovery_is_forbidden() -> None:
    capabilities = replace(
        integration_contract().capabilities,
        discover_executor=True,
    )

    contract = replace(
        integration_contract(),
        capabilities=capabilities,
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.block_reason is IntegrationBlockReason.CAPABILITY_CONTRACT_INVALID
    assert "EXECUTOR_DISCOVERY_FORBIDDEN" in result.errors


def test_invalid_integration_object_fails_closed() -> None:
    result = validate_integration(object())  # type: ignore[arg-type]

    assert result.allowed is False
    assert result.status is IntegrationLockStatus.INVALID
    assert result.block_reason is IntegrationBlockReason.INTEGRATION_CONTRACT_INVALID
    assert "contract must be an IntegrationContract." in result.errors


def test_incompatible_integration_contract_version_is_rejected() -> None:
    contract = replace(
        integration_contract(),
        integration_contract_version="999.0",
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert result.status is IntegrationLockStatus.INCOMPATIBLE
    assert "INTEGRATION_CONTRACT_VERSION_UNSUPPORTED" in result.errors


def test_capability_contract_validation_is_deterministic() -> None:
    capabilities = IntegrationCapabilities(
        mutate_state_directly=True,
        discover_executor=True,
    )

    errors_first = capabilities.validate()
    errors_second = capabilities.validate()

    assert errors_first == errors_second
    assert "DIRECT_STATE_MUTATION_FORBIDDEN" in errors_first
    assert "EXECUTOR_DISCOVERY_FORBIDDEN" in errors_first


def test_integration_contract_validation_is_side_effect_free() -> None:
    contract = integration_contract()

    first = validate_integration(contract)
    second = validate_integration(contract)

    assert first.to_dict() == second.to_dict()


def test_canonical_contract_does_not_grant_controller_approval() -> None:
    capabilities = integration_contract().capabilities

    assert capabilities.approve_gate is False
    assert capabilities.transition_controller is False


def test_canonical_contract_allows_observation_capabilities() -> None:
    capabilities = integration_contract().capabilities

    assert capabilities.observe_state is True
    assert capabilities.observe_plan is True
    assert capabilities.observe_gate is True
    assert capabilities.observe_verification is True


def test_authoritative_mutation_executor_is_explicit_capability_only() -> None:
    capabilities = integration_contract().capabilities

    assert capabilities.execute_authoritative_mutation is True
    assert capabilities.discover_executor is False


def test_lock_result_is_json_serializable_shape() -> None:
    result = verify_integration_lock()
    payload = result.to_dict()

    assert payload["status"] == IntegrationLockStatus.LOCKED.value
    assert payload["allowed"] is True
    assert payload["errors"] == []
    assert isinstance(payload["evidence"], dict)


@pytest.mark.parametrize(
    "field,value,expected_error",
    [
        (
            "controller_name",
            "",
            "CONTROLLER_NAME_INVALID",
        ),
        (
            "autonomy_engine_name",
            "",
            "AUTONOMY_ENGINE_NAME_INVALID",
        ),
        (
            "integration_contract_version",
            "0.0",
            "INTEGRATION_CONTRACT_VERSION_UNSUPPORTED",
        ),
    ],
)
def test_identity_and_version_tampering_fails_closed(
    field: str,
    value: str,
    expected_error: str,
) -> None:
    contract = replace(
        integration_contract(),
        **{field: value},
    )

    result = validate_integration(contract)

    assert result.allowed is False
    assert expected_error in result.errors
