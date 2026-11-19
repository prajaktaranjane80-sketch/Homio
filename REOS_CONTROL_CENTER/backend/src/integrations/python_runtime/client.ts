import {
  createHmac,
  randomBytes,
  randomUUID,
  timingSafeEqual
} from "node:crypto";
import {
  spawn,
  type ChildProcessWithoutNullStreams
} from "node:child_process";
import { isAbsolute } from "node:path";

import {
  PYTHON_RUNTIME_PROTOCOL_NAME,
  PYTHON_RUNTIME_PROTOCOL_VERSION,
  PYTHON_RUNTIME_SERVICE_ID,
  PYTHON_RUNTIME_AUDIENCE
} from "./contracts.js";
import type {
  JsonValue,
  PythonRuntimeClientOptions,
  PythonRuntimeErrorCode,
  PythonRuntimeInvocation,
  RuntimeCorrelationContext,
  TrustedRuntimeContext
} from "./contracts.js";
import { PythonRuntimeError } from "./contracts.js";

const RUNTIME_ID = "homio-python-runtime";
const DEFAULT_POOL_SIZE = 4;
const DEFAULT_QUEUE_LIMIT = 128;
const DEFAULT_TIMEOUT_MS = 10_000;
const DEFAULT_MESSAGE_BYTES = 1_048_576;
const MAX_JSON_ARRAY_ITEMS = 10_000;
const MAX_JSON_OBJECT_PROPERTIES = 10_000;

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Unicode General Category Cc covers C0 and C1 control characters.
const CONTROL_CHARACTER_PATTERN = /\p{Cc}/u;

const SAFE_ENVIRONMENT_NAMES = new Set([
  "HOMIO_OIDC_ISSUER",
  "HOMIO_OIDC_AUDIENCE",
  "HOMIO_OIDC_JWKS_URL"
]);

const OWNER_FACTORY_PATTERN =
  /^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$/;

const DOMAIN_FAILURE_CODES: readonly PythonRuntimeErrorCode[] = [
  "ISSUER_NOT_ALLOWED",
  "ACCESS_TOKEN_INVALID",
  "OIDC_VERIFIER_UNAVAILABLE",
  "OIDC_TRUST_CONFIGURATION_INVALID",
  "DOMAIN_OWNER_UNAVAILABLE",
  "TRUSTED_CONTEXT_STALE",
  "DOMAIN_DEPENDENCY_UNAVAILABLE",
  "DOMAIN_VALIDATION_FAILED",
  "DOMAIN_EXECUTION_FAILED",
  "DOMAIN_RESULT_INVALID",
  "TENANT_SCOPE_MISMATCH",
  "ORGANIZATION_SCOPE_MISMATCH",
  "ACTOR_SCOPE_MISMATCH",
  "OPERATION_NOT_ALLOWED"
];

interface RuntimeContextEnvelope {
  readonly correlationId: string;
  readonly actor?: TrustedRuntimeContext["actor"];
  readonly tenant?: TrustedRuntimeContext["tenant"];
}

interface RequestEnvelope {
  readonly protocol: string;
  readonly version: number;
  readonly messageType: "request";
  readonly serviceId: string;
  readonly audience: string;
  readonly requestId: string;
  readonly nonce: string;
  readonly issuedAtMs: number;
  readonly operation: PythonRuntimeInvocation["operation"];
  readonly context: RuntimeContextEnvelope;
  readonly payload: Record<string, JsonValue>;
  readonly idempotency: null;
  readonly signature: string;
}

interface PendingCall {
  readonly invocation: PythonRuntimeInvocation;
  readonly requestId: string;
  readonly resolve: (value: Record<string, JsonValue>) => void;
  readonly reject: (error: PythonRuntimeError) => void;
  readonly timeout: NodeJS.Timeout;
  abortListener: (() => void) | undefined;
  slot: WorkerSlot | undefined;
  settled: boolean;
}

interface WorkerSlot {
  readonly child: ChildProcessWithoutNullStreams;
  readonly secret: Buffer;
  output: string;
  stderrCode: string | undefined;
  stderrTail: string;
  active: PendingCall | undefined;
  retired: boolean;
  hasExited: boolean;
  readonly exitPromise: Promise<void>;
  readonly resolveExit: () => void;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function canonicalJson(value: unknown, depth = 0): string {
  if (depth > 32) {
    throw new TypeError("JSON nesting limit exceeded.");
  }

  if (value === null) return "null";

  if (typeof value === "string") {
    if ([...value].some((character) => {
      const code = character.codePointAt(0) ?? 0;
      return code >= 0xd800 && code <= 0xdfff;
    })) {
      throw new TypeError("JSON string contains an invalid Unicode scalar.");
    }
    return JSON.stringify(value);
  }

  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }

  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) {
      throw new TypeError(
        "Bridge JSON supports safe integers only; encode decimals as strings."
      );
    }
    return String(value);
  }

  if (Array.isArray(value)) {
    if (Object.getPrototypeOf(value) !== Array.prototype) {
      throw new TypeError("JSON arrays must use the standard Array prototype.");
    }
    if (value.length > MAX_JSON_ARRAY_ITEMS) {
      throw new TypeError("JSON array item limit exceeded.");
    }
    const ownKeys = Reflect.ownKeys(value);
    if (
      ownKeys.length !== value.length + 1 ||
      ownKeys.some((key) => typeof key !== "string")
    ) {
      throw new TypeError(
        "JSON arrays must be dense and cannot contain extra or symbol properties."
      );
    }
    const items: string[] = [];
    for (let index = 0; index < value.length; index += 1) {
      const descriptor = Object.getOwnPropertyDescriptor(value, String(index));
      if (
        descriptor === undefined ||
        !descriptor.enumerable ||
        !("value" in descriptor)
      ) {
        throw new TypeError(
          "JSON arrays cannot contain holes, accessors or hidden values."
        );
      }
      items.push(canonicalJson(descriptor.value, depth + 1));
    }
    return `[${items.join(",")}]`;
  }

  if (!isRecord(value)) {
    throw new TypeError("Bridge payload is not plain JSON.");
  }

  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) {
    throw new TypeError("Bridge payload must contain plain objects only.");
  }

  const ownKeys = Reflect.ownKeys(value);
  if (ownKeys.some((key) => typeof key !== "string")) {
    throw new TypeError("Bridge payload cannot contain symbol keys.");
  }
  if (ownKeys.length > MAX_JSON_OBJECT_PROPERTIES) {
    throw new TypeError("JSON object property limit exceeded.");
  }

  const descriptors = Object.getOwnPropertyDescriptors(value);
  const keys = Object.keys(descriptors).sort();
  const entries: string[] = [];

  for (const key of keys) {
    if (["__proto__", "prototype", "constructor"].includes(key)) {
      throw new TypeError("Bridge payload contains a forbidden key.");
    }

    const descriptor = descriptors[key];
    if (
      descriptor === undefined ||
      !descriptor.enumerable ||
      !("value" in descriptor)
    ) {
      throw new TypeError(
        "Bridge payload cannot contain accessors or hidden values."
      );
    }

    entries.push(
      `${canonicalJson(key, depth + 1)}:${canonicalJson(
        descriptor.value,
        depth + 1
      )}`
    );
  }

  return `{${entries.join(",")}}`;
}

