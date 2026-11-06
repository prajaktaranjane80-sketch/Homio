import type { FastifyRequest } from "fastify";

/** Verified by the existing OIDC trust owner; never constructed from request headers. */
export interface VerifiedExternalPrincipal {
  readonly issuer: string;
  readonly subject: string;
  readonly audiences: readonly string[];
}

/** Minimal, non-PII request context resolved from CORE-001 authoritative owners. */
export interface TrustedRequestContext {
  readonly identityId: string;
  readonly accountId: string;
  readonly tenantId: string;
  readonly tenantRevision: number;
  readonly organizationId: string;
  readonly membershipId: string;
  readonly membershipRevision: number;
}

export interface TokenVerificationPort {
  /** Verify signature, issuer, audience, expiry and allowed signing algorithm. */
  verifyAccessToken(token: string): Promise<VerifiedExternalPrincipal>;
}

export interface SessionValidationPort {
  /** Consult the canonical session/revocation owner; false means revoked or expired. */
  isSessionActive(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly accessToken: string;
  }): Promise<boolean>;
}

export interface TrustedContextResolverPort {
  /** Resolve external identity, account, selected tenant and active membership server-side. */
  resolve(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly requestedTenantId?: string;
  }): Promise<TrustedRequestContext | null>;
}

export interface AuthorizationDecision {
  readonly allowed: boolean;
  readonly reasonCode: string;
}

export interface AuthorizationPolicyPort {
  /** Delegate resource/action decisions to the canonical authorization owner. */
  authorize(input: {
    readonly context: TrustedRequestContext;
    readonly operation: string;
    readonly resourceId?: string;
  }): Promise<AuthorizationDecision>;
}

export interface RateLimitDecision {
  readonly allowed: boolean;
  readonly retryAfterSeconds?: number;
}

export interface RateLimitPort {
  /** The adapter owns policy thresholds and shared/distributed counter storage. */
  consume(input: {
    readonly bucket: "api-ip" | "api-identity-tenant";
    readonly key: string;
  }): Promise<RateLimitDecision>;
}

export interface SecurityAuditEvent {
  readonly eventType: "API_ACCESS_ALLOWED" | "API_ACCESS_DENIED" | "API_RATE_LIMITED";
  readonly requestId: string;
  readonly occurredAt: string;
  readonly reasonCode: string;
  readonly operation?: string;
  readonly actorIdentityId?: string;
  readonly tenantId?: string;
}

export interface SecurityAuditPort {
  /** Persist a structured, PII-minimized audit event through the approved audit owner. */
  record(event: SecurityAuditEvent): Promise<void>;
}

export interface BackendSecurityRuntime {
  readonly tokenVerifier: TokenVerificationPort;
  readonly sessionValidator: SessionValidationPort;
  readonly contextResolver: TrustedContextResolverPort;
  readonly authorization: AuthorizationPolicyPort;
  readonly rateLimiter: RateLimitPort;
  readonly audit: SecurityAuditPort;
}

export interface PublicApiRouteSecurityPolicy {
  readonly public: true;
}

export interface ProtectedApiRouteSecurityPolicy {
  readonly public?: false;
  /** Stable permission operation, for example inventory.read or leads.create. */
  readonly operation: string;
  /** Optional untrusted tenant selector from a route parameter; CORE-001 must validate membership. */
  readonly requestedTenantId?: (request: FastifyRequest) => string | undefined;
  /** Optional resource identifier; authorization owner must verify resource ownership. */
  readonly resourceId?: (request: FastifyRequest) => string | undefined;
}

export type ApiRouteSecurityPolicy =
  | PublicApiRouteSecurityPolicy
  | ProtectedApiRouteSecurityPolicy;
