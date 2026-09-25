from dataclasses import fields
from pathlib import Path
import json

from AUTONOMY_ENGINE.core.identity_tenant.identity import (
    ACCOUNT_STATUS_TRANSITIONS,
    FORBIDDEN_IDENTITY_FIELDS,
    IDENTITY_STATUS_TRANSITIONS,
    AccountStatus,
    ExternalIdentityReference,
    ExternalIdentityStatus,
    Identity,
    IdentityAccount,
    IdentityResolutionResult,
    IdentityResolutionStatus,
    IdentityStatus,
    IdentityType,
    PrivacyClass,
    identity_model_field_names,
)


CONTRACT = Path(
    "AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json"
)


def _load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_machine_contract_exists_and_is_valid():
    contract = _load_contract()

    assert contract["contract"]["domain"] == "CORE-001"
    assert contract["contract"]["subtask"] == "CORE-001-T01"
    assert contract["contract"]["status"] == "ACTIVE"
    assert contract["contract"]["version"] == "1.1.0"


def test_machine_contract_contains_all_identity_types():
    from AUTONOMY_ENGINE.core.identity_tenant.identity import IdentityType

    contract = _load_contract()

    assert contract["entities"]["Identity"]["identity_types"] == [
        x.value for x in IdentityType
    ]


def test_machine_contract_contains_identity_fields():
    contract = _load_contract()

    assert contract["entities"]["Identity"]["fields"] == [
        f.name for f in fields(Identity)
    ]


def test_machine_contract_contains_identity_statuses():
    contract = _load_contract()

    assert contract["entities"]["Identity"]["statuses"] == [
        x.value for x in IdentityStatus
    ]


def test_machine_contract_contains_privacy_classes():
    contract = _load_contract()

    assert contract["entities"]["Identity"]["privacy_classes"] == [
        x.value for x in PrivacyClass
    ]


def test_machine_contract_contains_identity_account_contract():
    contract = _load_contract()

    assert contract["entities"]["IdentityAccount"]["fields"] == [
        f.name for f in fields(IdentityAccount)
    ]

    assert contract["entities"]["IdentityAccount"]["statuses"] == [
        x.value for x in AccountStatus
    ]


def test_machine_contract_contains_external_identity_contract():
    contract = _load_contract()

    assert contract["entities"]["ExternalIdentityReference"]["fields"] == [
        f.name for f in fields(ExternalIdentityReference)
    ]

    assert contract["entities"]["ExternalIdentityReference"]["statuses"] == [
        x.value for x in ExternalIdentityStatus
    ]

    assert contract["entities"]["ExternalIdentityReference"]["key"] == [
        "provider",
        "subject",
    ]


def test_machine_contract_contains_resolution_contract():
    contract = _load_contract()

    assert contract["entities"]["IdentityResolutionResult"]["fields"] == [
        f.name for f in fields(IdentityResolutionResult)
    ]

    assert contract["entities"]["IdentityResolutionResult"]["statuses"] == [
        x.value for x in IdentityResolutionStatus
    ]


def test_machine_contract_identity_lifecycle_matches_runtime():
    contract = _load_contract()

    expected = {
        status.value: sorted(target.value for target in targets)
        for status, targets in IDENTITY_STATUS_TRANSITIONS.items()
    }

    assert contract["lifecycle"]["identity_status_transitions"] == expected


def test_machine_contract_account_lifecycle_matches_runtime():
    contract = _load_contract()

    expected = {
        status.value: sorted(target.value for target in targets)
        for status, targets in ACCOUNT_STATUS_TRANSITIONS.items()
    }

    assert contract["lifecycle"]["account_status_transitions"] == expected


def test_machine_contract_external_lifecycle_is_explicit():
    contract = _load_contract()

    assert contract["lifecycle"][
        "external_identity_status_transitions"
    ] == {
        "ACTIVE": ["REVOKED"],
        "REVOKED": [],
    }


