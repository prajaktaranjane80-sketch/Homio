import { execFileSync } from "node:child_process";
import { randomBytes, randomUUID } from "node:crypto";
import { EventEmitter } from "node:events";

import { Pool } from "pg";

import {
  describe,
  expect,
  it
} from "vitest";

import { createB4PostgresTestDatabase } from "../helpers/postgres-b4-test-database.js";

const TEST_TIMEOUT_MS = 180_000;
const POSTGRES_IMAGE = "postgres:18.4";
const CONTAINER_READY_TIMEOUT_MS = 45_000;
const CONTAINER_POLL_INTERVAL_MS = 250;
const LONG_TRANSACTION_IDLE_TIMEOUT_MS = 250;
const LONG_TRANSACTION_WAIT_MS = 500;
const STATEMENT_TIMEOUT_MS = 200;

interface DockerOptions {
  readonly environment?: NodeJS.ProcessEnv;
  readonly timeoutMs?: number;
}

function runDocker(
  args: readonly string[],
  options: DockerOptions = {}
): string {
  try {
    return execFileSync("docker", [...args], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
      env: options.environment ?? process.env,
      timeout: options.timeoutMs ?? 30_000,
      maxBuffer: 2 * 1024 * 1024
    }).trim();
  } catch (error) {
    const candidate = error as {
      readonly stderr?: Buffer | string;
      readonly message?: string;
    };

    const detail = Buffer.isBuffer(candidate.stderr)
      ? candidate.stderr.toString("utf8")
      : candidate.stderr ?? candidate.message ?? "unknown Docker error";

    const safeDetail = String(detail).slice(0, 1_000);

    throw new Error(
      "The isolated PostgreSQL operations container command failed: " +
      safeDetail
    );
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function waitForPostgresContainer(
  containerName: string,
  timeoutMs = CONTAINER_READY_TIMEOUT_MS
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown;

  while (Date.now() < deadline) {
    try {
      runDocker(
        [
          "exec",
          containerName,
          "pg_isready",
          "--host=127.0.0.1",
          "--port=5432",
          "--username=postgres",
          "--dbname=postgres"
        ],
        { timeoutMs: 5_000 }
      );

      return;
    } catch (error) {
      lastError = error;
      await wait(CONTAINER_POLL_INTERVAL_MS);
    }
  }

  throw new Error(
    "The isolated PostgreSQL 18.4 container did not become ready " +
    "within the bounded startup window.",
    { cause: lastError }
  );
}

function getPublishedPostgresPort(containerName: string): number {
  const mapping = runDocker([
    "port",
    containerName,
    "5432/tcp"
  ]);

  const ports = mapping
    .split(/\r?\n/)
    .map((value) => /:(\d+)$/.exec(value.trim())?.[1])
    .filter((value): value is string => value !== undefined);

  if (ports.length !== 1) {
    throw new Error(
      "The isolated PostgreSQL container must expose exactly one loopback host port."
    );
  }

  const port = Number(ports[0]);

  if (!Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error("Docker returned an invalid PostgreSQL host port.");
  }

  return port;
}

function makeAdminConnectionUrl(
  port: number,
  password: string
): string {
  const url = new URL(`postgresql://postgres@127.0.0.1:${port}/postgres`);
  url.password = password;
  url.searchParams.set("application_name", "homio-b4-phase8-operations-test");
  url.searchParams.set("connect_timeout", "5");
  return url.toString();
}

const b4OperationsSuite = process.env.CI === "true"
  ? describe
  : describe.skip;

b4OperationsSuite(
  "B4 PostgreSQL Phase 8 operational recovery",
  () => {
    it(
      "bounds pool acquisition and statements, terminates idle transactions, " +
      "recovers broken clients and PostgreSQL restart, and closes every resource",
      async () => {
        const suffix = randomUUID().replaceAll("-", "").slice(0, 12);
        const containerName = `homio-b4-ops-${suffix}`;
        const postgresPassword = randomBytes(48).toString("base64url");

        const dockerEnvironment: NodeJS.ProcessEnv = {
          ...process.env,
          POSTGRES_PASSWORD: postgresPassword,
          POSTGRES_DB: "postgres"
        };

        let containerCreated = false;

        let database:
          | Awaited<ReturnType<typeof createB4PostgresTestDatabase>>
          | undefined;

        const originalAdminUrl =
          process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;

        let restartPool: Pool | undefined;
        const restartPoolErrors: Error[] = [];

        let testError: unknown;
        const cleanupErrors: Error[] = [];

        try {
          runDocker(
            [
              "run",
              "--detach",
              "--name",
              containerName,
              "--publish",
              "127.0.0.1::5432",
              "--env",
              "POSTGRES_PASSWORD",
              "--env",
              "POSTGRES_DB",
              POSTGRES_IMAGE
            ],
            {
              environment: dockerEnvironment,
              timeoutMs: 60_000
            }
          );

          containerCreated = true;

          await waitForPostgresContainer(containerName);

          const postgresPort = getPublishedPostgresPort(containerName);

          const adminUrl = makeAdminConnectionUrl(
            postgresPort,
            postgresPassword
          );

          /*
           * The canonical helper remains the only owner of the disposable B4
           * database, roles, complete migration manifest, pools and runtime.
           * This test runs in its own Vitest worker and uses a dedicated server,
           * so the environment override cannot redirect another test file.
           */
          process.env.HOMIO_TEST_POSTGRES_ADMIN_URL = adminUrl;

          database = await createB4PostgresTestDatabase();

          expect(database.postgresServerVersion).toBeGreaterThanOrEqual(180004);
          expect(database.migrationHistory.length).toBeGreaterThan(0);

          // Pool exhaustion must time out, not grow without bound or hang.
          const leasedClients = await Promise.all([
            database.applicationPool.connect(),
            database.applicationPool.connect(),
            database.applicationPool.connect()
          ]);

          try {
            expect(leasedClients).toHaveLength(3);

            await expect(
              database.applicationPool.connect()
            ).rejects.toThrow(/timeout exceeded/i);
          } finally {
            for (const client of leasedClients) {
              client.release();
            }
          }

          await expect(
            database.applicationPool.query("SELECT 1 AS recovered")
          ).resolves.toMatchObject({
            rows: [{ recovered: 1 }]
          });

          // A cancelled statement must roll back cleanly and leave the pool usable.
          const statementClient = await database.applicationPool.connect();

          try {
            await statementClient.query("BEGIN");

            await statementClient.query(
              `SET LOCAL statement_timeout = '${STATEMENT_TIMEOUT_MS}ms'`
            );

            await expect(
              statementClient.query("SELECT pg_sleep(2)")
            ).rejects.toMatchObject({
              code: "57014"
            });

            await statementClient.query("ROLLBACK");
          } finally {
            statementClient.release();
          }

          await expect(
            database.applicationPool.query(
              "SELECT 1 AS statement_timeout_recovered"
            )
          ).resolves.toMatchObject({
            rows: [{ statement_timeout_recovered: 1 }]
          });

          // An abruptly disconnected application client must not leave an
          // open transaction or an occupied pool slot behind.
          const disconnectedClient = await database.applicationPool.connect();

          const disconnectedPidResult = await disconnectedClient.query<{
            pid: number;
          }>("SELECT pg_backend_pid()::integer AS pid");

          const disconnectedBackendPid = disconnectedPidResult.rows[0]?.pid;

          if (
            typeof disconnectedBackendPid !== "number" ||
            !Number.isSafeInteger(disconnectedBackendPid) ||
            disconnectedBackendPid <= 0
          ) {
            throw new Error(
              "PostgreSQL did not return a valid backend PID for the disconnect check."
            );
          }

          await disconnectedClient.query("BEGIN");
          disconnectedClient.release(true);

          let disconnectedBackendClosed = false;
          const disconnectDeadline = Date.now() + 10_000;

          while (Date.now() < disconnectDeadline) {
            const connectionState = await database.adminPool.query<{
              connection_exists: boolean;
            }>(
              "SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE pid = $1) AS connection_exists",
              [disconnectedBackendPid]
            );

            if (connectionState.rows[0]?.connection_exists === false) {
              disconnectedBackendClosed = true;
              break;
            }

            await wait(CONTAINER_POLL_INTERVAL_MS);
          }

          expect(disconnectedBackendClosed).toBe(true);

          await expect(
            database.applicationPool.query(
              "SELECT 1 AS client_disconnect_recovered"
            )
          ).resolves.toMatchObject({
            rows: [{ client_disconnect_recovered: 1 }]
          });

          // An idle, long-running transaction is terminated by PostgreSQL's
          // transaction timeout; the dead client is discarded, not reused.
          const idleTransactionClient =
            await database.applicationPool.connect();

          try {
            await idleTransactionClient.query("BEGIN");

            await idleTransactionClient.query(
              "SET LOCAL idle_in_transaction_session_timeout = '" +
              `${LONG_TRANSACTION_IDLE_TIMEOUT_MS}ms'`
            );

            await idleTransactionClient.query("SELECT 1");
            await wait(LONG_TRANSACTION_WAIT_MS);

            await expect(
              idleTransactionClient.query("SELECT 1")
            ).rejects.toMatchObject({
              code: "25P03"
            });
          } finally {
            idleTransactionClient.release(true);
          }

          await expect(
            database.applicationPool.query(
              "SELECT 1 AS idle_transaction_recovered"
            )
          ).resolves.toMatchObject({
            rows: [{ idle_transaction_recovered: 1 }]
          });

          // Terminating one backend simulates a broken client connection. The
          // pool must discard it and create a new authenticated session.
          const terminatedClient = await database.applicationPool.connect();
          let terminatedClientReleased = false;

          try {
            const pidResult = await terminatedClient.query<{ pid: number }>(
              "SELECT pg_backend_pid()::integer AS pid"
            );

            const backendPid = pidResult.rows[0]?.pid;

            if (
              typeof backendPid !== "number" ||
              !Number.isSafeInteger(backendPid) ||
              backendPid <= 0
            ) {
              throw new Error("PostgreSQL did not return a valid backend PID.");
            }

            const terminated =
              await database.adminPool.query<{ terminated: boolean }>(
                "SELECT pg_terminate_backend($1) AS terminated",
                [backendPid]
              );

            expect(terminated.rows[0]?.terminated).toBe(true);

            await expect(
              terminatedClient.query("SELECT 1")
            ).rejects.toMatchObject({
              code: "57P01"
            });

            terminatedClient.release(true);
            terminatedClientReleased = true;
          } finally {
            if (!terminatedClientReleased) {
              terminatedClient.release(true);
            }
          }

          await expect(
            database.applicationPool.query(
              "SELECT 1 AS broken_client_recovered"
            )
          ).resolves.toMatchObject({
            rows: [{ broken_client_recovered: 1 }]
          });

          // Runtime shutdown is idempotent; calls after close must fail closed.
          await database.runtime.verifyRuntimeRoleSafety();
          await database.runtime.close();

          await expect(
            database.runtime.verifyRuntimeRoleSafety()
          ).rejects.toThrow();

          // Close every canonical B4 pool before restarting the isolated server.
          // This avoids injecting a controlled outage into any other integration
          // suite and leaves only the dedicated restart probe connected.
          await database.close();
          database = undefined;

          if (originalAdminUrl === undefined) {
            delete process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
          } else {
            process.env.HOMIO_TEST_POSTGRES_ADMIN_URL = originalAdminUrl;
          }

          restartPool = new Pool({
            connectionString: adminUrl,
            max: 1,
            connectionTimeoutMillis: 5_000,
            idleTimeoutMillis: 120_000
          });

          /*
           * pg's runtime Pool inherits EventEmitter, but the installed public
           * Pool declaration does not expose .on(). Verify the runtime contract
           * before registering the idle-client error observer. This avoids an
           * unchecked structural cast and preserves strict callback typing.
           */
          if (!(restartPool instanceof EventEmitter)) {
            throw new Error(
              "The PostgreSQL pool does not expose the required EventEmitter error channel."
            );
          }

          restartPool.on("error", (error: Error) => {
            restartPoolErrors.push(error);
          });

          await expect(
            restartPool.query("SELECT 1 AS before_restart")
          ).resolves.toMatchObject({
            rows: [{ before_restart: 1 }]
          });

          const idleBeforeRestart = await restartPool.connect();
          await idleBeforeRestart.query("SELECT 1");
          idleBeforeRestart.release();

          runDocker(
            ["restart", "--time", "3", containerName],
            { timeoutMs: 60_000 }
          );

          await waitForPostgresContainer(containerName);

          let recoveredAfterRestart = false;
          const recoveryDeadline = Date.now() + 30_000;
          let lastRecoveryError: unknown;

          while (Date.now() < recoveryDeadline) {
            try {
              const result = await restartPool.query<{
                recovered: number;
              }>("SELECT 1 AS recovered");

              if (result.rows[0]?.recovered === 1) {
                recoveredAfterRestart = true;
                break;
              }
            } catch (error) {
              lastRecoveryError = error;
              await wait(CONTAINER_POLL_INTERVAL_MS);
            }
          }

          expect(
            recoveredAfterRestart,
            "The PostgreSQL pool did not recover after server restart: " +
              String(lastRecoveryError ?? "no query result")
          ).toBe(true);

          expect(restartPoolErrors.length).toBeGreaterThan(0);

          await restartPool.end();
          restartPool = undefined;
        } catch (error) {
          testError = error;
        } finally {
          if (originalAdminUrl === undefined) {
            delete process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
          } else {
            process.env.HOMIO_TEST_POSTGRES_ADMIN_URL = originalAdminUrl;
          }

          if (restartPool !== undefined) {
            try {
              await restartPool.end();
            } catch (error) {
              cleanupErrors.push(
                error instanceof Error
                  ? error
                  : new Error(
                      "The PostgreSQL restart probe pool did not close cleanly.",
                      { cause: error }
                    )
              );
            }
          }

          if (database !== undefined) {
            try {
              await database.close();
            } catch (error) {
              cleanupErrors.push(
                error instanceof Error
                  ? error
                  : new Error(
                      "B4 database helper cleanup failed.",
                      { cause: error }
                    )
              );
            }
          }

          if (containerCreated) {
            try {
              runDocker(
                ["rm", "--force", containerName],
                { timeoutMs: 30_000 }
              );
            } catch (error) {
              cleanupErrors.push(
                error instanceof Error
                  ? error
                  : new Error(
                      "The isolated PostgreSQL container cleanup failed.",
                      { cause: error }
                    )
              );
            }
          }
        }

        if (testError !== undefined && cleanupErrors.length > 0) {
          throw new AggregateError(
            [testError, ...cleanupErrors],
            "B4 PostgreSQL operational verification and cleanup both failed."
          );
        }

        if (testError !== undefined) {
          throw testError;
        }

        if (cleanupErrors.length > 0) {
          throw new AggregateError(
            cleanupErrors,
            "B4 PostgreSQL operational resources were not completely closed."
          );
        }
      },
      TEST_TIMEOUT_MS
    );
  }
);
