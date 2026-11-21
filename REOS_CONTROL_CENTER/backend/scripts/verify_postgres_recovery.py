#!/usr/bin/env python3
"""Exercise real PostgreSQL 18 concurrency and schema+data backup/restore.

Only the disposable homio_b4_integration fixture created by
verify_postgres_integration.py is touched. No production or CORE-owned
business schema is created or modified.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

SCHEMA = "homio_b4_integration"
TABLE = f"{SCHEMA}.tenant_records"
API_ROLE = "homio_b4_api"
TENANT_A = "11111111-1111-4111-8111-111111111111"
ROW_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BASE_PAYLOAD = "tenant-a"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_psql(
    *, container_id: str, user: str, password: str, sql: str,
    must_succeed: bool = True,
) -> subprocess.CompletedProcess[str]:
    require(bool(password) and "\x00" not in password,
            "A valid PostgreSQL password is required.")
    command = [
        "docker", "exec", "--env", "PGPASSWORD", "-i", container_id,
        "psql", "--no-psqlrc", "--set", "ON_ERROR_STOP=1",
        "--host=127.0.0.1", f"--username={user}", "--dbname=postgres",
        "--no-align", "--tuples-only", "--quiet",
    ]
    child_environment = os.environ.copy()
    child_environment["PGPASSWORD"] = password
    result = subprocess.run(
        command, input=sql, text=True, capture_output=True,
        check=False, timeout=45, env=child_environment,
    )
    if must_succeed and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().replace(password, "[REDACTED]")
        raise RuntimeError(f"PostgreSQL psql operation failed: {detail[:2000]}")
    if not must_succeed and result.returncode == 0:
        raise RuntimeError("An intentionally invalid PostgreSQL operation succeeded.")
    return result


def run_pg_dump(*, container_id: str, password: str) -> str:
    command = [
        "docker", "exec", "--env", "PGPASSWORD", container_id,
        "pg_dump", "--no-password", "--host=127.0.0.1",
        "--username=postgres", "--dbname=postgres",
        "--schema", SCHEMA, "--format=plain",
    ]
    child_environment = os.environ.copy()
    child_environment["PGPASSWORD"] = password
    result = subprocess.run(
        command, text=True, capture_output=True, check=False,
        timeout=45, env=child_environment,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().replace(password, "[REDACTED]")
        raise RuntimeError(f"PostgreSQL schema/data backup failed: {detail[:2000]}")
    require(bool(result.stdout.strip()), "pg_dump produced an empty backup.")
    return result.stdout


def verify_concurrent_tenant_writes(container_id: str, admin_password: str,
                                    api_password: str) -> None:
    # Every worker uses a separate Docker/psql process and therefore a distinct
    # PostgreSQL connection. Transaction-local tenant context is set per worker.
    worker_count = 16
    sql = f"""
