
import { randomUUID } from "node:crypto";

import Fastify, {
  type FastifyInstance,
  type FastifyPluginAsync
} from "fastify";

import type { BackendSecurityRuntime } from "./security/contracts.js";
import {
  assertBackendSecurityRuntime,
  createApiSecurityHook,
  createMutationReauthorizationHook,
  isValidApiRouteSecurityContract
} from "./security/api-security.js";
import type { BackendSettings } from "./config/settings.js";

export interface AppRuntime {
  readonly server: FastifyInstance;
  markReady(): void;
  markDraining(): void;
  isReady(): boolean;
}

const NOT_FOUND_RESPONSE = {
  statusCode: 404,
  error: "Not Found",
  message: "Route not found."
} as const;

type ErrorWithStatusCode = Error & {
  readonly statusCode?: unknown;
};

function getKnownError(
  value: unknown
): ErrorWithStatusCode | undefined {
  if (!(value instanceof Error)) {
    return undefined;
  }

  return value as ErrorWithStatusCode;
}

function getClientErrorStatus(
  error: ErrorWithStatusCode | undefined
): number {
  const candidateStatus = error?.statusCode;

  if (
    typeof candidateStatus === "number" &&
    Number.isInteger(candidateStatus) &&
    candidateStatus >= 400 &&
    candidateStatus < 500
  ) {
    return candidateStatus;
  }

  return 500;
}

export async function buildApp(
  settings: BackendSettings,
  apiV1Plugins: readonly FastifyPluginAsync[] = [],
  securityRuntime?: BackendSecurityRuntime
): Promise<AppRuntime> {
  let acceptingTraffic = false;
  let draining = false;
  let closed = false;

  const server = Fastify({
    logger:
      settings.nodeEnv === "test"
        ? false
        : {
            level: settings.logLevel,
            serializers: {
              req(request) {
                return {
                  method: request.method
                };
              }
            },
            redact: {
              paths: [
                "req.headers.authorization",
                "req.headers.cookie",
                "headers.authorization",
                "headers.cookie"
              ],
              censor: "[REDACTED]"
            }
          },
    trustProxy: false,
    requestIdHeader: false,
    genReqId: () => randomUUID(),
    bodyLimit: 1_048_576,
    requestTimeout: settings.requestTimeoutMs
  });

  server.decorateRequest("securityContext", null);

  server.addHook("onClose", async () => {
    acceptingTraffic = false;
    draining = true;
    closed = true;
  });

  server.setNotFoundHandler((request, reply) => {
    return reply.code(404).send({
      ...NOT_FOUND_RESPONSE,
      requestId: request.id
    });
  });

  server.setErrorHandler((error, request, reply) => {
    const knownError = getKnownError(error);
    const statusCode = getClientErrorStatus(knownError);

    const publicMessage =
      statusCode === 400
        ? "Request validation failed."
        : statusCode === 413
          ? "Request body is too large."
          : statusCode >= 500
            ? "An unexpected server error occurred."
            : "Request could not be processed.";

    const errorName =
      knownError !== undefined &&
      /^[A-Za-z][A-Za-z0-9]{0,63}$/.test(knownError.name)
        ? knownError.name
        : "Error";

    if (statusCode >= 500) {
      request.log.error(
        {
          requestId: request.id,
          statusCode,
          errorName
        },
        "Unhandled API request failure"
      );
    } else {
      request.log.warn(
        {
          requestId: request.id,
          statusCode
        },
        "API request rejected"
      );
    }

    return reply.code(statusCode).send({
      statusCode,
      error:
        statusCode >= 500
          ? "Internal Server Error"
          : "Request Error",
      message: publicMessage,
      requestId: request.id
    });
  });

  const healthRoutes: FastifyPluginAsync = async (instance) => {
    instance.get("/health/live", async (_request, reply) => {
      return reply.code(200).send({
        status: "ok"
      });
    });

    instance.get("/health/ready", async (_request, reply) => {
      if (!acceptingTraffic) {
        return reply.code(503).send({
          status: "not_ready"
        });
      }

      return reply.code(200).send({
        status: "ready"
      });
    });
  };

  try {
    await server.register(healthRoutes);

    if (apiV1Plugins.length > 0) {
      const activeSecurityRuntime = securityRuntime;

      if (activeSecurityRuntime === undefined) {
        throw new Error(
          "Protected API plugins require the complete B2 security runtime."
        );
      }

      // Validate the six authoritative adapters before registering customer routes.
      assertBackendSecurityRuntime(activeSecurityRuntime);

      await server.register(async (apiV1) => {
        apiV1.addHook("onRoute", (routeOptions) => {
          if (
            !isValidApiRouteSecurityContract(routeOptions)
          ) {
            throw new Error(
              "Every /api/v1 route must declare valid security metadata and mutation schemas."
            );
          }
        });

        apiV1.addHook(
          "onRequest",
          createApiSecurityHook(activeSecurityRuntime)
        );

        // Re-check protected mutations after Fastify request validation
        // and immediately before their route handlers execute.
        apiV1.addHook(
          "preHandler",
          createMutationReauthorizationHook(activeSecurityRuntime)
        );

        for (const plugin of apiV1Plugins) {
          await apiV1.register(plugin);
        }
      }, {
        prefix: "/api/v1"
      });
    }

    await server.ready();

    return {
      server,

      markReady(): void {
        if (draining || closed) {
          throw new Error(
            "Backend cannot become ready after shutdown has started."
          );
        }

        acceptingTraffic = true;
      },

      markDraining(): void {
        acceptingTraffic = false;
        draining = true;
      },

      isReady(): boolean {
        return acceptingTraffic && !draining && !closed;
      }
    };
  } catch (error) {
    await server.close().catch(() => undefined);
    throw error;
  }
}
