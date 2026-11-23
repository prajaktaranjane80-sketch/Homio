#!/usr/bin/env python3
"""Real PostgreSQL integration checks for HOMIO's canonical role/RLS guard.

Only disposable CI fixtures are created. No HOMIO business schema,
production database, or ARCH-037 migration is created or modified.
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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
POSTGRES_SOURCE = (
    ROOT
    / "REOS_CONTROL_CENTER"
    / "backend"
    / "src"
    / "persistence"
    / "postgres.ts"
)

SQL_PATTERN = re.compile(
    r"export const POSTGRES_RUNTIME_ROLE_SAFETY_SQL\s*=\s*`(?P<sql>.*?)`\.trim\(\);",
    re.DOTALL,
)

SCHEMA = "homio_b4_integration"
TABLE = f"{SCHEMA}.tenant_records"
API_ROLE = "homio_b4_api"
OWNER_ROLE = "homio_b4_schema_owner"
BYPASS_ROLE = "homio_b4_bypass_role"

TENANT_A = "11111111-1111-4111-8111-111111111111"
TENANT_B = "22222222-2222-4222-8222-222222222222"

ROW_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ROW_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def load_role_safety_sql() -> str:
    """Read the only production owner of the PostgreSQL security SQL."""
    try:
        source = POSTGRES_SOURCE.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Cannot read canonical PostgreSQL source: {POSTGRES_SOURCE}"
        ) from exc

    matches = list(SQL_PATTERN.finditer(source))

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one POSTGRES_RUNTIME_ROLE_SAFETY_SQL owner."
        )

    sql = matches[0].group("sql").strip()

    if not sql or "${" in sql or "`" in sql:
        raise RuntimeError("The canonical PostgreSQL safety SQL is malformed.")

    return sql


def run_psql(
    *,
    container_id: str,
    user: str,
    password: str,
    sql: str,
    must_succeed: bool = True,
) -> subprocess.CompletedProcess[str]:
    # Pass the secret through the Docker CLI's inherited environment.
    # Never place password material in the docker process argument vector.
    if not isinstance(password, str) or not password or "\x00" in password:
        raise ValueError("A valid PostgreSQL password is required.")

    command = [
        "docker",
        "exec",
        "--env",
        "PGPASSWORD",
        "-i",
        container_id,
        "psql",
        "--no-psqlrc",
        "--set",
        "ON_ERROR_STOP=1",
        "--host=127.0.0.1",
        f"--username={user}",
        "--dbname=postgres",
        "--no-align",
        "--tuples-only",
        "--quiet",
    ]

    child_environment = os.environ.copy()
    child_environment["PGPASSWORD"] = password

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
        raise RuntimeError(
            f"PostgreSQL command failed for role {user}: {detail[:2000]}"
        )

    if not must_succeed and result.returncode == 0:
        raise RuntimeError(
            "An intentionally forbidden PostgreSQL operation unexpectedly succeeded."
        )

    return result


def role_attestation(
    *,
    container_id: str,
    user: str,
    password: str,
    safety_sql: str,
) -> dict[str, Any]:
    query = (
        "SELECT row_to_json(homio_role_check)::text "
        f"FROM (\n{safety_sql}\n) AS homio_role_check;"
    )

    output = run_psql(
        container_id=container_id,
        user=user,
        password=password,
        sql=query,
    ).stdout.strip()

    lines = [line for line in output.splitlines() if line.strip()]

    if len(lines) != 1:
        raise RuntimeError(
            f"PostgreSQL role attestation returned {len(lines)} rows; expected one."
        )

    value = json.loads(lines[0])

    if not isinstance(value, dict):
        raise RuntimeError("PostgreSQL role attestation was not a JSON object.")

    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def bootstrap_database(
    *,
    container_id: str,
    admin_password: str,
    api_password: str,
) -> None:
    setup_sql = f"""
CREATE ROLE {OWNER_ROLE} NOLOGIN NOSUPERUSER NOBYPASSRLS;

CREATE ROLE {API_ROLE} LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
  PASSWORD '{api_password}';

CREATE SCHEMA {SCHEMA} AUTHORIZATION {OWNER_ROLE};

SET ROLE {OWNER_ROLE};

