
import { describe, expect, it, vi } from "vitest";

import {
  RedisRateLimitUnavailableError,
  RedisRateLimiter
} from "../../src/persistence/redis-rate-limit.js";
import type {
  RedisEvalClient,
  RedisRateLimitOptions
} from "../../src/persistence/redis-rate-limit.js";

const VALID_OPTIONS: RedisRateLimitOptions = {
  keySecret: "test-only-rate-limit-key-secret-32-bytes-minimum",
  keyVersion: "k1",
  policyVersion: "p1",
  policies: {
    "api-ip": {
      maxRequests: 120,
      windowMs: 60_000
    },
    "api-identity-tenant": {
      maxRequests: 60,
      windowMs: 60_000
    }
  }
};

function makeClient(result: unknown = [1, 60_000, 1]): {
  readonly client: RedisEvalClient;
  readonly eval: ReturnType<typeof vi.fn>;
  readonly calls: {
    readonly keys: readonly string[];
    readonly arguments: readonly string[];
  }[];
  readonly scripts: string[];
} {
  const calls: {
    readonly keys: readonly string[];
    readonly arguments: readonly string[];
  }[] = [];
  const scripts: string[] = [];

  const evaluate = vi.fn(async (
    script: string,
    options: {
      readonly keys: readonly string[];
      readonly arguments: readonly string[];
    }
  ) => {
    scripts.push(script);
    calls.push(options);
    return result;
  });

  const client: RedisEvalClient = {
    eval: evaluate
  };

  return {
    client,
    eval: evaluate,
    calls,
    scripts
  };
}

describe("shared Redis API rate limiter", () => {
  it("uses atomic Redis evaluation and never exposes the raw IP key", async () => {
    const fixture = makeClient([1, 60_000, 1]);
    const limiter = new RedisRateLimiter(fixture.client, VALID_OPTIONS);

    const result = await limiter.consume({
      bucket: "api-ip",
      key: "203.0.113.21"
    });

    expect(result).toEqual({ allowed: true });
    expect(fixture.eval).toHaveBeenCalledTimes(1);

    const script = fixture.scripts[0];
    const options = fixture.calls[0];

    if (script === undefined || options === undefined) {
      throw new Error("Redis evaluation was not captured.");
    }

    expect(script).toContain("redis.call('INCR'");
    expect(options.keys).toHaveLength(1);
    expect(options.keys[0]).toContain(
      "homio:api-rate-limit:p1:k1:api-ip:"
    );
    expect(options.keys[0]).not.toContain("203.0.113.21");
    expect(options.arguments).toEqual(["120", "60000"]);
  });

  it("applies a different approved policy to the identity-tenant bucket", async () => {
    const fixture = makeClient([1, 60_000, 1]);
    const limiter = new RedisRateLimiter(fixture.client, VALID_OPTIONS);

    await limiter.consume({
      bucket: "api-identity-tenant",
      key: "11111111-1111-4111-8111-111111111111:22222222-2222-4222-8222-222222222222"
    });

    const options = fixture.calls[0];

    if (options === undefined) {
      throw new Error("Redis evaluation was not captured.");
    }

    expect(options.keys[0]).toContain(
      "homio:api-rate-limit:p1:k1:api-identity-tenant:"
    );
    expect(options.arguments).toEqual(["60", "60000"]);
  });

  it("returns bounded retry-after seconds for a denied request", async () => {
    const fixture = makeClient([0, 1_001, 121]);
    const limiter = new RedisRateLimiter(fixture.client, VALID_OPTIONS);

    const result = await limiter.consume({
      bucket: "api-ip",
      key: "203.0.113.21"
    });

    expect(result).toEqual({
      allowed: false,
      retryAfterSeconds: 2
    });
  });

  it("rejects malformed and control-character caller keys without contacting Redis", async () => {
    const fixture = makeClient();
    const limiter = new RedisRateLimiter(fixture.client, VALID_OPTIONS);
    const invalidKeys = [
      " ",
      "ip\u0000key",
      "ip\nkey",
      "ip\u007fkey",
      "ip\u0085key"
    ];

    for (const key of invalidKeys) {
      await expect(
        limiter.consume({ bucket: "api-ip", key })
      ).rejects.toThrow("Rate-limit key is invalid.");
    }

    expect(fixture.eval).not.toHaveBeenCalled();
  });

  it("fails closed when Redis is unavailable", async () => {
    const failure = new Error("redis connection failed");

    const client: RedisEvalClient = {
      eval: vi.fn(async () => {
        throw failure;
      })
    };

    const limiter = new RedisRateLimiter(client, VALID_OPTIONS);

    await expect(
      limiter.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      })
    ).rejects.toBeInstanceOf(RedisRateLimitUnavailableError);
  });

  it("fails closed when Redis returns an invalid result", async () => {
    const fixture = makeClient(["allow", "soon", "many"]);
    const limiter = new RedisRateLimiter(fixture.client, VALID_OPTIONS);

    await expect(
      limiter.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      })
    ).rejects.toBeInstanceOf(RedisRateLimitUnavailableError);
  });

  it("requires both explicit bucket policies and a strong key secret", () => {
    const fixture = makeClient();

    expect(() => new RedisRateLimiter(fixture.client, {
      ...VALID_OPTIONS,
      keySecret: "short"
    })).toThrow(
      "Rate-limit HMAC secret must contain at least 32 UTF-8 bytes."
    );

    expect(() => new RedisRateLimiter(fixture.client, {
      ...VALID_OPTIONS,
      keySecret: `${VALID_OPTIONS.keySecret}\u0000`
    })).toThrow(
      "Rate-limit HMAC secret has an invalid format."
    );

    expect(() => new RedisRateLimiter(fixture.client, {
      keySecret: VALID_OPTIONS.keySecret,
      keyVersion: "k1",
      policyVersion: "p1",
      policies: {
        "api-ip": VALID_OPTIONS.policies["api-ip"]
      } as RedisRateLimitOptions["policies"]
    })).toThrow(
      "Both canonical API rate-limit bucket policies are required."
    );
  });

  it("supports concurrent requests through the same shared Redis key", async () => {
    const counts = new Map<string, number>();

    const client: RedisEvalClient = {
      eval: vi.fn(async (_script, commandOptions) => {
        const key = commandOptions.keys[0];

        if (key === undefined) {
          throw new Error("Redis key missing");
        }

        const count = (counts.get(key) ?? 0) + 1;
        counts.set(key, count);

        return [count <= 3 ? 1 : 0, 5_000, count];
      })
    };

    const firstInstance = new RedisRateLimiter(client, {
      ...VALID_OPTIONS,
      policies: {
        ...VALID_OPTIONS.policies,
        "api-ip": {
          maxRequests: 3,
          windowMs: 5_000
        }
      }
    });

    const secondInstance = new RedisRateLimiter(client, {
      ...VALID_OPTIONS,
      policies: {
        ...VALID_OPTIONS.policies,
        "api-ip": {
          maxRequests: 3,
          windowMs: 5_000
        }
      }
    });

    const decisions = await Promise.all([
      firstInstance.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      }),
      secondInstance.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      }),
      firstInstance.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      }),
      secondInstance.consume({
        bucket: "api-ip",
        key: "203.0.113.21"
      })
    ]);

    expect(decisions.map((item) => item.allowed)).toEqual([
      true,
      true,
      true,
      false
    ]);
    expect(counts.size).toBe(1);
  });
});
