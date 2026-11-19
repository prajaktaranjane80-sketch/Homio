export const PYTHON_RUNTIME_PROTOCOL_NAME = "homio.python-domain-runtime" as const;
export const PYTHON_RUNTIME_PROTOCOL_VERSION = 1 as const;
export const PYTHON_RUNTIME_SERVICE_ID = "homio-backend" as const;
export const PYTHON_RUNTIME_AUDIENCE = "homio-python-domain-runtime" as const;

export const PYTHON_RUNTIME_OPERATIONS = [
  "oidc.verify_access_token",
  "core001.identity.resolve",
  "core001.tenant.resolve_context",
  "core001.membership.resolve"
] as const;

export type JsonValue =
  | null
  | boolean
  | number
  | string
  | readonly JsonValue[]
  | { readonly [key: string]: JsonValue };

export interface RuntimeCorrelationContext {
  readonly correlationId: string;
}

export interface TrustedRuntimeContext extends RuntimeCorrelationContext {
  readonly actor: {
    readonly identityId: string;
    readonly accountId: string;
  };
  readonly tenant: {
    readonly tenantId: string;
    readonly tenantRevision: number;
    readonly organizationId: string;
    readonly membershipId: string;
    readonly membershipRevision: number;
  };
}

interface InvocationOptions {
  readonly signal?: AbortSignal;
  readonly timeoutMs?: number;
}

export type PythonRuntimeInvocation = InvocationOptions & (
  | {
      readonly operation: "oidc.verify_access_token";
      readonly context: RuntimeCorrelationContext;
      readonly payload: { readonly accessToken: string };
    }
  | {
      readonly operation: "core001.identity.resolve";
      readonly context: RuntimeCorrelationContext | TrustedRuntimeContext;
      readonly payload: { readonly provider: string; readonly subject: string };
    }
  | {
      readonly operation: "core001.tenant.resolve_context";
      readonly context: TrustedRuntimeContext;
      readonly payload: { readonly tenantId: string };
    }
  | {
      readonly operation: "core001.membership.resolve";
      readonly context: TrustedRuntimeContext;
      readonly payload: {
        readonly tenantId: string;
        readonly organizationId: string;
        readonly identityId: string;
      };
    }
);

export interface PythonRuntimeClientOptions {
  readonly pythonExecutable: string;
  readonly workerScript: string;
  readonly workingDirectory: string;
  readonly ownerFactory: string;
  readonly runtimeMode: "production" | "test";
  readonly environment?: Readonly<Record<string, string>>;
  readonly poolSize?: number;
  readonly queueLimit?: number;
  readonly requestTimeoutMs?: number;
  readonly maxRequestBytes?: number;
  readonly maxResponseBytes?: number;
}

export type PythonRuntimeErrorCode =
  | "RUNTIME_CLOSED"
  | "RUNTIME_QUEUE_FULL"
  | "RUNTIME_CANCELLED"
  | "RUNTIME_TIMEOUT"
  | "RUNTIME_OUTCOME_UNKNOWN"
  | "RUNTIME_UNAVAILABLE"
  | "RUNTIME_WORKER_EXITED"
  | "RUNTIME_PROTOCOL_INVALID"
  | "RUNTIME_AUTHENTICATION_FAILED"
  | "ISSUER_NOT_ALLOWED"
  | "ACCESS_TOKEN_INVALID"
  | "OIDC_VERIFIER_UNAVAILABLE"
  | "OIDC_TRUST_CONFIGURATION_INVALID"
  | "DOMAIN_OWNER_UNAVAILABLE"
  | "TRUSTED_CONTEXT_STALE"
  | "DOMAIN_DEPENDENCY_UNAVAILABLE"
  | "DOMAIN_VALIDATION_FAILED"
  | "DOMAIN_EXECUTION_FAILED"
  | "DOMAIN_RESULT_INVALID"
  | "TENANT_SCOPE_MISMATCH"
  | "ORGANIZATION_SCOPE_MISMATCH"
  | "ACTOR_SCOPE_MISMATCH"
  | "OPERATION_NOT_ALLOWED";

export interface PythonRuntimeErrorOptions {
  readonly retryable?: boolean;
  readonly requestId?: string;
  readonly idempotencyKey?: string;
  readonly cause?: unknown;
}

export class PythonRuntimeError extends Error {
  public readonly code: PythonRuntimeErrorCode;
  public readonly retryable: boolean;
  public readonly requestId?: string;
  public readonly idempotencyKey?: string;

  public constructor(
    code: PythonRuntimeErrorCode,
    options: PythonRuntimeErrorOptions = {}
  ) {
    super(
      code,
      options.cause === undefined ? undefined : { cause: options.cause }
    );
    this.name = "PythonRuntimeError";
    this.code = code;
    this.retryable = options.retryable ?? false;

    if (options.requestId !== undefined) {
      this.requestId = options.requestId;
    }
    if (options.idempotencyKey !== undefined) {
      this.idempotencyKey = options.idempotencyKey;
    }
  }
}
