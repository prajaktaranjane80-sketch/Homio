import {
  describe,
  expect,
  it
} from "vitest";

import type { AddressInfo } from "node:net";

import { startBackend } from "../../src/main.js";

import type { BackendSettings } from "../../src/config/settings.js";

const testSettings: BackendSettings = {
  nodeEnv: "test",
  host: "127.0.0.1",

  // Port 0 lets the operating system allocate a free test port.
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

      // Concurrent shutdown requests must share one operation.
      expect(secondShutdown).toBe(firstShutdown);

      await firstShutdown;

      expect(running.server.server.listening).toBe(false);
    } finally {
      if (running.server.server.listening) {
        await running.shutdown("manual");
      }
    }
  });
});