type JsonContainerFrame =
  | { readonly kind: "object"; readonly keys: Set<string> }
  | { readonly kind: "array" };

function isJsonWhitespace(value: string | undefined): boolean {
  return value === " " || value === "\t" || value === "\n" || value === "\r";
}

/** Reject duplicate object keys before JSON.parse can silently collapse them. */
function assertNoDuplicateJsonObjectKeys(serialized: string): void {
  const containers: JsonContainerFrame[] = [];
  let index = 0;
  while (index < serialized.length) {
    const character = serialized[index];
    if (character === '"') {
      const tokenStart = index;
      index += 1;
      while (index < serialized.length) {
        const current = serialized[index];
        if (current === "\\") { index += 2; continue; }
        if (current === '"') { index += 1; break; }
        index += 1;
      }
      let lookahead = index;
      while (isJsonWhitespace(serialized[lookahead])) lookahead += 1;
      if (serialized[lookahead] === ":") {
        const frame = containers[containers.length - 1];
        if (frame?.kind === "object") {
          const key: unknown = JSON.parse(serialized.slice(tokenStart, index));
          if (typeof key !== "string") {
            throw new TypeError("JSON object key is invalid.");
          }
          if (frame.keys.has(key)) {
            throw new TypeError("Runtime response contains a duplicate JSON object key.");
          }
          frame.keys.add(key);
        }
      }
      continue;
    }
    if (character === "{") {
      containers.push({ kind: "object", keys: new Set<string>() });
    } else if (character === "[") {
      containers.push({ kind: "array" });
    } else if (character === "}" || character === "]") {
      containers.pop();
    }
    index += 1;
  }
}

function hmac(secret: Buffer, value: unknown): string {
  return createHmac("sha256", secret)
    .update(canonicalJson(value), "utf8")
    .digest("hex");
}

function sameSignature(left: unknown, right: string): boolean {
  if (typeof left !== "string" || !/^[0-9a-f]{64}$/.test(left)) {
    return false;
  }

  const actual = Buffer.from(left, "hex");
  const expected = Buffer.from(right, "hex");

  return (
    actual.length === expected.length &&
    timingSafeEqual(actual, expected)
  );
}

function exactKeys(
  value: Record<string, unknown>,
  expected: readonly string[]
): boolean {
  return (
    Object.keys(value).sort().join(",") ===
    [...expected].sort().join(",")
  );
}

function assertUuid(
  value: unknown,
  field: string
): asserts value is string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    throw new TypeError(`${field} must be a UUID.`);
  }
}

function assertSafeText(
  value: unknown,
  field: string,
  maximum: number
): asserts value is string {
  if (
    typeof value !== "string" ||
    !value ||
    value.length > maximum ||
    value.trim() !== value ||
    CONTROL_CHARACTER_PATTERN.test(value)
  ) {
    throw new TypeError(`${field} is invalid.`);
  }
}

function validateCorrelationContext(
  context: RuntimeCorrelationContext
): void {
  const candidate = context as unknown as Record<string, unknown>;

  if (
    !isRecord(candidate) ||
    !exactKeys(candidate, ["correlationId"])
  ) {
    throw new TypeError("Correlation context shape is invalid.");
  }

  assertUuid(candidate.correlationId, "correlationId");
}

function validateTrustedContext(
  context: TrustedRuntimeContext
): void {
  const candidate = context as unknown as Record<string, unknown>;

  if (
    !isRecord(candidate) ||
    !exactKeys(candidate, ["actor", "tenant", "correlationId"])
  ) {
    throw new TypeError("Trusted context shape is invalid.");
  }

  validateCorrelationContext({
    correlationId: candidate.correlationId as string
  });

  if (
    !isRecord(candidate.actor) ||
    !exactKeys(candidate.actor, ["identityId", "accountId"])
  ) {
    throw new TypeError("Trusted actor context shape is invalid.");
  }

  if (
    !isRecord(candidate.tenant) ||
    !exactKeys(candidate.tenant, [
      "tenantId",
      "tenantRevision",
      "organizationId",
      "membershipId",
      "membershipRevision"
    ])
  ) {
    throw new TypeError("Trusted tenant context shape is invalid.");
  }

  assertUuid(candidate.actor.identityId, "actor.identityId");
  assertUuid(candidate.actor.accountId, "actor.accountId");
  assertUuid(candidate.tenant.tenantId, "tenant.tenantId");
  assertUuid(candidate.tenant.organizationId, "tenant.organizationId");
  assertUuid(candidate.tenant.membershipId, "tenant.membershipId");

  for (const revision of [
    candidate.tenant.tenantRevision,
    candidate.tenant.membershipRevision
  ]) {
    if (
      typeof revision !== "number" ||
      !Number.isSafeInteger(revision) ||
      revision < 1
    ) {
      throw new TypeError("Trusted context revision is invalid.");
    }
  }
}

