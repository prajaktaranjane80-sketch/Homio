
import { describe, expect, it } from "vitest";

import {
  ConfigurationError,
  loadSettings
} from "../../src/config/environment.js";

describe("backend runtime configuration", () => {
  it("loads safe development defaults", () => {
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

  it("accepts valid explicit configuration", () => {
    const settings = loadSettings({
      NODE_ENV: "production",
      HOMIO_BACKEND_HOST: "127.0.0.1",
      HOMIO_BACKEND_PORT: "8080",
      HOMIO_LOG_LEVEL: "warn",
      HOMIO_REQUEST_TIMEOUT_MS: "15000",
      HOMIO_SHUTDOWN_TIMEOUT_MS: "5000"
    } as NodeJS.ProcessEnv);

    expect(settings).toMatchObject({
      nodeEnv: "production",
      host: "127.0.0.1",
      port: 8080,
      logLevel: "warn",
      requestTimeoutMs: 15_000,
      shutdownTimeoutMs: 5_000
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

  it("rejects invalid runtime values together", () => {
    try {
      loadSettings({
        NODE_ENV: "invalid",
        HOMIO_BACKEND_HOST: "https://example.com",
        HOMIO_BACKEND_PORT: "70000",
        HOMIO_LOG_LEVEL: "verbose",
        HOMIO_REQUEST_TIMEOUT_MS: "-1",
        HOMIO_SHUTDOWN_TIMEOUT_MS: "999999"
      } as NodeJS.ProcessEnv);

      throw new Error(
        "Expected configuration validation to fail"
      );
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigurationError);

      const configurationError =
        error as ConfigurationError;

      expect(configurationError.issues).toHaveLength(6);

      expect(configurationError.message).toContain(
        "NODE_ENV"
      );

      expect(configurationError.message).toContain(
        "HOMIO_BACKEND_HOST"
      );

      expect(configurationError.message).toContain(
        "HOMIO_BACKEND_PORT"
      );

      expect(configurationError.message).toContain(
        "HOMIO_LOG_LEVEL"
      );
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
});
