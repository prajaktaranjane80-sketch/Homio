#!/usr/bin/env python3
"""Verify the real PostgreSQL migration-ledger bootstrap against its TS owner.

This is a disposable PostgreSQL 18.4 CI test only. It creates temporary roles
and the infrastructure ledger, verifies the exact catalog contract consumed
by PostgresMigrationRunner, proves the API role cannot read or create in the
infrastructure schema, exercises valid/invalid ledger writes, and drops every
fixture object. It never creates or mutates HOMIO business tables.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP_SQL = (
    ROOT
    / "REOS_CONTROL_CENTER"
    / "backend"
    / "scripts"
    / "postgres"
    / "bootstrap-migration-ledger.sql"
)
MIGRATION_SOURCE = (
    ROOT
    / "REOS_CONTROL_CENTER"
    / "backend"
    / "src"
    / "persistence"
    / "postgres-migrations.ts"
)
VERIFY_SQL_PATTERN = re.compile(
    r"export const POSTGRES_MIGRATION_VERIFY_SQL\s*=\s*`(?P<sql>.*?)`\.trim\(\);",
    re.DOTALL,
)

MIGRATION_ROLE = "homio_b4_migrator"
APPLICATION_ROLE = "homio_b4_ledger_api"
VALID_MIGRATION_ID = "00000001"
VALID_MIGRATION_NAME = "bootstrap-contract-check"
VALID_CHECKSUM = "a" * 64


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_source_sql(path: Path, pattern: re.Pattern[str]) -> str:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Cannot read canonical source file: {path}") from exc

    matches = list(pattern.finditer(source))
    require(len(matches) == 1, f"Expected exactly one SQL owner in {path}.")
    sql = matches[0].group("sql").strip()
    require(bool(sql) and "${" not in sql and "`" not in sql,
            f"Canonical SQL is malformed in {path}.")
    return sql


def run_psql(
    *,
    container_id: str,
    user: str,
    password: str,
    sql: str,
    environment: dict[str, str] | None = None,
    must_succeed: bool = True,
) -> subprocess.CompletedProcess[str]:
    require(bool(password) and "\x00" not in password,
            "A valid PostgreSQL password is required.")

    command = ["docker", "exec", "--env", "PGPASSWORD"]
    if environment:
        for name in environment:
            command.extend(["--env", name])
    command.extend([
        "-i", container_id,
        "psql", "--no-psqlrc", "--set", "ON_ERROR_STOP=1",
        "--host=127.0.0.1", f"--username={user}", "--dbname=postgres",
        "--no-align", "--tuples-only", "--quiet",
    ])

    child_environment = os.environ.copy()
    child_environment["PGPASSWORD"] = password
    if environment:
        child_environment.update(environment)

    result = subprocess.run(
        command,
        input=sql,
        text=True,
        capture_output=True,
        check=False,
        timeout=45,
        env=child_environment,
    )

    if must_succeed and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        secrets_to_redact = [password]
        if environment:
            secrets_to_redact.extend(
                value for key, value in environment.items()
                if "PASSWORD" in key.upper()
            )
        for secret in secrets_to_redact:
            if secret:
                detail = detail.replace(secret, "[REDACTED]")
        raise RuntimeError(f"PostgreSQL command failed: {detail[:2000]}")
    if not must_succeed and result.returncode == 0:
        raise RuntimeError("A PostgreSQL operation expected to be denied succeeded.")
    return result


def normalize_check_expression(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    source = value.lower()
    normalized = ""
    inside_string = False
    index = 0
    while index < len(source):
        character = source[index]
        if character == "'":
            normalized += character
            if inside_string and index + 1 < len(source) and source[index + 1] == "'":
                normalized += source[index + 1]
                index += 1
            else:
                inside_string = not inside_string
        elif not inside_string and (character in "()" or character.isspace()):
            pass
        else:
            normalized += character
        index += 1
    return re.sub(r"::(?:pg_catalog\.)?text\b", "", normalized)


def verify_metadata(container_id: str, migration_password: str) -> None:
    runtime = run_psql(
        container_id=container_id,
        user=MIGRATION_ROLE,
        password=migration_password,
        sql=(
            "SELECT session_user::text || '|' || current_user::text || '|' || "
            "current_setting('server_version_num')::text;"
        ),
    ).stdout.strip()
    runtime_parts = runtime.split("|")
    require(
        len(runtime_parts) == 3
        and runtime_parts[0] == MIGRATION_ROLE
        and runtime_parts[1] == MIGRATION_ROLE
        and runtime_parts[2].isdigit()
        and int(runtime_parts[2]) >= 180004,
        "The migration role/session identity or PostgreSQL 18.4 minimum is invalid.",
    )

    source_sql = load_source_sql(MIGRATION_SOURCE, VERIFY_SQL_PATTERN)
    parameter_count = source_sql.count("$1::name")
    require(parameter_count >= 1 and source_sql.count("$1") == parameter_count,
            "Migration metadata query contains an unsupported SQL parameter.")
    query_sql = source_sql.replace("$1::name", f"'{APPLICATION_ROLE}'::name")
    query = (
        "SELECT row_to_json(homio_migration_metadata)::text FROM (\n"
        f"{query_sql}\n"
        ") AS homio_migration_metadata;"
    )
    output = run_psql(
        container_id=container_id,
        user=MIGRATION_ROLE,
        password=migration_password,
        sql=query,
    ).stdout.strip()
    rows = [line for line in output.splitlines() if line.strip()]
    require(len(rows) == 1, "Migration metadata query must return exactly one ledger row.")
    metadata = json.loads(rows[0])
    require(isinstance(metadata, dict), "Migration metadata result is not an object.")

    expected_columns = [
        "migration_id:text:NO",
        "migration_name:text:NO",
        "checksum:text:NO",
        "applied_at:timestamp with time zone:NO",
    ]
    require(metadata.get("schema_owner") == MIGRATION_ROLE,
            "The infrastructure schema is not owned by the dedicated migration role.")
    require(metadata.get("table_owner") == MIGRATION_ROLE,
            "The migration ledger is not owned by the dedicated migration role.")
    require(metadata.get("columns") == expected_columns,
            "The migration ledger column order/types/nullability do not match its TS owner.")
    require(metadata.get("primary_key") == "PRIMARY KEY (migration_id)",
            "The migration ledger primary key is invalid.")
    require(metadata.get("unique_key") == "UNIQUE (migration_name)",
            "The migration ledger migration-name uniqueness constraint is invalid.")

    check_values = metadata.get("check_expressions")
    normalized_checks = (
        [normalize_check_expression(value) for value in check_values]
        if isinstance(check_values, list)
        else []
    )
    expected_checks = {
        "migration_id~'^[0-9]{8}$'",
        "migration_name~'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'",
        "checksum~'^[a-f0-9]{64}$'",
    }
    require(len(normalized_checks) == 3 and set(normalized_checks) == expected_checks,
            "The migration ledger check constraints do not match the TS owner.")
    require(metadata.get("check_constraints_validated") is True,
            "Migration ledger check constraints must be validated.")
    require(metadata.get("applied_at_default") == "clock_timestamp()",
            "Migration ledger applied_at must use clock_timestamp().")
    require(metadata.get("application_role_has_table_privileges") is False,
            "The API role must have no privilege on the migration ledger.")
    require(metadata.get("application_role_can_create_in_schema") is False,
            "The API role must not be able to create objects in reos_infra.")
    require(metadata.get("row_security_enabled") is False,
            "The infrastructure migration ledger must not carry tenant RLS.")


def verify_privileges(
    container_id: str,
    admin_password: str,
    application_password: str,
    migration_password: str,
) -> None:
    authenticated_role = run_psql(
        container_id=container_id,
        user=APPLICATION_ROLE,
        password=application_password,
        sql="SELECT current_user::text;",
    ).stdout.strip()
    require(authenticated_role == APPLICATION_ROLE,
            "The isolated API role could not authenticate to PostgreSQL.")

    role_flags = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            "SELECT rolname::text || '|' || rolsuper::text || '|' || "
            "rolbypassrls::text || '|' || rolcanlogin::text "
            "FROM pg_roles "
            f"WHERE rolname IN ('{MIGRATION_ROLE}', '{APPLICATION_ROLE}') "
            "ORDER BY rolname;"
        ),
    ).stdout.splitlines()
    require(
        role_flags == [
            f"{APPLICATION_ROLE}|false|false|true",
            f"{MIGRATION_ROLE}|false|false|true",
        ],
        "Migration and API roles must be login roles without superuser/BYPASSRLS.",
    )

    read = run_psql(
        container_id=container_id,
        user=APPLICATION_ROLE,
        password=application_password,
        sql="SELECT migration_id FROM reos_infra.schema_migrations;",
        must_succeed=False,
    )
    require(read.returncode != 0, "The API role unexpectedly read migration history.")

    insert = run_psql(
        container_id=container_id,
        user=APPLICATION_ROLE,
        password=application_password,
        sql=(
            "INSERT INTO reos_infra.schema_migrations "
            "(migration_id, migration_name, checksum) VALUES "
            f"('00000999', 'api-forbidden-write', '{VALID_CHECKSUM}');"
        ),
        must_succeed=False,
    )
    require(insert.returncode != 0,
            "The API role unexpectedly wrote migration history.")

    create = run_psql(
        container_id=container_id,
        user=APPLICATION_ROLE,
        password=application_password,
        sql=(
            "CREATE TABLE reos_infra.api_role_must_not_create "
            "(id integer PRIMARY KEY);"
        ),
        must_succeed=False,
    )
    require(create.returncode != 0,
            "The API role unexpectedly created an object in reos_infra.")

    run_psql(
        container_id=container_id,
        user=MIGRATION_ROLE,
        password=migration_password,
        sql=(
            "CREATE TABLE reos_infra.default_privilege_probe "
            "(id integer PRIMARY KEY);"
        ),
    )
    privilege_probe = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            "SELECT "
            f"has_table_privilege('{APPLICATION_ROLE}', "
            "'reos_infra.default_privilege_probe', 'SELECT')::text || '|' || "
            f"has_table_privilege('{APPLICATION_ROLE}', "
            "'reos_infra.default_privilege_probe', 'INSERT')::text;"
        ),
    ).stdout.strip()
    require(privilege_probe == "false|false",
            "Future migration-owned tables must not inherit API-role privileges.")
    run_psql(
        container_id=container_id,
        user=MIGRATION_ROLE,
        password=migration_password,
        sql="DROP TABLE reos_infra.default_privilege_probe;",
    )


def verify_ledger_constraints(container_id: str, migration_password: str) -> None:
    valid_insert = (
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        f"('{VALID_MIGRATION_ID}', '{VALID_MIGRATION_NAME}', '{VALID_CHECKSUM}') "
        "RETURNING migration_id, migration_name, checksum, applied_at;"
    )
    output = run_psql(
        container_id=container_id,
        user=MIGRATION_ROLE,
        password=migration_password,
        sql=valid_insert,
    ).stdout
    require(VALID_MIGRATION_ID in output and VALID_MIGRATION_NAME in output,
            "The dedicated migration role could not write the valid ledger row.")

    invalid_cases = [
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        f"('1', 'invalid-id', '{VALID_CHECKSUM}');",
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        f"('00000002', 'Invalid Name', '{VALID_CHECKSUM}');",
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        "('00000003', 'invalid-checksum', 'not-a-sha256');",
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        f"('00000004', '{VALID_MIGRATION_NAME}', '{VALID_CHECKSUM}');",
        "INSERT INTO reos_infra.schema_migrations "
        "(migration_id, migration_name, checksum) VALUES "
        f"('00000001', 'different-name', '{VALID_CHECKSUM}');",
    ]
    for statement in invalid_cases:
        run_psql(
            container_id=container_id,
            user=MIGRATION_ROLE,
            password=migration_password,
            sql=statement,
            must_succeed=False,
        )


def cleanup(container_id: str, admin_password: str) -> None:
    cleanup_sql = f"""