CREATE TABLE {TABLE} (
  record_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  payload text NOT NULL
);

ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;

CREATE POLICY homio_test_permissive ON {TABLE}
  AS PERMISSIVE FOR ALL TO {API_ROLE}
  USING (true)
  WITH CHECK (true);

CREATE POLICY homio_test_tenant_guard ON {TABLE}
  AS RESTRICTIVE FOR ALL TO {API_ROLE}
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

RESET ROLE;

GRANT USAGE ON SCHEMA {SCHEMA} TO {API_ROLE};

GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {API_ROLE};

INSERT INTO {TABLE} (record_id, tenant_id, payload) VALUES
  ('{ROW_A}', '{TENANT_A}', 'tenant-a'),
  ('{ROW_B}', '{TENANT_B}', 'tenant-b');
"""

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=setup_sql,
    )


def policy_catalog_diagnostics(
    *,
    container_id: str,
    api_password: str,
) -> list[dict[str, Any]]:
    """Read exact catalog facts behind the existing production guard."""
    query = f"""
SELECT COALESCE(
  json_agg(
    json_build_object(
      'schema_name', namespace.nspname,
      'table_name', relation.relname,
      'policy_name', policy.polname,
      'is_restrictive', NOT policy.polpermissive,
      'command', policy.polcmd,

      'roles', ARRAY(
        SELECT CASE
          WHEN role_entry.role_oid = 0::oid THEN 'PUBLIC'
          ELSE pg_catalog.pg_get_userbyid(role_entry.role_oid)
        END
        FROM unnest(policy.polroles) AS role_entry(role_oid)
      ),

      'role_applies', (
        policy.polroles @> ARRAY[0::oid]
        OR policy.polroles && ARRAY(
          SELECT candidate.oid
          FROM pg_roles AS candidate
          WHERE candidate.rolname = session_user
             OR pg_has_role(session_user, candidate.oid, 'USAGE')
        )
      ),

      'using_expression', pg_catalog.pg_get_expr(
        policy.polqual,
        policy.polrelid
      ),

      'using_normalized', pg_catalog.regexp_replace(
        pg_catalog.lower(
          pg_catalog.pg_get_expr(policy.polqual, policy.polrelid)
        ),
        '[[:space:]]',
        '',
        'g'
      ),

      'using_matches_expected', pg_catalog.regexp_replace(
        pg_catalog.lower(
          pg_catalog.pg_get_expr(policy.polqual, policy.polrelid)
        ),
        '[[:space:]]',
        '',
        'g'
      ) IN (
        '(tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THEN(current_setting(''app.tenant_id''::text,true))::uuidELSENULL::uuidEND)',
        'tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THEN(current_setting(''app.tenant_id''::text,true))::uuidELSENULL::uuidEND',
        '(tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THENcurrent_setting(''app.tenant_id''::text,true)::uuidELSENULL::uuidEND)',
        'tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THENcurrent_setting(''app.tenant_id''::text,true)::uuidELSENULL::uuidEND'
      ),

      'with_check_expression', pg_catalog.pg_get_expr(
        policy.polwithcheck,
        policy.polrelid
      ),

      'with_check_normalized', pg_catalog.regexp_replace(
        pg_catalog.lower(
          pg_catalog.pg_get_expr(policy.polwithcheck, policy.polrelid)
        ),
        '[[:space:]]',
        '',
        'g'
      ),

      'with_check_matches_expected', pg_catalog.regexp_replace(
        pg_catalog.lower(
          pg_catalog.pg_get_expr(policy.polwithcheck, policy.polrelid)
        ),
        '[[:space:]]',
        '',
        'g'
      ) IN (
        '(tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THEN(current_setting(''app.tenant_id''::text,true))::uuidELSENULL::uuidEND)',
        'tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THEN(current_setting(''app.tenant_id''::text,true))::uuidELSENULL::uuidEND',
        '(tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THENcurrent_setting(''app.tenant_id''::text,true)::uuidELSENULL::uuidEND)',
        'tenant_id=CASEWHENpg_input_is_valid(current_setting(''app.tenant_id''::text,true),''uuid''::text)THENcurrent_setting(''app.tenant_id''::text,true)::uuidELSENULL::uuidEND'
      ),

      'using_is_not_null', policy.polqual IS NOT NULL,
      'with_check_is_not_null', policy.polwithcheck IS NOT NULL
    )
    ORDER BY policy.polname
  ),
  '[]'::json
)::text
FROM pg_policy AS policy
JOIN pg_class AS relation
  ON relation.oid = policy.polrelid
