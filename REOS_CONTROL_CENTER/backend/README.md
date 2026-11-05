
# HOMIO / REOS Backend

The backend is the single public Fastify API boundary for HOMIO / REOS.

It is a backend-only application. It does not implement business-domain
invariants, a second AI platform, a second event engine, or background
worker orchestration.

## Runtime

- Node.js 24
- Fastify 5
- TypeScript
- Vitest
- ESLint

## Installation

The committed package-lock.json is required.

Install exact dependencies:

    npm ci

Run all B1 verification:

    npm run verify

Create a production build:

    npm run build

Run the deterministic build check:

    npm run verify:build-reproducibility

Start the compiled application:

    npm start

## Configuration

Configuration is validated before the application starts.

Supported environment variables:

| Variable | Default |
|---|---|
| NODE_ENV | development |
| HOMIO_BACKEND_HOST | 127.0.0.1 |
| HOMIO_BACKEND_PORT | 3001 |
| HOMIO_LOG_LEVEL | info |
| HOMIO_REQUEST_TIMEOUT_MS | 30000 |
| HOMIO_SHUTDOWN_TIMEOUT_MS | 10000 |

The bind host must be a valid IP address or DNS hostname.

Ports must be between 1 and 65535.

Timeouts must be between 1000 and 120000 milliseconds.

Invalid values stop startup. Configuration errors report variable names
and validation reasons, not raw environment values.

## Health endpoints

### GET /health/live

Reports whether the process can respond to HTTP requests.

Liveness remains independent of readiness.

### GET /health/ready

Reports whether the application is accepting traffic.

Readiness remains false until the HTTP listener starts successfully.

Readiness changes to 503 before graceful shutdown begins.

## Composition order

The application registers:

1. Application error and not-found handlers.
2. Liveness and readiness routes.
3. Explicitly supplied versioned API route plugins.
4. Fastify readiness validation.

Versioned route plugins are mounted under `/api/v1`.

The same plugin composition is supported by buildApp and startBackend.
There is one Fastify application factory and one HTTP listener owner.

## Runtime ownership

`src/app.ts` owns the single Fastify instance and route composition.

`src/main.ts` owns startup, process signals and graceful shutdown.

`src/config/` owns configuration validation and typed settings.

The public API entry point does not start a background worker.

## Graceful shutdown

Shutdown changes readiness to false before closing the server.

Active requests are allowed to finish during the graceful period.

The configured shutdown deadline bounds the shutdown wait. When the
deadline is exceeded, remaining connections are closed and shutdown
reports failure.

Repeated shutdown calls share the same shutdown operation.

## Reproducible build verification

The verification command:

1. Runs ESLint.
2. Runs TypeScript type checking.
3. Runs unit and contract tests.
4. Creates a clean production build.
5. Fingerprints every generated production file.
6. Creates a second clean production build.
7. Compares output file counts and SHA-256 fingerprints.

A reproducible build passes only when both clean builds produce identical
relative file paths and file contents.

## Verification

CI uses `npm ci` against the committed lockfile before running verification.

The B1 completion check must use the exact tested commit SHA.
