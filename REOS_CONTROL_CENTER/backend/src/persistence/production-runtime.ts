import { createRequire } from "node:module";

import type { BackendSettings } from "../config/settings.js";
import {
  PostgresRuntime,
  type PostgresDriverPool,
  type PostgresQueryResult
} from "./postgres.js";
import {
  RedisRateLimiter,
  type RedisEvalClient,
  type RedisRateLimitOptions
} from "./redis-rate-limit.js";
import { PostgresSessionStore } from "./postgres-session-store.js";
import { PostgresSecurityAuditStore } from "./postgres-security-audit.js";

const MINIMUM_POSTGRES_SERVER_VERSION_NUM = 180004;

export interface PostgresPoolOptions {
  readonly connectionString: string;
  readonly max: number;
  readonly connectionTimeoutMillis: number;
  readonly idleTimeoutMillis: number;
  readonly statement_timeout: number;
  readonly ssl: false | {
    readonly rejectUnauthorized: true;
    readonly ca?: string;
  };
  readonly allowExitOnIdle: false;
}

export interface RedisClientOptions {
  readonly url: string;
  readonly socket: {
    readonly connectTimeout: number;
    readonly tls: boolean;
    readonly ca?: string;
  };
  readonly commandOptions: {
    readonly timeout: number;
  };
}

export interface ProductionPostgresPool extends PostgresDriverPool {
  query(text: string, values?: unknown[]): Promise<PostgresQueryResult>;
  on(event: "error", listener: (error: Error) => void): unknown;
}

export interface ProductionRedisClient extends RedisEvalClient {
  readonly isOpen: boolean;
  connect(): Promise<unknown>;
  ping(): Promise<string>;
  quit(): Promise<unknown>;
  destroy(): void;
  on(
    event: "error" | "ready" | "reconnecting",
    listener: (error?: unknown) => void
  ): unknown;
}

export interface ProductionPersistenceDriverFactories {
  createPostgresPool(options: PostgresPoolOptions): ProductionPostgresPool;
  createRedisClient(options: RedisClientOptions): ProductionRedisClient;
}

export interface ProductionPersistenceRuntime {
  readonly postgres: PostgresRuntime;
  readonly redis: ProductionRedisClient;
  readonly sessions: PostgresSessionStore;
  readonly securityAudit: PostgresSecurityAuditStore;
  createRateLimiter(options: RedisRateLimitOptions): RedisRateLimiter;
  isHealthy(): boolean;
  verifyReadiness(): Promise<void>;
  close(): Promise<void>;
}

export class ProductionPersistenceConfigurationError extends Error {
  public constructor() {
    super(
      "Production persistence requires both PostgreSQL and Redis configuration."
    );
    this.name = "ProductionPersistenceConfigurationError";
  }
}

export class ProductionPersistenceUnavailableError extends Error {
  public constructor(message: string, cause?: unknown) {
    super(message, cause === undefined ? undefined : { cause });
    this.name = "ProductionPersistenceUnavailableError";
  }
}

function loadNodeDriverFactories(): ProductionPersistenceDriverFactories {
  const require = createRequire(import.meta.url);

  const postgresModule = require("pg") as {
    readonly Pool: new (
      options: PostgresPoolOptions
    ) => ProductionPostgresPool;
  };

  const redisModule = require("@redis/client") as {
    readonly createClient: (
      options: RedisClientOptions
    ) => ProductionRedisClient;
  };

  return {
    createPostgresPool(options) {
      return new postgresModule.Pool(options);
    },

    createRedisClient(options) {
      return redisModule.createClient({
        ...options,
        socket: {
          ...options.socket
        },
        commandOptions: {
          ...options.commandOptions
        }
      });
    }
  };
}

function createPostgresOptions(
  settings: NonNullable<BackendSettings["postgres"]>
): PostgresPoolOptions {
  const ssl = settings.sslMode === "verify-full"
    ? Object.freeze({
        rejectUnauthorized: true as const,
        ...(settings.caCertificate === undefined
          ? {}
          : { ca: settings.caCertificate })
      })
    : false;

  return Object.freeze({
    connectionString: settings.connectionString,
    max: settings.poolMax,
    connectionTimeoutMillis: settings.connectionTimeoutMs,
    idleTimeoutMillis: settings.idleTimeoutMs,
    statement_timeout: settings.statementTimeoutMs,
    ssl,
    allowExitOnIdle: false
  });
}

function createRedisOptions(
  settings: NonNullable<BackendSettings["redis"]>
): RedisClientOptions {
  const tls = settings.url.startsWith("rediss://");

  return Object.freeze({
    url: settings.url,
    socket: Object.freeze({
      connectTimeout: settings.connectTimeoutMs,
      tls,
      ...(settings.caCertificate === undefined
        ? {}
        : { ca: settings.caCertificate })
    }),
    commandOptions: Object.freeze({
      timeout: settings.connectTimeoutMs
    })
  });
}

