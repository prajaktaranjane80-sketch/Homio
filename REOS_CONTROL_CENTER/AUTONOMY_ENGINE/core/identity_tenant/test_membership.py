from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from AUTONOMY_ENGINE.core.identity_tenant.membership import (
    AssuranceLevel,
    AttributeConstraint,
    ConstraintOperator,
    Entitlement,
    EntitlementStatus,
    Membership,
    MembershipContextDeniedError,
    MembershipDirectory,
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


def ids():
    return uuid4(), uuid4(), uuid4()


def build_directory():
    tenant, org_id, identity = ids()
    org = Organization.create(
        tenant_id=tenant,
        display_name="REOS Brokerage",
        slug="reos-brokerage",
    )
    permission = Permission.create(
        key="deal.follow_up",
        display_name="Follow up on deals",
        description="Allows operational follow-up on assigned deals.",
        resource="deal",
        action="follow_up",
        business_capability="Follow up on a deal",
        sensitivity=PermissionSensitivity.SENSITIVE,
        required_assurance=AssuranceLevel.STRONG,
    )
    scope = Scope.tenant(tenant)
    relationship = Relationship.create(
        tenant_id=tenant,
        subject_identity_id=identity,
        relation_type=RelationType.OWNER,
        target_type="deal",
        target_id=uuid4(),
    )
    role = Role.create(
        key="broker",
        display_name="Broker",
        description="Business role for brokerage operations.",
        permission_ids=(permission.permission_id,),
        tenant_id=tenant,
        role_kind=RoleKind.TENANT,
        scope_ids=(scope.scope_id,),
        relationship_requirements=(
            RelationshipRequirement(
                relation_type=RelationType.OWNER,
                target_type="deal",
            ),
        ),
        required_assurance=AssuranceLevel.STRONG,
    )
    entitlement = Entitlement.create(
        key="deal.follow_up",
        display_name="Follow up on deals",
        description="Business capability for deal follow-up.",
        permission_ids=(permission.permission_id,),
        tenant_id=tenant,
        scope_ids=(scope.scope_id,),
    )
    membership = Membership.create(
        tenant_id=tenant,
        organization_id=org.organization_id,
        identity_id=identity,
        role_ids=(role.role_id,),
        entitlement_ids=(entitlement.entitlement_id,),
        scope_ids=(scope.scope_id,),
        relationship_ids=(relationship.relationship_id,),
        required_assurance=AssuranceLevel.STRONG,
    ).transition_to(MembershipStatus.PENDING).transition_to(
        MembershipStatus.ACTIVE
    )
    directory = MembershipDirectory()
    directory.register_organization(org)
    directory.register_permission(permission)
    directory.register_scope(scope)
    directory.register_relationship(relationship)
    directory.register_entitlement(entitlement)
    directory.register_role(role)
    directory.register_membership(membership)
    return directory, tenant, org, identity, membership, role, entitlement, scope, relationship


def test_organization_creation_and_tenant_binding():
    tenant, _, _ = ids()
    organization = Organization.create(
        tenant_id=tenant,
        display_name="Mumbai Brokerage",
        slug="mumbai-brokerage",
    )
    assert organization.tenant_id == tenant
    assert organization.is_active


def test_organization_rejects_self_parent():
    tenant = uuid4()
    organization_id = uuid4()
    with pytest.raises(ValueError):
        Organization(
            organization_id=organization_id,
            tenant_id=tenant,
            display_name="Bad",
            slug="bad-org",
            parent_organization_id=organization_id,
        )


def test_permission_has_business_language():
    permission = Permission.create(
        key="lead.view",
        display_name="View leads",
        description="View lead records.",
        resource="lead",
        action="view",
        business_capability="View lead information",
    )
    assert permission.business_capability == "View lead information"


def test_scope_is_always_tenant_bound():
    tenant = uuid4()
    scope = Scope.tenant(tenant)
    assert scope.tenant_id == tenant
    assert scope.is_tenant_wide


def test_resource_scope_requires_exactly_one_resource():
    tenant = uuid4()
    with pytest.raises(ValueError):
        Scope(
            scope_id=uuid4(),
            tenant_id=tenant,
            scope_kind=ScopeKind.RESOURCE,
            resource_type="deal",
        )


def test_constraint_shape_is_declarative():
    constraint = AttributeConstraint.equals("deal.status", "OPEN")
    assert constraint.operator is ConstraintOperator.EQUALS
    assert constraint.expected_values == ("OPEN",)


def test_constraint_rejects_invalid_expected_values():
    with pytest.raises(ValueError):
        AttributeConstraint(
            attribute_key="deal.status",
            operator=ConstraintOperator.EXISTS,
            expected_values=("OPEN",),
        )


def test_relationship_is_declarative_and_time_aware():
    relationship = Relationship.create(
        tenant_id=uuid4(),
        subject_identity_id=uuid4(),
        relation_type=RelationType.BROKER_OF,
        target_type="project",
        target_id=uuid4(),
    )
    assert relationship.status is RelationshipStatus.ACTIVE
    assert relationship.is_active_at()


def test_role_supports_rbac_abac_relationship_constraints():
    tenant = uuid4()
    permission_id = uuid4()
    role = Role.create(
        key="broker",
        display_name="Broker",
        description="Broker role.",
        permission_ids=(permission_id,),
        tenant_id=tenant,
        relationship_requirements=(
            RelationshipRequirement(
                relation_type=RelationType.OWNER,
                target_type="deal",
            ),
        ),
        attribute_constraints=(
            AttributeConstraint.equals(
                "operating_mode",
                "OWNED_INTERNATIONAL_BROKERAGE",
            ),
        ),
        required_assurance=AssuranceLevel.STRONG,
    )
    assert role.permission_ids == (permission_id,)
    assert role.relationship_requirements
    assert role.attribute_constraints


def test_system_role_cannot_have_tenant_or_organization_scope():
    with pytest.raises(ValueError):
        Role.create(
            key="system",
            display_name="System",
            description="System role.",
            permission_ids=(),
            role_kind=RoleKind.SYSTEM,
            tenant_id=uuid4(),
        )


def test_organization_role_requires_organization():
    with pytest.raises(ValueError):
        Role.create(
            key="org-admin",
            display_name="Organization Admin",
            description="Admin.",
            permission_ids=(),
            role_kind=RoleKind.ORGANIZATION,
            tenant_id=uuid4(),
        )


def test_membership_lifecycle_is_explicit():
    tenant, org, identity = uuid4(), uuid4(), uuid4()
    membership = Membership.create(
        tenant_id=tenant,
        organization_id=org,
        identity_id=identity,
    )
    assert membership.status is MembershipStatus.INVITED
    membership = membership.transition_to(MembershipStatus.PENDING)
    membership = membership.transition_to(MembershipStatus.ACTIVE)
    assert membership.is_active
    assert membership.joined_at is not None


def test_revoked_membership_is_terminal():
    tenant, org, identity = uuid4(), uuid4(), uuid4()
    membership = Membership.create(
        tenant_id=tenant,
        organization_id=org,
        identity_id=identity,
    ).transition_to(MembershipStatus.REVOKED)
    with pytest.raises(ValueError):
        membership.transition_to(MembershipStatus.ACTIVE)


def test_membership_time_window_fails_closed():
    now = datetime.now(timezone.utc)
    membership = Membership.create(
        tenant_id=uuid4(),
        organization_id=uuid4(),
        identity_id=uuid4(),
        valid_from=now + timedelta(hours=1),
    ).transition_to(MembershipStatus.PENDING).transition_to(
        MembershipStatus.ACTIVE
    )
    assert not membership.is_valid_at(now)


def test_membership_restricted_is_still_structurally_valid():
    membership = Membership.create(
        tenant_id=uuid4(),
        organization_id=uuid4(),
        identity_id=uuid4(),
    ).transition_to(MembershipStatus.PENDING).transition_to(
        MembershipStatus.ACTIVE
    ).transition_to(MembershipStatus.RESTRICTED)
    assert membership.is_valid_at()


def test_membership_revision_changes_on_grant_mutation():
    membership = Membership.create(
        tenant_id=uuid4(),
        organization_id=uuid4(),
        identity_id=uuid4(),
    )
    revised = membership.add_role(uuid4())
    assert revised.revision == membership.revision + 1


def test_directory_registers_complete_structure():
    directory, tenant, org, identity, membership, role, entitlement, scope, relationship = build_directory()
    assert directory.get_organization(org.organization_id) == org
    assert directory.get_role(role.role_id) == role
    assert directory.get_entitlement(entitlement.entitlement_id) == entitlement
    assert directory.get_scope(scope.scope_id) == scope
    assert directory.get_relationship(relationship.relationship_id) == relationship
    assert directory.get_membership(membership.membership_id) == membership


def test_directory_resolves_valid_membership():
    directory, tenant, org, identity, membership, *_ = build_directory()
    result = directory.resolve_membership(
        tenant_id=tenant,
        organization_id=org.organization_id,
        identity_id=identity,
    )
    assert result.status is MembershipResolutionStatus.RESOLVED
    assert result.resolved
    assert result.membership == membership


def test_directory_requires_valid_membership():
    directory, tenant, org, identity, *_ = build_directory()
    membership = directory.get_membership(
        directory.resolve_membership(
            tenant_id=tenant,
            organization_id=org.organization_id,
            identity_id=identity,
        ).membership_id
    )
    assert membership is not None
    revoked = membership.transition_to(MembershipStatus.REVOKED)
    directory.register_membership(revoked)
    with pytest.raises(MembershipContextDeniedError):
        directory.require_membership(
            tenant_id=tenant,
            organization_id=org.organization_id,
            identity_id=identity,
        )


def test_directory_rejects_missing_membership():
    directory = MembershipDirectory()
    with pytest.raises(MembershipContextDeniedError):
        directory.require_membership(
            tenant_id=uuid4(),
            organization_id=uuid4(),
            identity_id=uuid4(),
        )


def test_directory_rejects_cross_tenant_organization():
    directory = MembershipDirectory()
    tenant_a = uuid4()
    tenant_b = uuid4()
    org_b = Organization.create(
        tenant_id=tenant_b,
        display_name="Tenant B",
        slug="tenant-b",
    )
    directory.register_organization(org_b)
    membership = Membership.create(
        tenant_id=tenant_a,
        organization_id=org_b.organization_id,
        identity_id=uuid4(),
    )
    with pytest.raises(ValueError):
        directory.register_membership(membership)


def test_directory_rejects_cross_tenant_scope():
    directory, tenant, org, identity, membership, *_ = build_directory()
    foreign_scope = Scope.tenant(uuid4())
    directory.register_scope(foreign_scope)
    bad = membership.add_scope(foreign_scope.scope_id)
    with pytest.raises(ValueError):
        directory.register_membership(bad)


def test_directory_rejects_cross_tenant_role():
    directory, tenant, org, identity, membership, *_ = build_directory()
    foreign_permission = Permission.create(
        key="foreign.read",
        display_name="Foreign read",
        description="Foreign permission.",
        resource="foreign",
        action="read",
        business_capability="Read foreign records",
    )
    directory.register_permission(foreign_permission)
    foreign_role = Role.create(
        key="foreign",
        display_name="Foreign Role",
        description="Foreign role.",
        permission_ids=(foreign_permission.permission_id,),
        tenant_id=uuid4(),
        role_kind=RoleKind.TENANT,
    )
    directory.register_role(foreign_role)
    bad = membership.add_role(foreign_role.role_id)
    with pytest.raises(ValueError):
        directory.register_membership(bad)


def test_directory_rejects_cross_tenant_relationship():
    directory, tenant, org, identity, membership, *_ = build_directory()
    foreign_relationship = Relationship.create(
        tenant_id=uuid4(),
        subject_identity_id=identity,
        relation_type=RelationType.OWNER,
        target_type="deal",
        target_id=uuid4(),
    )
    directory.register_relationship(foreign_relationship)
    bad = membership.bind_relationship(foreign_relationship.relationship_id)
    with pytest.raises(ValueError):
        directory.register_membership(bad)


def test_same_revision_different_membership_state_is_rejected():
    directory, tenant, org, identity, membership, *_ = build_directory()
    changed = replace_without_revision(
        membership,
        status=MembershipStatus.RESTRICTED,
    )
    with pytest.raises(ValueError):
        directory.register_membership(changed)


def test_role_key_unique_within_same_scope():
    directory = MembershipDirectory()
    permission = Permission.create(
        key="lead.read",
        display_name="View leads",
        description="View leads.",
        resource="lead",
        action="view",
        business_capability="View leads",
    )
    directory.register_permission(permission)
    tenant = uuid4()
    role_a = Role.create(
        key="sales",
        display_name="Sales",
        description="Sales.",
        permission_ids=(permission.permission_id,),
        tenant_id=tenant,
    )
    role_b = Role.create(
        key="sales",
        display_name="Sales Two",
        description="Sales two.",
        permission_ids=(permission.permission_id,),
        tenant_id=tenant,
    )
    directory.register_role(role_a)
    with pytest.raises(ValueError):
        directory.register_role(role_b)


def test_global_system_role_can_be_reused_by_membership():
    directory, tenant, org, identity, membership, *_ = build_directory()
    system_permission = Permission.create(
        key="system.read",
        display_name="Read system",
        description="Read system metadata.",
        resource="system",
        action="read",
        business_capability="View system metadata",
    )
    directory.register_permission(system_permission)
    system_role = Role.create(
        key="platform-observer",
        display_name="Platform Observer",
        description="Global system role.",
        permission_ids=(system_permission.permission_id,),
        role_kind=RoleKind.SYSTEM,
    )
    directory.register_role(system_role)
    revised = membership.add_role(system_role.role_id)
    directory.register_membership(revised)
    assert directory.get_membership(membership.membership_id) == revised


def test_no_authorization_decision_engine_is_created():
    assert not hasattr(MembershipDirectory, "authorize")
    assert not hasattr(Membership, "authorize")


def replace_without_revision(membership: Membership, **changes) -> Membership:
    from dataclasses import replace
    return replace(membership, **changes)
