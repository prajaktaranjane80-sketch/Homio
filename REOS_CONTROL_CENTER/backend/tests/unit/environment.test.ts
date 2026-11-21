
import { describe, expect, it } from "vitest";

import {
  ConfigurationError,
  loadSettings
} from "../../src/config/environment.js";

const PRODUCTION_POSTGRES_URL =
  "postgresql://homio_app:db-secret-value@db.example.test:5432/homio";

const PRODUCTION_REDIS_URL =
  "rediss://homio_app:redis-secret-value@redis.example.test:6380/0";

describe("backend runtime configuration", () => {
  it("loads safe development defaults without requiring external services", () => {
    const settings = loadSettings(
      {} as NodeJS.ProcessEnv
    );

    expect(settings).toEqual({
      nodeEnv: "development",
      host: "127.0.0.1",
      port: 3001,
      logLevel: "info",
      requestTimeoutMs: 30_000,
      shutdownTimeoutMs: 10_000
    });
  });

  it("accepts valid production configuration with TLS-protected services", () => {
    const settings = loadSettings({
      NODE_ENV: "production",
      HOMIO_BACKEND_HOST: "127.0.0.1",
      HOMIO_BACKEND_PORT: "8080",
      HOMIO_LOG_LEVEL: "warn",
      HOMIO_REQUEST_TIMEOUT_MS: "15000",
      HOMIO_SHUTDOWN_TIMEOUT_MS: "5000",
      HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
      HOMIO_REDIS_URL: PRODUCTION_REDIS_URL
    } as NodeJS.ProcessEnv);

    expect(settings).toMatchObject({
      nodeEnv: "production",
      host: "127.0.0.1",
      port: 8080,
      logLevel: "warn",
      requestTimeoutMs: 15_000,
      shutdownTimeoutMs: 5_000,
      postgres: {
        connectionString: PRODUCTION_POSTGRES_URL,
        sslMode: "verify-full",
        poolMax: 10,
        connectionTimeoutMs: 5_000,
        idleTimeoutMs: 30_000,
        statementTimeoutMs: 15_000
      },
      redis: {
        url: PRODUCTION_REDIS_URL,
        connectTimeoutMs: 5_000
      }
    });
  });

  it("accepts valid DNS and IPv6 bind hosts", () => {
    expect(
      loadSettings({
        HOMIO_BACKEND_HOST: "localhost"
      } as NodeJS.ProcessEnv).host
    ).toBe("localhost");

    expect(
      loadSettings({
        HOMIO_BACKEND_HOST: "::1"
      } as NodeJS.ProcessEnv).host
    ).toBe("::1");
  });

  it("rejects invalid runtime values together without exposing URL secrets", () => {
    const postgresSecret = "postgres-secret-must-not-leak";
    const redisSecret = "redis-secret-must-not-leak";

    try {
      loadSettings({
        NODE_ENV: "invalid",
        HOMIO_BACKEND_HOST: "https://example.com",
        HOMIO_BACKEND_PORT: "70000",
        HOMIO_LOG_LEVEL: "verbose",
        HOMIO_REQUEST_TIMEOUT_MS: "-1",
        HOMIO_SHUTDOWN_TIMEOUT_MS: "999999",
        HOMIO_POSTGRES_URL:
          `postgresql://app:${postgresSecret}@db.invalid:5432/app`,
        HOMIO_REDIS_URL:
          `redis://app:${redisSecret}@redis.invalid:6379`
      } as NodeJS.ProcessEnv);

      throw new Error(
        "Expected configuration validation to fail"
      );
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigurationError);

      const configurationError = error as ConfigurationError;

      expect(configurationError.issues).toHaveLength(6);
      expect(configurationError.message).toContain("NODE_ENV");
      expect(configurationError.message).toContain("HOMIO_BACKEND_HOST");
      expect(configurationError.message).toContain("HOMIO_BACKEND_PORT");
      expect(configurationError.message).toContain("HOMIO_LOG_LEVEL");
      expect(configurationError.message).not.toContain(postgresSecret);
      expect(configurationError.message).not.toContain(redisSecret);
    }
  });

  it("rejects malformed bind hosts", () => {
    const invalidHosts = [
      "",
      "  ",
      " localhost ",
      "https://localhost",
      "localhost/path",
      "bad_host",
      "-invalid.example",
      "invalid-.example",
      "999.999.999.999",
      "::not-an-ip"
    ];

    for (const host of invalidHosts) {
      expect(() =>
        loadSettings({
          HOMIO_BACKEND_HOST: host
        } as NodeJS.ProcessEnv)
      ).toThrow(ConfigurationError);
    }
  });

  it("rejects a non-integer port", () => {
    expect(() =>
      loadSettings({
        HOMIO_BACKEND_PORT: "3000.5"
      } as NodeJS.ProcessEnv)
    ).toThrow(ConfigurationError);
  });

  it("requires both PostgreSQL and Redis endpoints in production", () => {
    expect(() =>
      loadSettings({
        NODE_ENV: "production"
      } as NodeJS.ProcessEnv)
    ).toThrowError(/HOMIO_POSTGRES_URL.*HOMIO_REDIS_URL/s);
  });

  it("rejects plaintext PostgreSQL TLS mode in production", () => {
    expect(() =>
      loadSettings({
        NODE_ENV: "production",
        HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
        HOMIO_REDIS_URL: PRODUCTION_REDIS_URL,
        HOMIO_POSTGRES_SSL_MODE: "disable"
      } as NodeJS.ProcessEnv)
    ).toThrowError(
      /HOMIO_POSTGRES_SSL_MODE must be verify-full in production/
    );
  });

  it("rejects plaintext Redis in production", () => {
    expect(() =>
      loadSettings({
        NODE_ENV: "production",
        HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
        HOMIO_REDIS_URL:
          "redis://homio_app:redis-secret-value@redis.example.test:6379/0"
      } as NodeJS.ProcessEnv)
    ).toThrowError(
      /HOMIO_REDIS_URL must use rediss:\/\/ TLS in production/
    );
  });

  it("rejects PostgreSQL URL TLS parameters that could override verified TLS settings", () => {
    expect(() =>
      loadSettings({
        NODE_ENV: "production",
        HOMIO_POSTGRES_URL:
          `${PRODUCTION_POSTGRES_URL}?sslmode=require`,
        HOMIO_REDIS_URL: PRODUCTION_REDIS_URL
      } as NodeJS.ProcessEnv)
    ).toThrowError(/must not contain sslmode/);
  });

  it("rejects Redis URL query options instead of accepting unreviewed client settings", () => {
    expect(() =>
      loadSettings({
        NODE_ENV: "production",
        HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
        HOMIO_REDIS_URL:
          `${PRODUCTION_REDIS_URL}?socket_timeout=1`
      } as NodeJS.ProcessEnv)
    ).toThrowError(
      /HOMIO_REDIS_URL query parameters are not accepted/
    );
  });

  it("validates service pool limits and timeout bounds", () => {
    expect(() =>
      loadSettings({
        HOMIO_POSTGRES_URL:
          "postgresql://app@localhost:5432/homio",
        HOMIO_POSTGRES_POOL_MAX: "0"
      } as NodeJS.ProcessEnv)
    ).toThrowError(/HOMIO_POSTGRES_POOL_MAX/);

    expect(() =>
      loadSettings({
        HOMIO_REDIS_URL: "redis://localhost:6379",
        HOMIO_REDIS_CONNECT_TIMEOUT_MS: "999999"
      } as NodeJS.ProcessEnv)
    ).toThrowError(/HOMIO_REDIS_CONNECT_TIMEOUT_MS/);
  });

  it("accepts custom CA certificates only when they contain complete PEM blocks", () => {
    const certificate = [
      "-----BEGIN CERTIFICATE-----",
      "ZmFrZS1jZXJ0aWZpY2F0ZS1kYXRh",
      "-----END CERTIFICATE-----"
    ].join("\n");

    const settings = loadSettings({
      NODE_ENV: "production",
      HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
      HOMIO_REDIS_URL: PRODUCTION_REDIS_URL,
      HOMIO_POSTGRES_CA_CERT: certificate,
      HOMIO_REDIS_CA_CERT: certificate
    } as NodeJS.ProcessEnv);

    expect(settings).toMatchObject({
      postgres: { caCertificate: certificate },
      redis: { caCertificate: certificate }
    });

    expect(() =>
      loadSettings({
        NODE_ENV: "production",
        HOMIO_POSTGRES_URL: PRODUCTION_POSTGRES_URL,
        HOMIO_REDIS_URL: PRODUCTION_REDIS_URL,
        HOMIO_POSTGRES_CA_CERT: "not-a-certificate"
      } as NodeJS.ProcessEnv)
    ).toThrowError(/HOMIO_POSTGRES_CA_CERT/);
  });

  it("allows explicitly configured local services in development", () => {
    const settings = loadSettings({
      HOMIO_POSTGRES_URL:
        "postgresql://homio@127.0.0.1:5432/homio",
      HOMIO_REDIS_URL: "redis://127.0.0.1:6379/0"
    } as NodeJS.ProcessEnv);

    expect(settings).toMatchObject({
      nodeEnv: "development",
      postgres: {
        sslMode: "disable",
        connectionString:
          "postgresql://homio@127.0.0.1:5432/homio"
      },
      redis: {
        url: "redis://127.0.0.1:6379/0"
      }
    });
  });
});