function freezeJsonTree(value: unknown): void {
  if (Array.isArray(value)) {
    for (const item of value) freezeJsonTree(item);
  } else if (isRecord(value)) {
    for (const item of Object.values(value)) freezeJsonTree(item);
  }

  if (typeof value === "object" && value !== null) {
    Object.freeze(value);
  }
}

function snapshotInvocation(
  invocation: PythonRuntimeInvocation
): PythonRuntimeInvocation {
  // Clone only JSON data. AbortSignal remains a live cancellation capability.
  const context = JSON.parse(
    canonicalJson(invocation.context)
  ) as RuntimeCorrelationContext | TrustedRuntimeContext;

  const payload = JSON.parse(
    canonicalJson(invocation.payload)
  ) as Record<string, JsonValue>;

  freezeJsonTree(context);
  freezeJsonTree(payload);

  return Object.freeze({
    operation: invocation.operation,
    context,
    payload,
    ...(invocation.signal === undefined
      ? {}
      : { signal: invocation.signal }),
    ...(invocation.timeoutMs === undefined
      ? {}
      : { timeoutMs: invocation.timeoutMs })
  }) as PythonRuntimeInvocation;
}

function validateInvocation(
  invocation: PythonRuntimeInvocation
): void {
  // Serialize first: rejects getters, class instances, unsafe prototypes and non-JSON values.
  canonicalJson({
    context: invocation.context,
    payload: invocation.payload
  });

  if (invocation.operation === "oidc.verify_access_token") {
    validateCorrelationContext(invocation.context);

    if (
      !exactKeys(
        invocation.payload as unknown as Record<string, unknown>,
        ["accessToken"]
      )
    ) {
      throw new TypeError("OIDC verification payload is invalid.");
    }

    assertSafeText(
      invocation.payload.accessToken,
      "accessToken",
      16_384
    );
    return;
  }

  if (invocation.operation === "core001.identity.resolve") {
    if ("actor" in invocation.context) {
      validateTrustedContext(invocation.context);
    } else {
      validateCorrelationContext(invocation.context);
    }

    const payload = invocation.payload as unknown as Record<string, unknown>;
    if (!exactKeys(payload, ["provider", "subject"])) {
      throw new TypeError("Identity resolution payload is invalid.");
    }

    assertSafeText(payload.provider, "provider", 255);

    const issuer = new URL(payload.provider);
    const issuerAuthority = payload.provider
      .slice(payload.provider.indexOf("://") + 3)
      .split(/[/?#]/, 1)[0] ?? "";

    if (
      issuer.protocol !== "https:" ||
      issuerAuthority.includes("@") ||
      issuer.username !== "" ||
      issuer.password !== "" ||
      issuer.search !== "" ||
      issuer.hash !== "" ||
      !issuer.hostname
    ) {
      throw new TypeError(
        "Identity provider must be a trusted HTTPS issuer URL."
      );
    }

    assertSafeText(payload.subject, "subject", 255);
    return;
  }

  validateTrustedContext(invocation.context);

  if (invocation.operation === "core001.tenant.resolve_context") {
    const payload = invocation.payload as unknown as Record<string, unknown>;

    if (!exactKeys(payload, ["tenantId"])) {
      throw new TypeError("Tenant resolution payload is invalid.");
    }

    assertUuid(payload.tenantId, "tenantId");

    if (payload.tenantId !== invocation.context.tenant.tenantId) {
      throw new TypeError(
        "Tenant selection does not match trusted context."
      );
    }
    return;
  }

  if (invocation.operation === "core001.membership.resolve") {
    const payload = invocation.payload as unknown as Record<string, unknown>;

    if (
      !exactKeys(payload, [
        "tenantId",
        "organizationId",
        "identityId"
      ])
    ) {
      throw new TypeError("Membership resolution payload is invalid.");
    }

    assertUuid(payload.tenantId, "tenantId");
    assertUuid(payload.organizationId, "organizationId");
    assertUuid(payload.identityId, "identityId");

    if (
      payload.tenantId !== invocation.context.tenant.tenantId ||
      payload.organizationId !== invocation.context.tenant.organizationId ||
      payload.identityId !== invocation.context.actor.identityId
    ) {
      throw new TypeError(
        "Membership scope does not match trusted context."
      );
    }
    return;
  }

  throw new TypeError("Python runtime operation is not allowlisted.");
}

function domainResultInvalid(): never {
  throw new PythonRuntimeError("DOMAIN_RESULT_INVALID");
}

function resultText(value: unknown, maximum: number): string {
  if (
    typeof value !== "string" ||
    !value ||
    value.length > maximum ||
    value.trim() !== value ||
    CONTROL_CHARACTER_PATTERN.test(value)
  ) {
    return domainResultInvalid();
  }
  return value;
}

function resultUuid(value: unknown): string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    return domainResultInvalid();
  }
  return value;
}

function optionalResultUuid(value: unknown): string | null {
  if (value === null) return null;
  return resultUuid(value);
}

function resultRevision(
  value: unknown,
  allowNull = false
): number | null {
  if (value === null && allowNull) return null;

  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < 1
  ) {
    return domainResultInvalid();
  }

  return value;
}

function resultStatus(
  value: unknown,
  allowed: readonly string[]
): string {
  if (typeof value !== "string" || !allowed.includes(value)) {
    return domainResultInvalid();
  }

    return value;
}

