from __future__ import annotations

from time import sleep
from types import SimpleNamespace
from uuid import UUID

from homio_python_runtime.protocol import PythonDomainRuntime


class _OIDC:
    def verify_access_token(self, token: str):
        if token != "bridge-test-token":
            raise ValueError("invalid token")

        return SimpleNamespace(
            issuer="https://issuer.example.test/",
            subject="probe-subject",
            audiences=("homio-api",),
            client_id="homio-web",
            token_id="probe-jti",
            email="must-not-leak@example.test",
        )


class _Identity:
    def resolve_external(self, provider: str, subject: str):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            identity_id=UUID("11111111-1111-4111-8111-111111111111"),
            reference_id=UUID("77777777-7777-4777-8777-777777777777"),
            provider=provider,
            subject=subject,
            reason="canonical identity resolved",
        )


class _Tenant:
    def resolve_context(self, tenant_id: UUID):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            tenant_id=tenant_id,
            tenant_revision=4,
            reason="tenant context resolved",
            context=SimpleNamespace(
                tenant_status=SimpleNamespace(value="ACTIVE"),
                tenant_kind=SimpleNamespace(value="BROKERAGE"),
                operating_mode=SimpleNamespace(value="BROKER_SAAS"),
            ),
        )


class _Membership:
    def resolve_membership(
        self,
        *,
        tenant_id: UUID,
        organization_id: UUID,
        identity_id: UUID,
    ):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            membership_id=UUID("55555555-5555-4555-8555-555555555555"),
            tenant_id=tenant_id,
            organization_id=organization_id,
            identity_id=identity_id,
            membership_revision=7,
            reason="membership resolved",
            membership=object(),
        )


def build_runtime() -> PythonDomainRuntime:
    return PythonDomainRuntime(
        oidc_verifier=_OIDC(),
        identity_resolver=_Identity(),
        tenant_resolver=_Tenant(),
        membership_resolver=_Membership(),
        trusted_issuer="https://issuer.example.test/",
        trusted_audience="homio-api",
    )


class _SlowOIDC(_OIDC):
    def verify_access_token(self, token: str):
        sleep(0.5)
        return super().verify_access_token(token)


def build_slow_runtime() -> PythonDomainRuntime:
    return PythonDomainRuntime(
        oidc_verifier=_SlowOIDC(),
        identity_resolver=_Identity(),
        tenant_resolver=_Tenant(),
        membership_resolver=_Membership(),
        trusted_issuer="https://issuer.example.test/",
        trusted_audience="homio-api",
    )
