
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

function importsFastify(source: string): boolean {
  return /(?:\bfrom\s*|\bimport\s*\(|\brequire\s*\()\s*["']fastify["']/.test(
    source
  );
}

function getFastifyFactoryNames(
  source: string
): string[] {
  const names = new Set<string>(["Fastify"]);

  const defaultImport = source.match(
    /\bimport\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:,\s*\{[\s\S]*?\})?\s+from\s*["']fastify["']/
  );

  if (defaultImport?.[1]) {
    names.add(defaultImport[1]);
  }

  const requireImport = source.match(
    /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*require\(["']fastify["']\)/
  );

  if (requireImport?.[1]) {
    names.add(requireImport[1]);
  }

  return [...names].filter((name) =>
    new RegExp(`\\b${name}\\s*\\(`, "g").test(source)
  );
}

describe("single public API ownership", () => {
  it("keeps one Fastify factory and one Fastify HTTP listener", async () => {
    const files = await collectSourceFiles(CONTROL_ROOT);

    const fastifyFactories: string[] = [];
    const listeners: string[] = [];

    for (const file of files) {
      const source = await readFile(file, "utf8");

      if (!importsFastify(source)) {
        continue;
      }

      const relativePath = relative(
        CONTROL_ROOT,
        file
      );

      for (const factoryName of getFastifyFactoryNames(source)) {
        const factoryPattern = new RegExp(
          `\\b${factoryName}\\s*\\(`,
          "g"
        );

        const factoryCount = (
          source.match(factoryPattern) ?? []
        ).length;

        for (let index = 0; index < factoryCount; index += 1) {
          fastifyFactories.push(relativePath);
        }
      }

      const listenerCount = (
        source.match(/\.listen\s*\(/g) ?? []
      ).length;

      for (let index = 0; index < listenerCount; index += 1) {
        listeners.push(relativePath);
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
