import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

import type { FastifyInstance } from "fastify";

import {
  ConfigurationError,
  loadSettings
} from "./config/environment.js";

import type { BackendSettings } from "./config/settings.js";

import { buildApp } from "./app.js";

export type ShutdownReason =
  | NodeJS.Signals
  | "manual";

export interface RunningBackend {
  readonly server: FastifyInstance;

  shutdown(reason?: ShutdownReason): Promise<void>;
}

async function closeWithinDeadline(
  server: FastifyInstance,
  timeoutMs: number
): Promise<void> {
  const closeOperation = server.close();

  let timer: NodeJS.Timeout | undefined;

  const deadline = new Promise<never>(
    (_resolve, reject) => {
      timer = setTimeout(() => {
        // The graceful period has expired.
        // Close remaining connections instead of hanging forever.
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
    if (timer !== undefined) {
      clearTimeout(timer);
    }
  }
}

export async function startBackend(
  settings: BackendSettings
): Promise<RunningBackend> {
  const runtime = await buildApp(settings);

  try {
    await runtime.server.listen({
      host: settings.host,
      port: settings.port
    });
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

    shutdownPromise = closeWithinDeadline(
      runtime.server,
      settings.shutdownTimeoutMs
    ).then(() => {
      runtime.server.log.info(
        { reason },
        "HOMIO backend shutdown completed"
      );
    });

    return shutdownPromise;
  }

  return {
    server: runtime.server,
    shutdown
  };
}

export async function runServer(
  env: NodeJS.ProcessEnv = process.env
): Promise<void> {
  // Configuration is validated before the application starts.
  const settings = loadSettings(env);

  const running = await startBackend(settings);

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
