import type {
  FastifyReply,
  FastifyRequest
} from "fastify";

import type {
  ApiRouteSecurityPolicy,
  BackendSecurityRuntime,
  ProtectedApiRouteSecurityPolicy,
  SecurityAuditEvent,
  TrustedRequestContext,
  VerifiedExternalPrincipal
} from "./contracts.js";

const MAX_ACCESS_TOKEN_CHARS = 16_384;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const OPERATION_PATTERN = /^[a-z][a-z0-9_.:-]{0,63}$/;
const RESOURCE_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const REASON_CODE_PATTERN = /^[A-Z][A-Z0-9_]{0,63}$/;

export class SecurityDependencyUnavailableError extends Error {
  public constructor() {
    super("A required security dependency is unavailable.");
    this.name = "SecurityDependencyUnavailableError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function isVerifiedPrincipal(value: unknown): value is VerifiedExternalPrincipal {
  if (!isRecord(value)) {
    return false;
  }

  const issuer = value.issuer;
  const subject = value.subject;
  const audiences = value.audiences;

  if (
    typeof issuer !== "string" ||
    issuer.length > 2048 ||
    issuer.trim() !== issuer ||
    typeof subject !== "string" ||
    subject.length === 0 ||
    subject.length > 255 ||
    subject.trim() !== subject ||
    !Array.isArray(audiences) ||
    audiences.length === 0 ||
    audiences.length > 16 ||
    !audiences.every((item: unknown) => typeof item === "string" && item.length > 0)
  ) {
    return false;
  }

  try {
    const parsedIssuer = new URL(issuer);
    return parsedIssuer.protocol === "https:" &&
      parsedIssuer.username === "" &&
      parsedIssuer.password === "";
  } catch {
    return false;
  }
}

function isTrustedContext(value: unknown): value is TrustedRequestContext {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isUuid(value.identityId) &&
    isUuid(value.accountId) &&
    isUuid(value.tenantId) &&
    isUuid(value.organizationId) &&
    isUuid(value.membershipId) &&
    typeof value.tenantRevision === "number" &&
    Number.isSafeInteger(value.tenantRevision) &&
    value.tenantRevision > 0 &&
    typeof value.membershipRevision === "number" &&
    Number.isSafeInteger(value.membershipRevision) &&
    value.membershipRevision > 0
  );
}

function parseBearerToken(request: FastifyRequest): string | undefined {
  const authorization = request.headers.authorization;

  if (
    typeof authorization !== "string" ||
    authorization.length > MAX_ACCESS_TOKEN_CHARS + 16
  ) {
    return undefined;
  }

  const match = /^Bearer[ \t]+([^\s,]+)$/i.exec(authorization);
  const token = match?.[1];

  if (
    token === undefined ||
    token.length === 0 ||
    token.length > MAX_ACCESS_TOKEN_CHARS
  ) {
    return undefined;
  }

  return token;
}

function isProtectedPolicy(
  policy: ApiRouteSecurityPolicy | undefined
): policy is ProtectedApiRouteSecurityPolicy {
  return (
    policy !== undefined &&
    policy.public !== true &&
    typeof policy.operation === "string" &&
    OPERATION_PATTERN.test(policy.operation)
  );
}

export function isValidApiRouteSecurityPolicy(
  policy: ApiRouteSecurityPolicy | undefined
): boolean {
  return policy?.public === true || isProtectedPolicy(policy);
}

function safeReasonCode(value: unknown, fallback: string): string {
  return typeof value === "string" && REASON_CODE_PATTERN.test(value)
    ? value
    : fallback;
}

async function writeAuditEvent(
  runtime: BackendSecurityRuntime,
  request: FastifyRequest,
  input: {
    readonly eventType: SecurityAuditEvent["eventType"];
    readonly reasonCode: string;
    readonly operation?: string;
    readonly context?: TrustedRequestContext;
  }
): Promise<boolean> {
  const event: SecurityAuditEvent = {
    eventType: input.eventType,
    requestId: request.id,
    occurredAt: new Date().toISOString(),
    reasonCode: input.reasonCode,
    ...(input.operation === undefined ? {} : { operation: input.operation }),
    ...(input.context === undefined ? {} : {
      actorIdentityId: input.context.identityId,
      tenantId: input.context.tenantId
    })
  };

  try {
    await runtime.audit.record(event);
    return true;
  } catch {
    request.log.error(
      { requestId: request.id },
      "Security audit dependency unavailable"
    );
    return false;
  }
}

function statusMessage(statusCode: number): {
  readonly error: string;
  readonly message: string;
} {
  switch (statusCode) {
    case 400:
      return { error: "Bad Request", message: "Request security context is invalid." };
    case 401:
      return { error: "Unauthorized", message: "A valid bearer session is required." };
    case 403:
      return { error: "Forbidden", message: "Access is denied." };
    case 429:
      return { error: "Too Many Requests", message: "Request rate limit exceeded." };
    case 500:
      return { error: "Internal Server Error", message: "API security policy is not configured correctly." };
    default:
      return { error: "Service Unavailable", message: "Security services are temporarily unavailable." };
  }
}

