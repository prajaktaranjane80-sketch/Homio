import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import type { FastifyPluginAsync } from "fastify";

import { buildApp, type AppRuntime } from "../../src/app.js";
import type { BackendSettings } from "../../src/config/settings.js";
import type {
  BackendSecurityRuntime,
  SecurityAuditEvent
} from "../../src/security/contracts.js";
import {
  createSecurityRuntime,
  TEST_CONTEXT,
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

function protectedPlugin(
  options: {
    readonly security?: {
      readonly operation: string;
    } | undefined;
    readonly bodySchema?: Record<string, unknown>;
  } = { security: { operation: "inventory.read" } }
): FastifyPluginAsync {
  return async (instance) => {
    instance.get(
      "/protected",
      {
        config: options.security === undefined
          ? {}
          : { homioSecurity: options.security }
      },
      async (request) => ({
        allowed: true,
        identityId: request.securityContext?.identityId ?? null
      })
    );

    instance.get(
      "/tenant/:tenantId/resources/:resourceId",
      {
        config: {
          homioSecurity: {
            operation: "inventory.read",
            requestedTenantId: (request) =>
              (request.params as { tenantId: string }).tenantId,
            resourceId: (request) =>
              (request.params as { resourceId: string }).resourceId
          }
        }
      },
      async (request) => ({
        tenantId: request.securityContext?.tenantId ?? null
      })
    );

    instance.post(
      "/validated",
      {
        schema: {
          body: options.bodySchema ?? {
            type: "object",
            additionalProperties: false,
            required: ["name"],
            properties: {
              name: { type: "string", minLength: 1, maxLength: 80 }
            }
          }
        },
        config: {
          homioSecurity: {
            operation: "leads.create"
          }
        }
      },
      async () => ({ created: true })
    );
  };
}

describe("B2 Fastify API security boundary", () => {
  let runtime: AppRuntime | undefined;

  afterEach(async () => {
    if (runtime !== undefined) {
      runtime.markDraining();
      await runtime.server.close();
      runtime = undefined;
    }
    vi.restoreAllMocks();
  });

  it("rejects cookie-only authentication and requires an explicit bearer token", async () => {
    const verifyAccessToken = vi.fn(async () => {
      throw new Error("must not be called");
    });
    const security = createSecurityRuntime({
      tokenVerifier: { verifyAccessToken }
    });
    runtime = await buildApp(testSettings, [protectedPlugin()], security);

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: {
        cookie: "homio_session=untrusted-cookie"
      }
    });

    expect(response.statusCode).toBe(401);
    expect(response.headers["www-authenticate"]).toContain("Bearer");
    expect(response.headers["cache-control"]).toBe("no-store, private");
    expect(response.body).not.toContain("untrusted-cookie");
    expect(verifyAccessToken).not.toHaveBeenCalled();
  });

  it("runs IP throttling, token verification, session, context, authorization and audit before the handler", async () => {
    const events: string[] = [];
    const auditRecords: SecurityAuditEvent[] = [];
    const security = createSecurityRuntime({
      rateLimiter: {
        consume: async ({ bucket }) => {
          events.push(`rate:${bucket}`);
          return { allowed: true };
        }
      },
      tokenVerifier: {
        verifyAccessToken: async () => {
          events.push("token");
          return {
            issuer: "https://identity.example.test/",
            subject: "provider-subject-001",
            audiences: ["homio-api"]
          };
        }
      },
      sessionValidator: {
        isSessionActive: async () => {
          events.push("session");
          return true;
        }
      },
      contextResolver: {
        resolve: async () => {
          events.push("context");
          return TEST_CONTEXT;
        }
      },
      authorization: {
        authorize: async () => {
          events.push("authorize");
          return { allowed: true, reasonCode: "ALLOWED" };
        }
      },
      audit: {
        record: async (event) => {
          auditRecords.push(event);
          events.push(`audit:${event.eventType}`);
        }
      }
    });

    const plugin: FastifyPluginAsync = async (instance) => {
      instance.get(
        "/protected",
        {
          config: {
            homioSecurity: { operation: "inventory.read" }
          }
        },
        async (request) => {
          events.push("handler");
          return {
            identityId: request.securityContext?.identityId,
            tenantId: request.securityContext?.tenantId
          };
        }
      );
    };

    runtime = await buildApp(testSettings, [plugin], security);
    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: {
        authorization: `Bearer ${VALID_TEST_TOKEN}`,
        "x-request-id": "attacker-controlled-request-id"
      }
    });

    expect(response.statusCode).toBe(200);
    expect(response.json().requestId).not.toBe("attacker-controlled-request-id");
    expect(response.json()).toEqual({
      identityId: TEST_CONTEXT.identityId,
      tenantId: TEST_CONTEXT.tenantId
    });
    expect(events).toEqual([
      "rate:api-ip",
      "token",
      "session",
      "context",
      "rate:api-identity-tenant",
      "authorize",
      "audit:API_ACCESS_ALLOWED",
      "handler"
    ]);
    expect(auditRecords).toHaveLength(1);
    expect(auditRecords[0]).toMatchObject({
      eventType: "API_ACCESS_ALLOWED",
      actorIdentityId: TEST_CONTEXT.identityId,
      tenantId: TEST_CONTEXT.tenantId,
      operation: "inventory.read"
    });
    const auditJson = JSON.stringify(auditRecords[0]);
    expect(auditJson).not.toContain(VALID_TEST_TOKEN);
    expect(auditJson).not.toContain("provider-subject-001");
    expect(auditJson).not.toContain("email");
    expect(auditJson).not.toContain("ip");
  });

  it("rejects revoked or expired sessions before resolving tenant context", async () => {
    const resolve = vi.fn(async () => TEST_CONTEXT);
    runtime = await buildApp(
      testSettings,
      [protectedPlugin()],
      createSecurityRuntime({
        sessionValidator: { isSessionActive: async () => false },
        contextResolver: { resolve }
      })
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` }
    });

    expect(response.statusCode).toBe(401);
    expect(resolve).not.toHaveBeenCalled();
  });

  it("denies missing tenant membership and never accepts client tenant headers as trusted context", async () => {
    const resolve = vi.fn(async () => null);
    runtime = await buildApp(
      testSettings,
      [protectedPlugin()],
      createSecurityRuntime({ contextResolver: { resolve } })
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: `/api/v1/tenant/${TEST_CONTEXT.tenantId}/resources/property-01`,
      headers: {
        authorization: `Bearer ${VALID_TEST_TOKEN}`,
        "x-tenant-id": "66666666-6666-4666-8666-666666666666"
      }
    });

    expect(response.statusCode).toBe(403);
    expect(resolve).toHaveBeenCalledWith({
      principal: expect.objectContaining({ subject: "provider-subject-001" }),
      requestedTenantId: TEST_CONTEXT.tenantId
    });
  });

  it("denies resource/action authorization without invoking the route handler", async () => {
    runtime = await buildApp(
      testSettings,
      [protectedPlugin()],
      createSecurityRuntime({
        authorization: {
          authorize: async () => ({
            allowed: false,
            reasonCode: "RESOURCE_NOT_OWNED"
          })
        }
      })
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` }
    });

    expect(response.statusCode).toBe(403);
    expect(response.body).not.toContain("RESOURCE_NOT_OWNED");
  });

  it("fails closed when session, tenant or authorization dependencies fail", async () => {
    const failureCases: Array<{
      readonly security: Partial<BackendSecurityRuntime>;
      readonly expectedStatus: number;
    }> = [
      {
        security: {
          sessionValidator: {
            isSessionActive: async () => {
              throw new Error("private session store detail");
            }
          }
        },
        expectedStatus: 503
      },
      {
        security: {
          contextResolver: {
            resolve: async () => {
              throw new Error("private identity store detail");
            }
          }
        },
        expectedStatus: 503
      },
      {
        security: {
          authorization: {
            authorize: async () => {
              throw new Error("private policy store detail");
            }
          }
        },
        expectedStatus: 503
      }
    ];

    for (const failureCase of failureCases) {
      runtime = await buildApp(
        testSettings,
        [protectedPlugin()],
        createSecurityRuntime(failureCase.security)
      );

      const response = await runtime.server.inject({
        method: "GET",
        url: "/api/v1/protected",
        headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` }
      });

      expect(response.statusCode).toBe(failureCase.expectedStatus);
      expect(response.body).not.toContain("private");

      runtime.markDraining();
      await runtime.server.close();
      runtime = undefined;
    }
  });

  it("enforces IP and tenant-identity rate-limit decisions", async () => {
    const security = createSecurityRuntime({
      rateLimiter: {
        consume: async ({ bucket }) => ({
          allowed: bucket !== "api-identity-tenant",
          retryAfterSeconds: 17
        })
      }
    });
    runtime = await buildApp(testSettings, [protectedPlugin()], security);

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` }
    });

    expect(response.statusCode).toBe(429);
    expect(response.headers["retry-after"]).toBe("17");
  });

  it("fails closed when audit persistence is unavailable", async () => {
    runtime = await buildApp(
      testSettings,
      [protectedPlugin()],
      createSecurityRuntime({
        audit: {
          record: async () => {
            throw new Error("private audit store detail");
          }
        }
      })
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/protected",
      headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` }
    });

    expect(response.statusCode).toBe(503);
    expect(response.body).not.toContain("private audit store detail");
  });

  it("rejects missing route security metadata and allows only explicit public routes", async () => {
    await expect(
      buildApp(
        testSettings,
        [protectedPlugin({ security: undefined })],
        createSecurityRuntime()
      )
    ).rejects.toThrow(
      "Every /api/v1 route must declare a valid B2 security policy."
    );

    const publicPlugin: FastifyPluginAsync = async (instance) => {
      instance.get(
        "/public-status",
        { config: { homioSecurity: { public: true } } },
        async () => ({ status: "public" })
      );
    };

    runtime = await buildApp(
      testSettings,
      [publicPlugin],
      createSecurityRuntime()
    );

    const publicResponse = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/public-status"
    });
    expect(publicResponse.statusCode).toBe(200);
    expect(publicResponse.json()).toEqual({ status: "public" });
  });

  it("uses Fastify JSON schema validation after authentication", async () => {
    runtime = await buildApp(testSettings, [protectedPlugin()], createSecurityRuntime());

    const unauthenticated = await runtime.server.inject({
      method: "POST",
      url: "/api/v1/validated",
      payload: {}
    });
    expect(unauthenticated.statusCode).toBe(401);

    const invalidPayload = await runtime.server.inject({
      method: "POST",
      url: "/api/v1/validated",
      headers: { authorization: `Bearer ${VALID_TEST_TOKEN}` },
      payload: {}
    });
    expect(invalidPayload.statusCode).toBe(400);
    expect(invalidPayload.body).not.toContain("test-bearer-token");
  });
});
