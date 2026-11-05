import {
  afterEach,
  describe,
  expect,
  it
} from "vitest";

import type { FastifyPluginAsync } from "fastify";

import { buildApp, type AppRuntime } from "../../src/app.js";

import type { BackendSettings } from "../../src/config/settings.js";

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
      await runtime.server.close();
      runtime = undefined;
    }
  });

  it("provides a live endpoint", async () => {
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

  it("reports readiness only while accepting traffic", async () => {
    runtime = await buildApp(testSettings);

    const readyResponse = await runtime.server.inject({
      method: "GET",
      url: "/health/ready"
    });

    expect(readyResponse.statusCode).toBe(200);

    expect(readyResponse.json()).toEqual({
      status: "ready"
    });

    runtime.markDraining();

    const drainingResponse =
      await runtime.server.inject({
        method: "GET",
        url: "/health/ready"
      });

    expect(drainingResponse.statusCode).toBe(503);

    expect(drainingResponse.json()).toEqual({
      status: "not_ready"
    });

    expect(runtime.isReady()).toBe(false);
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
        instance.get("/failure", async () => {
          throw new Error("internal-private-detail");
        });
      };

    runtime = await buildApp(
      testSettings,
      [failingPlugin]
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/failure"
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

  it("registers versioned routes under the v1 boundary", async () => {
    const routePlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get("/foundation-check", async () => ({
          status: "registered"
        }));
      };

    runtime = await buildApp(
      testSettings,
      [routePlugin]
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
});
