from __future__ import annotations

from dataclasses import replace
from time import sleep
from types import SimpleNamespace
from uuid import UUID

from AUTONOMY_ENGINE.core.identity_tenant.identity import (
    ExternalIdentityReference,
    Identity,
    IdentityRegistry,
    IdentityType,
)
from AUTONOMY_ENGINE.core.identity_tenant.membership import (
    Membership,
    MembershipDirectory,
    MembershipStatus,
    Organization,
)
from AUTONOMY_ENGINE.core.identity_tenant.tenant import (
    OperatingMode,
    Tenant,
    TenantKind,
    TenantRegistry,
    TenantStatus,
)

from homio_python_runtime.protocol import PythonDomainRuntime


PROBE_ISSUER = "https://issuer.example.test/"
PROBE_AUDIENCE = "homio-api"
PROBE_SUBJECT = "probe-subject"

PROBE_IDENTITY_ID = UUID(
    "11111111-1111-4111-8111-111111111111"
)
PROBE_TENANT_ID = UUID(
    "33333333-3333-4333-8333-333333333333"
)
PROBE_ORGANIZATION_ID = UUID(
    "44444444-4444-4444-8444-444444444444"
)
PROBE_MEMBERSHIP_ID = UUID(
    "55555555-5555-4555-8555-555555555555"
)
PROBE_REFERENCE_ID = UUID(
    "77777777-7777-4777-8777-777777777777"
)


class _OIDC:
    """Test-only verifier port.

    This fixture is deliberately not a production OIDC verifier.
    Production authentication must use the canonical OIDCVerifier owner.
    """

    def verify_access_token(self, token: str):
        if token != "bridge-test-token":
            raise ValueError("invalid token")

        return SimpleNamespace(
            issuer=PROBE_ISSUER,
            subject=PROBE_SUBJECT,
            audiences=(PROBE_AUDIENCE,),
            client_id="homio-web",
            token_id="probe-jti",
            email="must-not-leak@example.test",
        )


def _build_core_owners():
    """Build test registries using the actual canonical CORE-001 models.

    These are in-memory test fixtures only. They are not production
    persistence, session storage, or authorization adapters.
    """

    identity_registry = IdentityRegistry()

    identity = Identity.create(
        identity_type=IdentityType.HUMAN,
        display_name="HOMIO Runtime Probe",
        handle="homio.runtime.probe",
    )
    identity = replace(
        identity,
        identity_id=PROBE_IDENTITY_ID,
    )
    identity_registry.register_identity(identity)

    external_reference = ExternalIdentityReference.create(
        identity_id=PROBE_IDENTITY_ID,
        provider=PROBE_ISSUER,
        subject=PROBE_SUBJECT,
    )
    external_reference = replace(
        external_reference,
        reference_id=PROBE_REFERENCE_ID,
    )
    identity_registry.register_external_reference(
        external_reference
    )

    tenant_registry = TenantRegistry()

    tenant = Tenant.create(
        tenant_kind=TenantKind.BROKERAGE,
        operating_mode=OperatingMode.BROKER_SAAS,
        display_name="HOMIO Runtime Probe Tenant",
        slug="homio-runtime-probe",
    )
    tenant = replace(
        tenant,
        tenant_id=PROBE_TENANT_ID,
    )

    tenant = tenant.assign_administrators(
        owner_identity_id=PROBE_IDENTITY_ID,
        primary_admin_identity_id=PROBE_IDENTITY_ID,
    )
    tenant = tenant.transition_to(
        TenantStatus.PENDING_ACTIVATION
    )
    tenant = tenant.transition_to(
        TenantStatus.ACTIVE
    )

    if tenant.revision != 4:
        raise RuntimeError(
            "CORE-001 tenant fixture revision contract changed."
        )

    tenant_registry.register_tenant(tenant)

    membership_directory = MembershipDirectory()

    organization = Organization.create(
        tenant_id=PROBE_TENANT_ID,
        display_name="HOMIO Runtime Probe Organization",
        slug="homio-runtime-probe",
    )
    organization = replace(
        organization,
        organization_id=PROBE_ORGANIZATION_ID,
    )
    membership_directory.register_organization(organization)

    membership = Membership.create(
        tenant_id=PROBE_TENANT_ID,
        organization_id=PROBE_ORGANIZATION_ID,
        identity_id=PROBE_IDENTITY_ID,
    )
    membership = membership.transition_to(
        MembershipStatus.PENDING
    )
    membership = membership.transition_to(
        MembershipStatus.ACTIVE
    )
    membership = replace(
        membership,
        membership_id=PROBE_MEMBERSHIP_ID,
        revision=7,
    )

    membership_directory.register_membership(membership)

    return (
        identity_registry,
        tenant_registry,
        membership_directory,
    )


def build_runtime() -> PythonDomainRuntime:
    (
        identity_registry,
        tenant_registry,
        membership_directory,
    ) = _build_core_owners()

    return PythonDomainRuntime(
        oidc_verifier=_OIDC(),
        identity_resolver=identity_registry,
        tenant_resolver=tenant_registry,
        membership_resolver=membership_directory,
        trusted_issuer=PROBE_ISSUER,
        trusted_audience=PROBE_AUDIENCE,
    )


class _SlowOIDC(_OIDC):
    def verify_access_token(self, token: str):
        sleep(0.5)
        return super().verify_access_token(token)


def build_slow_runtime() -> PythonDomainRuntime:
    (
        identity_registry,
        tenant_registry,
        membership_directory,
    ) = _build_core_owners()

    return PythonDomainRuntime(
        oidc_verifier=_SlowOIDC(),
        identity_resolver=identity_registry,
        tenant_resolver=tenant_registry,
        membership_resolver=membership_directory,
        trusted_issuer=PROBE_ISSUER,
        trusted_audience=PROBE_AUDIENCE,
    )