JOIN pg_namespace AS namespace
  ON namespace.oid = relation.relnamespace
WHERE relation.oid = '{TABLE}'::regclass;
"""

    raw = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=query,
    ).stdout.strip()

    lines = [line for line in raw.splitlines() if line.strip()]

    if len(lines) != 1:
        raise RuntimeError(
            "PostgreSQL policy diagnostics returned an unexpected row count."
        )

    decoded = json.loads(lines[0])

    if not isinstance(decoded, list):
        raise RuntimeError(
            "PostgreSQL policy diagnostics returned an invalid value."
        )

    return decoded


def verify_safe_role(
    *,
    container_id: str,
    api_password: str,
    safety_sql: str,
) -> None:
    result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        result.get("role_name") == API_ROLE,
        "The API login role was not identified exactly.",
    )

    require(
        result.get("is_superuser") is False,
        "The API role unexpectedly has superuser privilege.",
    )

    require(
        result.get("bypasses_row_security") is False,
        "The API role unexpectedly bypasses RLS.",
    )

    require(
        result.get("owns_application_tables") is False,
        "The API role owns a table.",
    )

    require(
        result.get("tenant_table_count") == 1,
        "The isolated fixture must expose exactly one tenant table.",
    )

    require(
        result.get("tenant_tables_force_rls") is True,
        "FORCE ROW LEVEL SECURITY was not detected.",
    )

    if result.get("tenant_tables_have_tenant_restrictive_guard") is not True:
        policies = policy_catalog_diagnostics(
            container_id=container_id,
            api_password=api_password,
        )

        raise RuntimeError(
            "The exact production guard did not recognize the restrictive tenant policy. "
            f"Attestation={json.dumps(result, sort_keys=True)} "
            f"PolicyCatalog={json.dumps(policies, sort_keys=True)}"
        )


def verify_rls_isolation(
    *,
    container_id: str,
    api_password: str,
    admin_password: str,
) -> None:
    tenant_switch_same_connection = f"""
BEGIN;
SELECT set_config('app.tenant_id', '{TENANT_A}', true);
SELECT COALESCE(json_agg(payload ORDER BY payload), '[]'::json)::text
FROM {TABLE};
COMMIT;

BEGIN;
SELECT set_config('app.tenant_id', '{TENANT_B}', true);
SELECT COALESCE(json_agg(payload ORDER BY payload), '[]'::json)::text
FROM {TABLE};
COMMIT;
"""

    output = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=tenant_switch_same_connection,
    ).stdout.strip().splitlines()

    require(
        len(output) == 4
        and json.loads(output[1]) == ["tenant-a"]
        and json.loads(output[3]) == ["tenant-b"],
        "One reused PostgreSQL connection leaked or mixed tenant rows while switching A to B.",
    )

    missing_context = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=f"SELECT count(*)::text FROM {TABLE};",
    ).stdout.strip()

    require(
        missing_context.splitlines()[-1] == "0",
        "Missing tenant context did not fail closed.",
    )

    for invalid_tenant_id in ("", "not-a-uuid"):
        quoted_setting = "'" + invalid_tenant_id.replace("'", "''") + "'"
        invalid_context = f"""
BEGIN;
SELECT set_config('app.tenant_id', {quoted_setting}, true);
SELECT
  (SELECT count(*) FROM {TABLE})::text || ':' ||
  (SELECT count(*) FROM {TABLE})::text;
COMMIT;
"""

        invalid_output = run_psql(
            container_id=container_id,
            user=API_ROLE,
            password=api_password,
            sql=invalid_context,
        ).stdout.strip().splitlines()

        require(
            invalid_output and invalid_output[-1] == "0:0",
            f"Empty or malformed tenant context exposed rows: {invalid_tenant_id!r}.",
        )

    wrong_tenant_insert = f"""
