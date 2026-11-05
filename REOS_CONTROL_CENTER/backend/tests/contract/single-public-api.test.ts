import {
  describe,
  expect,
  it
} from "vitest";

import {
  readdir,
  readFile
} from "node:fs/promises";

import {
  extname,
  relative,
  resolve
} from "node:path";

import { fileURLToPath } from "node:url";

const BACKEND_ROOT = fileURLToPath(
  new URL("../../", import.meta.url)
);

const CONTROL_ROOT = resolve(
  BACKEND_ROOT,
  ".."
);

const SOURCE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".mts",
  ".cts",
  ".js",
  ".mjs",
  ".cjs"
]);

const IGNORED_DIRECTORIES = new Set([
  ".git",
  "node_modules",
  ".next",
  "dist",
  "coverage",
  "build",
  "__pycache__",
  ".venv"
]);

async function collectSourceFiles(
  directory: string
): Promise<string[]> {
  const entries = await readdir(directory, {
    withFileTypes: true
  });

  const results = await Promise.all(
    entries.map(async (entry) => {
      const path = resolve(directory, entry.name);

      if (entry.isDirectory()) {
        if (
          IGNORED_DIRECTORIES.has(entry.name) ||
          entry.name.startsWith("REOS_LAYER_BACKUP_")
        ) {
          return [];
        }

        return collectSourceFiles(path);
      }

      if (
        entry.isFile() &&
        SOURCE_EXTENSIONS.has(extname(entry.name))
      ) {
        return [path];
      }

      return [];
    })
  );

  return results.flat();
}

describe("single public API ownership", () => {
  it("keeps one Fastify factory and one HTTP listener", async () => {
    const files = await collectSourceFiles(CONTROL_ROOT);

    const fastifyFactories: string[] = [];
    const listeners: string[] = [];

    for (const file of files) {
      const source = await readFile(file, "utf8");

      if (/\bFastify\s*\(/.test(source)) {
        fastifyFactories.push(relative(CONTROL_ROOT, file));
      }

      if (/\.listen\s*\(/.test(source)) {
        listeners.push(relative(CONTROL_ROOT, file));
      }
    }

    expect(fastifyFactories).toEqual([
      "backend/src/app.ts"
    ]);

    expect(listeners).toEqual([
      "backend/src/main.ts"
    ]);
  });
});