function validateOperationResult(
  invocation: PythonRuntimeInvocation,
  value: unknown,
  environment: Readonly<Record<string, string>>
): Record<string, JsonValue> {
  if (!isRecord(value)) return domainResultInvalid();

  if (invocation.operation === "oidc.verify_access_token") {
    if (
      !exactKeys(value, [
        "issuer",
        "subject",
        "audiences",
        "clientId",
        "tokenId"
      ])
    ) {
      return domainResultInvalid();
    }

    const issuer = resultText(value.issuer, 255);
    let parsedIssuer: URL;

    try {
      parsedIssuer = new URL(issuer);
    } catch {
      return domainResultInvalid();
    }

    const issuerAuthority = issuer
      .slice(issuer.indexOf("://") + 3)
      .split(/[/?#]/, 1)[0] ?? "";

    if (
      parsedIssuer.protocol !== "https:" ||
      !parsedIssuer.hostname ||
      issuerAuthority.includes("@") ||
      parsedIssuer.username !== "" ||
      parsedIssuer.password !== "" ||
      parsedIssuer.search !== "" ||
      parsedIssuer.hash !== "" ||
      (
        environment.HOMIO_OIDC_ISSUER !== undefined &&
        issuer !== environment.HOMIO_OIDC_ISSUER
      )
    ) {
      return domainResultInvalid();
    }

    const subject = resultText(value.subject, 255);
    const clientId = resultText(value.clientId, 512);
    const tokenId = resultText(value.tokenId, 255);

    if (
      !Array.isArray(value.audiences) ||
      value.audiences.length < 1 ||
      value.audiences.length > 16
    ) {
      return domainResultInvalid();
    }

    const audiences = value.audiences.map(
      (audience) => resultText(audience, 2048)
    );

    if (
      environment.HOMIO_OIDC_AUDIENCE !== undefined &&
      !audiences.includes(environment.HOMIO_OIDC_AUDIENCE)
    ) {
      return domainResultInvalid();
    }

    return { issuer, subject, audiences, clientId, tokenId };
  }

  if (invocation.operation === "core001.identity.resolve") {
    if (
      !exactKeys(value, ["status", "identityId", "referenceId"])
    ) {
      return domainResultInvalid();
    }

    const status = resultStatus(
      value.status,
      ["RESOLVED", "NOT_FOUND", "REVOKED"]
    );
    const identityId = optionalResultUuid(value.identityId);
    const referenceId = optionalResultUuid(value.referenceId);

    if ("actor" in invocation.context) {
      if (status !== "RESOLVED" || identityId === null) {
        throw new PythonRuntimeError("TRUSTED_CONTEXT_STALE");
      }

      if (identityId !== invocation.context.actor.identityId) {
        throw new PythonRuntimeError("ACTOR_SCOPE_MISMATCH");
      }
    }

    if (
      status === "RESOLVED" &&
      (identityId === null || referenceId === null)
    ) {
      return domainResultInvalid();
    }

    return { status, identityId, referenceId };
  }

  if (invocation.operation === "core001.tenant.resolve_context") {
    if (
      !exactKeys(value, [
        "status",
        "tenantId",
        "tenantRevision",
        "context"
      ])
    ) {
      return domainResultInvalid();
    }

    const status = resultStatus(
      value.status,
      ["RESOLVED", "NOT_FOUND", "INACTIVE", "ARCHIVED"]
    );
    const tenantId = resultUuid(value.tenantId);

    if (tenantId !== invocation.context.tenant.tenantId) {
      return domainResultInvalid();
    }

    const tenantRevision = resultRevision(
      value.tenantRevision,
      true
    );

    if (
      status !== "RESOLVED" ||
      tenantRevision !== invocation.context.tenant.tenantRevision
    ) {
      throw new PythonRuntimeError("TRUSTED_CONTEXT_STALE");
    }

    if (status === "RESOLVED") {
      if (
        !isRecord(value.context) ||
        !exactKeys(value.context, [
          "tenantStatus",
          "tenantKind",
          "operatingMode"
        ])
      ) {
        return domainResultInvalid();
      }

      const context = {
        tenantStatus: resultStatus(
          value.context.tenantStatus,
          ["ACTIVE", "RESTRICTED"]
        ),
        tenantKind: resultStatus(
          value.context.tenantKind,
          ["BROKERAGE", "BUILDER", "ENTERPRISE", "PARTNER", "PLATFORM"]
        ),
        operatingMode: resultStatus(
          value.context.operatingMode,
          [
            "OWNED_INTERNATIONAL_BROKERAGE",
            "BROKER_SAAS",
            "BUILDER_SAAS",
            "ENTERPRISE_WHITE_LABEL",
            "PLATFORM_API_PARTNER"
          ]
        )
      };

      if (tenantRevision === null) return domainResultInvalid();
      return { status, tenantId, tenantRevision, context };
    }

    if (value.context !== null) return domainResultInvalid();
    return { status, tenantId, tenantRevision, context: null };
  }

  if (invocation.operation === "core001.membership.resolve") {
    if (
      !exactKeys(value, [
        "status",
        "membershipId",
        "tenantId",
        "organizationId",
        "identityId",
        "membershipRevision"
      ])
    ) {
      return domainResultInvalid();
    }

    const status = resultStatus(
      value.status,
      ["RESOLVED", "NOT_FOUND", "INACTIVE", "EXPIRED"]
    );
    const membershipId = optionalResultUuid(value.membershipId);
    const tenantId = resultUuid(value.tenantId);
    const organizationId = resultUuid(value.organizationId);
    const identityId = resultUuid(value.identityId);
    const membershipRevision = resultRevision(
      value.membershipRevision,
      true
    );

    if (
      tenantId !== invocation.context.tenant.tenantId ||
      organizationId !== invocation.context.tenant.organizationId ||
      identityId !== invocation.context.actor.identityId
    ) {
      return domainResultInvalid();
    }

    if (
      status !== "RESOLVED" ||
      membershipId === null ||
      membershipRevision !== invocation.context.tenant.membershipRevision
    ) {
      throw new PythonRuntimeError("TRUSTED_CONTEXT_STALE");
    }

    return {
      status,
      membershipId,
      tenantId,
      organizationId,
      identityId,
      membershipRevision
    };
  }

  return domainResultInvalid();
}

function validateHttpsConfiguration(
  name: string,
  value: string,
  maximumLength: number
): void {
  if (value.length > maximumLength) {
    throw new TypeError(
      `${name} must be a valid HTTPS URL of at most ${maximumLength} characters.`
    );
  }

  if (
    value !== value.trim() ||
    CONTROL_CHARACTER_PATTERN.test(value) ||
    value.includes(" ")
  ) {
    throw new TypeError(
      `${name} contains whitespace or control characters.`
    );
  }

  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new TypeError(`${name} must be a valid HTTPS URL.`);
  }

  const authority = value
    .slice(value.indexOf("://") + 3)
    .split(/[/?#]/, 1)[0] ?? "";

  if (
    parsed.protocol !== "https:" ||
    !parsed.hostname ||
    authority.includes("@") ||
    parsed.username !== "" ||
    parsed.password !== "" ||
    parsed.search !== "" ||
    parsed.hash !== ""
  ) {
    throw new TypeError(
      `${name} must be HTTPS without credentials, query or fragment.`
    );
  }
}

function mapRemoteCode(value: unknown): PythonRuntimeErrorCode {
  return (
    typeof value === "string" &&
    DOMAIN_FAILURE_CODES.includes(value as PythonRuntimeErrorCode)
  )
    ? value as PythonRuntimeErrorCode
    : "RUNTIME_PROTOCOL_INVALID";
}

function safeWorkerFailure(
  stderrCode: string | undefined,
  cause: unknown
): PythonRuntimeErrorCode {
  if (
    stderrCode === "AUTHENTICATION_FAILED" ||
    stderrCode === "SERVICE_SECRET_INVALID" ||
    stderrCode === "SERVICE_IDENTITY_INVALID"
  ) {
    return "RUNTIME_AUTHENTICATION_FAILED";
  }

  if (stderrCode === "OWNER_COMPOSITION_UNAVAILABLE") {
    return "RUNTIME_UNAVAILABLE";
  }

  if (
    stderrCode === "MESSAGE_FRAMING_INVALID" ||
    stderrCode === "RESPONSE_SIZE_EXCEEDED"
  ) {
    return "RUNTIME_PROTOCOL_INVALID";
  }

  if (
    stderrCode !== undefined &&
    /^[A-Z_]+$/.test(stderrCode)
  ) {
    return "RUNTIME_PROTOCOL_INVALID";
  }

  if (isRecord(cause) && cause.code === "ENOENT") {
    return "RUNTIME_UNAVAILABLE";
  }

  return "RUNTIME_WORKER_EXITED";
}

export class PythonRuntimeClient {
  private readonly options: Required<
    Omit<PythonRuntimeClientOptions, "environment">
  > & {
    readonly environment: Readonly<Record<string, string>>;
  };

  private readonly queue: PendingCall[] = [];
  private readonly workers: WorkerSlot[] = [];
  private readonly retiredWorkers = new Set<WorkerSlot>();

  private closed = false;
  private closePromise: Promise<void> | undefined;

  public constructor(options: PythonRuntimeClientOptions) {
    if (
      !isAbsolute(options.pythonExecutable) ||
      !isAbsolute(options.workerScript) ||
      !isAbsolute(options.workingDirectory)
    ) {
      throw new TypeError(
        "Python executable, worker script and working directory must be absolute paths."
      );
    }

    if (!OWNER_FACTORY_PATTERN.test(options.ownerFactory)) {
      throw new TypeError("Python runtime owner factory is invalid.");
    }

    if (
      options.runtimeMode !== "production" &&
      options.runtimeMode !== "test"
    ) {
      throw new TypeError("Python runtime mode is invalid.");
    }

    if (
      options.runtimeMode === "test" &&
      process.env.NODE_ENV !== "test"
    ) {
      throw new TypeError(
        "Test runtime composition is allowed only in a test process."
      );
    }

    const poolSize = options.poolSize ?? DEFAULT_POOL_SIZE;
    const queueLimit = options.queueLimit ?? DEFAULT_QUEUE_LIMIT;
    const requestTimeoutMs =
      options.requestTimeoutMs ?? DEFAULT_TIMEOUT_MS;
    const maxRequestBytes =
      options.maxRequestBytes ?? DEFAULT_MESSAGE_BYTES;
    const maxResponseBytes =
      options.maxResponseBytes ?? DEFAULT_MESSAGE_BYTES;

    if (!Number.isInteger(poolSize) || poolSize < 1 || poolSize > 32) {
      throw new TypeError("poolSize is invalid.");
    }
    if (!Number.isInteger(queueLimit) || queueLimit < 1 || queueLimit > 4096) {
      throw new TypeError("queueLimit is invalid.");
    }
    if (
      !Number.isInteger(requestTimeoutMs) ||
      requestTimeoutMs < 100 ||
      requestTimeoutMs > 120_000
    ) {
      throw new TypeError("requestTimeoutMs is invalid.");
    }
    if (
      !Number.isInteger(maxRequestBytes) ||
      maxRequestBytes < 1024 ||
      maxRequestBytes > DEFAULT_MESSAGE_BYTES
    ) {
      throw new TypeError("maxRequestBytes is invalid.");
    }
    if (
      !Number.isInteger(maxResponseBytes) ||
      maxResponseBytes < 1024 ||
      maxResponseBytes > DEFAULT_MESSAGE_BYTES
    ) {
      throw new TypeError("maxResponseBytes is invalid.");
    }

    const environment: Record<string, string> = {};

    for (const [name, value] of Object.entries(options.environment ?? {})) {
      if (
        !SAFE_ENVIRONMENT_NAMES.has(name) ||
        typeof value !== "string" ||
        CONTROL_CHARACTER_PATTERN.test(value)
      ) {
        throw new TypeError(
          `Runtime environment variable is not permitted: ${name}`
        );
      }
      environment[name] = value;
    }

    if (options.runtimeMode === "production") {
      const issuer = environment.HOMIO_OIDC_ISSUER;
      const audience = environment.HOMIO_OIDC_AUDIENCE;
      const jwksUrl = environment.HOMIO_OIDC_JWKS_URL;

      if (
        issuer === undefined ||
        audience === undefined ||
        jwksUrl === undefined
      ) {
        throw new TypeError(
          "Production Python runtime requires the configured OIDC issuer, audience and JWKS URL."
        );
      }

      validateHttpsConfiguration("HOMIO_OIDC_ISSUER", issuer, 255);
      validateHttpsConfiguration("HOMIO_OIDC_JWKS_URL", jwksUrl, 2_048);

      if (
        !audience ||
        audience.length > 512 ||
        audience !== audience.trim() ||
        CONTROL_CHARACTER_PATTERN.test(audience)
      ) {
        throw new TypeError("HOMIO_OIDC_AUDIENCE is invalid.");
      }
    }

    this.options = {
      pythonExecutable: options.pythonExecutable,
      workerScript: options.workerScript,
      workingDirectory: options.workingDirectory,
      ownerFactory: options.ownerFactory,
      runtimeMode: options.runtimeMode,
      environment: Object.freeze(environment),
      poolSize,
      queueLimit,
      requestTimeoutMs,
      maxRequestBytes,
      maxResponseBytes
    };
  }

  public invoke(
    invocation: PythonRuntimeInvocation
  ): Promise<Record<string, JsonValue>> {
    if (this.closed) {
      return Promise.reject(new PythonRuntimeError("RUNTIME_CLOSED"));
    }

    if (invocation.signal?.aborted) {
      return Promise.reject(new PythonRuntimeError("RUNTIME_CANCELLED"));
    }

    let snapshot: PythonRuntimeInvocation;

    try {
      validateInvocation(invocation);
      snapshot = snapshotInvocation(invocation);
    } catch (error) {
      return Promise.reject(error);
    }

    if (this.queue.length >= this.options.queueLimit) {
      return Promise.reject(
        new PythonRuntimeError("RUNTIME_QUEUE_FULL", { retryable: true })
      );
    }

    const timeoutMs =
      snapshot.timeoutMs ?? this.options.requestTimeoutMs;

    if (
      !Number.isInteger(timeoutMs) ||
      timeoutMs < 100 ||
      timeoutMs > 120_000
    ) {
      return Promise.reject(
        new TypeError("Invocation timeout is invalid.")
      );
    }

    const requestId = randomUUID();

    return new Promise((resolve, reject) => {
      const pending: PendingCall = {
        invocation: snapshot,
        requestId,
        resolve,
        reject,
        timeout: setTimeout(
          () => this.expire(pending),
          timeoutMs
        ),
        abortListener: undefined,
        slot: undefined,
        settled: false
      };

      if (snapshot.signal !== undefined) {
        pending.abortListener = (): void => this.abort(pending);
        snapshot.signal.addEventListener(
          "abort",
          pending.abortListener,
          { once: true }
        );

        if (snapshot.signal.aborted) {
          this.abort(pending);
          return;
        }
      }

      this.queue.push(pending);
      this.pump();
    });
  }

  public close(): Promise<void> {
    if (this.closePromise !== undefined) {
      return this.closePromise;
    }

    this.closed = true;

    for (const pending of [...this.queue]) {
      this.rejectPending(
        pending,
        new PythonRuntimeError("RUNTIME_CLOSED", {
          requestId: pending.requestId
        })
      );
    }

    this.queue.length = 0;

    const slots = [...this.workers, ...this.retiredWorkers];

    for (const slot of slots) {
      if (slot.active !== undefined) {
        this.rejectPending(
          slot.active,
          new PythonRuntimeError("RUNTIME_CLOSED", {
            requestId: slot.active.requestId
          })
        );
      }
      this.retire(slot);
    }

    this.closePromise = Promise.all(
      slots.map(async (slot) => {
        if (slot.hasExited) return;

        await this.waitForExit(slot, 1_000);

        if (!slot.hasExited) {
          slot.child.kill("SIGKILL");
          await this.waitForExit(slot, 1_000);
        }

        if (!slot.hasExited) {
          throw new PythonRuntimeError("RUNTIME_WORKER_EXITED");
        }
      })
    ).then(() => undefined);

    return this.closePromise;
  }

  private waitForExit(
    slot: WorkerSlot,
    timeoutMs: number
  ): Promise<void> {
    if (slot.hasExited) return Promise.resolve();

    return new Promise((resolvePromise) => {
      const timer = setTimeout(resolvePromise, timeoutMs);

      void slot.exitPromise.then(() => {
        clearTimeout(timer);
        resolvePromise();
      });
    });
  }

  private pump(): void {

        if (this.closed) return;

    while (this.queue.length > 0) {
      let slot = this.workers.find(
        (candidate) =>
          !candidate.retired &&
          candidate.active === undefined
      );

      if (
        slot === undefined &&
        this.workers.length + this.retiredWorkers.size <
          this.options.poolSize
      ) {
        try {
          slot = this.createWorker();
        } catch (error) {
          while (this.queue.length > 0) {
            const pending = this.queue.shift();
            if (pending !== undefined) {
              this.rejectPending(
                pending,
                new PythonRuntimeError("RUNTIME_UNAVAILABLE", {
                  cause: error
                })
              );
            }
          }
          return;
        }
      }

      if (slot === undefined) return;

      const pending = this.queue.shift();
      if (pending === undefined) return;

      if (pending.invocation.signal?.aborted) {
        this.rejectPending(
          pending,
          new PythonRuntimeError("RUNTIME_CANCELLED", {
            requestId: pending.requestId
          })
        );
        continue;
      }

      slot.active = pending;
      pending.slot = slot;
      this.send(slot, pending);
    }
  }

  private createWorker(): WorkerSlot {
    const secret = randomBytes(32);

    let child: ChildProcessWithoutNullStreams;
    try {
      child = spawn(
        this.options.pythonExecutable,
        ["-u", this.options.workerScript],
        {
          cwd: this.options.workingDirectory,
          shell: false,
          windowsHide: true,
          stdio: ["pipe", "pipe", "pipe"],
          env: {
            HOMIO_PYTHON_BRIDGE_SECRET: secret.toString("hex"),
            HOMIO_PYTHON_RUNTIME_MODE: this.options.runtimeMode,
            HOMIO_PYTHON_RUNTIME_OWNER_FACTORY: this.options.ownerFactory,
            PYTHONUTF8: "1",
            PYTHONUNBUFFERED: "1",
            PYTHONNOUSERSITE: "1",
            PYTHONDONTWRITEBYTECODE: "1",
            ...this.options.environment
          }
        }
      );
    } catch (error) {
      secret.fill(0);
      throw error;
    }

    let resolveExit!: () => void;
    const exitPromise = new Promise<void>((resolvePromise) => {
      resolveExit = resolvePromise;
    });

    const slot: WorkerSlot = {
      child,
      secret,
      output: "",
      stderrCode: undefined,
      stderrTail: "",
      active: undefined,
      retired: false,
      hasExited: false,
      exitPromise,
      resolveExit
    };

    this.workers.push(slot);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");

    child.stdout.on("data", (chunk: string) => {
      this.receive(slot, chunk);
    });

    child.stderr.on("data", (chunk: string) => {
      slot.stderrTail = (slot.stderrTail + chunk).slice(-512);
      const lines = slot.stderrTail.split(/\r?\n/);
      slot.stderrTail = lines.pop() ?? "";

      for (const line of lines) {
        const match =
          /^PYTHON_RUNTIME_(?:PROTOCOL_REJECTED:([A-Z_]+)|([A-Z_]+))$/.exec(
            line
          );

        if (match?.[1] !== undefined) {
          slot.stderrCode = match[1];
        } else if (match?.[2] !== undefined) {
          slot.stderrCode = match[2];
        }
      }
    });

    const markExited = (): void => {
      if (slot.hasExited) return;

      slot.hasExited = true;

      // The child no longer needs its per-process key; clear the parent copy.
      slot.secret.fill(0);
      slot.resolveExit();
      this.retiredWorkers.delete(slot);
      this.pump();
    };

    child.on("error", (error) => {
      this.workerFailed(slot, error);
    });

    child.on("exit", () => {
      markExited();
      this.workerFailed(slot);
    });

    child.on("close", () => {
      markExited();
      this.workerFailed(slot);
    });

    return slot;
  }

  private send(slot: WorkerSlot, pending: PendingCall): void {
    try {
      const unsigned = {
        protocol: PYTHON_RUNTIME_PROTOCOL_NAME,
        version: PYTHON_RUNTIME_PROTOCOL_VERSION,
        messageType: "request" as const,
        serviceId: PYTHON_RUNTIME_SERVICE_ID,
        audience: PYTHON_RUNTIME_AUDIENCE,
        requestId: pending.requestId,
        nonce: randomUUID(),
        issuedAtMs: Date.now(),
        operation: pending.invocation.operation,
        context: pending.invocation.context,
        payload: pending.invocation.payload,
        idempotency: null
      };

      const envelope: RequestEnvelope = {
        ...unsigned,
        signature: hmac(slot.secret, unsigned)
      };

      const frame = `${canonicalJson(envelope)}\n`;

      if (
        Buffer.byteLength(frame, "utf8") >
        this.options.maxRequestBytes
      ) {
        this.rejectActive(
          slot,
          new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
            requestId: pending.requestId
          })
        );
        this.retire(slot);
        return;
      }

      slot.child.stdin.write(frame, (error?: Error | null) => {
        if (error !== undefined && error !== null) {
          this.workerFailed(slot, error);
        }
      });
    } catch (error) {
      this.rejectActive(
        slot,
        new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
          requestId: pending.requestId,
          cause: error
        })
      );
      this.retire(slot);
    }
  }

  private receive(slot: WorkerSlot, chunk: string): void {
    if (slot.retired) return;

    slot.output += chunk;

    if (
      Buffer.byteLength(slot.output, "utf8") >
      this.options.maxResponseBytes + 1
    ) {
      this.rejectActive(
        slot,
        new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID")
      );
      this.retire(slot);
      return;
    }

    const newline = slot.output.indexOf("\n");
    if (newline < 0) return;

    const line = slot.output.slice(0, newline);
    const trailing = slot.output.slice(newline + 1);

    if (trailing.length > 0) {
      this.rejectActive(
        slot,
        new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID")
      );
      this.retire(slot);
      return;
    }

    const pending = slot.active;
    if (pending === undefined) {
      this.retire(slot);
      return;
    }

    try {
      assertNoDuplicateJsonObjectKeys(line);
      const response: unknown = JSON.parse(line);
      const result = this.verifyResponse(response, slot, pending);

      this.resolvePending(pending, result);
      slot.active = undefined;
      slot.output = "";
      this.pump();
    } catch (error) {
      const runtimeError =
        error instanceof PythonRuntimeError
          ? error
          : new PythonRuntimeError(
              "RUNTIME_PROTOCOL_INVALID",
              {
                requestId: pending.requestId,
                cause: error
              }
            );

      this.rejectActive(slot, runtimeError);

      if (this.isRemoteFailure(runtimeError.code)) {
        slot.output = "";
        this.pump();
      } else {
        this.retire(slot);
      }
    }
  }

  private verifyResponse(
    value: unknown,
    slot: WorkerSlot,
    pending: PendingCall
  ): Record<string, JsonValue> {
    if (!isRecord(value) || typeof value.signature !== "string") {
      throw new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
        requestId: pending.requestId
      });
    }

    const { signature, ...unsigned } = value;

    if (!sameSignature(signature, hmac(slot.secret, unsigned))) {
      throw new PythonRuntimeError("RUNTIME_AUTHENTICATION_FAILED", {
        requestId: pending.requestId
      });
    }

    try {
      canonicalJson(unsigned);

      if (
        Buffer.byteLength(canonicalJson(unsigned), "utf8") >
        this.options.maxResponseBytes
      ) {
        throw new TypeError(
          "Runtime response exceeded the configured size limit."
        );
      }
    } catch (cause) {
      throw new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
        requestId: pending.requestId,
        cause
      });
    }

    const successKeys = [
      "context",
      "messageType",
      "protocol",
      "requestId",
      "result",
      "runtimeId",
      "status",
      "version"
    ];
    const failureKeys = [
      "context",
      "error",
      "messageType",
      "protocol",
      "requestId",
      "runtimeId",
      "status",
      "version"
    ];

    const expectedKeys =
      unsigned.status === "success"
        ? successKeys
        : failureKeys;

    if (
      !exactKeys(unsigned, expectedKeys) ||
      unsigned.protocol !== PYTHON_RUNTIME_PROTOCOL_NAME ||
      unsigned.version !== PYTHON_RUNTIME_PROTOCOL_VERSION ||
      unsigned.messageType !== "response" ||
      unsigned.runtimeId !== RUNTIME_ID ||
      unsigned.requestId !== pending.requestId ||
      canonicalJson(unsigned.context) !==
        canonicalJson(pending.invocation.context)
    ) {
      throw new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
        requestId: pending.requestId
      });
    }

    if (
      unsigned.status === "success" &&
      isRecord(unsigned.result)
    ) {
      return validateOperationResult(
        pending.invocation,
        unsigned.result,
        this.options.environment
      );
    }

    if (
      unsigned.status === "failure" &&
      isRecord(unsigned.error)
    ) {
      if (
        !exactKeys(unsigned.error, [
          "code",
          "message",
          "retryable"
        ]) ||
        typeof unsigned.error.message !== "string" ||
        unsigned.error.message.length > 200 ||
        typeof unsigned.error.retryable !== "boolean"
      ) {
        throw new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
          requestId: pending.requestId
        });
      }

      const code = mapRemoteCode(unsigned.error.code);
      throw new PythonRuntimeError(code, {
        retryable: unsigned.error.retryable,
        requestId: pending.requestId
      });
    }

    throw new PythonRuntimeError("RUNTIME_PROTOCOL_INVALID", {
      requestId: pending.requestId
    });
  }

  private isRemoteFailure(
    code: PythonRuntimeErrorCode
  ): boolean {
    return DOMAIN_FAILURE_CODES.includes(code);
  }

  private expire(pending: PendingCall): void {
    if (pending.settled) return;

    const slot = pending.slot;

    if (slot === undefined) {
      const index = this.queue.indexOf(pending);
      if (index >= 0) this.queue.splice(index, 1);

      this.rejectPending(
        pending,
        new PythonRuntimeError("RUNTIME_TIMEOUT", {
          requestId: pending.requestId
        })
      );
      return;
    }

    this.rejectPending(
      pending,
      new PythonRuntimeError("RUNTIME_TIMEOUT", {
        requestId: pending.requestId
      })
    );
    this.retire(slot);
  }

  private abort(pending: PendingCall): void {
    if (pending.settled) return;

    const slot = pending.slot;

    if (slot === undefined) {
      const index = this.queue.indexOf(pending);
      if (index >= 0) this.queue.splice(index, 1);

      this.rejectPending(
        pending,
        new PythonRuntimeError("RUNTIME_CANCELLED", {
          requestId: pending.requestId
        })
      );
      return;
    }

    this.rejectPending(
      pending,
      new PythonRuntimeError("RUNTIME_CANCELLED", {
        requestId: pending.requestId
      })
    );
    this.retire(slot);
  }

  private workerFailed(
    slot: WorkerSlot,
    cause?: unknown
  ): void {
    if (slot.retired) return;

    if (slot.active !== undefined) {
      this.rejectActive(
        slot,
        new PythonRuntimeError(
          safeWorkerFailure(slot.stderrCode, cause),
          {
            requestId: slot.active.requestId,
            cause
          }
        )
      );
    }

    this.retire(slot);
  }

  private rejectActive(
    slot: WorkerSlot,
    error: PythonRuntimeError
  ): void {
    const pending = slot.active;
    if (pending === undefined) return;

    slot.active = undefined;
    this.rejectPending(pending, error);
  }

  private resolvePending(
    pending: PendingCall,
    result: Record<string, JsonValue>
  ): void {
    if (pending.settled) return;

    pending.settled = true;
    clearTimeout(pending.timeout);

    if (pending.abortListener !== undefined) {
      pending.invocation.signal?.removeEventListener(
        "abort",
        pending.abortListener
      );
    }

    pending.resolve(result);
  }

  private rejectPending(
    pending: PendingCall,
    error: PythonRuntimeError
  ): void {
    if (pending.settled) return;

    pending.settled = true;
    clearTimeout(pending.timeout);

    if (pending.abortListener !== undefined) {
      pending.invocation.signal?.removeEventListener(
        "abort",
        pending.abortListener
      );
    }

    pending.reject(error);
  }

  private retire(slot: WorkerSlot): void {
    if (slot.retired) return;

    slot.retired = true;

    const index = this.workers.indexOf(slot);
    if (index >= 0) this.workers.splice(index, 1);

    if (slot.active !== undefined) {
      this.rejectActive(
        slot,
        new PythonRuntimeError("RUNTIME_WORKER_EXITED")
      );
    }

    if (!slot.hasExited) {
      this.retiredWorkers.add(slot);

      void slot.exitPromise.then(() => {
        this.retiredWorkers.delete(slot);
        this.pump();
      });

      slot.child.kill("SIGTERM");

      const forceKill = setTimeout(() => {
        if (!slot.hasExited) {
          slot.child.kill("SIGKILL");
        }
      }, 250);

      forceKill.unref();
    }

    this.pump();
  }
}
