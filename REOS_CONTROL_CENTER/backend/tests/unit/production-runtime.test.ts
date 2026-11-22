import { describe, expect, it } from "vitest";

import type { BackendSettings } from "../../src/config/settings.js";
import type { PostgresDriverClient } from "../../src/persistence/postgres.js";
import type {
  ProductionPersistenceDriverFactories,
  ProductionPostgresPool,
  ProductionRedisClient,
  PostgresPoolOptions,
  RedisClientOptions
} from "../../src/persistence/production-runtime.js";
import {
  createProductionPersistenceRuntime,
  ProductionPersistenceUnavailableError
} from "../../src/persistence/production-runtime.js";

const productionSettings = {
  nodeEnv: "production",
  host: "127.0.0.1",
  port: 8080,
  logLevel: "warn",
  requestTimeoutMs: 15_000,
  shutdownTimeoutMs: 5_000,
  postgres: {
    connectionString:
      "postgresql://homio_app:secret-value@db.example.test:5432/homio",
    sslMode: "verify-full",
    caCertificate:
      "-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----",
    poolMax: 7,
    connectionTimeoutMs: 5_000,
    idleTimeoutMs: 30_000,
    statementTimeoutMs: 15_000
  },
  redis: {
    url: "rediss://homio_app:secret-value@redis.example.test:6380/0",
    caCertificate:
      "-----BEGIN CERTIFICATE-----\nZmFrZQ==\n-----END CERTIFICATE-----",
    connectTimeoutMs: 4_000
  }
} satisfies BackendSettings;

interface FakeState {
  serverVersion: number;
  tenantTableCount: number;
  redisConnectFails: boolean;
  postgresClosed: number;
  redisClosed: number;
  redisDestroyed: number;
  pgOptions?: PostgresPoolOptions;
  redisOptions?: RedisClientOptions;
}

function createFactories(
  state: FakeState
): ProductionPersistenceDriverFactories {
  const client: PostgresDriverClient = {
    async query(text: string) {
      if (text.startsWith("WITH effective_roles")) {
        return {
          rows: [{
            role_name: "homio_app",
            is_superuser: false,
            bypasses_row_security: false,
            owns_application_tables: false,
            tenant_table_count: state.tenantTableCount,
            tenant_tables_force_rls: true,
            tenant_tables_have_tenant_restrictive_guard: true
          }],
          rowCount: 1
        };
      }

      return {
        rows: [],
        rowCount: 0
      };
    },

    release(): void {}
  };

  const pool: ProductionPostgresPool = {
    async connect() {
      return client;
    },

    async end() {
      state.postgresClosed += 1;
    },

    async query(text: string) {
      if (text.includes("server_version_num")) {
        return {
          rows: [{
            server_version_num: state.serverVersion
          }],
          rowCount: 1
        };
      }

      return {
        rows: [{ value: 1 }],
        rowCount: 1
      };
    },

    on(): void {}
  };

  let redisIsOpen = false;

  const redis: ProductionRedisClient = {
    get isOpen() {
      return redisIsOpen;
    },

    async connect() {
      if (state.redisConnectFails) {
        throw new Error("redis connect failed");
      }

      redisIsOpen = true;
    },

    async ping() {
      return "PONG";
    },

    async quit() {
      state.redisClosed += 1;
      redisIsOpen = false;
      return "OK";
    },

    destroy() {
      state.redisDestroyed += 1;
      redisIsOpen = false;
    },

    on(): void {},

    async eval(_script, _options) {
      return [1, 1_000, 1];
    }
  };

  return {
    createPostgresPool(options) {
      state.pgOptions = options;
      return pool;
    },

    createRedisClient(options) {
      state.redisOptions = options;
      return redis;
    }
  };
}

function createState(
  overrides: Partial<FakeState> = {}
): FakeState {
  return {
    serverVersion: 180004,
    tenantTableCount: 1,
    redisConnectFails: false,
    postgresClosed: 0,
    redisClosed: 0,
    redisDestroyed: 0,
    ...overrides
  };
}

describe("B4 production persistence runtime", () => {
  it("creates one TLS-verified PostgreSQL pool and one shared Redis client", async () => {
    const state = createState();

    const runtime = await createProductionPersistenceRuntime(
      productionSettings,
      createFactories(state)
    );

    expect(state.pgOptions).toMatchObject({
      max: 7,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 30_000,
      statement_timeout: 15_000,
      ssl: {
        rejectUnauthorized: true,
        ca: productionSettings.postgres.caCertificate
      },
      allowExitOnIdle: false
    });

    expect(state.redisOptions).toMatchObject({
      url: productionSettings.redis.url,
      socket: {
        connectTimeout: 4_000,
        tls: true,
        ca: productionSettings.redis.caCertificate
      },
      commandOptions: {
        timeout: 4_000
      }
    });

    expect(runtime.isHealthy()).toBe(true);

    await runtime.verifyReadiness();

    await runtime.close();
    await runtime.close();

    expect(state.postgresClosed).toBe(1);
    expect(state.redisClosed).toBe(1);
    expect(state.redisDestroyed).toBe(0);
    expect(runtime.isHealthy()).toBe(false);
  });

  it("fails closed when the approved tenant RLS boundary is not installed", async () => {
    const state = createState({
      tenantTableCount: 0
    });

    await expect(
      createProductionPersistenceRuntime(
        productionSettings,
        createFactories(state)
      )
    ).rejects.toBeInstanceOf(Error);

    expect(state.postgresClosed).toBe(1);
    expect(state.redisClosed).toBe(1);
  });

  it("rejects PostgreSQL versions older than the locked minimum", async () => {
    const state = createState({
      serverVersion: 180003
    });

    await expect(
      createProductionPersistenceRuntime(
        productionSettings,
        createFactories(state)
      )
    ).rejects.toBeInstanceOf(
      ProductionPersistenceUnavailableError
    );

    expect(state.postgresClosed).toBe(1);
    expect(state.redisClosed).toBe(1);
  });

  it("cleans up PostgreSQL and Redis if Redis connection fails", async () => {
    const state = createState({
      redisConnectFails: true
    });

    await expect(
      createProductionPersistenceRuntime(
        productionSettings,
        createFactories(state)
      )
    ).rejects.toThrow("redis connect failed");

    expect(state.postgresClosed).toBe(1);
    expect(state.redisClosed).toBe(0);
    expect(state.redisDestroyed).toBe(1);
  });
});
