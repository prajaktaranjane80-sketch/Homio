/* global process */

import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import {
  relative,
  resolve,
  sep
} from "node:path";
import { fileURLToPath } from "node:url";

const BACKEND_ROOT = fileURLToPath(
  new URL("../", import.meta.url)
);

const DIST_ROOT = resolve(
  BACKEND_ROOT,
  "dist"
);

function runBuild(label) {
  const npmExecutable = process.env.npm_execpath;

  if (
    typeof npmExecutable !== "string" ||
    npmExecutable.length === 0
  ) {
    throw new Error(
      "Build reproducibility must run through npm."
    );
  }

  process.stdout.write(
    `B1_REPRODUCIBLE_BUILD=${label}:START\n`
  );

  const result = spawnSync(
    process.execPath,
    [
      resolve(npmExecutable),
      "run",
      "build"
    ],
    {
      cwd: BACKEND_ROOT,
      env: process.env,
      stdio: "inherit"
    }
  );

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(
      `The ${label} production build failed with status ${String(result.status)}.`
    );
  }
}

async function collectBuildFiles(
  directory,
  output = []
) {
  const entries = await readdir(directory, {
    withFileTypes: true
  });

  entries.sort((left, right) =>
    left.name < right.name
      ? -1
      : left.name > right.name
        ? 1
        : 0
  );

  for (const entry of entries) {
    const absolutePath = resolve(
      directory,
      entry.name
    );

    if (entry.isDirectory()) {
      await collectBuildFiles(
        absolutePath,
        output
      );

      continue;
    }

    if (!entry.isFile()) {
      throw new Error(
        `Unsupported build output entry: ${absolutePath}`
      );
    }

    output.push(absolutePath);
  }

  return output;
}

async function fingerprintBuild() {
  const files = await collectBuildFiles(
    DIST_ROOT
  );

  if (files.length === 0) {
    throw new Error(
      "Production build produced no files."
    );
  }

  const hash = createHash("sha256");

  for (const absolutePath of files) {
    const relativePath = relative(
      DIST_ROOT,
      absolutePath
    ).split(sep).join("/");

    const content = await readFile(
      absolutePath
    );

    hash.update(relativePath);
    hash.update("\0");
    hash.update(content);
    hash.update("\0");
  }

  return {
    sha256: hash.digest("hex"),
    fileCount: files.length
  };
}

async function main() {
  await runBuild("first");

  const firstBuild = await fingerprintBuild();

  await runBuild("second");

  const secondBuild = await fingerprintBuild();

  if (
    firstBuild.sha256 !== secondBuild.sha256 ||
    firstBuild.fileCount !== secondBuild.fileCount
  ) {
    throw new Error(
      "Production build outputs differ between clean builds."
    );
  }

  process.stdout.write(
    `B1_REPRODUCIBLE_BUILD_FILES=${secondBuild.fileCount}\n`
  );

  process.stdout.write(
    `B1_REPRODUCIBLE_BUILD_SHA256=${secondBuild.sha256}\n`
  );

  process.stdout.write(
    "B1_REPRODUCIBLE_BUILD=PASS\n"
  );
}

main().catch((error) => {
  const message =
    error instanceof Error
      ? error.message
      : "Unknown reproducible build failure.";

  process.stderr.write(
    `B1_REPRODUCIBLE_BUILD=FAIL: ${message}\n`
  );

  process.exitCode = 1;
});
