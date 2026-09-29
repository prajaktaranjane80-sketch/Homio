from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from .membership import Membership, MembershipStatus
from .tenant import (
    IsolationProfile,
    OperatingMode,
    Tenant,
    TenantContext,
    TenantKind,
    TenantStatus,
)
from .tenant_isolation import (
    TenantIsolationBoundary,
    TenantIsolationDecision,
    TenantIsolationReason,
    TenantIsolationDeniedError,
    TenantIsolationResource,
)


def _tenant(
    *,
    tenant_id=None,
    status=TenantStatus.ACTIVE,
):
    tenant_id = tenant_id or uuid4()

    tenant = Tenant.create(
        slug=f"tenant-{str(tenant_id)[:8]}",
        name="Test Tenant",
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.OWNED_INTERNATIONAL_BROKERAGE,
        isolation_profile=IsolationProfile.STRICT,
    )

    if tenant.tenant_id != tenant_id:
        tenant = tenant.__class__(
            **{
                **{
                    field.name: getattr(tenant, field.name)
                    for field in tenant.__dataclass_fields__.values()
                },
                "tenant_id": tenant_id,
            }
        )

    if tenant.status is not status:
        tenant = tenant.with_status(status)

    return tenant


def _context(tenant):
    return TenantContext(
        tenant_id=tenant.tenant_id,
        tenant_revision=tenant.revision,
        tenant_status=tenant.status,
        tenant_kind=tenant.tenant_kind,
        operating_mode=tenant.operating_mode,
        configuration_ref=tenant.configuration_ref,
        security_profile_ref=tenant.security_profile_ref,
        region_jurisdiction_ref=tenant.region_jurisdiction_ref,
    )


def _membership(
    tenant_id,
    organization_id,
    *,
    identity_id=None,
):
    return Membership.create(
        tenant_id=tenant_id,
        organization_id=organization_id,
        identity_id=identity_id or uuid4(),
    ).transition(MembershipStatus.PENDING).transition(
        MembershipStatus.ACTIVE
    )


def test_valid_tenant_context_allows_boundary():
    tenant = _tenant()
    context = _context(tenant)

    result = TenantIsolationBoundary().verify(
        tenant_context=context,
        requested_tenant_id=tenant.tenant_id,
    )

    assert result.decision is TenantIsolationDecision.ALLOW
    assert result.reason is TenantIsolationReason.VALID


def test_missing_tenant_context_denies():
    result = TenantIsolationBoundary().verify(
        tenant_context=None,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert result.reason is TenantIsolationReason.NO_TENANT_CONTEXT


def test_mismatched_tenant_denies():
    tenant_a = _tenant()
    tenant_b = _tenant()
    context = _context(tenant_a)

    result = TenantIsolationBoundary().verify(
        tenant_context=context,
        requested_tenant_id=tenant_b.tenant_id,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert result.reason is TenantIsolationReason.TENANT_MISMATCH


def test_cross_tenant_resource_denies():
    tenant_a = _tenant()
    tenant_b = _tenant()

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant_a),
        resource=TenantIsolationResource(
            resource_id=uuid4(),
            tenant_id=tenant_b.tenant_id,
        ),
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert (
        result.reason
        is TenantIsolationReason.RESOURCE_TENANT_MISMATCH
    )


def test_cross_tenant_membership_denies():
    tenant_a = _tenant()
    tenant_b = _tenant()

    membership = _membership(
        tenant_b.tenant_id,
        uuid4(),
    )

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant_a),
        membership=membership,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert (
        result.reason
        is TenantIsolationReason.MEMBERSHIP_TENANT_MISMATCH
    )


def test_wrong_organization_denies():
    tenant = _tenant()
    organization_a = uuid4()
    organization_b = uuid4()

    membership = _membership(
        tenant.tenant_id,
        organization_a,
    )

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
        membership=membership,
        requested_organization_id=organization_b,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert (
        result.reason
        is TenantIsolationReason.MEMBERSHIP_ORGANIZATION_MISMATCH
    )


def test_stale_membership_revision_denies():
    tenant = _tenant()
    membership = _membership(
        tenant.tenant_id,
        uuid4(),
    )

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
        membership=membership,
        expected_membership_revision=membership.revision + 1,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert (
        result.reason
        is TenantIsolationReason.MEMBERSHIP_REVISION_STALE
    )


def test_revoked_membership_denies():
    tenant = _tenant()
    membership = _membership(
        tenant.tenant_id,
        uuid4(),
    ).transition(MembershipStatus.REVOKED)

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
        membership=membership,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert result.reason is TenantIsolationReason.MEMBERSHIP_REVOKED


def test_expired_membership_denies():
    tenant = _tenant()

    now = datetime.now(timezone.utc)

    membership = Membership.create(
        tenant_id=tenant.tenant_id,
        organization_id=uuid4(),
        identity_id=uuid4(),
        valid_from=now - timedelta(hours=2),
        valid_until=now - timedelta(hours=1),
    ).transition(MembershipStatus.PENDING).transition(
        MembershipStatus.ACTIVE
    )

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
        membership=membership,
        at=now,
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert result.reason is TenantIsolationReason.MEMBERSHIP_INVALID


def test_inactive_tenant_context_denies():
    tenant = _tenant(status=TenantStatus.SUSPENDED)

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
    )

    assert result.decision is TenantIsolationDecision.DENY
    assert (
        result.reason
        is TenantIsolationReason.INVALID_TENANT_CONTEXT
    )


def test_archived_tenant_context_denies():
    tenant = _tenant(status=TenantStatus.ARCHIVED)

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
    )

    assert result.decision is TenantIsolationDecision.DENY


def test_require_valid_fails_closed():
    with pytest.raises(TenantIsolationDeniedError):
        TenantIsolationBoundary().require_valid(
            tenant_context=None,
        )


def test_valid_membership_and_resource_allow():
    tenant = _tenant()
    organization_id = uuid4()

    membership = _membership(
        tenant.tenant_id,
        organization_id,
    )

    result = TenantIsolationBoundary().verify(
        tenant_context=_context(tenant),
        requested_tenant_id=tenant.tenant_id,
        requested_organization_id=organization_id,
        resource=TenantIsolationResource(
            resource_id=uuid4(),
            tenant_id=tenant.tenant_id,
        ),
        membership=membership,
        expected_membership_revision=membership.revision,
    )

    assert result.allowed
    assert result.tenant_id == tenant.tenant_id
    assert result.organization_id == organization_id
    assert result.membership_id == membership.membership_id
