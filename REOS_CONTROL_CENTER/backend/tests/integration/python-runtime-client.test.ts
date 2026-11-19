import {
  afterEach,
  describe,
  expect,
  it
} from "vitest";
import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  PythonRuntimeClient
} from "../../src/integrations/python_runtime/client.js";

import {
  PYTHON_RUNTIME_AUDIENCE,
  PYTHON_RUNTIME_OPERATIONS,
  PYTHON_RUNTIME_PROTOCOL_NAME,
  PYTHON_RUNTIME_PROTOCOL_VERSION,
  PYTHON_RUNTIME_SERVICE_ID
} from "../../src/integrations/python_runtime/contracts.js";

import type {
  PythonRuntimeClientOptions,
  RuntimeCorrelationContext,
  TrustedRuntimeContext
} from "../../src/integrations/python_runtime/contracts.js";

const BACKEND_ROOT = fileURLToPath(
  new URL("../../", import.meta.url)
);

const CONTROL_CENTER_ROOT = resolve(BACKEND_ROOT, "..");

const WORKER_SCRIPT = resolve(
  BACKEND_ROOT,
  "python_runtime",
  "homio_python_runtime",
  "worker.py"
);

const CORRELATION_CONTEXT: RuntimeCorrelationContext = {
  correlationId: "66666666-6666-4666-8666-666666666666"
};

const TRUSTED_CONTEXT: TrustedRuntimeContext = {
  correlationId: CORRELATION_CONTEXT.correlationId,
  actor: {
    identityId: "11111111-1111-4111-8111-111111111111",
    accountId: "22222222-2222-4222-8222-222222222222"
  },
  tenant: {
    tenantId: "33333333-3333-4333-8333-333333333333",
    tenantRevision: 4,
    organizationId: "44444444-4444-4444-8444-444444444444",
    membershipId: "55555555-5555-4555-8555-555555555555",
    membershipRevision: 7
  }
};

let clients: PythonRuntimeClient[] = [];

function pythonExecutable(): string {
  const candidates = [
    process.env.PYTHON_EXECUTABLE,
    process.env.PYTHON,
    process.platform === "win32" ? "python" : "python3",
    "python"
  ].filter(
    (value): value is string =>
      typeof value === "string" && value.length > 0
  );

  for (const candidate of candidates) {
    try {
      const result = execFileSync(
        candidate,
        ["-c", "import sys; print(sys.executable)"],
        {
          cwd: CONTROL_CENTER_ROOT,
          encoding: "utf8",
          timeout: 5_000,
          windowsHide: true
        }
      ).trim();

      if (result.length > 0) return result;
    } catch {
      // Try the next executable name; never use a shell or a command string.
    }
  }

  throw new Error(
    "Python 3.12+ is required for the private runtime integration tests."
  );
}

function createClient(
  ownerFactory = "homio_python_runtime.tests.fixtures.probe_owners:build_runtime",
  poolSize = 2,
  requestTimeoutMs = 5_000,
  workerScript = WORKER_SCRIPT
): PythonRuntimeClient {
  const options: PythonRuntimeClientOptions = {
    pythonExecutable: pythonExecutable(),
    workerScript,
    workingDirectory: CONTROL_CENTER_ROOT,
    ownerFactory,
    runtimeMode: "test",
    poolSize,
    queueLimit: 8,
    requestTimeoutMs
  };

  const client = new PythonRuntimeClient(options);
  clients.push(client);
  return client;
}

it(
  "keeps the TypeScript client and versioned contract document compatible",
  async () => {
    const contractPath = resolve(
      BACKEND_ROOT,
      "contracts",
      "python-runtime",
      "v1",
      "contract.json"
    );

    const contract: unknown = JSON.parse(
      await readFile(contractPath, "utf8")
    );

    expect(contract).toMatchObject({
      contract: {
        protocol: PYTHON_RUNTIME_PROTOCOL_NAME,
        version: PYTHON_RUNTIME_PROTOCOL_VERSION,
        owner: "BACKEND-001-B3"
      }
    });

    const contractDocument = contract as {
      authentication: {
        service_id: string;
        audience: string;
      };
      operations: Record<string, unknown>;
    };

    expect(contractDocument.authentication.service_id).toBe(
      PYTHON_RUNTIME_SERVICE_ID
    );
    expect(contractDocument.authentication.audience).toBe(
      PYTHON_RUNTIME_AUDIENCE
    );
    expect(
      Object.keys(contractDocument.operations).sort()
    ).toEqual([...PYTHON_RUNTIME_OPERATIONS].sort());
  }
);

