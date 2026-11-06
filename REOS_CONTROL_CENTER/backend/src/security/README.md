# B2 public API security boundary

`api-security.ts` is the single Fastify ingress guard for `/api/v1`. All API
route plugins are mounted beneath it by `src/app.ts`.

## Route contract

Every v1 route must declare `config.homioSecurity`:

- `{ public: true }` is the only way to declare a public route.
- Protected routes must declare a stable `operation` and may provide trusted
  server callbacks for a requested tenant selector and resource identifier.
- Tenant and resource selectors are untrusted input. The context resolver and
  authorization owner must verify membership and ownership before access.
- Use Fastify JSON schemas for route params, query strings, headers and bodies.

## Required production adapters

`BackendSecurityRuntime` is mandatory whenever API route plugins are mounted.
It requires adapters to the existing owners for token verification, session
revocation, CORE-001 identity/tenant/membership resolution, resource/action
authorization, shared rate limiting and security audit persistence.

The token adapter must use the OIDC **access-token** verifier with the API
issuer/audience configuration. Invalid tokens should be rejected; signing-key
or verifier-service outages must be mapped to
`SecurityDependencyUnavailableError`. Do not accept the frontend encrypted
`homio_session` cookie as a backend credential: it is not a provider access
token and does not establish canonical tenant membership.

The session adapter must check durable session status and the canonical
account authentication epoch/revocation state. The context resolver must
resolve `(issuer, subject)` to an existing CORE-001 identity/account and an
active tenant membership; it must not auto-link by email. The authorization
adapter must evaluate resource/action permission using the canonical policy
owner. CORE-001 T03 is a grant/prerequisite model, not itself a decision engine.

Rate-limit adapters own approved thresholds and shared/distributed storage.
The audit adapter must persist the minimized event before a protected handler
runs. Every unavailable security dependency fails closed.

## CSRF and privacy boundary

The public API accepts explicit `Authorization: Bearer` credentials only; it
does not authenticate from browser cookies. This prevents ambient cookie
credentials from authorizing cross-site requests. Cookie-based frontend
sessions remain a separate frontend boundary and must not be forwarded as a
backend identity assertion.

The security hook never logs or audits tokens, provider subjects, email,
request bodies or client IP addresses. Audit records contain request ID,
operation, canonical actor/tenant IDs and a stable reason code. API responses
are marked `Cache-Control: no-store, private`.

This boundary is not a complete production integration by itself. Until the
required adapters are implemented, wired and verified against real CORE-001
and the approved identity/session/policy owners, no customer-facing v1 route
may be enabled.
