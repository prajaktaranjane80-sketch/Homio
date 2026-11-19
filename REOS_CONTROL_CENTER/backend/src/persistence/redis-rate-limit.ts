
import { createHmac } from "node:crypto";

import type {
  RateLimitDecision,
  RateLimitPort
} from "../security/contracts.js";

export type RedisRateLimitBucket =
  | "api-ip"
  | "api-identity-tenant";

export interface RedisRateLimitPolicy {
  /** Approved maximum requests in one fixed window. No default is supplied. */
  readonly maxRequests: number;
  /** Approved fixed-window duration in milliseconds. */
  readonly windowMs: number;
}

export interface RedisRateLimitPolicies {
  readonly "api-ip": RedisRateLimitPolicy;
  readonly "api-identity-tenant": RedisRateLimitPolicy;
}

export interface RedisEvalOptions {
  readonly keys: readonly string[];
  readonly arguments: readonly string[];
}

/** Structural subset implemented by the Redis 8 node client. */
export interface RedisEvalClient {
  eval(script: string, options: RedisEvalOptions): Promise<unknown>;
}

export interface RedisRateLimitOptions {
  /** Secret supplied by the runtime secret manager, never stored in source. */
  readonly keySecret: string;
  /** Change this value when rotating keySecret to isolate old key namespaces. */
  readonly keyVersion: string;
  /** Increment when any bucket threshold/window changes to isolate old counters. */
  readonly policyVersion: string;
  /** Explicit policy for both existing API security buckets. */
  readonly policies: RedisRateLimitPolicies;
}

const BUCKETS: readonly RedisRateLimitBucket[] = [
  "api-ip",
  "api-identity-tenant"
];

const KEY_VERSION_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$/;
const MAX_RAW_KEY_LENGTH = 2_048;
const MAX_REQUESTS_PER_WINDOW = 1_000_000_000;
const MAX_WINDOW_MS = 7 * 24 * 60 * 60 * 1_000;

/**
 * Detect Unicode C0, DEL and C1 control characters without a control-character
 * regular expression, keeping the check compatible with the strict ESLint rules.
 */
function containsControlCharacters(value: string): boolean {
  for (const character of value) {
    const codePoint = character.codePointAt(0);

    if (
      codePoint !== undefined &&
      (codePoint <= 0x1f ||
        (codePoint >= 0x7f && codePoint <= 0x9f))
    ) {
      return true;
    }
  }

  return false;
}

/**
 * All counter mutation and expiry logic runs atomically inside one Lua call.
 * The client never performs a separate INCR and PEXPIRE round trip.
 */
export const REDIS_RATE_LIMIT_SCRIPT = `
local limit = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])

if not limit or not window_ms or limit < 1 or window_ms < 1 then
  return redis.error_reply('INVALID_RATE_LIMIT_ARGUMENTS')
end

local count = redis.call('INCR', KEYS[1])

if count == 1 then
  redis.call('PEXPIRE', KEYS[1], window_ms)
end

local ttl = redis.call('PTTL', KEYS[1])

if ttl < 0 then
  redis.call('PEXPIRE', KEYS[1], window_ms)
  ttl = redis.call('PTTL', KEYS[1])
end

if ttl < 0 then
  return redis.error_reply('RATE_LIMIT_EXPIRY_UNAVAILABLE')
end

if count > limit then
  return { 0, ttl, count }
end

return { 1, ttl, count }
`.trim();

export class RedisRateLimitUnavailableError extends Error {
  public constructor(cause?: unknown) {
    super(
      "The shared API rate-limit service is unavailable.",
      cause === undefined ? undefined : { cause }
    );
    this.name = "RedisRateLimitUnavailableError";
  }
}

function validatePolicy(
  bucket: RedisRateLimitBucket,
  value: RedisRateLimitPolicy
): RedisRateLimitPolicy {
  if (
    typeof value !== "object" ||
    value === null ||
    !Number.isSafeInteger(value.maxRequests) ||
    value.maxRequests < 1 ||
    value.maxRequests > MAX_REQUESTS_PER_WINDOW ||
    !Number.isSafeInteger(value.windowMs) ||
    value.windowMs < 1_000 ||
    value.windowMs > MAX_WINDOW_MS
  ) {
    throw new TypeError(
      `Invalid explicit Redis rate-limit policy for ${bucket}.`
    );
  }

  return Object.freeze({
    maxRequests: value.maxRequests,
    windowMs: value.windowMs
  });
}

