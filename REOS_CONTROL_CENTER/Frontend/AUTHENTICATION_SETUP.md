# HOMIO sign-in and account setup

The frontend now contains a server-side OpenID Connect authorization-code flow with PKCE, an encrypted `HttpOnly` application-session cookie, a callback handler, a session-status endpoint, local sign-out, and a protected `/my` account page. It does not collect provider passwords in HOMIO.

## Required deployment variables

Set these in the hosting platform's encrypted environment settings; never commit real values to Git:

- `HOMIO_APP_URL`: the canonical origin only, for example `https://app.example.com` (no path, query or trailing route). Local HTTP is permitted only for localhost during development.
- `HOMIO_OIDC_ISSUER`: the exact HTTPS issuer URI published by the identity provider.
- `HOMIO_OIDC_CLIENT_ID`: the client ID registered with the provider.
- `HOMIO_SESSION_SECRET`: a random secret of at least 32 UTF-8 bytes. Use a different value per environment and keep it private.
- `HOMIO_OIDC_CLIENT_SECRET`: optional only when the provider application is registered as a public PKCE client. For a server-side confidential client, configure this secret in the hosting platform.

Register this exact redirect URI with the identity provider:

`{HOMIO_APP_URL}/api/auth/callback`

Enable Authorization Code Flow and PKCE using `S256`; allow scopes `openid profile email`. The implementation discovers authorization/token/JWKS endpoints from `/.well-known/openid-configuration` beneath the configured issuer, requires an exact issuer match and HTTPS endpoints, validates the ID-token signature/issuer/audience/time/nonce, and fails closed when configuration or the provider is unavailable.

The signup button sends `screen_hint=signup`. That is a provider-specific hint (supported by some providers, including Auth0), not a core OpenID Connect feature. Verify that the selected provider supports signup on its authorization endpoint before enabling this user journey in production.

## Endpoints

- `GET /api/auth/login`: starts login with state, nonce and PKCE.
- `GET /api/auth/callback`: validates the callback and establishes a protected app session.
- `GET /api/auth/session`: returns only a minimal authenticated/anonymous status, with `Cache-Control: no-store`.
- `POST /api/auth/logout`: checks same-origin `Origin` and clears the HOMIO app-session cookie.
- `/login`, `/signup`: account entry pages.
- `/my`: server-protected account page.

Sign-out clears the HOMIO application session; it does not promise to terminate the user's separate SSO session at the identity provider. The current app session is encrypted and expires after eight hours. A durable server-side session store is still required for immediate server-side revocation, and provider tokens are deliberately not stored in the browser session.

## Production identity and tenant gate

The OIDC callback validates an external provider identity and creates a short-lived encrypted frontend session. This alone does not resolve a canonical HOMIO account or authorize a tenant. Before production tenant-scoped features are enabled, the trusted backend must resolve the exact (issuer, sub) external identity to a durable REOS account, verify account status, and authorize active tenant membership and tenant isolation for every protected operation. Do not auto-link accounts by email. Until that adapter and its negative tests are connected, do not infer account provisioning, tenant membership, persistence, or cross-tenant access from the frontend session.
## Explicit remaining data boundary

Authentication establishes a trusted identity session; it does not create database-backed saved properties, saved searches, comparisons, visits, messages or transaction records. Those features must be connected to the canonical REOS persistence/API and tenant authorization boundaries before HOMIO may represent the data as synced or authoritative. The UI continues to disclose this limitation rather than manufacture data.