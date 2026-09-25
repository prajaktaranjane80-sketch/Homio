from dataclasses import fields
from pathlib import Path
import json

from AUTONOMY_ENGINE.core.identity_tenant.tenant import (
    DataResidencyMode,
    IsolationProfile,
    OperatingMode,
    ProvisioningIntentStatus,
    Tenant,
    TenantConfigurationReference,
    TenantContext,
    TenantKind,
    TenantProvisioningIntent,
    TenantRegionJurisdictionReference,
    TenantResolutionResult,
    TenantResolutionStatus,
    TenantSecurityProfileReference,
    TenantStatus,
)


CONTRACT = Path(
    "AUTONOMY_ENGINE/core/identity_tenant/tenant_contract.json"
)


def _load_contract():
    return json.loads(
        CONTRACT.read_text(
            encoding="utf-8"
        )
    )


def test_machine_contract_exists_and_is_valid():
    contract = _load_contract()

    assert contract["contract"]["domain"] == (
        "CORE-001"
    )
    assert contract["contract"]["subtask"] == (
        "CORE-001-T02"
    )
    assert contract["contract"]["status"] == (
        "ACTIVE"
    )
    assert contract["contract"]["version"] == (
        "2.0.0"
    )


def test_machine_contract_configuration_reference_matches_runtime():
    contract = _load_contract()

    assert contract["entities"][
        "TenantConfigurationReference"
    ]["fields"] == [
        field.name
        for field in fields(
            TenantConfigurationReference
        )
    ]


def test_machine_contract_security_profile_matches_runtime():
    contract = _load_contract()

    assert contract["entities"][
        "TenantSecurityProfileReference"
    ]["fields"] == [
        field.name
        for field in fields(
            TenantSecurityProfileReference
        )
    ]


def test_machine_contract_region_reference_matches_runtime():
    contract = _load_contract()

    assert contract["entities"][
        "TenantRegionJurisdictionReference"
    ]["fields"] == [
        field.name
        for field in fields(
            TenantRegionJurisdictionReference
        )
    ]


def test_machine_contract_tenant_matches_runtime():
    contract = _load_contract()

    assert contract["entities"]["Tenant"][
        "fields"
    ] == [
        field.name
        for field in fields(Tenant)
    ]

    assert contract["entities"]["Tenant"][
        "kinds"
    ] == [
        value.value
        for value in TenantKind
    ]

    assert contract["entities"]["Tenant"][
        "operating_modes"
    ] == [
        value.value
        for value in OperatingMode
    ]

    assert contract["entities"]["Tenant"][
        "statuses"
    ] == [
        value.value
        for value in TenantStatus
    ]

    assert contract["entities"]["Tenant"][
        "isolation_profiles"
    ] == [
        value.value
        for value in IsolationProfile
    ]

    assert contract["entities"]["Tenant"][
        "residency_modes"
    ] == [
        value.value
        for value in DataResidencyMode
    ]


def test_machine_contract_context_matches_runtime():
    contract = _load_contract()

    assert contract["entities"]["TenantContext"][
        "fields"
    ] == [
        field.name
        for field in fields(TenantContext)
    ]


def test_machine_contract_resolution_matches_runtime():
    contract = _load_contract()

    assert contract["entities"][
        "TenantResolutionResult"
    ]["fields"] == [
        field.name
        for field in fields(
            TenantResolutionResult
        )
    ]

    assert contract["entities"][
        "TenantResolutionResult"
    ]["statuses"] == [
        value.value
        for value in TenantResolutionStatus
    ]


def test_machine_contract_provisioning_matches_runtime():
    contract = _load_contract()

    assert contract["entities"][
        "TenantProvisioningIntent"
    ]["fields"] == [
        field.name
        for field in fields(
            TenantProvisioningIntent
        )
    ]

    assert contract["entities"][
        "TenantProvisioningIntent"
    ]["statuses"] == [
        value.value
        for value in ProvisioningIntentStatus
    ]