afterEach(async () => {
  await Promise.all(clients.map((client) => client.close()));
  clients = [];
});

describe("authenticated private Python domain runtime IPC", () => {
  it(
    "preserves correlation, resolves existing CORE owners and minimizes OIDC claims",
    async () => {
      const client = createClient();

      const identity = await client.invoke({
        operation: "core001.identity.resolve",
        context: CORRELATION_CONTEXT,
        payload: {
          provider: "https://issuer.example.test/",
          subject: "probe-subject"
        }
      });

      expect(identity).toEqual({
        status: "RESOLVED",
        identityId: TRUSTED_CONTEXT.actor.identityId,
        referenceId: "77777777-7777-4777-8777-777777777777"
      });

      const tenant = await client.invoke({
        operation: "core001.tenant.resolve_context",
        context: TRUSTED_CONTEXT,
        payload: {
          tenantId: TRUSTED_CONTEXT.tenant.tenantId
        }
      });

      expect(tenant).toEqual({
        status: "RESOLVED",
        tenantId: TRUSTED_CONTEXT.tenant.tenantId,
        tenantRevision: 4,
        context: {
          tenantStatus: "ACTIVE",
          tenantKind: "BROKERAGE",
          operatingMode: "BROKER_SAAS"
        }
      });

      const membership = await client.invoke({
        operation: "core001.membership.resolve",
        context: TRUSTED_CONTEXT,
        payload: {
          tenantId: TRUSTED_CONTEXT.tenant.tenantId,
          organizationId: TRUSTED_CONTEXT.tenant.organizationId,
          identityId: TRUSTED_CONTEXT.actor.identityId
        }
      });

      expect(membership).toEqual({
        status: "RESOLVED",
        membershipId: TRUSTED_CONTEXT.tenant.membershipId,
        tenantId: TRUSTED_CONTEXT.tenant.tenantId,
        organizationId: TRUSTED_CONTEXT.tenant.organizationId,
        identityId: TRUSTED_CONTEXT.actor.identityId,
        membershipRevision: 7
      });

      const principal = await client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" }
      });

      expect(principal).toEqual({
        issuer: "https://issuer.example.test/",
        subject: "probe-subject",
        audiences: ["homio-api"],
        clientId: "homio-web",
        tokenId: "probe-jti"
      });

      expect(JSON.stringify(principal)).not.toContain("must-not-leak");
    }
  );

  it(
    "snapshots queued context and payload before callers can mutate their references",
    async () => {
      const client = createClient(
        "homio_python_runtime.tests.fixtures.probe_owners:build_slow_runtime",
        1,
        5_000
      );

      const first = client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" }
      });

      const mutableContext = {
        correlationId: CORRELATION_CONTEXT.correlationId
      };

      const mutablePayload = {
        provider: "https://issuer.example.test/",
        subject: "probe-subject"
      };

      const queued = client.invoke({
        operation: "core001.identity.resolve",
        context: mutableContext,
        payload: mutablePayload
      });

      mutableContext.correlationId =
        "99999999-9999-4999-8999-999999999999";
      mutablePayload.provider = "https://attacker.example.test/";
      mutablePayload.subject = "attacker-subject";

      await first;

      await expect(queued).resolves.toMatchObject({
        status: "RESOLVED",
        identityId: TRUSTED_CONTEXT.actor.identityId
      });
    }
  );

  it(
    "rejects issuer URLs with user information before private transport",
    async () => {
      const client = createClient();

      await expect(client.invoke({
        operation: "core001.identity.resolve",
        context: CORRELATION_CONTEXT,
        payload: {
          provider: "https://@issuer.example.test/",
          subject: "probe-subject"
        }
      })).rejects.toThrow(/trusted HTTPS issuer URL/);
    }
  );

  it(
    "rejects C0 and C1 Unicode control characters before private transport",
    async () => {
      const client = createClient();
      const controlCharacters = [
        "\u0000",
        "\u001f",
        "\u007f",
        "\u0085",
        "\u009f"
      ];

      for (const controlCharacter of controlCharacters) {
        await expect(client.invoke({
          operation: "core001.identity.resolve",
          context: CORRELATION_CONTEXT,
          payload: {
            provider: "https://issuer.example.test/",
            subject: `subject${controlCharacter}value`
          }
        })).rejects.toThrow(/subject is invalid/);
      }
    }
  );

  it(
    "rejects forbidden control characters in production environment configuration",
    () => {
      const productionOptions: Omit<
        PythonRuntimeClientOptions,
        "environment"
      > = {
        pythonExecutable: pythonExecutable(),
        workerScript: WORKER_SCRIPT,
        workingDirectory: CONTROL_CENTER_ROOT,
        ownerFactory: "AUTONOMY_ENGINE.runtime_composition:build_runtime",
        runtimeMode: "production"
      };

      const controlCharacters = [
        "\u0000",
        "\u001f",
        "\u007f",
        "\u0085"
      ];

      for (const controlCharacter of controlCharacters) {
        expect(() => new PythonRuntimeClient({
          ...productionOptions,
          environment: {
            HOMIO_OIDC_ISSUER: "https://issuer.example.test/",
            HOMIO_OIDC_AUDIENCE: `homio-api${controlCharacter}`,
            HOMIO_OIDC_JWKS_URL: "https://issuer.example.test/jwks"
          }
        })).toThrow(/Runtime environment variable is not permitted/);
      }
    }
  );

  it(
    "rejects internal spaces in configured HTTPS issuer URLs",
    () => {
      expect(() => new PythonRuntimeClient({
        pythonExecutable: pythonExecutable(),
        workerScript: WORKER_SCRIPT,
        workingDirectory: CONTROL_CENTER_ROOT,
        ownerFactory: "AUTONOMY_ENGINE.runtime_composition:build_runtime",
        runtimeMode: "production",
        environment: {
          HOMIO_OIDC_ISSUER: "https://issuer.example.test/ invalid",
          HOMIO_OIDC_AUDIENCE: "homio-api",
          HOMIO_OIDC_JWKS_URL: "https://issuer.example.test/jwks"
        }
      })).toThrow(/contains whitespace or control characters/);
    }
  );

  it(
    "rejects an issuer longer than the canonical OIDC owner limit",
    () => {
      expect(() => new PythonRuntimeClient({
        pythonExecutable: pythonExecutable(),
        workerScript: WORKER_SCRIPT,
        workingDirectory: CONTROL_CENTER_ROOT,
        ownerFactory: "AUTONOMY_ENGINE.runtime_composition:build_runtime",
        runtimeMode: "production",
        environment: {
          HOMIO_OIDC_ISSUER: `https://${"a".repeat(240)}.example.test/`,
          HOMIO_OIDC_AUDIENCE: "homio-api",
          HOMIO_OIDC_JWKS_URL: "https://issuer.example.test/jwks"
        }
      })).toThrow(/valid HTTPS URL/);
    }
  );

  it(
    "rejects cross-tenant and cross-actor arguments before transport",
    async () => {
      const client = createClient();

      await expect(client.invoke({
        operation: "core001.tenant.resolve_context",
        context: TRUSTED_CONTEXT,
        payload: {
          tenantId: "99999999-9999-4999-8999-999999999999"
        }
      })).rejects.toThrow(
        /Tenant selection does not match trusted context/
      );

      await expect(client.invoke({
        operation: "core001.membership.resolve",
        context: TRUSTED_CONTEXT,
        payload: {
          tenantId: TRUSTED_CONTEXT.tenant.tenantId,
          organizationId: TRUSTED_CONTEXT.tenant.organizationId,
          identityId: "99999999-9999-4999-8999-999999999999"
        }
      })).rejects.toThrow(
        /Membership scope does not match trusted context/
      );
    }
  );

  it(
    "cancels an in-flight operation by retiring its worker and recovers with a fresh worker",
    async () => {
      const client = createClient(
        "homio_python_runtime.tests.fixtures.probe_owners:build_slow_runtime",
        1,
        5_000
      );

      const controller = new AbortController();

      const pending = client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" },
        signal: controller.signal
      });

      await new Promise((resolvePromise) =>
        setTimeout(resolvePromise, 60)
      );

      controller.abort();

      await expect(pending).rejects.toMatchObject({
        code: "RUNTIME_CANCELLED"
      });

      // The next call on the same client must use a replacement process.
      await expect(client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" }
      })).resolves.toMatchObject({
        subject: "probe-subject"
      });
    }
  );

  it(
    "times out an operation and reports a stable timeout class",
    async () => {
      const client = createClient(
        "homio_python_runtime.tests.fixtures.probe_owners:build_slow_runtime",
        1,
        5_000
      );

      const pending = client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" },
        timeoutMs: 120
      });

      await expect(pending).rejects.toMatchObject({
        code: "RUNTIME_TIMEOUT"
      });
    }
  );
});

