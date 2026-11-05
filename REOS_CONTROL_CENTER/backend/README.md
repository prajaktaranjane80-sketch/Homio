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

Start the compiled application:

    npm start

## Configuration

Configuration is validated before the server starts.

Supported environment variables:

| Variable | Default |
|---|---|
| NODE_ENV | development |
| HOMIO_BACKEND_HOST | 127.0.0.1 |
| HOMIO_BACKEND_PORT | 3001 |
| HOMIO_LOG_LEVEL | info |
| HOMIO_REQUEST_TIMEOUT_MS | 30000 |
| HOMIO_SHUTDOWN_TIMEOUT_MS | 10000 |

Invalid values stop startup. Configuration errors report variable names
and validation reasons, not raw environment values.

## Health endpoints

### GET /health/live

Reports whether the process can respond to HTTP requests.

### GET /health/ready

Reports whether the application is accepting traffic.

Readiness changes to `503` before graceful shutdown begins.
Liveness remains independent of readiness.

## Composition order

The application registers:

1. Application error and not-found handlers.
2. Liveness and readiness routes.
3. Explicitly supplied versioned API route plugins.
4. Fastify readiness validation.

Versioned route plugins are mounted under `/api/v1`.

## Runtime ownership

`src/app.ts` owns the single Fastify instance and route composition.

`src/main.ts` owns startup, process signals and graceful shutdown.

`src/config/` owns configuration validation and typed settings.

No background worker is started by the public API entry point.

## Verification

The `verify` command runs:

1. ESLint.
2. TypeScript type checking.
3. Unit and contract tests.
4. A clean production build.

CI uses `npm ci` against the committed lockfile before running verification.