BEGIN;
SELECT set_config('app.tenant_id', '{TENANT_A}', true);

INSERT INTO {TABLE} (record_id, tenant_id, payload)
VALUES (
  'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  '{TENANT_B}',
  'cross-tenant-write'
);

COMMIT;
"""

    rejected = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=wrong_tenant_insert,
        must_succeed=False,
    )

    require(
        "row-level security" in (rejected.stderr or "").lower(),
        "Cross-tenant INSERT failed for an unexpected reason, not RLS.",
    )

    local_context_reset = f"""
BEGIN;
SELECT set_config('app.tenant_id', '{TENANT_A}', true);
COMMIT;

SELECT (
  current_setting('app.tenant_id', true) IS DISTINCT FROM '{TENANT_A}'
)::text;
"""

    reset_result = run_psql(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        sql=local_context_reset,
    ).stdout.strip().splitlines()

    require(
        reset_result and reset_result[-1].lower() == "true",
        "Transaction-local tenant context leaked after COMMIT.",
    )

    unchanged = run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=(
            "SELECT count(*)::text FROM "
            f"{TABLE} WHERE payload = 'cross-tenant-write';"
        ),
    ).stdout.strip()

    require(
        unchanged.splitlines()[-1] == "0",
        "A rejected cross-tenant write persisted data.",
    )


def verify_unsafe_roles_and_policies(
    *,
    container_id: str,
    api_password: str,
    admin_password: str,
    safety_sql: str,
) -> None:
    bypass_setup = f"""
CREATE ROLE {BYPASS_ROLE} NOLOGIN NOSUPERUSER BYPASSRLS;
GRANT {BYPASS_ROLE} TO {API_ROLE};
"""

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=bypass_setup,
    )

    bypass_result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        bypass_result.get("bypasses_row_security") is True,
        "The effective-role check missed an inherited/assumable BYPASSRLS role.",
    )

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"REVOKE {BYPASS_ROLE} FROM {API_ROLE}; DROP ROLE {BYPASS_ROLE};",
    )

    owner_membership = f"GRANT {OWNER_ROLE} TO {API_ROLE};"

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=owner_membership,
    )

    owner_result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        owner_result.get("owns_application_tables") is True,
        "The effective-role check missed a table-owner role available to the API login.",
    )

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"REVOKE {OWNER_ROLE} FROM {API_ROLE};",
    )

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"DROP POLICY homio_test_tenant_guard ON {TABLE};",
    )

    missing_guard = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        missing_guard.get("tenant_tables_have_tenant_restrictive_guard") is False,
        "The production guard failed to detect a missing restrictive tenant policy.",
    )

    recreate_legacy_guard = f"""
CREATE POLICY homio_test_tenant_guard ON {TABLE}
  AS RESTRICTIVE FOR ALL TO {API_ROLE}
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
"""

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=recreate_legacy_guard,
    )

    legacy_policy_result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        legacy_policy_result.get("tenant_tables_have_tenant_restrictive_guard") is False,
        "The production guard accepted the legacy policy with an unsafe UUID cast.",
    )

    safe_recreate_guard = f"""
ALTER POLICY homio_test_tenant_guard ON {TABLE}
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );
"""

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=safe_recreate_guard,
    )

    safe_policy_result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        safe_policy_result.get("tenant_tables_have_tenant_restrictive_guard") is True,
        "The production guard failed to recognize the validated tenant-context policy.",
    )

    unsafe_table = f"""
CREATE TABLE {SCHEMA}.unsafe_tenant_records (
  tenant_id uuid NOT NULL
);

