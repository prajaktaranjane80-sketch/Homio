from uuid import UUID, uuid4

import pytest

from AUTONOMY_ENGINE.core.identity_tenant.tenant import (
    DataResidencyMode,
    IsolationProfile,
    OperatingMode,
    ProvisioningIntentStatus,
    Tenant,
    TenantConfigurationReference,
    TenantContextDeniedError,
    TenantKind,
    TenantProvisioningIntent,
    TenantRegionJurisdictionReference,
    TenantRegistry,
    TenantResolutionStatus,
    TenantSecurityProfileReference,
    TenantStatus,
)


def test_tenant_creation_is_typed_and_authoritative():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="HOMIO Brokerage",
        slug="homio-brokerage",
    )

    assert isinstance(tenant.tenant_id, UUID)
    assert tenant.tenant_kind is TenantKind.BROKERAGE
    assert (
        tenant.operating_mode
        is OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
    )
    assert tenant.status is TenantStatus.PROVISIONING
    assert tenant.revision == 1
    assert tenant.configuration_ref.configuration_key == (
        "default"
    )
    assert tenant.security_profile_ref.profile_key == (
        "default"
    )


@pytest.mark.parametrize(
    "mode",
    list(OperatingMode),
)
def test_all_approved_operating_modes_are_supported(mode):
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=mode,
        display_name="Tenant",
        slug=f"tenant-{mode.name.lower()}",
    )

    assert tenant.operating_mode is mode


@pytest.mark.parametrize(
    "kind",
    list(TenantKind),
)
def test_all_tenant_kinds_are_supported(kind):
    tenant = Tenant.create(
        tenant_kind=kind,
        operating_mode=(
            OperatingMode.PLATFORM_API_PARTNER
        ),
        display_name="Tenant",
        slug=f"kind-{kind.name.lower()}",
    )

    assert tenant.tenant_kind is kind


def test_slug_is_normalized():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BUILDER,
        operating_mode=OperatingMode.BUILDER_SAAS,
        display_name="Builder",
        slug="  ACME.BUILDER  ",
    )

    assert tenant.slug == "acme.builder"


@pytest.mark.parametrize(
    "slug",
    [
        "x",
        "",
        "bad slug",
        "bad/name",
        "_bad",
        "-bad",
    ],
)
def test_invalid_slug_is_rejected(slug):
    with pytest.raises((ValueError, TypeError)):
        Tenant.create(
            tenant_kind=TenantKind.BUILDER,
            operating_mode=OperatingMode.BUILDER_SAAS,
            display_name="Builder",
            slug=slug,
        )


def test_identity_and_timestamps_are_immutable_and_aware():
    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=(
            OperatingMode.ENTERPRISE_WHITE_LABEL
        ),
        display_name="Enterprise",
        slug="enterprise",
    )

    assert tenant.tenant_id is not None
    assert tenant.created_at.tzinfo is not None
    assert tenant.updated_at.tzinfo is not None

    with pytest.raises(Exception):
        tenant.slug = "changed"


def test_activation_requires_owner_and_admin():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="brokerage",
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    )

    with pytest.raises(ValueError):
        tenant.transition_to(
            TenantStatus.ACTIVE
        )


def test_tenant_becomes_active_only_with_administrators():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="brokerage-active",
    )

    owner = uuid4()

    tenant = tenant.assign_administrators(
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    )

    active = tenant.transition_to(
        TenantStatus.ACTIVE
    )

    assert active.is_active
    assert active.accepts_new_activity
    assert active.is_context_valid
    assert active.revision == tenant.revision + 1


def test_valid_lifecycle_transitions():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="lifecycle",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    tenant = tenant.transition_to(
        TenantStatus.PENDING_ACTIVATION
    )
    tenant = tenant.transition_to(
        TenantStatus.ACTIVE
    )
    tenant = tenant.transition_to(
        TenantStatus.SUSPENDED
    )
    tenant = tenant.transition_to(
        TenantStatus.ACTIVE
    )
    tenant = tenant.transition_to(
        TenantStatus.DEACTIVATING
    )
    tenant = tenant.transition_to(
        TenantStatus.DEACTIVATED
    )
    tenant = tenant.transition_to(
        TenantStatus.ARCHIVED
    )

    assert tenant.status is TenantStatus.ARCHIVED
    assert not tenant.is_context_valid