async function denyRequest(
  runtime: BackendSecurityRuntime,
  request: FastifyRequest,
  reply: FastifyReply,
  input: {
    readonly statusCode: 400 | 401 | 403 | 429 | 500 | 503;
    readonly reasonCode: string;
    readonly operation?: string;
    readonly context?: TrustedRequestContext;
    readonly retryAfterSeconds?: number;
  }
): Promise<void> {
  const eventType: SecurityAuditEvent["eventType"] =
    input.statusCode === 429 ? "API_RATE_LIMITED" : "API_ACCESS_DENIED";

  const audited = await writeAuditEvent(runtime, request, {
    eventType,
    reasonCode: input.reasonCode,
    ...(input.operation === undefined ? {} : { operation: input.operation }),
    ...(input.context === undefined ? {} : { context: input.context })
  });

  const statusCode = audited ? input.statusCode : 503;
  const publicError = statusMessage(statusCode);

  if (statusCode === 401) {
    reply.header("WWW-Authenticate", 'Bearer realm="homio-api"');
  }

  if (
    statusCode === 429 &&
    input.retryAfterSeconds !== undefined &&
    Number.isSafeInteger(input.retryAfterSeconds) &&
    input.retryAfterSeconds > 0
  ) {
    reply.header("Retry-After", String(input.retryAfterSeconds));
  }

  request.log.warn(
    { requestId: request.id, statusCode },
    "API security policy denied request"
  );

  reply.code(statusCode).send({
    statusCode,
    error: publicError.error,
    message: publicError.message,
    requestId: request.id
  });
}

function isRateLimitDecision(
  value: unknown
): value is { readonly allowed: boolean; readonly retryAfterSeconds?: number } {
  if (!isRecord(value) || typeof value.allowed !== "boolean") {
    return false;
  }

  return value.retryAfterSeconds === undefined || (
    typeof value.retryAfterSeconds === "number" &&
    Number.isSafeInteger(value.retryAfterSeconds) &&
    value.retryAfterSeconds >= 0
  );
}

async function consumeRateLimit(
  runtime: BackendSecurityRuntime,
  input: {
    readonly bucket: "api-ip" | "api-identity-tenant";
    readonly key: string;
  }
): Promise<{ readonly allowed: boolean; readonly retryAfterSeconds?: number }> {
  let result: unknown;

  try {
    result = await runtime.rateLimiter.consume(input);
  } catch {
    throw new SecurityDependencyUnavailableError();
  }

  if (!isRateLimitDecision(result)) {
    throw new SecurityDependencyUnavailableError();
  }

  return result;
}

/**
 * Applies a fail-closed API security boundary to every route below /api/v1.
 * Routes must explicitly opt into public access or declare a permission operation.
 * Cookie authentication is deliberately unsupported here: only explicit bearer
 * authorization is accepted, so browser cookies cannot silently authenticate API calls.
 */
