import type { FastifyRequest } from "fastify";

export interface VerifiedExternalPrincipal {
  readonly issuer: string;
  readonly subject: string;
  readonly audiences: readonly string[];
  readonly clientId: string;
  readonly tokenId: string;
  /** Verified JWT iat in Unix seconds; required for durable session creation. */
  readonly issuedAtEpochSeconds?: number;
  /** Verified JWT exp in Unix seconds; required for durable session creation. */
  readonly expiresAtEpochSeconds?: number;
}

export interface TrustedRequestContext {
  readonly identityId: string;
  readonly accountId: string;
  /** Current CORE-001 IdentityAccount.authentication_epoch. */
  readonly authenticationEpoch: number;
  readonly tenantId: string;
  readonly tenantRevision: number;
  readonly organizationId: string;
  readonly membershipId: string;
  readonly membershipRevision: number;
}

export type TokenVerificationFailureKind =
  | "invalid"
  | "unavailable";

export class TokenVerificationError extends Error {
  public readonly kind: TokenVerificationFailureKind;

  public constructor(kind: TokenVerificationFailureKind) {
    super(
      kind === "invalid"
        ? "The access token is invalid."
        : "The access-token verification service is unavailable."
    );

    this.name = "TokenVerificationError";
    this.kind = kind;
  }
}

export interface TokenVerificationPort {
  verifyAccessToken(token: string): Promise<VerifiedExternalPrincipal>;
}

export interface SessionValidationPort {
  isSessionActive(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly context: TrustedRequestContext;
  }): Promise<boolean>;
}

export interface TrustedContextResolverPort {
  resolve(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly requestedTenantId?: string;
    readonly requestedOrganizationId?: string;
  }): Promise<TrustedRequestContext | null>;
}

export interface AuthorizationDecision {
  readonly allowed: boolean;
  readonly reasonCode: string;
}

export interface AuthorizationPolicyPort {
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
  consume(input: {
    readonly bucket: "api-ip" | "api-identity-tenant";
    readonly key: string;
  }): Promise<RateLimitDecision>;
}

export interface SecurityAuditEvent {
  readonly eventType:
    | "API_ACCESS_ALLOWED"
    | "API_ACCESS_DENIED"
    | "API_RATE_LIMITED"
    | "API_MUTATION_REAUTHORIZED";
  readonly requestId: string;
  readonly occurredAt: string;
  readonly reasonCode: string;
  readonly operation?: string;
  readonly actorIdentityId?: string;
  readonly tenantId?: string;
}

export interface SecurityAuditPort {
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
  readonly operation: string;
  readonly requestedTenantId?: (request: FastifyRequest) => string | undefined;
  readonly requestedOrganizationId?: (request: FastifyRequest) => string | undefined;
  readonly resourceId?: (request: FastifyRequest) => string | undefined;
  readonly reauthorizeBeforeMutation?: true;
}

export type ApiRouteSecurityPolicy =
  | PublicApiRouteSecurityPolicy
  | ProtectedApiRouteSecurityPolicy;