describe("Python runtime worker authentication", () => {
  it(
    "rejects a response that is not authenticated with the per-worker key",
    async () => {
      const forgedWorker = resolve(
        BACKEND_ROOT,
        "python_runtime",
        "homio_python_runtime",
        "tests",
        "fixtures",
        "invalid_response_worker.py"
      );

      const client = createClient(
        "homio_python_runtime.tests.fixtures.probe_owners:build_runtime",
        1,
        5_000,
        forgedWorker
      );

      await expect(client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" }
      })).rejects.toMatchObject({
        code: "RUNTIME_AUTHENTICATION_FAILED"
      });
    }
  );
});

describe("Python runtime response contract validation", () => {
  it(
    "rejects an authenticated owner response containing a C1 control character",
    async () => {
      const malformedWorker = resolve(
        BACKEND_ROOT,
        "python_runtime",
        "homio_python_runtime",
        "tests",
        "fixtures",
        "invalid_result_worker.py"
      );

      const client = createClient(
        "homio_python_runtime.tests.fixtures.probe_owners:build_runtime",
        1,
        5_000,
        malformedWorker
      );

      await expect(client.invoke({
        operation: "oidc.verify_access_token",
        context: CORRELATION_CONTEXT,
        payload: { accessToken: "bridge-test-token" }
      })).rejects.toMatchObject({
        code: "DOMAIN_RESULT_INVALID"
      });
    }
  );

  it(
    "fails closed when production OIDC trust configuration is incomplete",
    () => {
      expect(() => new PythonRuntimeClient({
        pythonExecutable: pythonExecutable(),
        workerScript: WORKER_SCRIPT,
        workingDirectory: CONTROL_CENTER_ROOT,
        ownerFactory: "AUTONOMY_ENGINE.runtime_composition:build_runtime",
        runtimeMode: "production"
      })).toThrow(
        /requires the configured OIDC issuer, audience and JWKS URL/
      );

      expect(() => new PythonRuntimeClient({
        pythonExecutable: pythonExecutable(),
        workerScript: WORKER_SCRIPT,
        workingDirectory: CONTROL_CENTER_ROOT,
        ownerFactory: "AUTONOMY_ENGINE.runtime_composition:build_runtime",
        runtimeMode: "production",
        environment: {
          HOMIO_OIDC_ISSUER: "https://@issuer.example.test/",
          HOMIO_OIDC_AUDIENCE: "homio-api",
          HOMIO_OIDC_JWKS_URL: "https://issuer.example.test/jwks"
        }
      })).toThrow(
        /must be HTTPS without credentials/
      );
    }
  );
});