function readPostgresServerVersion(
  result: PostgresQueryResult
): number {
  const row = result.rows[0];

  if (
    typeof row !== "object" ||
    row === null ||
    Array.isArray(row)
  ) {
    throw new ProductionPersistenceUnavailableError(
      "PostgreSQL did not return a valid server version."
    );
  }

  const version = (row as Record<string, unknown>).server_version_num;

  if (
    typeof version !== "number" ||
    !Number.isSafeInteger(version)
  ) {
    throw new ProductionPersistenceUnavailableError(
      "PostgreSQL did not return a valid server version."
    );
  }

  return version;
}

export async function createProductionPersistenceRuntime(
  settings: BackendSettings,
  factories: ProductionPersistenceDriverFactories = loadNodeDriverFactories()
): Promise<ProductionPersistenceRuntime> {
  const postgresSettings = settings.postgres;
  const redisSettings = settings.redis;

  if (postgresSettings === undefined || redisSettings === undefined) {
    throw new ProductionPersistenceConfigurationError();
  }

  const pool = factories.createPostgresPool(
    createPostgresOptions(postgresSettings)
  );

  let postgres: PostgresRuntime | undefined;
  let redis: ProductionRedisClient | undefined;

  let postgresHealthy = false;
  let redisHealthy = false;
  let closed = false;
  let closePromise: Promise<void> | undefined;

  async function closePostgres(): Promise<void> {
    if (postgres !== undefined) {
      await postgres.close();
      return;
    }

    await pool.end();
  }

  async function closeRedis(): Promise<void> {
    const client = redis;

    if (client === undefined) {
      return;
    }

    if (!client.isOpen) {
      client.destroy();
      return;
    }

    try {
      await client.quit();
    } catch (error) {
      client.destroy();
      throw error;
    }
  }

  async function close(): Promise<void> {
    if (closePromise !== undefined) {
      return closePromise;
    }

    closed = true;
    postgresHealthy = false;
    redisHealthy = false;

    closePromise = (async () => {
      const results = await Promise.allSettled([
        closePostgres(),
        closeRedis()
      ]);

      const failures = results
        .filter((result): result is PromiseRejectedResult =>
          result.status === "rejected"
        )
        .map((result) => result.reason);

      if (failures.length > 0) {
        throw new AggregateError(
          failures,
          "One or more production persistence clients failed to close cleanly."
        );
      }
    })();

    return closePromise;
  }

  async function verifyReadiness(): Promise<void> {
    if (closed) {
      throw new ProductionPersistenceUnavailableError(
        "Production persistence is closed."
      );
    }

    const activeRedis = redis;

    if (postgres === undefined || activeRedis === undefined) {
      throw new ProductionPersistenceUnavailableError(
        "Production persistence clients have not been initialized."
      );
    }

    try {
      const [postgresResult, redisResult] = await Promise.all([
        pool.query("SELECT 1"),
        activeRedis.ping()
      ]);

      if (postgresResult.rowCount !== 1 || redisResult !== "PONG") {
        throw new Error(
          "A persistence dependency returned an invalid health result."
        );
      }

      postgresHealthy = true;
      redisHealthy = true;
    } catch (cause) {
      postgresHealthy = false;
      redisHealthy = false;

      throw new ProductionPersistenceUnavailableError(
        "PostgreSQL or Redis readiness verification failed.",
        cause
      );
    }
  }

  try {
    postgres = new PostgresRuntime(pool);

    pool.on("error", () => {
      postgresHealthy = false;
    });

    redis = factories.createRedisClient(
      createRedisOptions(redisSettings)
    );

    redis.on("error", () => {
      redisHealthy = false;
    });

    redis.on("reconnecting", () => {
      redisHealthy = false;
    });

    redis.on("ready", () => {
      redisHealthy = true;
    });

    const activeRedis = redis;
    const activePostgres = postgres;
    const sessions = new PostgresSessionStore(activePostgres);
    const securityAudit = new PostgresSecurityAuditStore(pool);

    await Promise.all([
      pool.query(
        "SELECT current_setting('server_version_num')::integer AS server_version_num"
      ).then((result) => {
        const version = readPostgresServerVersion(result);

        if (version < MINIMUM_POSTGRES_SERVER_VERSION_NUM) {
          throw new ProductionPersistenceUnavailableError(
            "PostgreSQL 18.4 or newer is required by the approved backend stack."
          );
        }
      }),

      activeRedis.connect()
    ]);

    await activePostgres.verifyRuntimeRoleSafety();

    await verifyReadiness();

    return Object.freeze({
      postgres: activePostgres,
      redis: activeRedis,
      sessions,
      securityAudit,

      createRateLimiter(options: RedisRateLimitOptions): RedisRateLimiter {
        if (closed) {
          throw new ProductionPersistenceUnavailableError(
            "Production persistence is closed."
          );
        }

        return new RedisRateLimiter(activeRedis, options);
      },

      isHealthy(): boolean {
        return !closed && postgresHealthy && redisHealthy;
      },

      verifyReadiness,

      close
    });
  } catch (cause) {
    await close().catch(() => undefined);
    throw cause;
  }
}