export function createApiSecurityHook(runtime: BackendSecurityRuntime) {
  return async function enforceApiSecurity(
    request: FastifyRequest,
    reply: FastifyReply
  ): Promise<void> {
    request.securityContext = null;
    reply.header("Cache-Control", "no-store, private");

    let ipLimit: Awaited<ReturnType<typeof consumeRateLimit>>;
    try {
      ipLimit = await consumeRateLimit(runtime, {
        bucket: "api-ip",
        key: request.ip
      });
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "RATE_LIMIT_SERVICE_UNAVAILABLE"
      });
      return;
    }

    if (!ipLimit.allowed) {
      await denyRequest(runtime, request, reply, {
        statusCode: 429,
        reasonCode: "IP_RATE_LIMITED",
        ...(ipLimit.retryAfterSeconds === undefined ? {} : {
          retryAfterSeconds: ipLimit.retryAfterSeconds
        })
      });
      return;
    }

    const routePolicy = request.routeOptions.config.homioSecurity;

    if (routePolicy?.public === true) {
      return;
    }

    if (!isProtectedPolicy(routePolicy)) {
      await denyRequest(runtime, request, reply, {
        statusCode: 500,
        reasonCode: "ROUTE_SECURITY_POLICY_MISSING"
      });
      return;
    }

    let requestedTenantId: string | undefined;
    let resourceId: string | undefined;

    try {
      requestedTenantId = routePolicy.requestedTenantId?.(request);
      resourceId = routePolicy.resourceId?.(request);
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 500,
        reasonCode: "ROUTE_SECURITY_SELECTOR_FAILED",
        operation: routePolicy.operation
      });
      return;
    }

    if (requestedTenantId !== undefined && !isUuid(requestedTenantId)) {
      await denyRequest(runtime, request, reply, {
        statusCode: 400,
        reasonCode: "INVALID_TENANT_SELECTION",
        operation: routePolicy.operation
      });
      return;
    }

    if (
      resourceId !== undefined &&
      (typeof resourceId !== "string" || !RESOURCE_ID_PATTERN.test(resourceId))
    ) {
      await denyRequest(runtime, request, reply, {
        statusCode: 400,
        reasonCode: "INVALID_RESOURCE_REFERENCE",
        operation: routePolicy.operation
      });
      return;
    }

    const accessToken = parseBearerToken(request);
    if (accessToken === undefined) {
      await denyRequest(runtime, request, reply, {
        statusCode: 401,
        reasonCode: "BEARER_TOKEN_REQUIRED",
        operation: routePolicy.operation
      });
      return;
    }

    let principal: VerifiedExternalPrincipal;
    try {
      const verified: unknown = await runtime.tokenVerifier.verifyAccessToken(accessToken);
      if (!isVerifiedPrincipal(verified)) {
        throw new SecurityDependencyUnavailableError();
      }
      principal = verified;
    } catch (error) {
      const unavailable = error instanceof SecurityDependencyUnavailableError;
      await denyRequest(runtime, request, reply, {
        statusCode: unavailable ? 503 : 401,
        reasonCode: unavailable
          ? "TOKEN_VERIFICATION_UNAVAILABLE"
          : "INVALID_BEARER_TOKEN",
        operation: routePolicy.operation
      });
      return;
    }

    let sessionActive: unknown;
    try {
      sessionActive = await runtime.sessionValidator.isSessionActive({
        principal,
        accessToken
      });
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "SESSION_VALIDATION_UNAVAILABLE",
        operation: routePolicy.operation
      });
      return;
    }

    if (sessionActive !== true) {
      await denyRequest(runtime, request, reply, {
        statusCode: sessionActive === false ? 401 : 503,
        reasonCode: sessionActive === false
          ? "SESSION_INACTIVE"
          : "SESSION_VALIDATION_INVALID_RESPONSE",
        operation: routePolicy.operation
      });
      return;
    }

    let contextValue: unknown;
    try {
      contextValue = await runtime.contextResolver.resolve({
        principal,
        ...(requestedTenantId === undefined ? {} : { requestedTenantId })
      });
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "TRUSTED_CONTEXT_UNAVAILABLE",
        operation: routePolicy.operation
      });
      return;
    }

    if (contextValue === null) {
      await denyRequest(runtime, request, reply, {
        statusCode: 403,
        reasonCode: "NO_VALID_TENANT_MEMBERSHIP",
        operation: routePolicy.operation
      });
      return;
    }

    if (!isTrustedContext(contextValue)) {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "TRUSTED_CONTEXT_INVALID",
        operation: routePolicy.operation
      });
      return;
    }

    const context: TrustedRequestContext = contextValue;

    let identityLimit: Awaited<ReturnType<typeof consumeRateLimit>>;
    try {
      identityLimit = await consumeRateLimit(runtime, {
        bucket: "api-identity-tenant",
        key: `${context.tenantId}:${context.identityId}`
      });
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "RATE_LIMIT_SERVICE_UNAVAILABLE",
        operation: routePolicy.operation,
        context
      });
      return;
    }

    if (!identityLimit.allowed) {
      await denyRequest(runtime, request, reply, {
        statusCode: 429,
        reasonCode: "IDENTITY_TENANT_RATE_LIMITED",
        operation: routePolicy.operation,
        context,
        ...(identityLimit.retryAfterSeconds === undefined ? {} : {
          retryAfterSeconds: identityLimit.retryAfterSeconds
        })
      });
      return;
    }

    let decisionValue: unknown;
    try {
      decisionValue = await runtime.authorization.authorize({
        context,
        operation: routePolicy.operation,
        ...(resourceId === undefined ? {} : { resourceId })
      });
    } catch {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "AUTHORIZATION_SERVICE_UNAVAILABLE",
        operation: routePolicy.operation,
        context
      });
      return;
    }

    if (
      !isRecord(decisionValue) ||
      typeof decisionValue.allowed !== "boolean" ||
      typeof decisionValue.reasonCode !== "string"
    ) {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "AUTHORIZATION_INVALID_RESPONSE",
        operation: routePolicy.operation,
        context
      });
      return;
    }

    if (decisionValue.allowed !== true) {
      await denyRequest(runtime, request, reply, {
        statusCode: 403,
        reasonCode: safeReasonCode(decisionValue.reasonCode, "AUTHORIZATION_DENIED"),
        operation: routePolicy.operation,
        context
      });
      return;
    }

    const audited = await writeAuditEvent(runtime, request, {
      eventType: "API_ACCESS_ALLOWED",
      reasonCode: "AUTHORIZED",
      operation: routePolicy.operation,
      context
    });

    if (!audited) {
      reply.code(503).send({
        statusCode: 503,
        error: "Service Unavailable",
        message: "Security services are temporarily unavailable.",
        requestId: request.id
      });
      return;
    }

    request.securityContext = context;
  };
}
