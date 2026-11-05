import Fastify, {
  type FastifyInstance,
  type FastifyPluginAsync
} from "fastify";

import type { BackendSettings } from "./config/settings.js";

export interface AppRuntime {
  readonly server: FastifyInstance;

  markDraining(): void;

  isReady(): boolean;
}

const NOT_FOUND_RESPONSE = {
  statusCode: 404,
  error: "Not Found",
  message: "Route not found."
} as const;

export async function buildApp(
  settings: BackendSettings,
  apiV1Plugins: readonly FastifyPluginAsync[] = []
): Promise<AppRuntime> {
  let acceptingTraffic = false;

  const server = Fastify({
    logger:
      settings.nodeEnv === "test"
        ? false
        : {
            level: settings.logLevel,
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

    bodyLimit: 1_048_576,

    requestTimeout: settings.requestTimeoutMs
  });

  server.setNotFoundHandler(
    (request, reply) => {
      return reply.code(404).send({
        ...NOT_FOUND_RESPONSE,
        requestId: request.id
      });
    }
  );

  server.setErrorHandler(
    (error, request, reply) => {
      const candidateStatus = error.statusCode;

      const statusCode =
        typeof candidateStatus === "number" &&
        Number.isInteger(candidateStatus) &&
        candidateStatus >= 400 &&
        candidateStatus < 500
          ? candidateStatus
          : 500;

      const publicMessage =
        statusCode === 400
          ? "Request validation failed."
          : statusCode === 413
            ? "Request body is too large."
            : statusCode >= 500
              ? "An unexpected server error occurred."
              : "Request could not be processed.";

      const errorName =
        /^[A-Za-z][A-Za-z0-9]{0,63}$/.test(error.name)
          ? error.name
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
    }
  );

  const healthRoutes: FastifyPluginAsync = async (instance) => {
    instance.get(
      "/health/live",
      async (_request, reply) => {
        return reply.code(200).send({
          status: "ok"
        });
      }
    );

    instance.get(
      "/health/ready",
      async (_request, reply) => {
        if (!acceptingTraffic) {
          return reply.code(503).send({
            status: "not_ready"
          });
        }

        return reply.code(200).send({
          status: "ready"
        });
      }
    );
  };

  try {
    // 1. Register application health routes.
    await server.register(healthRoutes);

    // 2. Register only explicitly supplied v1 API plugins.
    for (const plugin of apiV1Plugins) {
      await server.register(plugin, {
        prefix: "/api/v1"
      });
    }

    // 3. Validate the complete Fastify plugin graph.
    await server.ready();

    acceptingTraffic = true;

    return {
      server,

      markDraining(): void {
        acceptingTraffic = false;
      },

      isReady(): boolean {
        return acceptingTraffic;
      }
    };
  } catch (error) {
    await server.close().catch(() => undefined);
    throw error;
  }
}
