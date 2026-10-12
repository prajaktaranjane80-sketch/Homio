# HOMIO / REOS ? OIDC token verification

This is a server-side JWT verification boundary. It does not own canonical
identity records or tenant membership.

Required deployment environment variables:
- HOMIO_OIDC_ISSUER: the exact trusted HTTPS issuer.
- HOMIO_OIDC_AUDIENCE: the API/resource audience.
- HOMIO_OIDC_JWKS_URL: the trusted HTTPS issuer signing-key endpoint.

The verifier fails closed if configuration is absent or unsafe. Use the
identity provider's official JWKS endpoint. Never put credentials or secrets
in repository source files.

Usage:
    from AUTONOMY_ENGINE.security.authentication import OIDCSettings, OIDCVerifier
    settings = OIDCSettings.from_env()
    verifier = OIDCVerifier(settings)
    principal = verifier.verify_access_token(access_token)

Authorization, tenant membership, roles and scopes must still be checked by
the API before allowing an operation. Use (issuer, subject) as the stable
external identity key; never automatically link accounts using email alone.

This package only verifies tokens. It is not a complete login system and does
not implement browser redirects, authorization-code/PKCE callbacks, signup,
refresh, logout, persistent application sessions or API routes.