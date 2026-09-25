import json
from uuid import uuid4

import pytest

from AUTONOMY_ENGINE.core.identity_tenant.tenant import (
    DataResidencyMode,
    IsolationProfile,
    OperatingMode,
    ProvisioningIntentStatus,
    Tenant,
    TenantKind,
    TenantProvisioningIntent,
    TenantStatus,
)


def test_tenant_creation_is_typed_and_authoritative():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="HOMIO Brokerage",
        slug="homio-brokerage",
    )

    assert tenant.tenant_id
    assert tenant.tenant_kind is TenantKind.BROKERAGE
    assert tenant.operating_mode is OperatingMode.OWNED_INTERNATIONAL_BROKERAGE
    assert tenant.status is TenantStatus.PROVISIONING
    assert tenant.revision == 1


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
        operating_mode=OperatingMode.PLATFORM_API_PARTNER,
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
    ["x", "", "bad slug", "bad/name", "_bad", "-bad"],
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
        operating_mode=OperatingMode.ENTERPRISE_WHITE_LABEL,
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
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="Brokerage",
        slug="brokerage",
    ).transition_to(TenantStatus.PENDING_ACTIVATION)

    with pytest.raises(ValueError):
        tenant.transition_to(TenantStatus.ACTIVE)


def test_tenant_becomes_active_only_with_administrators():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="Brokerage",
        slug="brokerage-active",
    )

    owner = uuid4()

    tenant = tenant.assign_administrators(
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    ).transition_to(TenantStatus.PENDING_ACTIVATION)

    active = tenant.transition_to(TenantStatus.ACTIVE)

    assert active.is_active
    assert active.accepts_new_activity
    assert active.revision == tenant.revision + 1


def test_valid_lifecycle_transitions():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="Brokerage",
        slug="lifecycle",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    tenant = tenant.transition_to(TenantStatus.PENDING_ACTIVATION)
    tenant = tenant.transition_to(TenantStatus.ACTIVE)
    tenant = tenant.transition_to(TenantStatus.SUSPENDED)
    tenant = tenant.transition_to(TenantStatus.ACTIVE)
    tenant = tenant.transition_to(TenantStatus.DEACTIVATING)
    tenant = tenant.transition_to(TenantStatus.DEACTIVATED)
    tenant = tenant.transition_to(TenantStatus.ARCHIVED)

    assert tenant.status is TenantStatus.ARCHIVED


@pytest.mark.parametrize(
    "start,end",
    [
        (TenantStatus.ARCHIVED, TenantStatus.ACTIVE),
        (TenantStatus.DEACTIVATED, TenantStatus.ACTIVE),
        (TenantStatus.DEACTIVATING, TenantStatus.ACTIVE),
        (TenantStatus.PROVISIONING, TenantStatus.ACTIVE),
        (TenantStatus.ACTIVE, TenantStatus.ARCHIVED),
    ],
)
def test_invalid_lifecycle_transitions_fail_closed(start, end):
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="Brokerage",
        slug=f"invalid-{start.name.lower()}-{end.name.lower()}",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    while tenant.status is not start:
        next_states = {
            TenantStatus.PROVISIONING: TenantStatus.PENDING_ACTIVATION,
            TenantStatus.PENDING_ACTIVATION: TenantStatus.ACTIVE,
            TenantStatus.ACTIVE: TenantStatus.DEACTIVATING,
            TenantStatus.DEACTIVATING: TenantStatus.DEACTIVATED,
            TenantStatus.DEACTIVATED: TenantStatus.ARCHIVED,
        }

        if tenant.status not in next_states:
            break

        tenant = tenant.transition_to(next_states[tenant.status])

    if tenant.status is start:
        with pytest.raises(ValueError):
            tenant.transition_to(end)


def test_restricted_residency_requires_scope():
    with pytest.raises(ValueError):
        Tenant.create(
            tenant_kind=TenantKind.ENTERPRISE,
            operating_mode=OperatingMode.ENTERPRISE_WHITE_LABEL,
            display_name="Enterprise",
            slug="enterprise-residency",
            residency_mode=DataResidencyMode.REGION_BOUND,
        )


def test_region_bound_residency_is_supported():
    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=OperatingMode.ENTERPRISE_WHITE_LABEL,
        display_name="Enterprise",
        slug="region-bound",
        residency_mode=DataResidencyMode.REGION_BOUND,
        residency_region="eu-west-1",
    )

    assert tenant.residency_mode is DataResidencyMode.REGION_BOUND
    assert tenant.residency_region == "eu-west-1"


def test_isolation_profile_is_explicit():
    tenant = Tenant.create(
        tenant_kind=TenantKind.ENTERPRISE,
        operating_mode=OperatingMode.ENTERPRISE_WHITE_LABEL,
        display_name="Enterprise",
        slug="dedicated",
        isolation_profile=IsolationProfile.TENANT_DEDICATED,
    )

    assert tenant.isolation_profile is IsolationProfile.TENANT_DEDICATED


def test_owner_and_admin_assignment_is_immutable():
    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
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


def test_provisioning_intent_is_idempotency_keyed():
    tenant_id = uuid4()

    intent = TenantProvisioningIntent.create(
        tenant_id=tenant_id,
        idempotency_key="tenant-create-001",
    )

    assert intent.key() == (tenant_id, "tenant-create-001")
    assert intent.status is ProvisioningIntentStatus.REQUESTED


def test_provisioning_intent_state_is_immutable():
    intent = TenantProvisioningIntent.create(
        tenant_id=uuid4(),
        idempotency_key="tenant-create-002",
    )

    applied = intent.with_status(
        ProvisioningIntentStatus.APPLIED
    )

    assert intent.status is ProvisioningIntentStatus.REQUESTED
    assert applied.status is ProvisioningIntentStatus.APPLIED
    assert applied.revision == intent.revision + 1


def test_provisioning_intent_invalid_key_is_rejected():
    with pytest.raises((ValueError, TypeError)):
        TenantProvisioningIntent.create(
            tenant_id=uuid4(),
            idempotency_key="",
        )


def test_archived_tenant_is_terminal():
    owner = uuid4()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        display_name="Archived",
        slug="archived-tenant",
        owner_identity_id=owner,
        primary_admin_identity_id=owner,
    )

    tenant = tenant.transition_to(TenantStatus.PENDING_ACTIVATION)
    tenant = tenant.transition_to(TenantStatus.ACTIVE)
    tenant = tenant.transition_to(TenantStatus.DEACTIVATING)
    tenant = tenant.transition_to(TenantStatus.DEACTIVATED)
    archived = tenant.transition_to(TenantStatus.ARCHIVED)

    with pytest.raises(ValueError):
        archived.transition_to(TenantStatus.ACTIVE)