GRANT SELECT ON {SCHEMA}.unsafe_tenant_records TO {API_ROLE};
"""

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=unsafe_table,
    )

    unsafe_result = role_attestation(
        container_id=container_id,
        user=API_ROLE,
        password=api_password,
        safety_sql=safety_sql,
    )

    require(
        unsafe_result.get("tenant_tables_force_rls") is False,
        "The production guard failed to detect a tenant table without forced RLS.",
    )

    run_psql(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        sql=f"DROP TABLE {SCHEMA}.unsafe_tenant_records;",
    )

    superuser_result = role_attestation(
        container_id=container_id,
        user="postgres",
        password=admin_password,
        safety_sql=safety_sql,
    )

    require(
        superuser_result.get("is_superuser") is True,
        "The production guard failed to identify a PostgreSQL superuser.",
    )


def verify_psql_password_is_not_exposed_in_process_arguments() -> None:
    """Regression-test the secret transport without Docker or a database."""
    password = "homio-postgres-harness-secret-self-test"
    captured: dict[str, Any] = {}
    original_environment_value = os.environ.get("PGPASSWORD")

    def fake_run(
        command: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = list(command)
        captured["environment"] = kwargs.get("env")
        return subprocess.CompletedProcess(command, 0, "", "")

    with patch("subprocess.run", side_effect=fake_run) as mocked_run:
        result = run_psql(
            container_id="homio-postgres-self-test",
            user="postgres",
            password=password,
            sql="SELECT 1;",
        )

    command = captured.get("command")
    child_environment = captured.get("environment")

    require(result.returncode == 0, "The mocked PostgreSQL command did not succeed.")
    require(
        mocked_run.call_count == 1,
        "The PostgreSQL command did not execute exactly once.",
    )
    require(isinstance(command, list), "The Docker command arguments were not captured.")
    require(
        password not in "\0".join(command),
        "The PostgreSQL password leaked into process arguments.",
    )
    require(
        "PGPASSWORD" in command and "--env" in command,
        "Docker was not instructed to inherit PGPASSWORD from the child environment.",
    )
    require(
        isinstance(child_environment, dict)
        and child_environment.get("PGPASSWORD") == password,
        "The PostgreSQL password was not passed through the child process environment.",
    )
    require(
        os.environ.get("PGPASSWORD") == original_environment_value,
        "The PostgreSQL password unexpectedly mutated the parent process environment.",
    )


def self_test() -> None:
    verify_psql_password_is_not_exposed_in_process_arguments()

    sql = load_role_safety_sql()

    required_fragments = (
        "pg_has_role(session_user, candidate.oid, 'USAGE')",
        "pg_has_role(session_user, candidate.oid, 'SET')",
        "relation.relowner IN (SELECT oid FROM effective_roles)",
        "policy.polpermissive = false",
        "policy.polcmd = '*'",
        "policy.polwithcheck IS NOT NULL",
        "pg_input_is_valid(current_setting",
        "ELSENULL::uuidEND",
        "tenant_tables_have_tenant_restrictive_guard",
    )

    missing = [
        fragment
        for fragment in required_fragments
        if fragment not in sql
    ]

    require(
        not missing,
        f"Canonical PostgreSQL guard is missing required checks: {missing}",
    )

    print(
        "PASS: exact PostgreSQL role/RLS SQL loaded from the canonical TypeScript owner."
    )


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
        return 0

    container_id = os.environ.get(
        "POSTGRES_SERVICE_CONTAINER",
        "",
    ).strip()

    admin_password = os.environ.get(
        "POSTGRES_TEST_PASSWORD",
        "",
    )

    if not container_id or not admin_password:
        raise RuntimeError(
            "POSTGRES_SERVICE_CONTAINER and POSTGRES_TEST_PASSWORD are required in CI."
        )

    if shutil.which("docker") is None:
        raise RuntimeError(
            "Docker CLI is required to execute the ephemeral PostgreSQL service test."
        )

    safety_sql = load_role_safety_sql()
    api_password = secrets.token_urlsafe(32)

    bootstrap_database(
        container_id=container_id,
        admin_password=admin_password,
        api_password=api_password,
    )

    verify_safe_role(
        container_id=container_id,
        api_password=api_password,
        safety_sql=safety_sql,
    )

    verify_rls_isolation(
        container_id=container_id,
        api_password=api_password,
        admin_password=admin_password,
    )

    verify_unsafe_roles_and_policies(
        container_id=container_id,
        api_password=api_password,
        admin_password=admin_password,
        safety_sql=safety_sql,
    )

    print(
        "PASS: real PostgreSQL role safety, inherited privilege, table ownership, "
        "validated restrictive RLS policy, empty/malformed tenant-context denial, "
        "transaction-local context, cross-tenant write denial and superuser detection."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"FAIL: PostgreSQL integration verification: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