@pytest.mark.parametrize(
    "start,end",
    [
        (
            TenantStatus.ARCHIVED,
            TenantStatus.ACTIVE,
        ),
        (
            TenantStatus.DEACTIVATED,
            TenantStatus.ACTIVE,
        ),
        (
            TenantStatus.DEACTIVATING,
            TenantStatus.ACTIVE,
        ),
        (
            TenantStatus.PROVISIONING,
            TenantStatus.ACTIVE,
        ),
        (
            TenantStatus.ACTIVE,
            TenantStatus.ARCHIVED,
        ),
    ],
)
def test_invalid_lifecycle_transitions_fail_closed(
    start,
    end,
):
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug=(
            f"invalid-{start.name.lower()}"
            f"-{end.name.lower()}"
        ),
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    while tenant.status is not start:
        next_states = {
            TenantStatus.PROVISIONING:
                TenantStatus.PENDING_ACTIVATION,
            TenantStatus.PENDING_ACTIVATION:
                TenantStatus.ACTIVE,
            TenantStatus.ACTIVE:
                TenantStatus.DEACTIVATING,
            TenantStatus.DEACTIVATING:
                TenantStatus.DEACTIVATED,
            TenantStatus.DEACTIVATED:
                TenantStatus.ARCHIVED,
        }

        if tenant.status not in next_states:
            break

        tenant = tenant.transition_to(
            next_states[tenant.status]
        )

    if tenant.status is start:
        with pytest.raises(ValueError):
            tenant.transition_to(end)


def test_restricted_residency_requires_scope():
    with pytest.raises(ValueError):
        Tenant.create(
            tenant_kind=TenantKind.ENTERPRISE,
            operating_mode=(
                OperatingMode.ENTERPRISE_WHITE_LABEL
            ),
            display_name="Enterprise",
            slug="enterprise-residency",
            residency_mode=(
                DataResidencyMode.REGION_BOUND
            ),
        )


def test_region_bound_residency_is_supported():
    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=(
            OperatingMode.ENTERPRISE_WHITE_LABEL
        ),
        display_name="Enterprise",
        slug="region-bound",
        residency_mode=(
            DataResidencyMode.REGION_BOUND
        ),
        residency_region="eu-west-1",
    )

    assert (
        tenant.residency_mode
        is DataResidencyMode.REGION_BOUND
    )
    assert tenant.residency_region == "eu-west-1"
    assert (
        tenant.region_jurisdiction_ref is not None
    )
    assert (
        tenant.region_jurisdiction_ref.region
        == "eu-west-1"
    )


def test_isolation_profile_is_explicit():
    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=(
            OperatingMode.ENTERPRISE_WHITE_LABEL
        ),
        display_name="Enterprise",
        slug="dedicated",
        isolation_profile=(
            IsolationProfile.TENANT_DEDICATED
        ),
    )

    assert (
        tenant.isolation_profile
        is IsolationProfile.TENANT_DEDICATED
    )


def test_owner_and_admin_assignment_is_immutable():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="admin-assignment",
    )

    owner = uuid4()

    updated = tenant.assign_administrators(
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    assert tenant.owner_identity_id is None
    assert updated.owner_identity_id == owner
    assert updated.revision == tenant.revision + 1


def test_configuration_reference_is_first_class():
    reference = TenantConfigurationReference.create(
        "broker.default",
        version=3,
    )

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="configuration-reference",
        configuration_ref=reference,
    )

    assert (
        tenant.configuration_ref
        is reference
    )

    replacement = TenantConfigurationReference.create(
        "broker.production",
        version=4,
    )

    updated = tenant.with_configuration_reference(
        replacement
    )

    assert (
        updated.configuration_ref
        is replacement
    )
    assert updated.revision == tenant.revision + 1


def test_security_profile_is_fail_closed():
    reference = TenantSecurityProfileReference.create(
        "international-brokerage",
        version=2,
    )

    assert reference.fail_closed
    assert reference.require_valid_tenant_context

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Brokerage",
        slug="security-profile",
        security_profile_ref=reference,
    )

    assert (
        tenant.security_profile_ref
        is reference
    )


def test_security_profile_cannot_be_fail_open():
    with pytest.raises(ValueError):
        TenantSecurityProfileReference(
            reference_id=uuid4(),
            profile_key="unsafe",
            fail_closed=False,
        )


def test_region_jurisdiction_reference_is_first_class():
    reference = (
        TenantRegionJurisdictionReference.create(
            region="eu-west-1",
            jurisdiction="DE",
        )
    )

    assert reference.region == "eu-west-1"
    assert reference.jurisdiction == "DE"

    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=(
            OperatingMode.ENTERPRISE_WHITE_LABEL
        ),
        display_name="Germany Enterprise",
        slug="germany-enterprise",
        region_jurisdiction_ref=reference,
    )

    assert (
        tenant.region_jurisdiction_ref
        is reference
    )


