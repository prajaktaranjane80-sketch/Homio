import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

import type {
  FastifyInstance,
  FastifyPluginAsync
} from "fastify";

import {
  ConfigurationError,
  loadSettings
} from "./config/environment.js";

import type { BackendSettings } from "./config/settings.js";
import type { BackendSecurityRuntime } from "./security/contracts.js";
import { buildApp } from "./app.js";
import {
  createProductionPersistenceRuntime,
  type ProductionPersistenceDriverFactories,
  type ProductionPersistenceRuntime
} from "./persistence/production-runtime.js";

export type ShutdownReason =
  | NodeJS.Signals
  | "manual";

export interface RunningBackend {
  readonly server: FastifyInstance;
  readonly persistence?: ProductionPersistenceRuntime;
  isReady(): boolean;
  shutdown(reason?: ShutdownReason): Promise<void>;
}

const IDLE_CONNECTION_REAP_INTERVAL_MS = 50;

async function closeWithinDeadline(
  server: FastifyInstance,
  timeoutMs: number
): Promise<void> {
  const closeOperation = server.close();

  const idleConnectionSweep = setInterval(() => {
    server.server.closeIdleConnections();
  }, IDLE_CONNECTION_REAP_INTERVAL_MS);

  idleConnectionSweep.unref();

  server.server.closeIdleConnections();

  let timer: NodeJS.Timeout | undefined;

  const deadline = new Promise<never>(
    (_resolve, reject) => {
      timer = setTimeout(() => {
        server.server.closeAllConnections();

        reject(
          new Error(
            "Backend graceful shutdown deadline exceeded"
          )
        );
      }, timeoutMs);

      timer.unref();
    }
  );

  try {
    await Promise.race([
      closeOperation,
      deadline
    ]);
  } finally {
    clearInterval(idleConnectionSweep);

    if (timer !== undefined) {
      clearTimeout(timer);
    }
  }
}

export async function startBackend(
  settings: BackendSettings,
  apiV1Plugins: readonly FastifyPluginAsync[] = [],
  securityRuntime?: BackendSecurityRuntime,
  persistenceFactories?: ProductionPersistenceDriverFactories
): Promise<RunningBackend> {
  const hasPostgres = settings.postgres !== undefined;
  const hasRedis = settings.redis !== undefined;

  if (hasPostgres !== hasRedis) {
    throw new ConfigurationError([
      "HOMIO_POSTGRES_URL and HOMIO_REDIS_URL must be configured together"
    ]);
  }

  let persistence: ProductionPersistenceRuntime | undefined;

  try {
    if (hasPostgres && hasRedis) {
      persistence = await createProductionPersistenceRuntime(
        settings,
        persistenceFactories
      );

      // Verify the database role, tenant RLS boundary and Redis
      // before allowing the HTTP listener to accept traffic.
      await persistence.verifyReadiness();
    }

    const runtime = await buildApp(
      settings,
      apiV1Plugins,
      securityRuntime,
      persistence?.verifyReadiness
    );

    try {
      await runtime.server.listen({
        host: settings.host,
        port: settings.port
      });

      runtime.markReady();
    } catch (error) {
      runtime.markDraining();
      await runtime.server.close().catch(() => undefined);
      throw error;
    }

    let shutdownPromise: Promise<void> | undefined;

    function shutdown(
      reason: ShutdownReason = "manual"
    ): Promise<void> {
      if (shutdownPromise !== undefined) {
        return shutdownPromise;
      }

      runtime.markDraining();

      runtime.server.log.info(
        { reason },
        "HOMIO backend graceful shutdown started"
      );

      shutdownPromise = (async () => {
        try {
          await closeWithinDeadline(
            runtime.server,
            settings.shutdownTimeoutMs
          );
        } finally {
          // Keep persistence available while active requests drain.
          await persistence?.close();
        }
      })().then(() => {
        runtime.server.log.info(
          { reason },
          "HOMIO backend shutdown completed"
        );
      });

      return shutdownPromise;
    }

    return {
      server: runtime.server,
      ...(persistence === undefined ? {} : { persistence }),
      isReady(): boolean {
        return runtime.isReady() && (persistence?.isHealthy() ?? true);
      },
      shutdown
    };
  } catch (error) {
    await persistence?.close().catch(() => undefined);
    throw error;
  }
}

export async function runServer(
  env: NodeJS.ProcessEnv = process.env,
  apiV1Plugins: readonly FastifyPluginAsync[] = [],
  securityRuntime?: BackendSecurityRuntime
): Promise<void> {
  const settings = loadSettings(env);

  const running = await startBackend(
    settings,
    apiV1Plugins,
    securityRuntime
  );

  const handleSignal = (signal: NodeJS.Signals): void => {
    void running.shutdown(signal).catch(() => {
      process.exitCode = 1;

      process.stderr.write(
        "HOMIO backend shutdown did not finish cleanly.\n"
      );
    });
  };

  process.once("SIGINT", () => {
    handleSignal("SIGINT");
  });

  process.once("SIGTERM", () => {
    handleSignal("SIGTERM");
  });
}

const entrypoint = process.argv[1];

const isMainModule =
  entrypoint !== undefined &&
  pathToFileURL(resolve(entrypoint)).href === import.meta.url;

if (isMainModule) {
  void runServer().catch((error: unknown) => {
    process.exitCode = 1;

    if (error instanceof ConfigurationError) {
      process.stderr.write(
        `HOMIO backend configuration failed: ${error.message}\n`
      );
    } else {
      process.stderr.write(
        "HOMIO backend startup failed. Check runtime configuration and startup logs.\n"
      );
    }
  });
}
