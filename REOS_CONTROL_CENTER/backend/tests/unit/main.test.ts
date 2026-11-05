
import {
  describe,
  expect,
  it
} from "vitest";

import type { AddressInfo } from "node:net";
import type { FastifyPluginAsync } from "fastify";

import { startBackend } from "../../src/main.js";

import type { BackendSettings } from "../../src/config/settings.js";

const testSettings: BackendSettings = {
  nodeEnv: "test",
  host: "127.0.0.1",
  port: 0,
  logLevel: "silent",
  requestTimeoutMs: 30_000,
  shutdownTimeoutMs: 10_000
};

describe("backend startup and shutdown", () => {
  it("starts, serves health, and shuts down gracefully", async () => {
    const running = await startBackend(testSettings);

    try {
      expect(running.server.server.listening).toBe(true);
      expect(running.isReady()).toBe(true);

      const address = running.server.server.address();

      if (!address || typeof address === "string") {
        throw new Error(
          "Expected a valid TCP server address"
        );
      }

      const serverAddress = address as AddressInfo;

      const response = await fetch(
        `http://127.0.0.1:${serverAddress.port}/health/ready`
      );

      expect(response.status).toBe(200);

      expect(await response.json()).toEqual({
        status: "ready"
      });

      const firstShutdown = running.shutdown("manual");
      const secondShutdown = running.shutdown("manual");

      expect(secondShutdown).toBe(firstShutdown);
      expect(running.isReady()).toBe(false);

      await firstShutdown;

      expect(running.server.server.listening).toBe(false);
      expect(running.isReady()).toBe(false);
    } finally {
      if (running.server.server.listening) {
        await running.shutdown("manual");
      }
    }
  });

  it("allows an active request to finish and then reaps its idle keep-alive connection", async () => {
    let signalRequestStarted: () => void = () => undefined;
    let releaseActiveRequest: () => void = () => undefined;

    const requestStarted = new Promise<void>((resolveStarted) => {
      signalRequestStarted = resolveStarted;
    });

    const activeRequestGate = new Promise<void>((resolveRequest) => {
      releaseActiveRequest = resolveRequest;
    });

    const slowRoutePlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get("/slow-drain", async () => {
          signalRequestStarted();

          await activeRequestGate;

          return {
            status: "completed"
          };
        });
      };

    const running = await startBackend(
      testSettings,
      [slowRoutePlugin]
    );

    let pendingResponse: Promise<Response> | undefined;
    let shutdownPromise: Promise<void> | undefined;

    try {
      const address = running.server.server.address();

      if (!address || typeof address === "string") {
        throw new Error(
          "Expected a valid TCP server address"
        );
      }

      const serverAddress = address as AddressInfo;

      pendingResponse = fetch(
        `http://127.0.0.1:${serverAddress.port}/api/v1/slow-drain`,
        {
          signal: AbortSignal.timeout(3_000)
        }
      );

      // Detect a route miss or early response instead of waiting forever
      // for a handler-start signal that will never arrive.
      const requestStartResult = await Promise.race([
        requestStarted.then(() => "started" as const),
        pendingResponse.then((response) => ({
          response
        }))
      ]);

      if (requestStartResult !== "started") {
        await requestStartResult.response.arrayBuffer();

        throw new Error(
          "Expected the slow-drain route handler to start, " +
          `but HTTP ${requestStartResult.response.status} returned first.`
        );
      }

      // The request is now confirmed active and blocked on the test gate.
      shutdownPromise = running.shutdown("manual");

      expect(running.isReady()).toBe(false);

      let shutdownSettled = false;

      void shutdownPromise.then(() => {
        shutdownSettled = true;
      });

      // Shutdown must remain pending while the handler is still active.
      await new Promise<void>((resolveTurn) => {
        setImmediate(resolveTurn);
      });

      expect(shutdownSettled).toBe(false);

      // Let the in-flight request finish. The server must then reap its
      // newly idle keep-alive connection without waiting for keepAliveTimeout.
      releaseActiveRequest();

      const response = await pendingResponse;

      expect(response.status).toBe(200);

      expect(await response.json()).toEqual({
        status: "completed"
      });

      await shutdownPromise;

      expect(running.server.server.listening).toBe(false);
      expect(running.isReady()).toBe(false);
    } finally {
      // Never leave the test handler blocked if an assertion fails.
      releaseActiveRequest();

      if (shutdownPromise !== undefined) {
        await shutdownPromise.catch(() => undefined);
      } else if (running.server.server.listening) {
        await running.shutdown("manual").catch(() => undefined);
      }

      if (pendingResponse !== undefined) {
        await pendingResponse.catch(() => undefined);
      }
    }
  });
});