def test_region_jurisdiction_requires_scope():
    with pytest.raises(ValueError):
        TenantRegionJurisdictionReference.create()


def test_archived_tenant_is_terminal():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Archived",
        slug="archived-tenant",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    tenant = tenant.transition_to(
        TenantStatus.PENDING_ACTIVATION
    )
    tenant = tenant.transition_to(
        TenantStatus.ACTIVE
    )
    tenant = tenant.transition_to(
        TenantStatus.DEACTIVATING
    )
    tenant = tenant.transition_to(
        TenantStatus.DEACTIVATED
    )
    archived = tenant.transition_to(
        TenantStatus.ARCHIVED
    )

    with pytest.raises(ValueError):
        archived.transition_to(
            TenantStatus.ACTIVE
        )


def test_provisioning_intent_is_idempotency_keyed():
    tenant_id = uuid4()

    intent = TenantProvisioningIntent.create(
        tenant_id=tenant_id,
        idempotency_key="tenant-create-001",
    )

    assert intent.key() == (
        tenant_id,
        "tenant-create-001",
    )
    assert (
        intent.status
        is ProvisioningIntentStatus.REQUESTED
    )


def test_provisioning_intent_state_is_immutable():
    intent = TenantProvisioningIntent.create(
        tenant_id=uuid4(),
        idempotency_key="tenant-create-002",
    )

    applied = intent.with_status(
        ProvisioningIntentStatus.APPLIED
    )

    assert (
        intent.status
        is ProvisioningIntentStatus.REQUESTED
    )
    assert (
        applied.status
        is ProvisioningIntentStatus.APPLIED
    )
    assert (
        applied.revision
        == intent.revision + 1
    )


def test_provisioning_intent_same_status_is_noop():
    intent = TenantProvisioningIntent.create(
        tenant_id=uuid4(),
        idempotency_key="tenant-create-003",
    )

    assert (
        intent.with_status(
            ProvisioningIntentStatus.REQUESTED
        )
        is intent
    )


def test_provisioning_intent_invalid_key_is_rejected():
    with pytest.raises((ValueError, TypeError)):
        TenantProvisioningIntent.create(
            tenant_id=uuid4(),
            idempotency_key="",
        )


def test_registry_registers_and_resolves_active_tenant():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Resolvable",
        slug="resolvable",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    ).transition_to(
        TenantStatus.ACTIVE
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    result = registry.resolve_context(
        tenant.tenant_id
    )

    assert result.resolved
    assert result.status is (
        TenantResolutionStatus.RESOLVED
    )
    assert result.context is not None
    assert (
        result.context.tenant_id
        == tenant.tenant_id
    )
    assert (
        result.context.tenant_revision
        == tenant.revision
    )
    assert result.context.is_valid
    assert result.context.accepts_new_activity


def test_registry_lookup_by_slug_is_canonical():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BUILDER,
        operating_mode=OperatingMode.BUILDER_SAAS,
        display_name="Builder",
        slug="ACME.Builder",
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    assert (
        registry.get_tenant_by_slug(
            " acme.builder "
        )
        == tenant
    )


def test_registry_enforces_unique_slug():
    first = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="First",
        slug="same-slug",
    )

    second = Tenant.create(
        tenant_kind=TenantKind.BUILDER,
        operating_mode=OperatingMode.BUILDER_SAAS,
        display_name="Second",
        slug="SAME-SLUG",
    )

    registry = TenantRegistry()
    registry.register_tenant(first)

    with pytest.raises(ValueError):
        registry.register_tenant(second)


def test_registry_rejects_same_revision_different_state():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Original",
        slug="revision-safe",
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    conflicting = Tenant(
        tenant_id=tenant.tenant_id,
        tenant_kind=tenant.tenant_kind,
        operating_mode=tenant.operating_mode,
        display_name="Different",
        slug=tenant.slug,
        status=tenant.status,
        isolation_profile=tenant.isolation_profile,
        residency_mode=tenant.residency_mode,
        residency_region=tenant.residency_region,
        jurisdiction=tenant.jurisdiction,
        quota_profile=tenant.quota_profile,
        owner_identity_id=tenant.owner_identity_id,
        primary_admin_identity_id=(
            tenant.primary_admin_identity_id
        ),
        configuration_ref=(
            tenant.configuration_ref
        ),
        security_profile_ref=(
            tenant.security_profile_ref
        ),
        region_jurisdiction_ref=(
            tenant.region_jurisdiction_ref
        ),
        revision=tenant.revision,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )

    with pytest.raises(ValueError):
        registry.register_tenant(
            conflicting
        )


