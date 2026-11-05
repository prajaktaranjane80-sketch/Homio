
import { readFile } from "node:fs/promises";

import { resolve } from "node:path";

import { fileURLToPath } from "node:url";

import {
  describe,
  expect,
  it
} from "vitest";

const REPOSITORY_ROOT = fileURLToPath(
  new URL("../../../../", import.meta.url)
);

const BACKEND_CI_ACTION = resolve(
  REPOSITORY_ROOT,
  ".github/actions/homio-backend-ci/verification/action.yml"
);

const B1_START_MARKER =
  "# BACKEND-001-B1: Unified Fastify API foundation.";

const B1_END_MARKER =
  "# Existing ACRL evidence and cache publication.";

describe("BACKEND-001-B1 CI enforcement contract", () => {
  it("requires committed backend manifests and lockfile", async () => {
    const actionSource = await readFile(
      BACKEND_CI_ACTION,
      "utf8"
    );

    const start = actionSource.indexOf(
      B1_START_MARKER
    );

    const end = actionSource.indexOf(
      B1_END_MARKER,
      start + B1_START_MARKER.length
    );

    expect(start).toBeGreaterThanOrEqual(0);
    expect(end).toBeGreaterThan(start);

    const b1Section = actionSource.slice(
      start,
      end
    );

    expect(b1Section).toContain(
      "test -s REOS_CONTROL_CENTER/backend/package.json"
    );

    expect(b1Section).toContain(
      "test -s REOS_CONTROL_CENTER/backend/package-lock.json"
    );

    expect(b1Section).toContain(
      "git ls-files --error-unmatch"
    );

    expect(b1Section).toContain(
      "node-version: \"24\""
    );

    expect(b1Section).toContain(
      "cache-dependency-path: REOS_CONTROL_CENTER/backend/package-lock.json"
    );

    expect(b1Section).toContain(
      "npm ci --no-audit --fund=false"
    );

    expect(b1Section).toContain(
      "npm run verify"
    );

    expect(b1Section).not.toMatch(
      /^\s*if\s*:/m
    );

    expect(b1Section).not.toContain(
      "hashFiles("
    );

    expect(b1Section).not.toContain(
      "npm install --package-lock-only"
    );

    expect(b1Section).not.toContain(
      "lockfile_generated"
    );

    expect(
      b1Section.indexOf("npm ci --no-audit --fund=false")
    ).toBeLessThan(
      b1Section.indexOf("npm run verify")
    );
  });
});
