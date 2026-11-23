import {
  lstat,
  readFile,
  readdir
} from "node:fs/promises";

import {
  resolve,
  sep
} from "node:path";

import {
  validatePostgresMigrationManifest
} from "./postgres-migrations.js";

import type {
  ValidatedPostgresMigration
} from "./postgres-migrations.js";

const MIGRATION_FILE_PATTERN =
  /^([0-9]{8})-([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\.sql$/;

const ROLE_PATTERN =
  /^[a-z_][a-z0-9_$]{0,62}$/;

const SCHEMA_PATTERN =
  /^[a-z][a-z0-9_]{0,62}$/;

export interface PostgresMigrationManifestOptions {
  readonly migrationRole: string;
  readonly applicationRole: string;
  readonly schemaName: string;
}

function quoteIdentifier(value: string): string {
  return `"${value.replaceAll('"', '""')}"`;
}

function validateOptions(
  options: PostgresMigrationManifestOptions
): PostgresMigrationManifestOptions {
  if (
    typeof options !== "object" ||
    options === null ||
    !ROLE_PATTERN.test(options.migrationRole) ||
    !ROLE_PATTERN.test(options.applicationRole) ||
    options.migrationRole === options.applicationRole ||
    !SCHEMA_PATTERN.test(options.schemaName)
  ) {
    throw new TypeError(
      "PostgreSQL migration roles and schema name are invalid."
    );
  }

  return Object.freeze({ ...options });
}

function assertDirectoryPath(path: string): string {
  if (typeof path !== "string" || path.trim().length === 0) {
    throw new TypeError(
      "A PostgreSQL migration directory is required."
    );
  }

  return resolve(path);
}

export async function loadPostgresMigrationManifest(
  directory: string,
  rawOptions: PostgresMigrationManifestOptions
): Promise<readonly ValidatedPostgresMigration[]> {
  const options = validateOptions(rawOptions);
  const root = assertDirectoryPath(directory);

  const rootStat = await lstat(root);

  if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) {
    throw new Error(
      "The PostgreSQL migration path must be a real directory."
    );
  }

  const entries = await readdir(root, {
    withFileTypes: true
  });

  const migrations: {
    id: string;
    name: string;
    sql: string;
  }[] = [];

  const applicationRole = quoteIdentifier(
    options.applicationRole
  );

  for (const entry of entries) {
    if (
      entry.isDirectory() ||
      entry.isSymbolicLink() ||
      !entry.isFile()
    ) {
      throw new Error(
        "The PostgreSQL migration directory may contain regular SQL files only."
      );
    }

    const match = MIGRATION_FILE_PATTERN.exec(entry.name);

    if (match === null) {
      throw new Error(
        `Invalid PostgreSQL migration filename: ${entry.name}`
      );
    }

    const filePath = resolve(root, entry.name);

    if (
      !filePath.startsWith(`${root}${sep}`)
    ) {
      throw new Error(
        "A PostgreSQL migration resolved outside its directory."
      );
    }

    const fileStat = await lstat(filePath);

    if (!fileStat.isFile() || fileStat.isSymbolicLink()) {
      throw new Error(
        `PostgreSQL migration is not a regular file: ${entry.name}`
      );
    }

    const source = await readFile(filePath, "utf8");

    if (source.trim().length === 0) {
      throw new Error(
        `PostgreSQL migration is empty: ${entry.name}`
      );
    }

    let sql = source.replace(/\r\n/g, "\n");

    sql = sql.replaceAll(
      "__HOMIO_APPLICATION_ROLE__",
      applicationRole
    );

    sql = sql.replaceAll(
      "__HOMIO_CORE002_SCHEMA__",
      quoteIdentifier(options.schemaName)
    );

    if (/__HOMIO_[A-Z0-9_]+__/.test(sql)) {
      throw new Error(
        `Unresolved deployment token in migration: ${entry.name}`
      );
    }

    migrations.push({
      id: match[1] ?? "",
      name: match[2] ?? "",
      sql
    });
  }

  migrations.sort((left, right) =>
    left.id.localeCompare(right.id)
  );

  return validatePostgresMigrationManifest(migrations);
}
