# HOMIO / REOS — OIDC access-token verification

This package owns server-side verification of OAuth 2.0 JWT access tokens.
It does not own canonical identities, accounts, sessions, tenant membership,
authorization decisions, persistence or audit storage.

## Required deployment configuration

- `HOMIO_OIDC_ISSUER`: exact trusted HTTPS issuer.
- `HOMIO_OIDC_AUDIENCE`: API/resource-server audience.
- `HOMIO_OIDC_JWKS_URL`: trusted issuer signing-key endpoint.

All values must be configured outside source control. Never commit provider
secrets, private keys, access tokens or refresh tokens.

## Access-token contract

The verifier implements the JWT access-token profile in RFC 9068.

It requires:

- `typ` equal to `at+jwt` or `application/at+jwt`.
- An asymmetric signature using an allowed signing algorithm.
- A trusted signing key from the configured issuer JWKS.
- Exact issuer matching.
- The configured API audience.
- Valid `exp`, `iat` and optional `nbf` time constraints.
- Required `sub`, `client_id` and `jti` claims.

Ordinary OpenID Connect ID tokens are not accepted as API bearer tokens.
A valid signature alone does not establish that a JWT is an access token.

## Canonical identity resolution

The verified external identity key is `(issuer, subject)`.

The API must resolve that pair against the existing CORE-001 external identity
reference. It must not auto-link an account by email, display name or other
mutable profile attribute.

Unknown, revoked or inactive external identity references fail closed.

## Session and revocation

JWT signature and expiry validation do not, by themselves, provide immediate
revocation. The API must use the approved session/revocation owner or a
supported OAuth token-introspection service. A missing or unavailable
revocation dependency must fail closed.

The API must also check current CORE-001 account, tenant and membership state
before protected domain operations.

## Authorization boundary

CORE-001 T03 stores roles, permissions, entitlements, scopes and relationship
requirements. Its contract explicitly excludes the authorization decision
engine. The API must delegate each operation/resource decision to the
approved authorization owner; possession of a role or membership record alone
does not authorize an operation.

## Runtime integration

The public Fastify API must use the existing private, versioned runtime
boundary to invoke Python-owned security capabilities. Do not create a second
public API, duplicate identity registry, duplicate tenant registry or
independent domain authorization engine.

Until the real token, session, CORE-001 context, authorization, rate-limit and
audit adapters are composed and verified, protected customer routes must
remain disabled.
