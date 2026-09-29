from dataclasses import fields
from pathlib import Path
import json

from AUTONOMY_ENGINE.core.identity_tenant.membership import (
    AssuranceLevel,
    AttributeConstraint,
    ConstraintOperator,
    Entitlement,
    EntitlementStatus,
    Membership,
    MembershipResolutionResult,
    MembershipResolutionStatus,
    MembershipStatus,
    Organization,
    OrganizationStatus,
    Permission,
    PermissionSensitivity,
    RelationType,
    Relationship,
    RelationshipRequirement,
    RelationshipStatus,
    Role,
    RoleKind,
    Scope,
    ScopeKind,
)


CONTRACT = Path(
    "AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json"
)


def _load_contract():
    return json.loads(
        CONTRACT.read_text(encoding="utf-8")
    )


def test_contract_identity():
    contract = _load_contract()
    assert contract["contract"] == {
        "name": "REOS Membership, Roles & Permission Model Contract",
        "version": "1.0.0",
        "domain": "CORE-001",
        "subtask": "CORE-001-T03",
        "status": "ACTIVE",
    }


def test_entity_fields_match_runtime():
    contract = _load_contract()
    classes = (
        AttributeConstraint,
        RelationshipRequirement,
        Organization,
        Permission,
        Scope,
        Relationship,
        Entitlement,
        Role,
        Membership,
        MembershipResolutionResult,
    )
    for cls in classes:
        assert contract["entities"][cls.__name__]["fields"] == [
            field.name for field in fields(cls)
        ]


def test_enum_values_match_runtime():
    contract = _load_contract()
    enums = (
        OrganizationStatus,
        MembershipStatus,
        RoleKind,
        PermissionSensitivity,
        ScopeKind,
        RelationshipStatus,
        RelationType,
        ConstraintOperator,
        AssuranceLevel,
        EntitlementStatus,
        MembershipResolutionStatus,
    )
    for enum in enums:
        assert contract["enums"][enum.__name__]["values"] == [
            value.value for value in enum
        ]


def test_membership_lifecycle_is_locked():
    contract = _load_contract()
    assert contract["lifecycle"]["membership_status_transitions"] == {
        "INVITED": ["PENDING", "REVOKED"],
        "PENDING": ["ACTIVE", "REVOKED"],
        "ACTIVE": ["EXPIRED", "RESTRICTED", "REVOKED", "SUSPENDED"],
        "RESTRICTED": ["ACTIVE", "EXPIRED", "REVOKED", "SUSPENDED"],
        "SUSPENDED": ["ACTIVE", "EXPIRED", "RESTRICTED", "REVOKED"],
        "REVOKED": [],
        "EXPIRED": [],
    }


def test_authorization_boundary_is_locked():
    contract = _load_contract()
    model = contract["authorization_model"]
    assert model["rbac"]
    assert model["abac"]
    assert model["relationship"]
    assert model["contextual"]
    assert model["decision_boundary"].startswith(
        "T03 stores grants"
    )


def test_scope_rules_are_locked():
    contract = _load_contract()
    assert set(contract["scope_rules"]) == {
        "every scope is tenant-bound",
        "organization scope requires organization_id",
        "resource scope requires resource_type and exactly one resource_id",
        "resource_set scope requires resource_type and at least one resource_id",
        "cross-tenant scope reference is rejected",
    }


def test_isolation_rules_are_locked():
    contract = _load_contract()
    assert len(contract["isolation_rules"]) == 5


def test_no_decision_engine_or_sensitive_boundary_leak():
    contract = _load_contract()
    excluded = set(
        contract["source_of_truth_boundary"]["excluded_from_T03"]
    )
    assert {
        "authentication_credentials",
        "sessions",
        "tenant_isolation_engine",
        "authorization_decision_engine",
        "audit_storage",
        "event_persistence",
        "policy_evaluator",
        "AI_decision_engine",
    }.issubset(excluded)


def test_security_invariants_are_complete():
    contract = _load_contract()
    required = {
        "membership_identity_is_immutable",
        "membership_tenant_is_immutable",
        "membership_organization_is_immutable",
        "membership_revision_is_monotonic",
        "same_membership_revision_cannot_represent_different_state",
        "membership_validity_is_time_bounded_when_configured",
        "revoked_membership_is_terminal",
        "expired_membership_is_terminal",
        "tenant_bound_scope_cannot_cross_tenant",
        "organization_role_cannot_cross_organization",
        "tenant_role_cannot_cross_tenant",
        "tenant_entitlement_cannot_cross_tenant",
        "relationship_reference_cannot_cross_tenant",
        "no_credentials_or_tokens_in_T03_models",
        "no_authorization_decision_engine_in_T03",
    }
    assert required.issubset(
        set(contract["security_invariants"])
    )


def test_hard_rule_is_fail_closed():
    contract = _load_contract()
    assert contract["hard_rules"] == [
        "NO_VALID_MEMBERSHIP",
        "DENY",
    ]