def test_machine_contract_canonicalization_is_locked():
    contract = _load_contract()

    handle = contract["canonicalization"]["handle"]

    assert handle["normalized"] is True
    assert handle["normalization"] == "trim_then_lowercase"
    assert handle["case_sensitive"] is False
    assert handle["unique"] is True


def test_machine_contract_registry_boundary_is_locked():
    contract = _load_contract()

    registry = contract["registry"]

    assert registry["type"] == "in_memory_domain_boundary"
    assert registry["authoritative_resolution_boundary"] is True
    assert registry["persistence_owned_elsewhere"] is True

    assert registry["indexes"] == [
        "identity_id",
        "handle",
        "external_provider_subject",
    ]


def test_machine_contract_capabilities_are_enabled():
    contract = _load_contract()

    capabilities = contract["capabilities"]

    required = {
        "human_identity",
        "service_identity",
        "ai_identity",
        "system_principal",
        "external_identity_reference",
        "deterministic_external_resolution",
        "immutable_identity_model",
        "account_identity_separation",
        "authorization_ready_context",
        "canonical_handle_uniqueness",
        "controlled_identity_lifecycle",
        "controlled_account_lifecycle",
        "canonical_identity_account_binding",
    }

    assert required.issubset(
        key
        for key, value in capabilities.items()
        if value is True
    )


def test_machine_contract_contains_required_security_invariants():
    contract = _load_contract()

    invariants = set(contract["security_invariants"])

    required = {
        "identity_id_is_immutable",
        "identity_is_distinct_from_account",
        "identity_is_distinct_from_credential",
        "identity_is_distinct_from_session",
        "canonical_handle_is_unique",
        "canonical_handle_is_case_insensitive",
        "registered_identity_cannot_change_canonical_handle",
        "identity_status_transition_is_valid",
        "deactivated_identity_is_terminal",
        "account_requires_canonical_identity",
        "account_status_transition_is_valid",
        "disabled_account_is_terminal",
        "authentication_epoch_is_monotonic",
        "created_at_is_immutable",
        "updated_at_is_timezone_aware",
        "revision_starts_at_one",
        "mutation_increments_revision_by_one",
        "no_op_does_not_increment_revision",
        "identity_id_survives_revision",
        "external_provider_subject_is_deterministic_key",
        "duplicate_external_binding_cannot_rebind_identity",
        "revoked_external_identity_is_terminal",
        "unknown_external_identity_fails_closed",
        "revoked_external_identity_fails_closed",
        "inactive_canonical_identity_fails_closed",
        "no_authentication_secret_is_stored_in_identity_model",
        "registry_resolution_is_fail_closed",
    }

    assert required.issubset(invariants)


def test_machine_contract_source_of_truth_boundary_is_locked():
    contract = _load_contract()

    boundary = contract["source_of_truth_boundary"]

    assert boundary["Identity"] == (
        "canonical identity domain record"
    )

    assert boundary["IdentityAccount"] == (
        "account and authentication-epoch boundary"
    )

    assert boundary["ExternalIdentityReference"] == (
        "external provider identity binding"
    )

    assert boundary["IdentityRegistry"] == (
        "deterministic T01 identity resolution boundary"
    )

    assert set(boundary["excluded_from_T01"]) == {
        "credentials",
        "sessions",
        "authorization",
        "tenant_membership",
        "persistence",
        "event_bus",
        "audit_engine",
    }


def test_machine_contract_forbidden_fields_match_runtime():
    contract = _load_contract()

    assert set(contract["forbidden_identity_fields"]) == set(
        FORBIDDEN_IDENTITY_FIELDS
    )

    assert identity_model_field_names().isdisjoint(
        FORBIDDEN_IDENTITY_FIELDS
    )


def test_machine_contract_resolution_outcomes_match_runtime():
    contract = _load_contract()

    assert contract["resolution_outcomes"] == [
        x.value for x in IdentityResolutionStatus
    ]
