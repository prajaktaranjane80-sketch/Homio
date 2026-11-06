import {
  afterEach,
  describe,
  expect,
  it
} from "vitest";

import type { FastifyPluginAsync } from "fastify";

import { buildApp, type AppRuntime } from "../../src/app.js";
import type { BackendSettings } from "../../src/config/settings.js";
import {
  createSecurityRuntime,
  VALID_TEST_TOKEN
} from "../helpers/security-runtime.js";

const testSettings: BackendSettings = {
  nodeEnv: "test",
  host: "127.0.0.1",
  port: 3001,
  logLevel: "silent",
  requestTimeoutMs: 30_000,
  shutdownTimeoutMs: 10_000
};

describe("single Fastify application", () => {
  let runtime: AppRuntime | undefined;

  afterEach(async () => {
    if (runtime !== undefined) {
      runtime.markDraining();
      await runtime.server.close();
      runtime = undefined;
    }
  });

  it("provides an independent liveness endpoint", async () => {
    runtime = await buildApp(testSettings);

    const response = await runtime.server.inject({
      method: "GET",
      url: "/health/live"
    });

    expect(response.statusCode).toBe(200);

    expect(response.json()).toEqual({
      status: "ok"
    });
  });

  it("opens readiness only after the listener lifecycle marks it ready", async () => {
    runtime = await buildApp(testSettings);

    expect(runtime.isReady()).toBe(false);

    const beforeListening = await runtime.server.inject({
      method: "GET",
      url: "/health/ready"
    });

    expect(beforeListening.statusCode).toBe(503);

    expect(beforeListening.json()).toEqual({
      status: "not_ready"
    });

    runtime.markReady();

    expect(runtime.isReady()).toBe(true);

    const readyResponse = await runtime.server.inject({
      method: "GET",
      url: "/health/ready"
    });

    expect(readyResponse.statusCode).toBe(200);

    expect(readyResponse.json()).toEqual({
      status: "ready"
    });

    runtime.markDraining();

    expect(runtime.isReady()).toBe(false);

    const drainingResponse = await runtime.server.inject({
      method: "GET",
      url: "/health/ready"
    });

    expect(drainingResponse.statusCode).toBe(503);

    expect(drainingResponse.json()).toEqual({
      status: "not_ready"
    });
  });

  it("does not become ready again after shutdown begins", async () => {
    runtime = await buildApp(testSettings);

    runtime.markDraining();

    expect(() => runtime?.markReady()).toThrow(
      "Backend cannot become ready after shutdown has started."
    );

    expect(runtime.isReady()).toBe(false);
  });

  it("clears readiness when Fastify closes", async () => {
    runtime = await buildApp(testSettings);

    runtime.markReady();

    expect(runtime.isReady()).toBe(true);

    await runtime.server.close();

    expect(runtime.isReady()).toBe(false);

    runtime = undefined;
  });

  it("returns a safe not-found response", async () => {
    runtime = await buildApp(testSettings);

    const response = await runtime.server.inject({
      method: "GET",
      url: "/not-a-real-route"
    });

    expect(response.statusCode).toBe(404);

    expect(response.json()).toMatchObject({
      statusCode: 404,
      error: "Not Found",
      message: "Route not found."
    });
  });

  it("maps internal errors without exposing implementation details", async () => {
    const failingPlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get(
          "/failure",
          {
            config: {
              homioSecurity: {
                operation: "test.failure"
              }
            }
          },
          async () => {
            throw new Error("internal-private-detail");
          }
        );
      };

    runtime = await buildApp(
      testSettings,
      [failingPlugin],
      createSecurityRuntime()
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/failure",
      headers: {
        authorization: `Bearer ${VALID_TEST_TOKEN}`
      }
    });

    expect(response.statusCode).toBe(500);

    expect(response.body).not.toContain(
      "internal-private-detail"
    );

    expect(response.json()).toMatchObject({
      statusCode: 500,
      error: "Internal Server Error",
      message: "An unexpected server error occurred."
    });
  });

  it("registers versioned public routes only when explicitly marked public", async () => {
    const routePlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get(
          "/foundation-check",
          {
            config: {
              homioSecurity: {
                public: true
              }
            }
          },
          async () => ({
            status: "registered"
          })
        );
      };

    runtime = await buildApp(
      testSettings,
      [routePlugin],
      createSecurityRuntime()
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/foundation-check"
    });

    expect(response.statusCode).toBe(200);

    expect(response.json()).toEqual({
      status: "registered"
    });
  });

  it("refuses to compose public API plugins without B2 security dependencies", async () => {
    const routePlugin: FastifyPluginAsync = async (instance) => {
      instance.get("/unsecured", async () => ({ ok: true }));
    };

    await expect(
      buildApp(testSettings, [routePlugin])
    ).rejects.toThrow(
      "Protected API plugins require the complete B2 security runtime."
    );
  });
});