def test_machine_contract_lifecycle_is_explicit():
    contract = _load_contract()

    expected = {
        status.value: sorted(
            target.value
            for target in {
                TenantStatus.PROVISIONING: {
                    TenantStatus.PENDING_ACTIVATION,
                    TenantStatus.RESTRICTED,
                    TenantStatus.DEACTIVATING,
                },
                TenantStatus.PENDING_ACTIVATION: {
                    TenantStatus.ACTIVE,
                    TenantStatus.RESTRICTED,
                    TenantStatus.SUSPENDED,
                    TenantStatus.DEACTIVATING,
                },
                TenantStatus.ACTIVE: {
                    TenantStatus.RESTRICTED,
                    TenantStatus.SUSPENDED,
                    TenantStatus.DEACTIVATING,
                },
                TenantStatus.RESTRICTED: {
                    TenantStatus.ACTIVE,
                    TenantStatus.SUSPENDED,
                    TenantStatus.DEACTIVATING,
                },
                TenantStatus.SUSPENDED: {
                    TenantStatus.ACTIVE,
                    TenantStatus.RESTRICTED,
                    TenantStatus.DEACTIVATING,
                },
                TenantStatus.DEACTIVATING: {
                    TenantStatus.DEACTIVATED,
                },
                TenantStatus.DEACTIVATED: {
                    TenantStatus.ARCHIVED,
                },
                TenantStatus.ARCHIVED: set(),
            }[status]
        )
        for status in TenantStatus
    }

    assert (
        contract["lifecycle"]["transitions"]
        == expected
    )


def test_machine_contract_context_rules_are_locked():
    contract = _load_contract()

    context = contract["context_resolution"]

    assert context["authoritative_boundary"] is True
    assert context["lookup_indexes"] == [
        "tenant_id",
        "slug",
    ]
    assert context["valid_context_statuses"] == [
        "ACTIVE",
        "RESTRICTED",
    ]
    assert context["archived_status"] == "ARCHIVED"


def test_machine_contract_source_boundary_is_locked():
    contract = _load_contract()

    excluded = set(
        contract["source_of_truth_boundary"][
            "excluded_from_T02"
        ]
    )

    assert excluded == {
        "memberships",
        "roles",
        "permissions",
        "authorization_decisions",
        "cross_tenant_enforcement",
        "credentials",
        "sessions",
        "audit_storage",
        "event_persistence",
    }


def test_machine_contract_hard_rule_is_fail_closed():
    contract = _load_contract()

    assert contract["hard_rules"] == [
        "NO_VALID_TENANT_CONTEXT",
        "DENY",
    ]


def test_machine_contract_security_invariants_are_complete():
    contract = _load_contract()

    required = {
        "tenant_id_is_immutable",
        "slug_is_canonical",
        "tenant_slug_is_unique",
        "tenant_revision_is_monotonic",
        "same_revision_cannot_represent_different_state",
        "tenant_lifecycle_transitions_are_explicit",
        "invalid_transitions_fail_closed",
        "active_tenant_requires_owner_and_primary_admin",
        "active_tenant_requires_fail_closed_security_profile",
        "active_tenant_requires_valid_tenant_context_policy",
        "restricted_residency_requires_scope",
        "provisioning_is_idempotency_keyed",
        "archived_tenant_is_terminal",
        "tenant_configuration_is_reference_only",
        "tenant_security_profile_is_reference_only",
        "tenant_region_jurisdiction_is_reference_only",
        "no_credentials_or_tokens_in_tenant_model",
        "unknown_tenant_context_fails_closed",
        "inactive_tenant_context_fails_closed",
        "archived_tenant_context_fails_closed",
        "valid_tenant_context_contains_current_revision",
        "valid_tenant_context_contains_operating_mode",
        "valid_tenant_context_contains_configuration_reference",
        "valid_tenant_context_contains_security_profile_reference",
    }

    actual = set(
        contract["security_invariants"]
    )

    assert required.issubset(actual)