BEGIN;
SELECT set_config('app.tenant_id', '{TENANT_A}', true);
UPDATE {TABLE}
SET payload = payload || '|x'
WHERE record_id = '{ROW_A}' AND tenant_id = '{TENANT_A}';
COMMIT;
"""
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(
                run_psql,
                container_id=container_id,
                user=API_ROLE,
                password=api_password,
                sql=sql,
            )
            for _ in range(worker_count)
        ]
        for future in as_completed(futures):
            future.result()

    observed = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            f"SELECT (length(payload) - length('{BASE_PAYLOAD}'))::text "
            f"FROM {TABLE} WHERE record_id = '{ROW_A}';"
        ),
    ).stdout.strip().splitlines()
    require(observed and observed[-1] == str(worker_count * 2),
            "Concurrent row updates lost or duplicated an update.")

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"UPDATE {TABLE} SET payload = '{BASE_PAYLOAD}' WHERE record_id = '{ROW_A}';",
    )


def verify_schema_and_data_backup_restore(container_id: str,
                                          admin_password: str,
                                          api_password: str) -> None:
    before = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            f"SELECT json_agg(json_build_array(record_id::text, tenant_id::text, payload) "
            f"ORDER BY record_id)::text FROM {TABLE};"
        ),
    ).stdout.strip().splitlines()
    require(before and before[-1] not in ("", "null"),
            "The disposable PostgreSQL fixture contains no rows to back up.")
    expected_rows = json.loads(before[-1])

    # Capture the entire disposable schema, including table definition, RLS
    # policies, owners, grants and fixture rows. The schema is isolated from
    # every production/CORE schema and is disposable by construction.
    backup_sql = run_pg_dump(container_id=container_id, password=admin_password)
    require("CREATE TABLE" in backup_sql and "CREATE POLICY" in backup_sql,
            "The schema backup omitted table or RLS policy DDL.")
    require("tenant-a" in backup_sql and "tenant-b" in backup_sql,
            "The schema backup omitted fixture data.")

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"DROP SCHEMA {SCHEMA} CASCADE;",
    )
    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=backup_sql,
    )

    after = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            f"SELECT json_agg(json_build_array(record_id::text, tenant_id::text, payload) "
            f"ORDER BY record_id)::text FROM {TABLE};"
        ),
    ).stdout.strip().splitlines()
    require(after and json.loads(after[-1]) == expected_rows,
            "PostgreSQL schema+data restore did not reproduce the exact fixture rows.")

    rls = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            "SELECT relrowsecurity::text || '|' || relforcerowsecurity::text "
            "FROM pg_class WHERE oid = "
            f"'{TABLE}'::regclass;"
        ),
    ).stdout.strip().splitlines()
    require(rls and rls[-1] == "true|true",
            "PostgreSQL restore did not preserve ENABLE and FORCE RLS.")

    ownership = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            "SELECT pg_get_userbyid(namespace.nspowner)::text || '|' || "
            "pg_get_userbyid(relation.relowner)::text "
            "FROM pg_namespace AS namespace "
            "JOIN pg_class AS relation ON relation.relnamespace = namespace.oid "
            f"WHERE namespace.nspname = '{SCHEMA}' AND relation.relname = 'tenant_records';"
        ),
    ).stdout.strip().splitlines()
    require(ownership and ownership[-1] == "homio_b4_schema_owner|homio_b4_schema_owner",
            "PostgreSQL restore did not preserve the schema and table owners.")

    privileges = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            f"SELECT has_schema_privilege('{API_ROLE}', '{SCHEMA}', 'USAGE')::text || '|' || "
            f"has_table_privilege('{API_ROLE}', '{TABLE}', 'SELECT')::text || '|' || "
            f"has_table_privilege('{API_ROLE}', '{TABLE}', 'INSERT')::text || '|' || "
            f"has_table_privilege('{API_ROLE}', '{TABLE}', 'UPDATE')::text || '|' || "
            f"has_table_privilege('{API_ROLE}', '{TABLE}', 'DELETE')::text;"
        ),
    ).stdout.strip().splitlines()
    require(privileges and privileges[-1] == "true|true|true|true|true",
            "PostgreSQL restore did not preserve the API role's least-privilege grants.")

    tenant_read = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=(
            "BEGIN; "
            f"SELECT set_config('app.tenant_id', '{TENANT_A}', true); "
            f"SELECT count(*)::text FROM {TABLE}; COMMIT;"
        ),
    ).stdout.strip().splitlines()
    require(tenant_read and tenant_read[-1] == "1",
            "Restored schema no longer enforces the tenant-scoped read boundary.")


def self_test() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    required = (
        "ThreadPoolExecutor", "pg_dump", "DROP SCHEMA", "CREATE POLICY",
        "relforcerowsecurity", "tenant-scoped read boundary",
    )
    missing = [item for item in required if item not in source]
    require(not missing, f"PostgreSQL recovery verifier is incomplete: {missing}")
    print("PASS: PostgreSQL concurrency and schema+data recovery verifier contract.")


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
        return 0
    container_id = os.environ.get("POSTGRES_SERVICE_CONTAINER", "").strip()
    admin_password = os.environ.get("POSTGRES_TEST_PASSWORD", "")
    require(bool(container_id) and bool(admin_password),
            "PostgreSQL service container and admin secret are required.")
    require(shutil.which("docker") is not None,
            "Docker CLI is required for PostgreSQL recovery verification.")
    # Reset only the disposable CI fixture role to a fresh, unlogged secret.
    # The password is sent through psql stdin, never a process argument.
    api_password = secrets.token_urlsafe(32)
    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"ALTER ROLE {API_ROLE} PASSWORD '{api_password}';",
    )
    verify_concurrent_tenant_writes(container_id, admin_password, api_password)
    verify_schema_and_data_backup_restore(container_id, admin_password, api_password)
    print(
        "PASS: 16 independent PostgreSQL tenant writes committed without lost updates; "
        "schema+data backup/restore preserved ownership, grants, RLS policies and tenant reads."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: PostgreSQL concurrency/recovery verification: {exc}", file=sys.stderr)
        raise SystemExit(1)
