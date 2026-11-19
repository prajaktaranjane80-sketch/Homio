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