function validateOptions(options: RedisRateLimitOptions): {
  readonly keySecret: string;
  readonly keyVersion: string;
  readonly policyVersion: string;
  readonly policies: RedisRateLimitPolicies;
} {
  if (
    typeof options !== "object" ||
    options === null ||
    typeof options.keySecret !== "string" ||
    Buffer.byteLength(options.keySecret, "utf8") < 32
  ) {
    throw new TypeError(
      "Rate-limit HMAC secret must contain at least 32 UTF-8 bytes."
    );
  }

  if (
    options.keySecret !== options.keySecret.trim() ||
    containsControlCharacters(options.keySecret)
  ) {
    throw new TypeError("Rate-limit HMAC secret has an invalid format.");
  }

  if (
    typeof options.keyVersion !== "string" ||
    !KEY_VERSION_PATTERN.test(options.keyVersion)
  ) {
    throw new TypeError("Rate-limit key version is invalid.");
  }

  if (
    typeof options.policyVersion !== "string" ||
    !KEY_VERSION_PATTERN.test(options.policyVersion)
  ) {
    throw new TypeError("Rate-limit policy version is invalid.");
  }

  if (
    typeof options.policies !== "object" ||
    options.policies === null ||
    !BUCKETS.every((bucket) =>
      Object.prototype.hasOwnProperty.call(options.policies, bucket)
    )
  ) {
    throw new TypeError(
      "Both canonical API rate-limit bucket policies are required."
    );
  }

  return Object.freeze({
    keySecret: options.keySecret,
    keyVersion: options.keyVersion,
    policyVersion: options.policyVersion,
    policies: Object.freeze({
      "api-ip": validatePolicy(
        "api-ip",
        options.policies["api-ip"]
      ),
      "api-identity-tenant": validatePolicy(
        "api-identity-tenant",
        options.policies["api-identity-tenant"]
      )
    })
  });
}

function validateInput(
  input: Parameters<RateLimitPort["consume"]>[0]
): asserts input is {
  readonly bucket: RedisRateLimitBucket;
  readonly key: string;
} {
  if (
    typeof input !== "object" ||
    input === null ||
    !BUCKETS.includes(input.bucket as RedisRateLimitBucket) ||
    typeof input.key !== "string" ||
    input.key.length === 0 ||
    input.key.length > MAX_RAW_KEY_LENGTH ||
    input.key !== input.key.trim() ||
    containsControlCharacters(input.key)
  ) {
    throw new TypeError("Rate-limit key is invalid.");
  }
}

function parseRedisDecision(value: unknown): RateLimitDecision {
  if (
    !Array.isArray(value) ||
    value.length !== 3 ||
    !value.every((item) =>
      typeof item === "number" && Number.isSafeInteger(item)
    )
  ) {
    throw new RedisRateLimitUnavailableError();
  }

  const [allowedValue, ttlMilliseconds, count] = value;

  if (
    (allowedValue !== 0 && allowedValue !== 1) ||
    typeof ttlMilliseconds !== "number" ||
    ttlMilliseconds < 0 ||
    typeof count !== "number" ||
    count < 1
  ) {
    throw new RedisRateLimitUnavailableError();
  }

  if (allowedValue === 1) {
    return { allowed: true };
  }

  return {
    allowed: false,
    retryAfterSeconds: Math.max(
      1,
      Math.ceil(ttlMilliseconds / 1_000)
    )
  };
}

/**
 * Shared, distributed implementation of the existing Fastify RateLimitPort.
 * Raw IP, identity and tenant keys are never written to Redis; the Redis key
 * contains only a versioned HMAC digest.
 */
export class RedisRateLimiter implements RateLimitPort {
  private readonly client: RedisEvalClient;
  private readonly keySecret: string;
  private readonly keyVersion: string;
  private readonly policyVersion: string;
  private readonly policies: RedisRateLimitPolicies;

  public constructor(
    client: RedisEvalClient,
    options: RedisRateLimitOptions
  ) {
    if (
      typeof client !== "object" ||
      client === null ||
      typeof client.eval !== "function"
    ) {
      throw new TypeError("A Redis 8 eval-capable client is required.");
    }

    const validated = validateOptions(options);
    this.client = client;
    this.keySecret = validated.keySecret;
    this.keyVersion = validated.keyVersion;
    this.policyVersion = validated.policyVersion;
    this.policies = validated.policies;
  }

  public async consume(
    input: Parameters<RateLimitPort["consume"]>[0]
  ): Promise<RateLimitDecision> {
    validateInput(input);

    const policy = this.policies[input.bucket];
    const digest = createHmac("sha256", this.keySecret)
      .update(`${input.bucket}\0${input.key}`, "utf8")
      .digest("hex");
    const redisKey = [
      "homio",
      "api-rate-limit",
      this.policyVersion,
      this.keyVersion,
      input.bucket,
      digest
    ].join(":");

    let response: unknown;

    try {
      response = await this.client.eval(REDIS_RATE_LIMIT_SCRIPT, {
        keys: [redisKey],
        arguments: [
          String(policy.maxRequests),
          String(policy.windowMs)
        ]
      });
    } catch (error) {
      throw new RedisRateLimitUnavailableError(error);
    }

    return parseRedisDecision(response);
  }
}