def test_registry_rejects_revision_rollback():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Rollback",
        slug="revision-rollback",
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    updated = tenant.assign_administrators(
        owner_identity_id=uuid4(),
        primary_admin_identity_id=uuid4(),
    )

    registry.register_tenant(updated)

    older = Tenant(
        tenant_id=updated.tenant_id,
        tenant_kind=updated.tenant_kind,
        operating_mode=updated.operating_mode,
        display_name=updated.display_name,
        slug=updated.slug,
        status=updated.status,
        isolation_profile=updated.isolation_profile,
        residency_mode=updated.residency_mode,
        residency_region=updated.residency_region,
        jurisdiction=updated.jurisdiction,
        quota_profile=updated.quota_profile,
        owner_identity_id=tenant.owner_identity_id,
        primary_admin_identity_id=(
            tenant.primary_admin_identity_id
        ),
        configuration_ref=(
            tenant.configuration_ref
        ),
        security_profile_ref=(
            tenant.security_profile_ref
        ),
        region_jurisdiction_ref=(
            tenant.region_jurisdiction_ref
        ),
        revision=tenant.revision,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )

    with pytest.raises(ValueError):
        registry.register_tenant(older)


def test_unknown_tenant_fails_closed():
    registry = TenantRegistry()

    result = registry.resolve_context(
        uuid4()
    )

    assert (
        result.status
        is TenantResolutionStatus.NOT_FOUND
    )
    assert not result.resolved
    assert result.context is None


def test_suspended_tenant_does_not_create_valid_context():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Suspended",
        slug="suspended",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    ).transition_to(
        TenantStatus.ACTIVE
    ).transition_to(
        TenantStatus.SUSPENDED
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    result = registry.resolve_context(
        tenant.tenant_id
    )

    assert (
        result.status
        is TenantResolutionStatus.INACTIVE
    )
    assert not result.resolved
    assert result.context is None


def test_restricted_tenant_keeps_context_but_blocks_new_activity():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Restricted",
        slug="restricted",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    ).transition_to(
        TenantStatus.ACTIVE
    ).transition_to(
        TenantStatus.RESTRICTED
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    context = registry.require_context(
        tenant.tenant_id
    )

    assert context.is_valid
    assert not context.accepts_new_activity


def test_archived_tenant_context_is_rejected():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=(
            OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
        ),
        display_name="Archived",
        slug="context-archived",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    ).transition_to(
        TenantStatus.ACTIVE
    ).transition_to(
        TenantStatus.DEACTIVATING
    ).transition_to(
        TenantStatus.DEACTIVATED
    ).transition_to(
        TenantStatus.ARCHIVED
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    result = registry.resolve_context(
        tenant.tenant_id
    )

    assert (
        result.status
        is TenantResolutionStatus.ARCHIVED
    )
    assert not result.resolved


def test_require_context_denies_missing_tenant():
    registry = TenantRegistry()

    with pytest.raises(
        TenantContextDeniedError,
        match="NO_VALID_TENANT_CONTEXT",
    ):
        registry.require_context(
            uuid4()
        )


def test_active_tenant_context_carries_complete_t02_scope():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=(
            OperatingMode.ENTERPRISE_WHITE_LABEL
        ),
        display_name="Global Enterprise",
        slug="global-enterprise",
        residency_mode=(
            DataResidencyMode.REGION_BOUND
        ),
        residency_region="eu-west-1",
        jurisdiction="DE",
        configuration_ref=(
            TenantConfigurationReference.create(
                "enterprise.eu",
                version=4,
            )
        ),
        security_profile_ref=(
            TenantSecurityProfileReference.create(
                "enterprise-secure",
                version=3,
            )
        ),
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(
        TenantStatus.PENDING_ACTIVATION
    ).transition_to(
        TenantStatus.ACTIVE
    )

    registry = TenantRegistry()
    registry.register_tenant(tenant)

    context = registry.require_context(
        tenant.tenant_id
    )

    assert context.tenant_id == tenant.tenant_id
    assert (
        context.tenant_revision
        == tenant.revision
    )
    assert (
        context.operating_mode
        is OperatingMode.ENTERPRISE_WHITE_LABEL
    )
    assert (
        context.configuration_ref.configuration_key
        == "enterprise.eu"
    )
    assert (
        context.security_profile_ref.profile_key
        == "enterprise-secure"
    )
    assert (
        context.region_jurisdiction_ref is not None
    )
    assert (
        context.region_jurisdiction_ref.region
        == "eu-west-1"
    )
    assert (
        context.region_jurisdiction_ref.jurisdiction
        == "DE"
    )
