
import {
  afterEach,
  describe,
  expect,
  it
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
  TEST_PRINCIPAL,
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

const PRINCIPAL_KEYS = [
  "audiences",
  "clientId",
  "issuer",
  "subject",
  "tokenId"
].sort();

const CONTEXT_KEYS = [
  "accountId",
  "identityId",
  "membershipId",
  "membershipRevision",
  "organizationId",
  "tenantId",
  "tenantRevision"
].sort();

describe("B2 adapter trust-boundary normalization", () => {
  let runtime: AppRuntime | undefined;

  afterEach(async () => {
    if (runtime !== undefined) {
      runtime.markDraining();
      await runtime.server.close();
      runtime = undefined;
    }
  });

  it("refuses production readiness when only health endpoints are mounted", async () => {
    await expect(
      buildApp({
        ...testSettings,
        nodeEnv: "production"
      })
    ).rejects.toThrow(
      "Production backend cannot become ready without at least one registered /api/v1 route."
    );
  });

  it("refuses production readiness when an API plugin registers no routes", async () => {
    const emptyPlugin: FastifyPluginAsync = async () => undefined;

    await expect(
      buildApp(
        {
          ...testSettings,
          nodeEnv: "production"
        },
        [emptyPlugin],
        createSecurityRuntime()
      )
    ).rejects.toThrow(
      "Production backend cannot become ready without at least one registered /api/v1 route."
    );
  });

  it("strips non-contract identity claims and freezes principal and tenant snapshots", async () => {
    const auditRecords: SecurityAuditEvent[] = [];
    const observations = {
      principalKeys: [] as string[],
      principalFrozen: false,
      audiencesFrozen: false,
      contextKeysAtAuthorization: [] as string[],
      contextFrozenAtAuthorization: false
    };

    const adapterPrincipal = {
      ...TEST_PRINCIPAL,
      email: "private@example.test",
      accessToken: "must-never-cross-the-verifier-boundary",
      phoneNumber: "+10000000000"
    };

    const adapterContext = {
      ...TEST_CONTEXT,
      email: "private@example.test",
      roles: ["platform-admin"],
      profile: {
        phoneNumber: "+10000000000"
      }
    };

    const overrides: Partial<BackendSecurityRuntime> = {
      tokenVerifier: {
        verifyAccessToken: async () =>
          adapterPrincipal as never
      },
      sessionValidator: {
        isSessionActive: async ({ principal }) => {
          observations.principalKeys =
            Object.keys(principal).sort();
          observations.principalFrozen =
            Object.isFrozen(principal);
          observations.audiencesFrozen =
            Object.isFrozen(principal.audiences);

          return true;
        }
      },
      contextResolver: {
        resolve: async () =>
          adapterContext as never
      },
      authorization: {
        authorize: async ({ context }) => {
          observations.contextKeysAtAuthorization =
            Object.keys(context).sort();
          observations.contextFrozenAtAuthorization =
            Object.isFrozen(context);

          return {
            allowed: true,
            reasonCode: "ALLOWED"
          };
        }
      },
      audit: {
        record: async (event) => {
          auditRecords.push(event);
        }
      }
    };

    const protectedPlugin: FastifyPluginAsync =
      async (instance) => {
        instance.get(
          "/trusted-context",
          {
            config: {
              homioSecurity: {
                operation: "identity.context.read"
              }
            }
          },
          async (request) => ({
            contextKeys: Object.keys(
              request.securityContext ?? {}
            ).sort(),
            contextFrozen: Object.isFrozen(
              request.securityContext
            ),
            email: (
              request.securityContext as
                | (typeof TEST_CONTEXT & { email?: string })
                | null
            )?.email ?? null
          })
        );
      };

    runtime = await buildApp(
      testSettings,
      [protectedPlugin],
      createSecurityRuntime(overrides)
    );

    const response = await runtime.server.inject({
      method: "GET",
      url: "/api/v1/trusted-context",
      headers: {
        authorization: `Bearer ${VALID_TEST_TOKEN}`
      }
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      contextKeys: CONTEXT_KEYS,
      contextFrozen: true,
      email: null
    });

    expect(observations.principalKeys).toEqual(PRINCIPAL_KEYS);
    expect(observations.principalFrozen).toBe(true);
    expect(observations.audiencesFrozen).toBe(true);
    expect(observations.contextKeysAtAuthorization).toEqual(
      CONTEXT_KEYS
    );
    expect(observations.contextFrozenAtAuthorization).toBe(true);

    const serializedAudit = JSON.stringify(auditRecords);

    expect(serializedAudit).not.toContain("private@example.test");
    expect(serializedAudit).not.toContain("must-never-cross-the-verifier-boundary");
    expect(serializedAudit).not.toContain("+10000000000");
    expect(response.body).not.toContain("private@example.test");
    expect(response.body).not.toContain("platform-admin");
  });
});
