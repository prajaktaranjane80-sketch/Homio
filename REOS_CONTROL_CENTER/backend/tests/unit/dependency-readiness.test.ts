import { describe, expect, it } from "vitest";

import { buildApp } from "../../src/app.js";
import type { BackendSettings } from "../../src/config/settings.js";

const testSettings: BackendSettings = {
  nodeEnv: "test",
  host: "127.0.0.1",
  port: 0,
  logLevel: "silent",
  requestTimeoutMs: 30_000,
  shutdownTimeoutMs: 10_000
};

describe("dependency-aware readiness", () => {
  it("returns 503 while a required persistence dependency is unavailable", async () => {
    let available = false;

    const runtime = await buildApp(
      testSettings,
      [],
      undefined,
      async () => {
        if (!available) {
          throw new Error("dependency unavailable");
        }
      }
    );

    try {
      runtime.markReady();

      const unavailable = await runtime.server.inject({
        method: "GET",
        url: "/health/ready"
      });

      expect(unavailable.statusCode).toBe(503);
      expect(unavailable.json()).toEqual({
        status: "not_ready"
      });

      available = true;

      const ready = await runtime.server.inject({
        method: "GET",
        url: "/health/ready"
      });

      expect(ready.statusCode).toBe(200);
      expect(ready.json()).toEqual({
        status: "ready"
      });
    } finally {
      runtime.markDraining();
      await runtime.server.close();
    }
  });
});
