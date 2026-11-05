
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

  it("allows an active request to finish before graceful shutdown completes", async () => {
    let signalRequestStarted: () => void = () => undefined;

    const requestStarted = new Promise<void>((resolveStarted) => {
      signalRequestStarted = resolveStarted;
    });

    const slowRoutePlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get("/slow-drain", async () => {
          signalRequestStarted();

          await new Promise<void>((resolveDelay) => {
            setTimeout(resolveDelay, 25);
          });

          return {
            status: "completed"
          };
        });
      };

    const running = await startBackend(
      testSettings,
      [slowRoutePlugin]
    );

    try {
      const address = running.server.server.address();

      if (!address || typeof address === "string") {
        throw new Error(
          "Expected a valid TCP server address"
        );
      }

      const serverAddress = address as AddressInfo;

      const pendingResponse = fetch(
        `http://127.0.0.1:${serverAddress.port}/api/v1/slow-drain`
      );

      await requestStarted;

      const shutdownPromise = running.shutdown("manual");

      expect(running.isReady()).toBe(false);

      const response = await pendingResponse;

      expect(response.status).toBe(200);

      expect(await response.json()).toEqual({
        status: "completed"
      });

      await shutdownPromise;

      expect(running.server.server.listening).toBe(false);
    } finally {
      if (running.server.server.listening) {
        await running.shutdown("manual");
      }
    }
  });
});