DROP SCHEMA IF EXISTS reos_infra CASCADE;
DROP ROLE IF EXISTS {APPLICATION_ROLE};
DROP ROLE IF EXISTS {MIGRATION_ROLE};
"""
    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=cleanup_sql,
    )


def self_test() -> None:
    bootstrap = BOOTSTRAP_SQL.read_text(encoding="utf-8")
    metadata_sql = load_source_sql(MIGRATION_SOURCE, VERIFY_SQL_PATTERN)
    require(
        bootstrap.count("CREATE TABLE") == 1
        and "CREATE TABLE reos_infra.schema_migrations" in bootstrap,
        "Bootstrap SQL must create only the canonical infrastructure ledger.",
    )
    require("CREATE ROLE :\"migration_role\"" in bootstrap,
            "The dedicated migration role must be explicitly provisioned.")
    require("CREATE ROLE :\"application_role\"" in bootstrap,
            "The distinct application role must be explicitly provisioned.")
    require("SET ROLE :\"migration_role\"" in bootstrap,
            "Ledger creation must execute as the dedicated migration role.")
    require("DEFAULT clock_timestamp()" in bootstrap,
            "Ledger applied_at default is missing.")
    require("ALTER DEFAULT PRIVILEGES" in bootstrap,
            "Future migration objects must have restricted default privileges.")
    require(metadata_sql.count("$1::name") >= 1
            and metadata_sql.count("$1") == metadata_sql.count("$1::name"),
            "Canonical migration metadata query lost or changed its bound API-role parameters.")
    require("core001_" not in bootstrap.lower() and "core002_" not in bootstrap.lower(),
            "Infrastructure bootstrap must not introduce domain-owned tables.")
    print("PASS: migration-ledger bootstrap and canonical metadata source contracts are present.")


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
        return 0

    container_id = os.environ.get("POSTGRES_SERVICE_CONTAINER", "").strip()
    admin_password = os.environ.get("POSTGRES_TEST_PASSWORD", "")
    require(bool(container_id) and bool(admin_password),
            "PostgreSQL service container and admin secret are required.")
    require(shutil.which("docker") is not None,
            "Docker CLI is required for the PostgreSQL service test.")
    require(BOOTSTRAP_SQL.is_file(),
            f"Migration ledger bootstrap SQL is missing: {BOOTSTRAP_SQL}")

    migration_password = secrets.token_urlsafe(32)
    application_password = secrets.token_urlsafe(32)
    environment = {
        "HOMIO_MIGRATION_ROLE": MIGRATION_ROLE,
        "HOMIO_APPLICATION_ROLE": APPLICATION_ROLE,
        "HOMIO_MIGRATION_PASSWORD": migration_password,
        "HOMIO_APPLICATION_PASSWORD": application_password,
    }
    bootstrap_sql = BOOTSTRAP_SQL.read_text(encoding="utf-8")

    try:
        run_psql(
            container_id=container_id,
            user="postgres",
            password=admin_password,
            sql=bootstrap_sql,
            environment=environment,
        )
        verify_metadata(container_id, migration_password)
        verify_privileges(
            container_id,
            admin_password,
            application_password,
            migration_password,
        )
        verify_ledger_constraints(container_id, migration_password)
    finally:
        cleanup(container_id, admin_password)

    print(
        "PASS: PostgreSQL migration ledger is provisioned by the dedicated role, "
        "matches the canonical TypeScript metadata contract, rejects malformed "
        "history, and is inaccessible to the API role."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: PostgreSQL migration-ledger verification: {exc}", file=sys.stderr)
        raise SystemExit(1)
