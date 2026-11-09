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

const READ_ONLY_METHODS = new Set([
  "GET",
  "HEAD",
  "OPTIONS"
]);

const METHODS_REQUIRING_BODY_SCHEMA = new Set([
  "POST",
  "PUT",
  "PATCH"
]);

type ApiRouteRegistration = {
  readonly method: unknown;
  readonly url?: unknown;
  readonly schema?: unknown;
  readonly config?: unknown;
};

export class SecurityDependencyUnavailableError extends Error {
  public constructor() {
    super("A required security dependency is unavailable.");
    this.name = "SecurityDependencyUnavailableError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function isVerifiedPrincipal(
  value: unknown
): value is VerifiedExternalPrincipal {
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
    !audiences.every(
      (item: unknown) =>
        typeof item === "string" &&
        item.length > 0 &&
        item.trim() === item
    )
  ) {
    return false;
  }

  try {
    const parsedIssuer = new URL(issuer);

    return (
      parsedIssuer.protocol === "https:" &&
      parsedIssuer.username === "" &&
      parsedIssuer.password === "" &&
      parsedIssuer.search === "" &&
      parsedIssuer.hash === ""
    );
  } catch {
    return false;
  }
}

function isTrustedContext(
  value: unknown
): value is TrustedRequestContext {
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

function hasSameTrustedContext(
  left: TrustedRequestContext,
  right: TrustedRequestContext
): boolean {
  return (
    left.identityId === right.identityId &&
    left.accountId === right.accountId &&
    left.tenantId === right.tenantId &&
    left.organizationId === right.organizationId &&
    left.membershipId === right.membershipId &&
    left.tenantRevision === right.tenantRevision &&
    left.membershipRevision === right.membershipRevision
  );
}

function parseBearerToken(
  request: FastifyRequest
): string | undefined {
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
  if (
    policy === undefined ||
    !isRecord(policy) ||
    policy.public === true ||
    (policy.public !== undefined && policy.public !== false)
  ) {
    return false;
  }

  if (
    typeof policy.operation !== "string" ||
    !OPERATION_PATTERN.test(policy.operation)
  ) {
    return false;
  }

  if (
    policy.requestedTenantId !== undefined &&
    typeof policy.requestedTenantId !== "function"
  ) {
    return false;
  }

  if (
    policy.requestedOrganizationId !== undefined &&
    typeof policy.requestedOrganizationId !== "function"
  ) {
    return false;
  }

  if (
    policy.resourceId !== undefined &&
    typeof policy.resourceId !== "function"
  ) {
    return false;
  }

  return (
    policy.reauthorizeBeforeMutation === undefined ||
    policy.reauthorizeBeforeMutation === true
  );
}

export function isValidApiRouteSecurityPolicy(
  policy: ApiRouteSecurityPolicy | undefined
): boolean {
  if (!isRecord(policy)) {
    return false;
  }

  if (policy.public === true) {
    return Object.keys(policy).length === 1;
  }

  return isProtectedPolicy(
    policy as ApiRouteSecurityPolicy
  );
}

export function isValidApiRouteSecurityContract(
  routeOptions: ApiRouteRegistration
): boolean {
  const config = isRecord(routeOptions.config)
    ? routeOptions.config
    : undefined;

  const policy = config?.homioSecurity as
    | ApiRouteSecurityPolicy
    | undefined;

  if (
    policy === undefined ||
    !isValidApiRouteSecurityPolicy(policy)
  ) {
    return false;
  }

  const methods = Array.isArray(routeOptions.method)
    ? routeOptions.method
    : [routeOptions.method];

  if (
    methods.length === 0 ||
    !methods.every(
      (method) =>
        typeof method === "string" &&
        method.length > 0 &&
        method === method.toUpperCase()
    )
  ) {
    return false;
  }

  const normalizedMethods = methods as string[];

  const isMutation = normalizedMethods.some(
    (method) => !READ_ONLY_METHODS.has(method)
  );

  const schema = isRecord(routeOptions.schema)
    ? routeOptions.schema
    : undefined;

  const hasPathParameters =
    typeof routeOptions.url === "string" &&
    /(?:^|\/):[A-Za-z][A-Za-z0-9_]*/.test(routeOptions.url);

  // Parameterized reads and mutations both require params validation.
  if (
    hasPathParameters &&
    (
      schema === undefined ||
      !isRecord(schema.params)
    )
  ) {
    return false;
  }

  if (isMutation) {
    if (schema === undefined) {
      return false;
    }

    if (
      normalizedMethods.some((method) =>
        METHODS_REQUIRING_BODY_SCHEMA.has(method)
      ) &&
      !isRecord(schema.body)
    ) {
      return false;
    }

    if (policy.public !== true) {
      if (!isProtectedPolicy(policy)) {
        return false;
      }

      if (policy.reauthorizeBeforeMutation !== true) {
        return false;
      }
    }
  } else if (
    isProtectedPolicy(policy) &&
    policy.reauthorizeBeforeMutation === true
  ) {
    return false;
  }

  return true;
}

export function assertBackendSecurityRuntime(
  runtime: BackendSecurityRuntime
): void {
  const value: unknown = runtime;

  if (!isRecord(value)) {
    throw new Error(
      "B2 security runtime must provide all six authoritative adapters."
    );
  }

  const requiredMethods = [
    ["tokenVerifier", "verifyAccessToken"],
    ["sessionValidator", "isSessionActive"],
    ["contextResolver", "resolve"],
    ["authorization", "authorize"],
    ["rateLimiter", "consume"],
    ["audit", "record"]
  ] as const;

  for (const [owner, method] of requiredMethods) {
    const adapter = value[owner];

    if (
      !isRecord(adapter) ||
      typeof adapter[method] !== "function"
    ) {
      throw new Error(
        `B2 security runtime adapter is incomplete: ${owner}.${method}.`
      );
    }
  }
}

function safeReasonCode(
  value: unknown,
  fallback: string
): string {
  return (
    typeof value === "string" &&
    REASON_CODE_PATTERN.test(value)
  )
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
    ...(input.operation === undefined
      ? {}
      : { operation: input.operation }),
    ...(input.context === undefined
      ? {}
      : {
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

function statusMessage(
  statusCode: number
): {
  readonly error: string;
  readonly message: string;
} {
  switch (statusCode) {
    case 400:
      return {
        error: "Bad Request",
        message: "Request security context is invalid."
      };
    case 401:
      return {
        error: "Unauthorized",
        message: "A valid bearer session is required."
      };
    case 403:
      return {
        error: "Forbidden",
        message: "Access is denied."
      };
    case 429:
      return {
        error: "Too Many Requests",
        message: "Request rate limit exceeded."
      };
    case 500:
      return {
        error: "Internal Server Error",
        message: "API security policy is not configured correctly."
      };
    default:
      return {
        error: "Service Unavailable",
        message: "Security services are temporarily unavailable."
      };
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
    input.statusCode === 429
      ? "API_RATE_LIMITED"
      : "API_ACCESS_DENIED";

  const audited = await writeAuditEvent(runtime, request, {
    eventType,
    reasonCode: input.reasonCode,
    ...(input.operation === undefined
      ? {}
      : { operation: input.operation }),
    ...(input.context === undefined
      ? {}
      : { context: input.context })
  });

  const statusCode = audited
    ? input.statusCode
    : 503;

  const publicError = statusMessage(statusCode);

  if (statusCode === 401) {
    reply.header(
      "WWW-Authenticate",
      'Bearer realm="homio-api"'
    );
  }

  if (
    statusCode === 429 &&
    input.retryAfterSeconds !== undefined &&
    Number.isSafeInteger(input.retryAfterSeconds) &&
    input.retryAfterSeconds > 0
  ) {
    reply.header(
      "Retry-After",
      String(input.retryAfterSeconds)
    );
  }

  request.log.warn(
    {
      requestId: request.id,
      statusCode
    },
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
): value is {
  readonly allowed: boolean;
  readonly retryAfterSeconds?: number;
} {
  if (
    !isRecord(value) ||
    typeof value.allowed !== "boolean"
  ) {
    return false;
  }

  return (
    value.retryAfterSeconds === undefined ||
    (
      typeof value.retryAfterSeconds === "number" &&
      Number.isSafeInteger(value.retryAfterSeconds) &&
      value.retryAfterSeconds >= 0
    )
  );
}

async function consumeRateLimit(
  runtime: BackendSecurityRuntime,
  input: {
    readonly bucket: "api-ip" | "api-identity-tenant";
    readonly key: string;
  }
): Promise<{
  readonly allowed: boolean;
  readonly retryAfterSeconds?: number;
}> {
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

async function authorizeProtectedRequest(
  runtime: BackendSecurityRuntime,
  request: FastifyRequest,
  reply: FastifyReply,
  routePolicy: ProtectedApiRouteSecurityPolicy,
  options: {
    readonly consumeIdentityRateLimit: boolean;
    readonly successEventType:
      | "API_ACCESS_ALLOWED"
      | "API_MUTATION_REAUTHORIZED";
    readonly expectedContext?: TrustedRequestContext;
  }
): Promise<boolean> {
  let requestedTenantId: string | undefined;
  let requestedOrganizationId: string | undefined;
  let resourceId: string | undefined;

  try {
    requestedTenantId =
      routePolicy.requestedTenantId?.(request);

    requestedOrganizationId =
      routePolicy.requestedOrganizationId?.(request);

    resourceId = routePolicy.resourceId?.(request);
  } catch {
    await denyRequest(runtime, request, reply, {
      statusCode: 500,
      reasonCode: "ROUTE_SECURITY_SELECTOR_FAILED",
      operation: routePolicy.operation
    });
    return false;
  }

  if (
    requestedTenantId !== undefined &&
    !isUuid(requestedTenantId)
  ) {
    await denyRequest(runtime, request, reply, {
      statusCode: 400,
      reasonCode: "INVALID_TENANT_SELECTION",
      operation: routePolicy.operation
    });
    return false;
  }

  if (
    requestedOrganizationId !== undefined &&
    !isUuid(requestedOrganizationId)
  ) {
    await denyRequest(runtime, request, reply, {
      statusCode: 400,
      reasonCode: "INVALID_ORGANIZATION_SELECTION",
      operation: routePolicy.operation
    });
    return false;
  }

  if (
    resourceId !== undefined &&
    (
      typeof resourceId !== "string" ||
      !RESOURCE_ID_PATTERN.test(resourceId)
    )
  ) {
    await denyRequest(runtime, request, reply, {
      statusCode: 400,
      reasonCode: "INVALID_RESOURCE_REFERENCE",
      operation: routePolicy.operation
    });
    return false;
  }

  const accessToken = parseBearerToken(request);

  if (accessToken === undefined) {
    await denyRequest(runtime, request, reply, {
      statusCode: 401,
      reasonCode: "BEARER_TOKEN_REQUIRED",
      operation: routePolicy.operation
    });
    return false;
  }

  let principal: VerifiedExternalPrincipal;

  try {
    const verified: unknown =
      await runtime.tokenVerifier.verifyAccessToken(accessToken);

    if (!isVerifiedPrincipal(verified)) {
      throw new SecurityDependencyUnavailableError();
    }

    principal = verified;
  } catch (error) {
    const unavailable =
      error instanceof SecurityDependencyUnavailableError;

    await denyRequest(runtime, request, reply, {
      statusCode: unavailable ? 503 : 401,
      reasonCode: unavailable
        ? "TOKEN_VERIFICATION_UNAVAILABLE"
        : "INVALID_BEARER_TOKEN",
      operation: routePolicy.operation
    });
    return false;
  }

  let sessionActive: unknown;

  try {
    sessionActive =
      await runtime.sessionValidator.isSessionActive({
        principal,
        accessToken
      });
  } catch {
    await denyRequest(runtime, request, reply, {
      statusCode: 503,
      reasonCode: "SESSION_VALIDATION_UNAVAILABLE",
      operation: routePolicy.operation
    });
    return false;
  }

  if (sessionActive !== true) {
    await denyRequest(runtime, request, reply, {
      statusCode: sessionActive === false ? 401 : 503,
      reasonCode: sessionActive === false
        ? "SESSION_INACTIVE"
        : "SESSION_VALIDATION_INVALID_RESPONSE",
      operation: routePolicy.operation
    });
    return false;
  }

  let contextValue: unknown;

  try {
    contextValue = await runtime.contextResolver.resolve({
      principal,
      ...(requestedTenantId === undefined
        ? {}
        : { requestedTenantId }),
      ...(requestedOrganizationId === undefined
        ? {}
        : { requestedOrganizationId })
    });
  } catch {
    await denyRequest(runtime, request, reply, {
      statusCode: 503,
      reasonCode: "TRUSTED_CONTEXT_UNAVAILABLE",
      operation: routePolicy.operation
    });
    return false;
  }

  if (contextValue === null) {
    await denyRequest(runtime, request, reply, {
      statusCode: 403,
      reasonCode: "NO_VALID_TENANT_MEMBERSHIP",
      operation: routePolicy.operation
    });
    return false;
  }

  if (!isTrustedContext(contextValue)) {
    await denyRequest(runtime, request, reply, {
      statusCode: 503,
      reasonCode: "TRUSTED_CONTEXT_INVALID",
      operation: routePolicy.operation
    });
    return false;
  }

  const context: TrustedRequestContext = contextValue;

  // A mutation must execute under exactly the context authorized at ingress.
  // Re-resolving to a different identity, account, tenant, organization,
  // membership or revision is a time-of-check/time-of-use boundary change.
  if (
    options.expectedContext !== undefined &&
    !hasSameTrustedContext(context, options.expectedContext)
  ) {
    await denyRequest(runtime, request, reply, {
      statusCode: 403,
      reasonCode: "TRUSTED_CONTEXT_CHANGED_DURING_REQUEST",
      operation: routePolicy.operation,
      context: options.expectedContext
    });
    return false;
  }

  // Never allow an adapter to widen the requested tenant or organization.
  if (
    (
      requestedTenantId !== undefined &&
      context.tenantId !== requestedTenantId
    ) ||
    (
      requestedOrganizationId !== undefined &&
      context.organizationId !== requestedOrganizationId
    )
  ) {
    await denyRequest(runtime, request, reply, {
      statusCode: 503,
      reasonCode: "TRUSTED_CONTEXT_SCOPE_MISMATCH",
      operation: routePolicy.operation,
      context
    });
    return false;
  }

  if (options.consumeIdentityRateLimit) {
    let identityLimit: Awaited<
      ReturnType<typeof consumeRateLimit>
    >;

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
      return false;
    }

    if (!identityLimit.allowed) {
      await denyRequest(runtime, request, reply, {
        statusCode: 429,
        reasonCode: "IDENTITY_TENANT_RATE_LIMITED",
        operation: routePolicy.operation,
        context,
        ...(identityLimit.retryAfterSeconds === undefined
          ? {}
          : {
              retryAfterSeconds:
                identityLimit.retryAfterSeconds
            })
      });
      return false;
    }
  }

  let decisionValue: unknown;

  try {
    decisionValue = await runtime.authorization.authorize({
      context,
      operation: routePolicy.operation,
      ...(resourceId === undefined
        ? {}
        : { resourceId })
    });
  } catch {
    await denyRequest(runtime, request, reply, {
      statusCode: 503,
      reasonCode: "AUTHORIZATION_SERVICE_UNAVAILABLE",
      operation: routePolicy.operation,
      context
    });
    return false;
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
    return false;
  }

  if (decisionValue.allowed !== true) {
    await denyRequest(runtime, request, reply, {
      statusCode: 403,
      reasonCode: safeReasonCode(
        decisionValue.reasonCode,
        "AUTHORIZATION_DENIED"
      ),
      operation: routePolicy.operation,
      context
    });
    return false;
  }

  const audited = await writeAuditEvent(runtime, request, {
    eventType: options.successEventType,
    reasonCode: options.successEventType === "API_ACCESS_ALLOWED"
      ? "AUTHORIZED"
      : "MUTATION_REAUTHORIZED",
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
    return false;
  }

  request.securityContext = context;
  return true;
}

/**
 * IP rate limiting applies to public and protected routes.
 * Protected routes additionally require bearer, session, tenant and permission checks.
 */
export function createApiSecurityHook(
  runtime: BackendSecurityRuntime
) {
  return async function enforceApiSecurity(
    request: FastifyRequest,
    reply: FastifyReply
  ): Promise<void> {
    request.securityContext = null;
    reply.header("Cache-Control", "no-store, private");

    let ipLimit: Awaited<
      ReturnType<typeof consumeRateLimit>
    >;

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
        ...(ipLimit.retryAfterSeconds === undefined
          ? {}
          : {
              retryAfterSeconds: ipLimit.retryAfterSeconds
            })
      });
      return;
    }

    const routePolicy =
      request.routeOptions.config?.homioSecurity;

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

    await authorizeProtectedRequest(
      runtime,
      request,
      reply,
      routePolicy,
      {
        consumeIdentityRateLimit: true,
        successEventType: "API_ACCESS_ALLOWED"
      }
    );
  };
}

/**
 * Re-resolves bearer, session, tenant membership and permission after
 * Fastify validation and immediately before protected mutation handlers.
 */
export function createMutationReauthorizationHook(
  runtime: BackendSecurityRuntime
) {
  return async function reauthorizeMutation(
    request: FastifyRequest,
    reply: FastifyReply
  ): Promise<void> {
    const routePolicy =
      request.routeOptions.config?.homioSecurity;

    if (
      !isProtectedPolicy(routePolicy) ||
      routePolicy.reauthorizeBeforeMutation !== true
    ) {
      return;
    }

    const initialContext = request.securityContext;

    if (initialContext === null) {
      await denyRequest(runtime, request, reply, {
        statusCode: 503,
        reasonCode: "INITIAL_SECURITY_CONTEXT_MISSING",
        operation: routePolicy.operation
      });
      return;
    }

    await authorizeProtectedRequest(
      runtime,
      request,
      reply,
      routePolicy,
      {
        consumeIdentityRateLimit: false,
        successEventType: "API_MUTATION_REAUTHORIZED",
        expectedContext: initialContext
      }
    );
  };
}
