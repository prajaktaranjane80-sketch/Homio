import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();

function fail(message) {
  console.error(`FAIL-CLOSED: ${message}`);
  process.exit(1);
}

function readJson(relativePath) {
  const absolutePath = path.join(root, relativePath);

  if (!fs.existsSync(absolutePath)) {
    fail(`Required dependency file is missing: ${relativePath}`);
  }

  try {
    return JSON.parse(fs.readFileSync(absolutePath, "utf8"));
  } catch {
    fail(`Invalid JSON in dependency file: ${relativePath}`);
  }
}

const manifest = readJson("package.json");
const lock = readJson("package-lock.json");

if (lock.lockfileVersion !== 3) {
  fail(
    `Expected npm lockfileVersion 3; found ${lock.lockfileVersion ?? "missing"}.`,
  );
}

const lockedRoot = lock.packages?.[""];

if (!lockedRoot) {
  fail("package-lock.json is missing its root package record.");
}

if (
  lockedRoot.name !== manifest.name ||
  lockedRoot.version !== manifest.version
) {
  fail("package.json and package-lock.json root identity do not match.");
}

for (const section of [
  "dependencies",
  "devDependencies",
  "optionalDependencies",
]) {
  const declared = manifest[section] ?? {};
  const lockedDeclarations = lockedRoot[section] ?? {};

  const declaredNames = Object.keys(declared).sort();
  const lockedNames = Object.keys(lockedDeclarations).sort();

  if (JSON.stringify(declaredNames) !== JSON.stringify(lockedNames)) {
    fail(
      `${section} declarations differ between package.json and package-lock.json.`,
    );
  }

  for (const [name, requestedVersion] of Object.entries(declared)) {
    if (lockedDeclarations[name] !== requestedVersion) {
      fail(
        `${section} version declaration mismatch for "${name}".`,
      );
    }

    const installRecord = lock.packages?.[`node_modules/${name}`];

    if (!installRecord || typeof installRecord.version !== "string") {
      fail(`Resolved installation record missing for "${name}".`);
    }

    if (
      typeof installRecord.resolved !== "string" ||
      !installRecord.resolved.startsWith("https://")
    ) {
      fail(`Expected an HTTPS package source for "${name}".`);
    }

    if (
      typeof installRecord.integrity !== "string" ||
      !installRecord.integrity.trim()
    ) {
      fail(`Integrity metadata missing for "${name}".`);
    }
  }
}

console.log("");
console.log("===============================================");
console.log("FRONTEND DEPENDENCY LOCK CONTRACT = PASS");
console.log("LOCKFILE V3                      = PASS");
console.log("ROOT PACKAGE IDENTITY            = PASS");
console.log("DIRECT DEPENDENCY DECLARATIONS    = PASS");
console.log("RESOLVED DIRECT DEPENDENCIES      = PASS");
console.log("HTTPS PACKAGE SOURCES             = PASS");
console.log("INTEGRITY METADATA                = PASS");
console.log("===============================================");
