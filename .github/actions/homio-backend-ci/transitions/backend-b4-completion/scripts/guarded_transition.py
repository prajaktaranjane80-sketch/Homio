from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    urlopen,
)


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data" / "state.json"
PACKET = CONTROL / "packets" / "NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"

APPROVAL_PREFIX = "[CONTROL-CENTER-COMPLETE-BACKEND-001-B4]"
OIDC_AUDIENCE = "homio-control-center-backend-b4-completion"
OIDC_JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"

# Verified source checkpoint after the owner saved the final B4 schema and
# target-recovery evidence readbacks. This is not a B4 completion result.
BASELINE_HEAD = "13d4f01ea39ba0f2f1fd3e848207c15ebd0ff7fa"
BASELINE_STATE_BLOB_SHA = "5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b"
BASELINE_MASTER_BLOB_SHA = "f8d9cd456568cc6c8eaae0caf764123a7e859ba6"
BASELINE_PLAN_BLOB_SHA = "84c94c82ac5b0fde7c7bdf94acca235402c465ab"
BASELINE_REGISTER_BLOB_SHA = "fe1deafb694534743447d9113ae52930d8b68d02"
BASELINE_ENTRYPOINT_BLOB_SHA = "2e1d66cec0a8ca17b24ccf285d3133ff16ca2834"
BASELINE_SCHEMA_MANIFEST_BLOB_SHA = "935cd4950d5e8de117a349ac3608cf4e7b663462"
BASELINE_TARGET_RECOVERY_BLOB_SHA = "9798c2b964426dd37f190108460f9120a6174555"
BASELINE_GUARD_TEST_BLOB_SHA = "d56def9aa22a0d31d48916faaf3f6558685c43bf"

STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
MASTER_PATH = (
    "REOS_CONTROL_CENTER/architecture/backend/plans/"
    "HOMIO_Backend_Structure"
)
PLAN_PATH = "REOS_CONTROL_CENTER/B4 ka work plan"
REGISTER_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B4-search-reference-register.md"
)
ENTRYPOINT_PATH = "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
SCHEMA_MANIFEST_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B4-physical-schema-implementation-manifest.md"
)
TARGET_RECOVERY_EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B4-target-backup-restore-evidence.md"
)
B4_COMPLETION_EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B4-completion-ci-evidence.md"
)

ACTION_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b4-completion/action.yml"
)
GUARD_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b4-completion/scripts/guarded_transition.py"
)
GUARD_TEST_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b4-completion/scripts/test_guarded_transition.py"
)
REUSABLE_WORKFLOW_PATH = ".github/workflows/reusable-backend-b4-completion.yml"
WORKFLOW_PATH = ".github/workflows/backend-ci.yml"

# The approved owner bundle changes only the B4 guard and its own regression
# tests. All other implementation, workflow, authority and evidence files
# remain protected by their exact baseline blob identities.
EXPECTED_SOURCE_PATHS = {
    GUARD_PATH,
    GUARD_TEST_PATH,
}

MIGRATION_DIRECTORY = (
    CONTROL / "backend" / "scripts" / "postgres" / "migrations"
)

EXPECTED_MIGRATION_SHA256 = {
    "00000001-core002-event-outbox.sql": (
        "49e6e2d7bccde078df47ca22a7c01f630596ef6d16c09d9ff0741df9a9216203"
    ),
    "00000002-core002-safe-tenant-context.sql": (
        "fdd73252087e6920aa1de7cdad08e4b8197e2a7ac20b82e862815f7e92018e32"
    ),
    "00000003-b4-durable-api-sessions.sql": (
        "54284ed7ef2607a57828a3a4d6e8f30d862de764f7e05573181a1116de8d16b2"
    ),
    "00000004-b4-minimized-security-audit.sql": (
        "fc3c5de7e86e30126c394b91d4a20f85e0ffd93a8386b54f3a0fab14fdb1d3de"
    ),
    "00000005-core001-identity-tenant.sql": (
        "233fae3e95328ea1210f01993025d1aa4e1681c76af20e02703ea85290db6852"
    ),
    "00000006-core003-lead-ownership.sql": (
        "9231350d4aeb6c73a5d3bed8cef28fc079a249b0f00d33f9764cd26efb527457"
    ),
    "00000007-core004-inventory.sql": (
        "c1e46540126d8ee048b8b1793bb440add5df970a8912408d0067207427cffaf0"
    ),
    "00000008-core006-deal-transaction.sql": (
        "d69a681d60f6070fbd1b91687bad53b635405edd1efaa599bc6fc9d6494c79df"
    ),
    "00000009-core007-trust-governance.sql": (
        "023e7893f32bbae9e3bf9aab9766980295dc3208e22ab40e0c215a9973db29f5"
    ),
    "00000010-core008-financial.sql": (
        "0815e3afafa7582e84f66b3268a9a61cbdcbc17379390767a3d1a7e06d6454ea"
    ),
    "00000011-b4-security-audit-tenant-write-guard.sql": (
        "5497c17b3b7d6290643cf7776d273459dd8831607d8b11120d340f203773e8b9"
    ),
}

EXPECTED_B4_SOURCE_BLOBS = {
    STATE_PATH: BASELINE_STATE_BLOB_SHA,
    MASTER_PATH: BASELINE_MASTER_BLOB_SHA,
    PLAN_PATH: BASELINE_PLAN_BLOB_SHA,
    REGISTER_PATH: BASELINE_REGISTER_BLOB_SHA,
    ENTRYPOINT_PATH: BASELINE_ENTRYPOINT_BLOB_SHA,
    SCHEMA_MANIFEST_PATH: BASELINE_SCHEMA_MANIFEST_BLOB_SHA,
    TARGET_RECOVERY_EVIDENCE_PATH: BASELINE_TARGET_RECOVERY_BLOB_SHA,
    "REOS_CONTROL_CENTER/reos_control_center.py": (
        "bd48949d7ef562573294b08addc87f356363ae1d"
    ),
    "REOS_CONTROL_CENTER/context/backend_workstream_transition.py": (
        "be43a493e9e8130c286028a7cc9d58733a7960bb"
    ),
    "REOS_CONTROL_CENTER/context/github_actions_identity.py": (
        "bf55c359c32676181bb72e283c2113e98120bad4"
    ),
    "REOS_CONTROL_CENTER/context/phase_projection.py": (
        "d49e0d868b6a5f590dee716e63c1ea48bec9e92d"
    ),
    "REOS_CONTROL_CENTER/backend/package.json": (
        "14cb30187b5d9b8d791243b6534a0b7ac28e6e44"
    ),
    "REOS_CONTROL_CENTER/backend/package-lock.json": (
        "e27d6bd2c10a00646519dbfae3dfaaa612d5fddf"
    ),
    "REOS_CONTROL_CENTER/backend/src/persistence/postgres.ts": (
        "46ff8b6f2b7a53387f80aa7056c7cccdf703bce9"
    ),
    "REOS_CONTROL_CENTER/backend/src/persistence/postgres-migrations.ts": (
        "c0f06e5c71431d2f52b780dc4c2906410b01290b"
    ),
    "REOS_CONTROL_CENTER/backend/src/persistence/postgres-migration-manifest.ts": (
        "4a03cf4f398b2e8c9b24c7083ad8e161e3c3c275"
    ),
    "REOS_CONTROL_CENTER/backend/src/persistence/postgres-session-store.ts": (
        "0abbd0546cc74776b426a924dbf5a31b9fda848c"
    ),
    "REOS_CONTROL_CENTER/backend/src/persistence/postgres-security-audit.ts": (
        "fb547e5cc774cef8e1e66e638149d96a54b8f93b"
    ),
    "REOS_CONTROL_CENTER/backend/tests/integration/postgres-arch037-schema.integration.test.ts": (
        "99b548c2c50cbe168cb335a8bfd3ebfbb72672b8"
    ),
    "REOS_CONTROL_CENTER/backend/tests/integration/postgres-b4-recovery.integration.test.ts": (
        "bfbb50bcf0fcda8f857a6c63a4006ef98e28c322"
    ),
    "REOS_CONTROL_CENTER/backend/tests/integration/postgres-session-store.integration.test.ts": (
        "a6d3135821e9059ea2ac17cf15f516ce3f0d2550"
    ),
    "REOS_CONTROL_CENTER/backend/tests/integration/postgres-security-audit.integration.test.ts": (
        "c30ca982ea2c7ddd5414748c0e2b2fc8e2dcbebe"
    ),
    "REOS_CONTROL_CENTER/backend/tests/unit/postgres-migrations.test.ts": (
        "ba0476341e1604354656076b4f1b3e8954fc65e9"
    ),
    "REOS_CONTROL_CENTER/backend/tests/unit/postgres-session-store.test.ts": (
        "2c2b957cb9cb30df8b79ce6301ca221e9c0fc56b"
    ),
    "REOS_CONTROL_CENTER/backend/tests/unit/postgres-security-audit.test.ts": (
        "b54907df955e2532e71397e98855e4f173e1f6ec"
    ),
    ".github/workflows/reusable-backend-verification.yml": (
        "7d7e635a617de69d12d3de24fdcafaab9f230ee9"
    ),
    ".github/actions/homio-backend-ci/verification/action.yml": (
        "870a86fd75618b80dbcfb8d0bf8841e93d399f73"
    ),
    ".github/actions/homio-backend-ci/transitions/backend-b3-completion/scripts/guarded_transition.py": (
        "506db521ba7c2e6804a8cbeec9ca21515f021227"
    ),
    ".github/actions/homio-backend-ci/transitions/backend-b3-completion/scripts/test_guarded_transition.py": (
        "e509f5691b53567c79bf11afb64278ad35b9f33c"
    ),
    ".github/actions/homio-backend-ci/transitions/backend-b3-completion/action.yml": (
        "e17b1981af0ee5c09119b29d73183977e5c0485b"
    ),
    ".github/workflows/reusable-backend-b3-completion.yml": (
        "8f19b6a77ee4249b3c2c88b40c26159d1a682283"
    ),
}

EXPECTED_MIGRATION_BLOBS = {
    "00000001-core002-event-outbox.sql": "639684197d11544c1645b0c33bd5e8b824b4a008",
    "00000002-core002-safe-tenant-context.sql": "5b6898055f74c3f536d09edc9dd59cf8676e8bdc",
    "00000003-b4-durable-api-sessions.sql": "73a367292df0bdc67303a0ab61fae000aaaf2143",
    "00000004-b4-minimized-security-audit.sql": "28278391025782b796ef0783af6814fac6a3dbf8",
    "00000005-core001-identity-tenant.sql": "8b03856276aac8ad9b74893f9eea8bee4e33fb12",
    "00000006-core003-lead-ownership.sql": "9263de1c5242359df0af4245342d8e4ada6febb7",
    "00000007-core004-inventory.sql": "11ca89e1aabf3b83a735d99405ab66110205787c",
    "00000008-core006-deal-transaction.sql": "ec338deaac7164836be85d3d1c2f90720613ec3c",
    "00000009-core007-trust-governance.sql": "cacf5e0930b4c2705aa8e65f565bed575fb62dbf",
    "00000010-core008-financial.sql": "a87b097628d70af7bc73ed37b7907d83e6bd4daf",
    "00000011-b4-security-audit-tenant-write-guard.sql": "d974aa3a8c3b741da85217ef04b11612a98a6102",
}

BACKEND_PYTHON_RUNTIME = CONTROL / "backend" / "python_runtime"
for import_root in (ROOT, CONTROL, BACKEND_PYTHON_RUNTIME):
    value = str(import_root)
    if value in sys.path:
        sys.path.remove(value)
    sys.path.insert(0, value)

os.chdir(ROOT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from REOS_CONTROL_CENTER import reos_control_center as controller  # noqa: E402
from REOS_CONTROL_CENTER.context.backend_workstream_transition import (  # noqa: E402
    BACKEND_STAGES,
    BACKEND_TECHNICAL_SEQUENCE,
    B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA,
    B3_ACCEPTANCE_CRITERIA,
    B4_ACCEPTANCE_CRITERIA,
)
from REOS_CONTROL_CENTER.context.github_actions_identity import (  # noqa: E402
    BRANCH,
    BRANCH_REF,
    EXPECTED_OIDC_SUBJECT,
    OIDC_ISSUER,
    OWNER,
    REPOSITORY,
    OWNER_ID,
    REPOSITORY_ID,
    GitHubActionsIdentityError,
    validate_github_actions_identity_claims,
)
from REOS_CONTROL_CENTER.context.phase_projection import is_phase_coherent  # noqa: E402
from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_autonomy import (  # noqa: E402
    OperatorAutonomyEngine,
    OperatorRequest,
)
from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_policy import (  # noqa: E402
    OperatorActionType,
    OperatorRisk,
)
from AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_validation import (  # noqa: E402
    OperatorContext,
)
from AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (  # noqa: E402
    ChangeImpactAnalyzer,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_identity import (  # noqa: E402
    approval_scope_fingerprint,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (  # noqa: E402
    AuthorizationRequest,
    HumanApproval,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_policy import (  # noqa: E402
    SafeAuthorizationPolicy,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.execution_authorization import (  # noqa: E402
    ExecutionAuthorizationGuard,
)
from AUTONOMY_ENGINE.security.authentication.oidc_config import OIDCSettings  # noqa: E402
from AUTONOMY_ENGINE.security.authentication.oidc_verifier import (  # noqa: E402
    AuthenticatedIdentityPrincipal,
    AuthenticationError,
    OIDCVerifier,
)


def fail(message: str) -> None:
    raise SystemExit(f"BACKEND-001-B4 COMPLETION BLOCKED: {message}")


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = True,
    display: bool = True,
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    output = (completed.stdout or "") if capture else ""
    if output and display:
        print(output, end="" if output.endswith("\n") else "\n")
    if completed.returncode != 0:
        fail(f"command failed ({completed.returncode}): {' '.join(command)}")
    return output.strip()


def file_blob_sha(path: str, ref: str = "HEAD") -> str:
    return run(["git", "rev-parse", f"{ref}:{path}"], display=False)


def validate_source_paths(paths: list[str] | set[str] | tuple[str, ...]) -> None:
    actual = set(paths)
    if actual != EXPECTED_SOURCE_PATHS:
        missing = sorted(EXPECTED_SOURCE_PATHS - actual)
        unexpected = sorted(actual - EXPECTED_SOURCE_PATHS)
        fail(
            "exact B4 source-path allowlist mismatch; "
            f"missing={missing}; unexpected={unexpected}"
        )


def assert_exact_branch(expected_sha: str) -> None:
    if run(["git", "rev-parse", "HEAD"], display=False) != expected_sha:
        fail("checked-out HEAD differs from the exact verified source commit")
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("canonical branch moved; refusing a stale B4 transition")


def verify_owner_push(expected_sha: str) -> dict:
    required = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_RUN_ATTEMPT",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        fail(f"required GitHub environment values are missing: {missing}")
    if os.environ["GITHUB_ACTOR"] != OWNER:
        fail("only the immutable repository owner may authorize B4 completion")
    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("B4 completion requires an owner push, not PR or manual dispatch")
    if os.environ["GITHUB_REF"] != BRANCH_REF:
        fail("B4 transition is restricted to reos-development")
    if os.environ["GITHUB_REPOSITORY"] != REPOSITORY:
        fail("unexpected GitHub repository identity")
    if os.environ["ACTIONS_REPOSITORY"] != REPOSITORY:
        fail("Actions repository identity differs from the canonical repository")
    if os.environ["EXPECTED_SHA"] != expected_sha:
        fail("EXPECTED_SHA differs from the triggering source commit")
    if os.environ["VERIFIED_CODE_SHA"] != expected_sha:
        fail("verification SHA differs from the triggering source commit")

    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    if not event_path.is_file():
        fail("GitHub push event payload is missing")
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("GitHub push event payload is invalid")
    if event.get("ref") != BRANCH_REF or event.get("after") != expected_sha:
        fail("push event ref or SHA differs from the canonical branch commit")
    if event.get("repository", {}).get("full_name") != REPOSITORY:
        fail("push event belongs to a different repository")
    if event.get("sender", {}).get("login") != OWNER:
        fail("push event sender is not the immutable repository owner")
    head_commit = event.get("head_commit")
    if not isinstance(head_commit, dict):
        fail("push event does not contain a head commit")
    message = head_commit.get("message", "")
    if not isinstance(message, str) or not message.startswith(APPROVAL_PREFIX):
        fail("owner commit lacks the exact B4 completion approval prefix")
    return event


def verify_source_baseline(expected_sha: str) -> list[str]:
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("canonical branch moved before B4 completion preflight")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_HEAD, expected_sha],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail("the exact audited B4 baseline is not an ancestor of this change")
    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("source checkout is not clean before the guarded transition")

    baseline_pins = (
        (STATE_PATH, BASELINE_STATE_BLOB_SHA),
        (MASTER_PATH, BASELINE_MASTER_BLOB_SHA),
        (PLAN_PATH, BASELINE_PLAN_BLOB_SHA),
        (REGISTER_PATH, BASELINE_REGISTER_BLOB_SHA),
        (ENTRYPOINT_PATH, BASELINE_ENTRYPOINT_BLOB_SHA),
        (SCHEMA_MANIFEST_PATH, BASELINE_SCHEMA_MANIFEST_BLOB_SHA),
        (TARGET_RECOVERY_EVIDENCE_PATH, BASELINE_TARGET_RECOVERY_BLOB_SHA),
        (GUARD_TEST_PATH, BASELINE_GUARD_TEST_BLOB_SHA),
    )
    for path, expected_blob in baseline_pins:
        if file_blob_sha(path, BASELINE_HEAD) != expected_blob:
            fail(f"audited B4 baseline blob differs from the pinned SHA: {path}")
        if path != GUARD_TEST_PATH and file_blob_sha(path, expected_sha) != expected_blob:
            fail(f"B4 owner change modified a protected baseline file: {path}")

    changed = run(
        ["git", "diff", "--name-only", BASELINE_HEAD, expected_sha],
        display=False,
    ).splitlines()
    validate_source_paths(changed)

    for path, expected_blob in EXPECTED_B4_SOURCE_BLOBS.items():
        if file_blob_sha(path, expected_sha) != expected_blob:
            fail(f"existing B4 owner changed unexpectedly: {path}")
    for migration_name, expected_blob in EXPECTED_MIGRATION_BLOBS.items():
        path = (
            "REOS_CONTROL_CENTER/backend/scripts/postgres/migrations/"
            f"{migration_name}"
        )
        if file_blob_sha(path, expected_sha) != expected_blob:
            fail(f"canonical migration blob changed unexpectedly: {migration_name}")

    if not (ROOT / TARGET_RECOVERY_EVIDENCE_PATH).is_file():
        fail("required B4 target backup/restore evidence is missing")
    if not (ROOT / SCHEMA_MANIFEST_PATH).is_file():
        fail("required B4 physical-schema implementation manifest is missing")
    if (ROOT / B4_COMPLETION_EVIDENCE_PATH).exists():
        fail("B4 completion evidence already exists; duplicate transition is forbidden")
    return sorted(changed)


def verify_master_and_plan(expected_sha: str) -> tuple[str, str]:
    master = run(["git", "show", f"{expected_sha}:{MASTER_PATH}"], display=False)
    plan = run(["git", "show", f"{expected_sha}:{PLAN_PATH}"], display=False)
    master_markers = (
        "### B3 — Python domain-runtime bridge",
        "### B4 — PostgreSQL integration",
        "### B2-PRODUCTION-BINDING — API security and trusted context production binding",
        "ARCH-037",
        "PostgreSQL integration",
    )
    for marker in master_markers:
        if marker not in master:
            fail(f"backend technical master is missing required B4 contract marker: {marker}")
    b3_index = master.index("### B3 — Python domain-runtime bridge")
    b4_index = master.index("### B4 — PostgreSQL integration")
    production_index = master.index(
        "### B2-PRODUCTION-BINDING — API security and trusted context production binding"
    )
    if not b3_index < b4_index < production_index:
        fail("technical master no longer places B4 between B3 and B2 production binding")

    plan_markers = (
        "## 3. The eight canonical B4 acceptance criteria",
        "B4-AC01",
        "B4-AC08",
        "## 32. Target backup and restore",
        TARGET_RECOVERY_EVIDENCE_PATH,
        "## 39. B4 guarded completion workflow",
        REUSABLE_WORKFLOW_PATH,
        ACTION_PATH,
        GUARD_PATH,
        GUARD_TEST_PATH,
        "## 47. Phase 8 — Full recovery and operations",
        "## 48. Phase 9 — Guarded B4 completion",
        "## 51. B4 completion evidence format",
        "## 52. B4 guarded transition policy",
        APPROVAL_PREFIX,
        "## 55. Mandatory completion checklist",
        "No B4 completion claim is permitted before all eight canonical acceptance criteria",
    )
    for marker in plan_markers:
        if marker not in plan:
            fail(f"B4 work plan is missing required completion marker: {marker}")
    return file_blob_sha(MASTER_PATH, expected_sha), file_blob_sha(PLAN_PATH, expected_sha)


def verify_physical_schema_manifest() -> dict:
    path = ROOT / SCHEMA_MANIFEST_PATH
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        fail("B4 physical-schema implementation manifest is unreadable")
    required = (
        "One existing `PostgresRuntime`",
        "One existing migration manifest",
        "One existing migration runner",
        "One existing tenant transaction boundary",
        "No ORM",
        "No second tenant registry",
        "### 4.1 CORE-001",
        "### 4.2 CORE-003",
        "### 4.3 CORE-004",
        "### 4.4 CORE-006",
        "### 4.5 CORE-007",
        "### 4.6 CORE-008",
        "core001",
        "core002",
        "core003",
        "core004",
        "core006",
        "core007",
        "core008",
        "reos_infra",
        "ENABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
    )
    for marker in required:
        if marker not in content:
            fail(f"physical-schema manifest is missing canonical mapping marker: {marker}")
    if re.search(r"(?i)\bcore005\b", content):
        fail("B4 physical-schema manifest introduces a competing CORE-005 schema owner")
    return {
        "schemas": [
            "core001",
            "core002",
            "core003",
            "core004",
            "core006",
            "core007",
            "core008",
            "reos_infra",
        ],
        "canonical_owners": [
            "CORE-001",
            "CORE-002",
            "CORE-003",
            "CORE-004",
            "CORE-006",
            "CORE-007",
            "CORE-008",
            "B4",
        ],
        "no_second_schema_authority": True,
    }


def verify_target_recovery_evidence_text(content: str) -> dict:
    required = (
        "CI_RECOVERY_VERIFIED_TARGET_ENVIRONMENT_PENDING",
        "FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE",
        "afbaa1910696a9def96f1c7b1f79e8eaa9b78106",
        "45627180980",
        "bfbb50bcf0fcda8f857a6c63a4006ef98e28c322",
        "B4_RECOVERY_SCHEMA_INTEGRITY=PASS",
        "B4_RECOVERY_DATA_INTEGRITY=PASS",
        "B4_RECOVERY_TENANT_ISOLATION=PASS",
        "B4_RECOVERY_DATABASE_ACL=PASS",
        "B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS",
        "B4_RECOVERY_VERIFICATION=PASS",
        "EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4",
        "B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED",
        "Controlled target-environment recovery:** `NOT_VERIFIED`",
        "Point-in-time recovery:** `NOT_TESTED`",
        "| Backup encryption at rest | `NOT_TESTED` |",
        "| Secure backup transport | `NOT_TESTED` |",
        "| Production backup access control | `NOT_TESTED` |",
        "| Retention metadata and retention enforcement | `NOT_TESTED` |",
        "| Backup access audit | `NOT_TESTED` |",
        "| Key management and key rotation | `NOT_TESTED` |",
        "| Restricted restore operator | `NOT_TESTED` |",
        "| Target-environment restore runbook | `NOT_TESTED` |",
        "| Independent controlled non-production restore | `NOT_TESTED` |",
        "| Production disaster-recovery exercise | `NOT_TESTED` |",
        "| WAL archive configuration and availability | `NOT_TESTED` |",
        "| Base backup and recovery-target selection | `NOT_TESTED` |",
        "| Point-in-time recovery (PITR) | `NOT_TESTED` |",
        "| Post-PITR tenant and schema verification | `NOT_TESTED` |",
    )
    for marker in required:
        if marker not in content:
            fail(f"B4 target recovery evidence is missing required marker: {marker}")
    source_match = re.search(
        r"\| Source database \| `([^`]+)` \|", content
    )
    target_match = re.search(
        r"\| Restore database \| `([^`]+)` \|", content
    )
    backup_match = re.search(
        r"\| Backup SHA-256 \| `([0-9a-f]{64})` \|", content
    )
    schema_match = re.search(
        r"\| Schema fingerprint SHA-256 \| `([0-9a-f]{64})` \|", content
    )
    bytes_match = re.search(r"\| Backup size \| `([0-9]+)` bytes \|", content)
    if not all((source_match, target_match, backup_match, schema_match, bytes_match)):
        fail("B4 recovery evidence has incomplete backup identities")
    source_db = source_match.group(1)
    target_db = target_match.group(1)
    if source_db == target_db:
        fail("B4 recovery evidence does not identify an independent restore database")
    return {
        "source_database": source_db,
        "target_database": target_db,
        "backup_sha256": backup_match.group(1),
        "schema_sha256": schema_match.group(1),
        "backup_bytes": int(bytes_match.group(1)),
        "classification": "EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4",
        "production_tested": False,
        "pitr_tested": False,
    }


def verify_target_recovery_evidence() -> dict:
    try:
        content = (ROOT / TARGET_RECOVERY_EVIDENCE_PATH).read_text(
            encoding="utf-8"
        )
    except (OSError, UnicodeError):
        fail("B4 target backup/restore evidence cannot be read")
    return verify_target_recovery_evidence_text(content)


def verify_migration_manifest(directory: Path = MIGRATION_DIRECTORY) -> list[dict]:
    if not directory.is_dir():
        fail("canonical PostgreSQL migration directory is missing")
    entries = list(directory.iterdir())
    if any(
        entry.is_symlink() or not entry.is_file() or entry.suffix != ".sql"
        for entry in entries
    ):
        fail("canonical migration directory may contain regular SQL files only")
    files = sorted(path.name for path in entries)
    expected_names = sorted(EXPECTED_MIGRATION_SHA256)
    if files != expected_names:
        fail(
            "canonical SQL migration inventory differs from the B4 manifest; "
            f"expected={expected_names}; actual={files}"
        )
    records: list[dict] = []
    for index, name in enumerate(expected_names, start=1):
        path = directory / name
        if not path.is_file() or path.is_symlink():
            fail(f"migration is missing, non-regular or symlinked: {name}")
        raw = path.read_bytes()
        if not raw:
            fail(f"migration file is empty: {name}")
        actual = hashlib.sha256(raw).hexdigest()
        expected = EXPECTED_MIGRATION_SHA256[name]
        if actual != expected:
            fail(f"migration content checksum differs from the pinned B4 value: {name}")
        migration_id = name[:8]
        if migration_id != f"{index:08d}":
            fail(f"migration order is not contiguous at {name}")
        records.append(
            {
                "id": migration_id,
                "name": name,
                "sha256": actual,
                "bytes": len(raw),
            }
        )
    return records


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)


def _test_file_count(log: str, path: str) -> int:
    pattern = re.compile(
        r"✓\s+" + re.escape(path) + r"\s+\((\d+)\s+tests?\)",
        re.MULTILINE,
    )
    match = pattern.search(log)
    if match is None or int(match.group(1)) < 1:
        fail(f"required B4 verification test file did not execute: {path}")
    return int(match.group(1))


def validate_backend_verification_log(raw_log: str) -> dict:
    log = _strip_ansi(raw_log)
    required_markers = (
        "PASS: 16 independent PostgreSQL tenant writes committed without lost updates",
        "PASS: Redis 8.0.3 atomic shared-window enforcement",
        "B4_RECOVERY_METHOD=FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE",
        "B4_RECOVERY_MIGRATION_COUNT=11",
        "B4_RECOVERY_REPLAY_APPLIED_COUNT=0",
        "B4_RECOVERY_SCHEMA_INTEGRITY=PASS",
        "B4_RECOVERY_DATA_INTEGRITY=PASS",
        "B4_RECOVERY_TENANT_ISOLATION=PASS",
        "B4_RECOVERY_DATABASE_ACL=PASS",
        "B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS",
        "B4_RECOVERY_TARGET_CLASS=EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4",
        "B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED",
        "B4_RECOVERY_VERIFICATION=PASS",
        "B1_REPRODUCIBLE_BUILD=PASS",
    )
    for marker in required_markers:
        if marker not in log:
            fail(f"exact-SHA verification logs are missing required B4 marker: {marker}")

    file_summary = re.search(
        r"\bTest Files\s+(\d+)\s+passed\s+\((\d+)\)", log
    )
    test_summary = re.search(
        r"\bTests\s+(\d+)\s+passed\s+\((\d+)\)", log
    )
    if file_summary is None or test_summary is None:
        fail("Vitest summary is incomplete or reports failed/skipped test files")
    test_files_passed, test_files_total = map(int, file_summary.groups())
    tests_passed, tests_total = map(int, test_summary.groups())
    if test_files_passed != test_files_total or test_files_passed < 24:
        fail("one or more Vitest files failed/skipped or the required suite inventory shrank")
    if tests_passed != tests_total or tests_passed < 201:
        fail("one or more Vitest tests failed/skipped or the required test inventory shrank")

    test_counts = {
        "arch037_schema": _test_file_count(
            log, "tests/integration/postgres-arch037-schema.integration.test.ts"
        ),
        "b4_recovery": _test_file_count(
            log, "tests/integration/postgres-b4-recovery.integration.test.ts"
        ),
        "postgres_migrations": _test_file_count(
            log, "tests/unit/postgres-migrations.test.ts"
        ),
        "postgres_session_integration": _test_file_count(
            log, "tests/integration/postgres-session-store.integration.test.ts"
        ),
        "postgres_audit_integration": _test_file_count(
            log, "tests/integration/postgres-security-audit.integration.test.ts"
        ),
        "postgres_global_transaction": _test_file_count(
            log, "tests/unit/postgres-global-transaction.test.ts"
        ),
        "postgres_role_safety": _test_file_count(
            log, "tests/unit/postgres-role-safety.test.ts"
        ),
        "redis_rate_limit": _test_file_count(
            log, "tests/unit/redis-rate-limit.test.ts"
        ),
        "production_persistence": _test_file_count(
            log, "tests/integration/production-persistence.integration.test.ts"
        ),
        "core002_outbox": _test_file_count(
            log, "tests/integration/core002-outbox.integration.test.ts"
        ),
        "postgres_runtime": _test_file_count(
            log, "tests/unit/postgres.test.ts"
        ),
        "production_runtime": _test_file_count(
            log, "tests/unit/production-runtime.test.ts"
        ),
        "dependency_readiness": _test_file_count(
            log, "tests/unit/dependency-readiness.test.ts"
        ),
        "api_security": _test_file_count(
            log, "tests/unit/api-security.test.ts"
        ),
    }

    acrl_start = log.find("Run complete ACRL suite")
    if acrl_start < 0:
        fail("complete ACRL regression step is missing from verification logs")
    acrl_segment = log[acrl_start:]
    acrl_match = re.search(r"\b(\d+)\s+passed in [0-9.]+s", acrl_segment)
    if acrl_match is None:
        fail("complete ACRL suite did not report a successful non-empty run")
    acrl_passed = int(acrl_match.group(1))
    if acrl_passed < 1466:
        fail("complete ACRL suite test inventory is below the verified B4 baseline")

    release_ready_match = re.search(
        r"\bPRODUCTION_RELEASE_READY=(true|false)\b", log, re.IGNORECASE
    )
    release_blockers_match = re.search(
        r"\bPRODUCTION_RELEASE_BLOCKERS=(\d+)\b", log
    )
    if release_ready_match is None or release_blockers_match is None:
        fail("workflow product release-readiness boundary is missing from the exact-SHA log")
    release_ready = release_ready_match.group(1).lower() == "true"
    release_blockers = int(release_blockers_match.group(1))

    recovery_values: dict[str, str] = {}
    for key in (
        "B4_RECOVERY_SOURCE_DATABASE",
        "B4_RECOVERY_TARGET_DATABASE",
        "B4_RECOVERY_BACKUP_SHA256",
        "B4_RECOVERY_BACKUP_BYTES",
        "B4_RECOVERY_SCHEMA_SHA256",
        "B4_RECOVERY_TARGET_CLASS",
    ):
        match = re.search(
            rf"(?m)(?:^|\s){key}=([^\r\n]+)$",
            log,
        )
        if match is None:
            fail(f"verification log is missing recovery identity: {key}")
        recovery_values[key] = match.group(1).strip()
    if recovery_values["B4_RECOVERY_SOURCE_DATABASE"] == recovery_values[
        "B4_RECOVERY_TARGET_DATABASE"
    ]:
        fail("current CI recovery log did not restore into a separate database")
    if not re.fullmatch(r"[0-9a-f]{64}", recovery_values["B4_RECOVERY_BACKUP_SHA256"]):
        fail("current CI backup checksum is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", recovery_values["B4_RECOVERY_SCHEMA_SHA256"]):
        fail("current CI schema fingerprint is invalid")
    backup_bytes = int(recovery_values["B4_RECOVERY_BACKUP_BYTES"])
    if backup_bytes < 1:
        fail("current CI recovery backup size is invalid")

    return {
        "test_files_passed": test_files_passed,
        "test_files_total": test_files_total,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "acrl_tests_passed": acrl_passed,
        "production_release_ready": release_ready,
        "production_release_blockers": release_blockers,
        "test_counts": test_counts,
        "recovery": {
            **recovery_values,
            "backup_bytes": backup_bytes,
            "migration_count": 11,
            "replay_applied_count": 0,
            "schema_integrity": "PASS",
            "data_integrity": "PASS",
            "tenant_isolation": "PASS",
            "database_acl": "PASS",
            "role_and_grant_integrity": "PASS",
            "verification": "PASS",
        },
        "failed": 0,
        "skipped": 0,
        "blocked": 0,
    }


def _api_url(path: str) -> str:
    base = os.environ.get("ACTIONS_API_URL", "").rstrip("/")
    if not base:
        fail("ACTIONS_API_URL is missing; exact run verification is unavailable")
    return f"{base}{path}"


class _CredentialSafeRedirectHandler(HTTPRedirectHandler):
    """Never forward GitHub API credentials to a different redirect origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(
            req, fp, code, msg, headers, newurl
        )
        if redirected is None:
            return None

        source = urlsplit(req.full_url)
        target = urlsplit(newurl)
        source_origin = (source.scheme.lower(), source.netloc.lower())
        target_origin = (target.scheme.lower(), target.netloc.lower())

        if source_origin != target_origin:
            redirected.remove_header("Authorization")
            redirected.remove_header("Proxy-Authorization")

        return redirected


def _api_get_bytes(url: str) -> bytes:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        fail("GITHUB_TOKEN is missing; exact Actions job logs cannot be verified")
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "HOMIO-B4-Guarded-Transition",
        },
        method="GET",
    )
    try:
        opener = build_opener(_CredentialSafeRedirectHandler())
        with opener.open(request, timeout=45) as response:
            return response.read()
    except HTTPError as exc:
        request_path = urlsplit(url).path
        fail(
            "GitHub Actions evidence request failed: "
            f"HTTP {exc.code} for API path {request_path}"
        )
    except Exception as exc:
        fail(f"GitHub Actions evidence request failed: {type(exc).__name__}")
    raise AssertionError("unreachable")


def _api_get_json(url: str) -> dict:
    raw = _api_get_bytes(url)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        fail("GitHub Actions API returned invalid JSON")
    if not isinstance(value, dict):
        fail("GitHub Actions API response is not an object")
    return value


def _download_job_log(job_id: int) -> str:
    if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id <= 0:
        fail("GitHub Actions verification job ID must be a positive integer")

    raw = _api_get_bytes(
        _api_url(f"/repos/{REPOSITORY}/actions/jobs/{job_id}/logs")
    )
    if not raw:
        fail("GitHub Actions verification job log is empty")

    # GitHub's individual-job logs endpoint redirects to a plain-text log.
    # It is not the workflow-run archive endpoint and must never be unzipped.
    # Reject an accidental binary/ZIP response before parsing verification
    # markers; otherwise decode safely while preserving all readable evidence.
    if raw.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        fail("GitHub Actions job-log endpoint returned ZIP data instead of plain text")
    if b"\x00" in raw[:4096]:
        fail("GitHub Actions job-log endpoint returned binary data instead of plain text")

    log = raw.decode("utf-8-sig", errors="replace")
    if not log.strip():
        fail("GitHub Actions verification job log contains no readable text")
    return log
    def verify_actions_run(expected_sha: str) -> dict:
    run_id = os.environ.get("ACTIONS_RUN_ID", "")
    attempt = os.environ.get("ACTIONS_RUN_ATTEMPT", "")
    if not run_id.isdigit() or not attempt.isdigit():
        fail("GitHub Actions run ID or attempt is invalid")

    run_payload = _api_get_json(
        _api_url(f"/repos/{REPOSITORY}/actions/runs/{run_id}")
    )
    if run_payload.get("head_sha") != expected_sha:
        fail("Actions run head SHA differs from the owner-pushed source SHA")
    if run_payload.get("head_branch") != BRANCH:
        fail("Actions run does not target the canonical B4 branch")
    if run_payload.get("event") != "push":
        fail("B4 completion requires a push-triggered verification run")
    if str(run_payload.get("run_attempt")) != attempt:
        fail("Actions run attempt differs from the triggering attempt")

    jobs_payload = _api_get_json(
        _api_url(
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/jobs?filter=latest&per_page=100"
        )
    )
    jobs = jobs_payload.get("jobs")
    if not isinstance(jobs, list):
        fail("GitHub Actions run has no readable jobs list")
    verification_jobs = [
        job
        for job in jobs
        if isinstance(job, dict)
        and "Backend, T21, and ACRL runtime verification" in str(job.get("name", ""))
    ]
    if len(verification_jobs) != 1:
        fail(
            "expected exactly one canonical backend/T21/ACRL verification job; "
            f"found {len(verification_jobs)}"
        )
    job = verification_jobs[0]
    if job.get("conclusion") != "success" or job.get("status") != "completed":
        fail("the exact-SHA backend/T21/ACRL verification job did not pass")
    if job.get("head_sha") not in (None, expected_sha):
        fail("verification job head SHA differs from the exact owner commit")
    if str(job.get("run_attempt", attempt)) != attempt:
        fail("verification job attempt differs from the exact Actions attempt")

    job_id = job.get("id")
    if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id <= 0:
        fail("canonical verification job has an invalid GitHub job ID")

    steps = job.get("steps")
    if not isinstance(steps, list):
        fail("verification job steps are missing")
    step_results = {
        str(step.get("name")): step.get("conclusion")
        for step in steps
        if isinstance(step, dict)
    }
    required_steps = (
        "Checkout exact triggering commit with verified ancestry",
        "Execute real PostgreSQL tenant and runtime-role integration checks",
        "Execute PostgreSQL concurrent-write and full fixture backup/restore checks",
        "Execute Redis 8 distributed rate-limit concurrency and expiry checks",
        "Execute real PostgreSQL migration-ledger and least-privilege integration checks",
        "Run modular backend verification suite",
    )
    for step_name in required_steps:
        if step_results.get(step_name) != "success":
            fail(f"required exact-SHA verification step did not pass: {step_name}")

    raw_log = _download_job_log(job_id)
    if f"HEAD is now at {expected_sha[:7]}" not in raw_log:
        fail("verification log does not prove checkout of the exact triggering SHA")
    summary = validate_backend_verification_log(raw_log)

    artifacts_payload = _api_get_json(
        _api_url(
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100"
        )
    )
    artifacts_raw = artifacts_payload.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        fail("GitHub Actions artifact inventory is malformed")
    artifacts = [
        {
            "name": item.get("name"),
            "id": item.get("id"),
            "expired": item.get("expired"),
        }
        for item in artifacts_raw
        if isinstance(item, dict)
    ]
    return {
        "run_id": run_id,
        "attempt": attempt,
        "job_id": str(job_id),
        "job_name": str(job.get("name", "")),
        "job_conclusion": str(job.get("conclusion", "")),
        "workflow_name": str(run_payload.get("name", "HOMIO Backend and ACRL Runtime CI")),
        "run_url": (
            f"{os.environ['ACTIONS_SERVER_URL'].rstrip('/')}/"
            f"{REPOSITORY}/actions/runs/{run_id}"
        ),
        "tested_sha": expected_sha,
        "summary": summary,
        "artifacts": artifacts,
    }


def verify_b4_implementation(expected_sha: str) -> dict:
    plan_blob_sha, master_blob_sha = file_blob_sha(PLAN_PATH, expected_sha), file_blob_sha(
        MASTER_PATH, expected_sha
    )
    if plan_blob_sha != BASELINE_PLAN_BLOB_SHA:
        fail("B4 execution plan changed after the pinned completion baseline")
    if master_blob_sha != BASELINE_MASTER_BLOB_SHA:
        fail("backend technical master changed after the pinned completion baseline")

    schema = verify_physical_schema_manifest()
    target_recovery = verify_target_recovery_evidence()
    migrations = verify_migration_manifest(MIGRATION_DIRECTORY)
    if len(migrations) != 11:
        fail("canonical B4 migration inventory is incomplete")
    return {
        "schema": schema,
        "target_recovery": target_recovery,
        "migrations": migrations,
        "plan_blob_sha": plan_blob_sha,
        "master_blob_sha": master_blob_sha,
        "register_blob_sha": BASELINE_REGISTER_BLOB_SHA,
        "schema_manifest_blob_sha": BASELINE_SCHEMA_MANIFEST_BLOB_SHA,
        "target_recovery_blob_sha": BASELINE_TARGET_RECOVERY_BLOB_SHA,
    }


def request_github_oidc_token() -> str:
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not request_url or not request_token:
        fail("GitHub OIDC token request unavailable; id-token: write is required")
    parts = urlsplit(request_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["audience"] = OIDC_AUDIENCE
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {request_token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        fail("GitHub OIDC token request failed")
    token = payload.get("value")
    if not isinstance(token, str) or not token:
        fail("GitHub OIDC endpoint returned no identity token")
    return token


class GitHubActionsPrincipalVerifier:
    """Verify the signed GitHub Actions owner workload identity for T18."""

    def __init__(self, expected_sha: str) -> None:
        self.expected_sha = expected_sha
        self.verifier = OIDCVerifier(
            OIDCSettings(
                issuer=OIDC_ISSUER,
                audience=OIDC_AUDIENCE,
                jwks_url=OIDC_JWKS_URL,
            )
        )
        self.claims: dict[str, object] = {}

    def verify_identity_token(self, token: str) -> dict[str, object]:
        try:
            claims = self.verifier.verify_identity_token(token)
        except AuthenticationError:
            raise
        try:
            validate_github_actions_identity_claims(
                claims, expected_sha=self.expected_sha
            )
        except GitHubActionsIdentityError as exc:
            raise AuthenticationError("invalid_github_actions_identity") from exc
        if claims.get("iss") != OIDC_ISSUER or claims.get("sub") != EXPECTED_OIDC_SUBJECT:
            raise AuthenticationError("unexpected_identity_subject")
        if claims.get("actor_id") != OWNER_ID or claims.get("repository_id") != REPOSITORY_ID:
            raise AuthenticationError("unexpected_identity_actor")
        audience = claims.get("aud")
        audiences = (
            (audience,)
            if isinstance(audience, str)
            else tuple(audience)
            if isinstance(audience, list)
            else ()
        )
        if OIDC_AUDIENCE not in audiences:
            raise AuthenticationError("unexpected_identity_audience")
        self.claims = dict(claims)
        return self.claims

    def verify_access_token(self, token: str) -> AuthenticatedIdentityPrincipal:
        claims = self.verify_identity_token(token)
        issuer = claims.get("iss")
        subject = claims.get("sub")
        audience = claims.get("aud")
        audiences = (
            (audience,)
            if isinstance(audience, str)
            else tuple(audience)
            if isinstance(audience, list)
            else ()
        )
        if not isinstance(issuer, str) or not isinstance(subject, str) or not audiences:
            raise AuthenticationError("invalid_verified_identity")
        return AuthenticatedIdentityPrincipal(
            issuer=issuer,
            subject=subject,
            audiences=audiences,
        )


def authorize_b4_completion(
    *,
    expected_sha: str,
    changed_paths: list[str],
    owner_event: dict,
    master_blob_sha: str,
    ci_evidence: dict,
) -> tuple[dict, dict, dict, dict]:
    token = request_github_oidc_token()
    principal_verifier = GitHubActionsPrincipalVerifier(expected_sha)
    try:
        principal_verifier.verify_identity_token(token)
    except AuthenticationError as exc:
        fail(f"GitHub Actions OIDC identity verification failed: {exc.code}")
    claims = principal_verifier.claims

    context = OperatorContext(
        gate="BACKEND-001",
        subtask="BACKEND-001-B4",
        task=(
            "Complete only the canonical ARCH-037 PostgreSQL persistence boundary "
            "after exact-SHA database, migration, tenant isolation, session, Redis, "
            "audit, backup and recovery verification."
        ),
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
        metadata={
            "baseline_head": BASELINE_HEAD,
            "state_blob_sha": BASELINE_STATE_BLOB_SHA,
            "backend_master_blob_sha": master_blob_sha,
            "owner_source_commit": expected_sha,
            "owner_id": OWNER_ID,
            "repository_id": REPOSITORY_ID,
            "oidc_subject": EXPECTED_OIDC_SUBJECT,
            "current_subtask": "BACKEND-001-B4",
            "next_subtask": "BACKEND-001-B2-PRODUCTION-BINDING",
            "b4_acceptance_criteria_count": len(B4_ACCEPTANCE_CRITERIA),
            "ci_run_id": ci_evidence["run_id"],
            "ci_run_attempt": ci_evidence["attempt"],
            "production_release_ready": ci_evidence["summary"]["production_release_ready"],
            "production_release_blockers": ci_evidence["summary"]["production_release_blockers"],
            "production_recovery_tested": False,
        },
    )
    operator_request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.PROPOSE_CHANGE,
        objective=(
            "Record the exact-SHA verified completion of BACKEND-001-B4 only. "
            "Preserve ARCH-037 as the sole database schema authority, the existing "
            "PostgresRuntime and migration runner, the canonical CORE write owners, "
            "tenant RLS/FORCE RLS, durable session/revocation storage, shared Redis "
            "rate limiting and minimized append-only audit persistence. Require the "
            "complete ordered migration ledger, concurrency and separate-database "
            "full-database recovery proof. Keep production release readiness, "
            "production disaster recovery and PITR explicitly unclaimed. Do not "
            "introduce another database, schema, transaction, migration or state owner."
        ),
        evidence=(
            f"baseline_head={BASELINE_HEAD}",
            f"state_blob_sha={BASELINE_STATE_BLOB_SHA}",
            f"backend_master_blob_sha={master_blob_sha}",
            f"owner_source_commit={expected_sha}",
            f"owner_id={OWNER_ID}",
            f"repository_id={REPOSITORY_ID}",
            f"oidc_subject={EXPECTED_OIDC_SUBJECT}",
            f"changed_path_count={len(changed_paths)}",
            f"actions_run_id={ci_evidence['run_id']}",
            f"actions_run_attempt={ci_evidence['attempt']}",
            f"backend_tests_passed={ci_evidence['summary']['tests_passed']}",
            f"acrl_tests_passed={ci_evidence['summary']['acrl_tests_passed']}",
            "b4_recovery=PASS",
            "production_recovery=NOT_TESTED",
        ),
        metadata={
            "workstream": "BACKEND",
            "subtask": "BACKEND-001-B4",
            "scope": "B4_ONLY",
        },
    )
    operator_report = OperatorAutonomyEngine.operate(operator_request)
    if operator_report.decision.value != "PROPOSE":
        fail(f"T15 did not produce PROPOSE: {operator_report.decision.value}")

    analyzer = ChangeImpactAnalyzer(ROOT)
    impact_report = analyzer.analyze(changed_paths)
    analyzer.validate_report(impact_report)
    if (
        not impact_report.ready_for_handoff
        or impact_report.unknown_paths
        or impact_report.protected_paths
    ):
        fail(
            "T17 exact-path impact analysis is not clear: "
            f"unknown={list(impact_report.unknown_paths)}, "
            f"protected={list(impact_report.protected_paths)}"
        )

    nonce = (
        f"{os.environ['ACTIONS_RUN_ID']}:{os.environ['ACTIONS_RUN_ATTEMPT']}:{expected_sha}"
    )
    base_request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce=nonce,
    )
    approval = HumanApproval(
        approval_id=f"GH-OWNER-PUSH:{expected_sha}",
        authority="GITHUB_REPOSITORY_OWNER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(base_request),
        evidence=(
            f"GitHub repository owner: {OWNER}",
            f"GitHub repository owner ID: {OWNER_ID}",
            f"GitHub actor: {claims['actor']}",
            f"GitHub actor ID: {claims['actor_id']}",
            f"Repository: {REPOSITORY}",
            f"Repository ID: {REPOSITORY_ID}",
            f"Branch: {BRANCH}",
            f"Owner-approved source commit: {expected_sha}",
            f"Required commit prefix: {APPROVAL_PREFIX}",
            f"OIDC immutable subject: {EXPECTED_OIDC_SUBJECT}",
            f"Push event sender: {owner_event['sender']['login']}",
            f"Actions run ID: {os.environ['ACTIONS_RUN_ID']}",
            f"Actions run attempt: {os.environ['ACTIONS_RUN_ATTEMPT']}",
        ),
        principal_issuer=str(claims["iss"]),
        principal_subject=str(claims["sub"]),
        authentication_token=token,
    )
    authorization = ExecutionAuthorizationGuard(
        SafeAuthorizationPolicy(
            maximum_risk=OperatorRisk.MEDIUM,
            trusted_approver_principals=((OIDC_ISSUER, EXPECTED_OIDC_SUBJECT),),
        ),
        principal_verifier=principal_verifier,
    ).authorize(
        AuthorizationRequest(
            operator_report=operator_report,
            impact_report=impact_report,
            approval=approval,
            nonce=nonce,
        )
    )
    if (
        authorization.decision.value != "AUTHORIZE"
        or authorization.execution_authorized is not True
        or authorization.state_mutated is not False
        or authorization.requires_external_executor is not True
    ):
        fail(
            "T18 did not authorize the bounded external Control Center transition: "
            f"{authorization.decision.value}/{authorization.reason.value}"
        )

    approval_record = {
        "actor": claims["actor"],
        "actor_id": str(claims["actor_id"]),
        "source_commit": expected_sha,
        "state_blob_sha": BASELINE_STATE_BLOB_SHA,
        "oidc_issuer": str(claims["iss"]),
        "oidc_subject": str(claims["sub"]),
        "owner_id": OWNER_ID,
        "repository_id": REPOSITORY_ID,
        "actions_run_id": os.environ["ACTIONS_RUN_ID"],
        "actions_run_attempt": os.environ["ACTIONS_RUN_ATTEMPT"],
    }
    # The OIDC bearer token is never returned, logged or persisted.
    return (
        operator_report.to_dict(),
        impact_report.to_dict(),
        authorization.to_dict(),
        approval_record,
    )


def read_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("canonical state.json is missing or invalid")


def _subtasks_by_id(gate: dict) -> dict[str, dict]:
    raw = gate.get("subtasks")
    if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
        fail("BACKEND-001 subtask list is malformed")
    ids = [item.get("id") for item in raw]
    if (
        any(not isinstance(value, str) or not value for value in ids)
        or len(ids) != len(set(ids))
    ):
        fail("BACKEND-001 subtask identifiers are missing or duplicated")
    return {item["id"]: item for item in raw}


def expected_subtask_statuses(transitioned: bool) -> dict[str, str]:
    statuses = {
        "BACKEND-001-B0": "DONE",
        "BACKEND-001-B1": "DONE",
        "BACKEND-001-B2-FOUNDATION": "DONE",
        "BACKEND-001-B3": "DONE",
        "BACKEND-001-B4": "DONE" if transitioned else "CURRENT",
        "BACKEND-001-B2-PRODUCTION-BINDING": "CURRENT" if transitioned else "PENDING",
    }
    statuses.update({f"BACKEND-001-B{number}": "PENDING" for number in range(5, 11)})
    return statuses


def validate_state(
    state: dict,
    *,
    transitioned: bool,
    expected_sha: str | None = None,
    run_id: str | None = None,
) -> None:
    if not isinstance(state, dict):
        fail("canonical state must be an object")
    integrity = state.get("integrity", {})
    if integrity.get("sha256") != controller.calculate_hash(state):
        fail("canonical state integrity hash is invalid")
    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get("BACKEND-001")
    if not isinstance(gate, dict):
        fail("canonical BACKEND-001 gate is missing")
    if execution.get("current_gate") != "BACKEND-001" or gate.get("status") != "CURRENT":
        fail("BACKEND-001 is no longer the current gate")
    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution mode is not CONTROL_CENTER_DRIVEN")
    if gate.get("technical_sequence") != BACKEND_TECHNICAL_SEQUENCE:
        fail("canonical backend technical sequence differs from the approved plan")

    actual_ids = [
        item.get("id") for item in gate.get("subtasks", []) if isinstance(item, dict)
    ]
    expected_order = [
        f"BACKEND-001-{stage_id}" for stage_id, _, _ in BACKEND_STAGES
    ]
    if actual_ids != expected_order:
        fail("canonical backend subtask order or identifier inventory changed")
    subtasks = _subtasks_by_id(gate)
    wanted = expected_subtask_statuses(transitioned)
    if set(subtasks) != set(wanted):
        fail("canonical backend subtask inventory differs from the exact B0-B10 contract")
    for subtask_id, status in wanted.items():
        if subtasks[subtask_id].get("status") != status:
            fail(
                f"{subtask_id} must be {status}; "
                f"found {subtasks[subtask_id].get('status')!r}"
            )

    current = (
        "BACKEND-001-B2-PRODUCTION-BINDING"
        if transitioned
        else "BACKEND-001-B4"
    )
    if gate.get("current_subtask") != current or execution.get("current_subtask") != current:
        fail(f"Control Center current subtask must be {current}")
    expected_acceptance = (
        B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
        if transitioned
        else B4_ACCEPTANCE_CRITERIA
    )
    if execution.get("current_acceptance_criteria") != expected_acceptance:
        fail("execution acceptance-criteria projection does not match the current backend subtask")

    if subtasks["BACKEND-001-B3"].get("acceptance_criteria") != B3_ACCEPTANCE_CRITERIA:
        fail("B3 acceptance-criteria contract has changed")
    if subtasks["BACKEND-001-B4"].get("acceptance_criteria") != B4_ACCEPTANCE_CRITERIA:
        fail("B4 acceptance-criteria contract has changed")
    if (
        subtasks["BACKEND-001-B2-PRODUCTION-BINDING"].get("acceptance_criteria")
        != B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
    ):
        fail("B2 production-binding acceptance-criteria contract has changed")

    criteria = gate.get("criteria_state", [])
    if not isinstance(criteria, list) or len(criteria) != 10:
        fail("backend gate-level AC01-AC10 inventory has changed")
    expected_criteria_ids = {
        f"BACKEND-001-AC{number:02d}" for number in range(1, 11)
    }
    actual_criteria_ids = {
        item.get("id") for item in criteria if isinstance(item, dict)
    }
    if actual_criteria_ids != expected_criteria_ids:
        fail("backend gate-level acceptance criterion identifiers changed")
    if any(
        not isinstance(item, dict)
        or item.get("status") != "PENDING"
        or item.get("evidence") is not None
        or item.get("verified_at") is not None
        for item in criteria
    ):
        fail("B4 transition must leave all BACKEND-001-AC01 through AC10 PENDING")
    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("Control Center handoff path is not repository-relative")
    if not is_phase_coherent(state):
        fail("canonical Control Center phase projection is not coherent")

    if transitioned:
        note = subtasks["BACKEND-001-B4"].get("note", "")
        if not isinstance(note, str) or not expected_sha or expected_sha not in note:
            fail("B4 completion note is not bound to the exact verified source SHA")
        if not run_id or run_id not in note:
            fail("B4 completion note is not bound to the exact Actions run ID")
        if "all eight b4 acceptance criteria" not in note.lower():
            fail("B4 completion note does not record all eight acceptance criteria")
        if "production release readiness is not claimed" not in note.lower():
            fail("B4 completion note incorrectly implies production release readiness")


def verify_current_state(state: dict) -> None:
    validate_state(state, transitioned=False)
    if state.get("execution", {}).get("current_subtask") != "BACKEND-001-B4":
        fail("canonical execution position is not BACKEND-001-B4")


def validate_transition_state(state: dict, *, expected_sha: str, run_id: str) -> None:
    validate_state(
        state,
        transitioned=True,
        expected_sha=expected_sha,
        run_id=run_id,
    )


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"], cwd=ROOT
    )
    if original.count(b"\n") > 0 and original.count(b"\n") == original.count(b"\r\n"):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def build_completion_evidence(
    *,
    expected_sha: str,
    ci: dict,
    implementation: dict,
    operator_report: dict,
    impact_report: dict,
    authorization: dict,
    approval_record: dict,
    state_blob_sha: str,
) -> str:
    summary = ci["summary"]
    recovery = summary["recovery"]
    run_url = ci["run_url"]
    lines = [
        "# HOMIO / REOS — B4 Completion CI Evidence",
        "",
        "**Document ID:** B4-CI-001  ",
        "**Workstream:** BACKEND-001  ",
        "**Subtask:** BACKEND-001-B4 — PostgreSQL integration  ",
        "**Architecture:** ARCH-037 — Database Final Schema Design v1.0  ",
        "**Evidence status:** `GUARDED_B4_COMPLETION_VERIFIED`  ",
        "**Production release readiness:** `NOT_CLAIMED`",
        "",
        "## 1. Exact source and authority identity",
        "",
        f"- Repository: `{REPOSITORY}`",
        f"- Branch: `{BRANCH}`",
        f"- Exact source SHA: `{expected_sha}`",
        f"- `state.json` baseline blob SHA: `{BASELINE_STATE_BLOB_SHA}`",
        f"- B4 work-plan blob SHA: `{implementation['plan_blob_sha']}`",
        f"- Backend master blob SHA: `{implementation['master_blob_sha']}`",
        f"- B4 research register blob SHA: `{implementation['register_blob_sha']}`",
        f"- Physical-schema manifest blob SHA: `{implementation['schema_manifest_blob_sha']}`",
        f"- Target recovery evidence blob SHA: `{implementation['target_recovery_blob_sha']}`",
        f"- Post-transition state blob SHA: `{state_blob_sha}`",
        "",
        "## 2. GitHub Actions identity",
        "",
        f"- Workflow: `{ci['workflow_name']}`",
        f"- Run ID: `{ci['run_id']}`",
        f"- Attempt: `{ci['attempt']}`",
        f"- Run URL: [{ci['run_id']}]({run_url})",
        f"- Verification job ID: `{ci['job_id']}`",
        f"- Verification job conclusion: `{ci['job_conclusion']}`",
        f"- Exact tested source SHA: `{ci['tested_sha']}`",
        "- Verification job checked out the exact triggering commit: **PASS**",
        "- Backend/T21/ACRL verification dependency: **PASS**",
        "",
        "## 3. Environment and commands",
        "",
        "- Node.js: `24`",
        "- Python: `3.12`",
        "- PostgreSQL: `18.4`",
        "- Redis: `8.0.3`",
        "- Backend command: `npm ci --no-audit --fund=false && npm run verify`",
        "- `npm run verify`: lint, typecheck, Vitest and reproducible build verification",
        "- PostgreSQL integration and recovery: existing verification workflow scripts and B4 Vitest integration tests",
        "- Redis integration: existing Redis 8 distributed rate-limit verifier and Vitest tests",
        "- ACRL: complete existing ACRL regression suite",
        "",
        "## 4. Test execution",
        "",
        f"- Vitest files: `{summary['test_files_passed']}/{summary['test_files_total']} passed`",
        f"- Vitest test cases: `{summary['tests_passed']}/{summary['tests_total']} passed`",
        f"- Failed tests: `{summary['failed']}`",
        f"- Skipped tests: `{summary['skipped']}`",
        f"- Blocked tests: `{summary['blocked']}`",
        f"- Complete ACRL regression: `{summary['acrl_tests_passed']} passed`",
        "- B1 reproducible build verification: `PASS`",
        "",
        "### Required B4 test file results",
        "",
        "| Test owner | Tests passed |",
        "|---|---:|",
        f"| ARCH-037 physical schema integration | {summary['test_counts']['arch037_schema']} |",
        f"| B4 full-database recovery integration | {summary['test_counts']['b4_recovery']} |",
        f"| Ordered PostgreSQL migration validation | {summary['test_counts']['postgres_migrations']} |",
        f"| Durable session integration | {summary['test_counts']['postgres_session_integration']} |",
        f"| Security audit integration | {summary['test_counts']['postgres_audit_integration']} |",
        f"| Global PostgreSQL transaction owner | {summary['test_counts']['postgres_global_transaction']} |",
        f"| PostgreSQL runtime role safety | {summary['test_counts']['postgres_role_safety']} |",
        f"| Shared Redis rate-limit tests | {summary['test_counts']['redis_rate_limit']} |",
        f"| Production persistence composition | {summary['test_counts']['production_persistence']} |",
        f"| CORE-002 transactional outbox | {summary['test_counts']['core002_outbox']} |",
        f"| PostgreSQL runtime and transaction owner | {summary['test_counts']['postgres_runtime']} |",
        f"| Production runtime wiring | {summary['test_counts']['production_runtime']} |",
        f"| Dependency failure readiness | {summary['test_counts']['dependency_readiness']} |",
        f"| API security regression | {summary['test_counts']['api_security']} |",
        "",
        "## 5. Canonical migration inventory and checksums",
        "",
        "The guard recomputed SHA-256 from the exact UTF-8 SQL file bytes and verified the existing migration-runner manifest. IDs are contiguous and ordered from `00000001` through `00000011`.",
        "",
        "| Migration ID | SQL migration | SHA-256 | Bytes |",
        "|---|---|---|---:|",
    ]
    for migration in implementation["migrations"]:
        lines.append(
            f"| `{migration['id']}` | `{migration['name']}` | "
            f"`{migration['sha256']}` | {migration['bytes']} |"
        )
    lines.extend(
        [
            "",
            "## 6. Physical schema and canonical ownership",
            "",
            "| PostgreSQL schema | Canonical owner |",
            "|---|---|",
            "| `core001` | CORE-001 — identity, tenant and membership |",
            "| `core002` | CORE-002 — event envelope and transactional outbox |",
            "| `core003` | CORE-003 — lead and ownership |",
            "| `core004` | CORE-004 — project and inventory |",
            "| `core006` | CORE-006 — deal and transaction |",
            "| `core007` | CORE-007 — trust, fraud and governance |",
            "| `core008` | CORE-008 — commission and financial ledger |",
            "| `reos_infra` | B4 — sessions, audit, migration and database infrastructure |",
            "",
            "The physical-schema manifest maps canonical source owners, relations, columns, constraints and indexes. The guard verifies the manifest SHA and required owner mapping. CORE-005 remains owned by search/retrieval infrastructure and is not introduced as a second PostgreSQL business owner.",
            "",
            "## 7. Persistence security and transaction proof",
            "",
            "- Migration role and application role separation: **PASS**",
            "- Runtime-role safety and least privilege: **PASS**",
            "- ENABLE RLS and FORCE RLS on tenant-bearing relations: **PASS**",
            "- Fail-closed empty/malformed tenant context: **PASS**",
            "- Cross-tenant read/write denial: **PASS**",
            "- One existing `PostgresRuntime` transaction owner: **PASS**",
            "- No duplicate migration runner or schema authority: **PASS**",
            "- Durable session and revocation persistence: **PASS**",
            "- Minimized append-only security audit persistence: **PASS**",
            "- Redis 8 shared rate-limit concurrency and TTL reset: **PASS**",
            "",
            "## 8. Current full-database recovery result",
            "",
            f"- Source database: `{recovery['B4_RECOVERY_SOURCE_DATABASE']}`",
            f"- Separate restore database: `{recovery['B4_RECOVERY_TARGET_DATABASE']}`",
            f"- Backup SHA-256: `{recovery['B4_RECOVERY_BACKUP_SHA256']}`",
            f"- Backup size: `{recovery['backup_bytes']}` bytes",
            f"- Schema SHA-256: `{recovery['B4_RECOVERY_SCHEMA_SHA256']}`",
            f"- Canonical migration count: `{recovery['migration_count']}`",
            f"- Replay-applied migration count: `{recovery['replay_applied_count']}`",
            "- Schema integrity: **PASS**",
            "- Data integrity: **PASS**",
            "- Tenant isolation after restore: **PASS**",
            "- Database ACL and role/grant integrity: **PASS**",
            f"- Target classification: `{recovery['B4_RECOVERY_TARGET_CLASS']}`",
            "- Controlled non-production target restore: `NOT_VERIFIED`",
            "- Production disaster-recovery exercise: `NOT_TESTED`",
            "- WAL/PITR: `NOT_TESTED`",
            "",
            "The restore ran against a separate database inside the disposable GitHub Actions PostgreSQL 18.4 service. It is not evidence of an independently hosted target, production backup encryption, retention, key management, WAL archiving or PITR. The companion evidence file preserves these classifications:",
            "",
            f"`{TARGET_RECOVERY_EVIDENCE_PATH}`",
            "",
            "## 9. The eight B4 acceptance criteria",
            "",
            "| Criterion | Guarded completion evidence |",
            "|---|---|",
            "| B4-AC01 — approved ARCH-037 schema and canonical owners | Physical-schema mapping, canonical owners and exact source manifest verified. |",
            "| B4-AC02 — deterministic ordered migrations and integrity | 11 ordered migrations and exact SQL SHA-256 checksums verified; restore ledger matched; replay applied zero migrations. |",
            "| B4-AC03 — tenant access at persistence boundary | PostgreSQL role safety, ENABLE/FORCE RLS and cross-tenant isolation checks passed. |",
            "| B4-AC04 — explicit repository and transaction write ownership | Existing `PostgresRuntime` transaction owner and global transaction tests passed; no parallel persistence owner introduced. |",
            "| B4-AC05 — durable session and revocation storage | Session integration and full restore checks passed. |",
            "| B4-AC06 — shared rate limit and minimized audit persistence | Redis distributed concurrency/TTL and append-only security-audit tests passed. |",
            "| B4-AC07 — migration, concurrency, backup and recovery | Migration, concurrent writes and complete separate-database backup/restore passed on disposable CI PostgreSQL. |",
            "| B4-AC08 — no second schema or persistence authority | Existing runtime, migration runner, ARCH-037 and CORE owners reused; source allowlist rejects new competing owners. |",
            "",
            "## 10. Guarded owner authorization",
            "",
            "- Owner push and exact commit prefix: **PASS**",
            f"- Immutable owner identity: `{OWNER}` / `{OWNER_ID}`",
            f"- Repository identity: `{REPOSITORY}` / `{REPOSITORY_ID}`",
            f"- OIDC issuer: `{approval_record['oidc_issuer']}`",
            f"- OIDC subject: `{approval_record['oidc_subject']}`",
            "- T15: `PROPOSE`",
            f"- T15 request fingerprint: `{operator_report['request_fingerprint']}`",
            "- T17: `ANALYZE`",
            f"- T17 impact fingerprint: `{impact_report['fingerprint']}`",
            f"- T17 changed source paths: `{len(impact_report['changed_paths'])}`",
            f"- T17 unknown/protected paths: `{len(impact_report['unknown_paths'])}/{len(impact_report['protected_paths'])}`",
            "- T18: `AUTHORIZE`",
            f"- T18 authorization fingerprint: `{authorization['authorization_fingerprint']}`",
            "- OIDC bearer token persisted: **NO**",
            "",
            "## 11. Canonical Control Center result",
            "",
            "- BACKEND-001-B0: `DONE`",
            "- BACKEND-001-B1: `DONE`",
            "- BACKEND-001-B2-FOUNDATION: `DONE`",
            "- BACKEND-001-B3: `DONE`",
            "- BACKEND-001-B4: `DONE`",
            "- BACKEND-001-B2-PRODUCTION-BINDING: `CURRENT`",
            "- BACKEND-001-B5 through B10: `PENDING`",
            "- BACKEND-001-AC01 through AC10: `PENDING`",
            "- BACKEND-001 gate: remains `CURRENT`; the full backend gate is not closed",
            "",
            "## 12. GitHub Actions artifacts",
            "",
        ]
    )
    if ci["artifacts"]:
        lines.extend(
            ["| Artifact ID | Name | Expired |", "|---:|---|---|"]
        )
        for artifact in ci["artifacts"]:
            lines.append(
                f"| `{artifact['id']}` | `{artifact['name']}` | `{artifact['expired']}` |"
            )
    else:
        lines.append("No workflow artifacts were published by the exact run.")
    lines.extend(
        [
            "",
            "No B4 backup archive is claimed as an Actions artifact. The backup identity and digest are recorded in the job log and in the B4 target recovery evidence.",
            "",
            "## 13. Production-readiness boundary",
            "",
            f"B4 completion does not grant whole-backend release approval. The workflow product release evaluation reported `PRODUCTION_RELEASE_READY={str(summary['production_release_ready']).lower()}` and `PRODUCTION_RELEASE_BLOCKERS={summary['production_release_blockers']}`. Production security controls, controlled target recovery and PITR remain outside the verified disposable-CI recovery scope.",
            "",
            "## 14. Guard and readback decision",
            "",
            "- Existing Control Center `cmd_complete_subtask`: **USED**",
            "- Manual `state.json` editing: **NOT PERFORMED**",
            "- Guarded B4 subtask transition: **PASS**",
            "- Next current task: `BACKEND-001-B2-PRODUCTION-BINDING`",
            "- Exact source SHA and run/attempt binding: **PASS**",
            "- Remote branch/state/evidence/packet readback: **CHECKED AFTER GUARDED PUSH; REQUIRED FOR JOB SUCCESS**",
            "",
            "The guarded job pushes the Controller-produced transition commit, fetches the canonical branch again, and validates the remote commit SHA, state blob SHA, evidence markers and handoff packet markers. The workflow reports transition PASS only after all remote readbacks succeed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    required_env = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_RUN_ATTEMPT",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
        "ACTIONS_API_URL",
        "GITHUB_TOKEN",
        "RUNNER_TEMP",
    )
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        fail(f"required GitHub environment values are missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        fail("triggering source SHA is invalid")
    if os.environ["VERIFIED_CODE_SHA"] != expected_sha:
        fail("exact source verification SHA mismatch")

    owner_event = verify_owner_push(expected_sha)
    assert_exact_branch(expected_sha)
    changed_paths = verify_source_baseline(expected_sha)
    master_blob_sha, plan_blob_sha = verify_master_and_plan(expected_sha)
    implementation = verify_b4_implementation(expected_sha)

    run(
        [sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"],
        capture=False,
    )
    state = controller.load_state()
    verify_current_state(state)

    ci_evidence = verify_actions_run(expected_sha)
    operator_report, impact_report, authorization, approval_record = (
        authorize_b4_completion(
            expected_sha=expected_sha,
            changed_paths=changed_paths,
            owner_event=owner_event,
            master_blob_sha=master_blob_sha,
            ci_evidence=ci_evidence,
        )
    )

    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    run_id = os.environ["ACTIONS_RUN_ID"]
    attempt = os.environ["ACTIONS_RUN_ATTEMPT"]
    note = (
        "BACKEND-001-B4 completed through the guarded Control Center after exact-SHA "
        f"backend, PostgreSQL, Redis, migration, tenant-isolation, session, audit, "
        f"full-database backup/recovery and complete ACRL verification passed for "
        f"source commit {expected_sha}; GitHub Actions run {run_id}, attempt {attempt}. "
        "All eight B4 acceptance criteria were independently verified against the "
        "canonical ARCH-037 schema, ordered migration checksums, PostgreSQL role/RLS "
        "boundary, existing PostgresRuntime transaction owner, durable session and "
        "revocation store, shared Redis rate limit, minimized append-only audit store, "
        "concurrency tests and full-database separate-target CI recovery. The recovery "
        "target was disposable GitHub Actions PostgreSQL 18.4; controlled non-production "
        "target restore, production disaster recovery and WAL/PITR remain NOT TESTED. "
        "No second schema, persistence, migration, transaction or task-state owner was "
        "introduced. B4 is DONE and BACKEND-001-B2-PRODUCTION-BINDING is now CURRENT. "
        "BACKEND-001-AC01 through AC10 remain PENDING. Production release readiness "
        "is not claimed."
    )
    controller.cmd_complete_subtask(state, "BACKEND-001-B4", note)

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    run(
        [sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"],
        capture=False,
    )
    transitioned = controller.load_state()
    validate_transition_state(
        transitioned,
        expected_sha=expected_sha,
        run_id=run_id,
    )

    packet_markers = (
        "CURRENT_SUBTASK=BACKEND-001-B2-PRODUCTION-BINDING",
        "BACKEND-001-B4|DONE|PostgreSQL integration",
        "BACKEND-001-B2-PRODUCTION-BINDING|CURRENT|API security and trusted context — production binding",
        "BACKEND-001-AC01|PENDING|",
        "BACKEND-001-AC10|PENDING|",
    )
    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in packet_markers:
            if marker not in content:
                fail(f"{path.name} is missing expected handoff marker {marker!r}")

    state_blob_sha = run(["git", "hash-object", str(STATE)], display=False)
    evidence_content = build_completion_evidence(
        expected_sha=expected_sha,
        ci=ci_evidence,
        implementation=implementation,
        operator_report=operator_report,
        impact_report=impact_report,
        authorization=authorization,
        approval_record=approval_record,
        state_blob_sha=state_blob_sha,
    )
    evidence_path = ROOT / B4_COMPLETION_EVIDENCE_PATH
    if evidence_path.exists():
        fail("B4 completion evidence appeared during the guarded transition")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(evidence_content, encoding="utf-8", newline="\n")

    tracked_allowlist = {
        STATE_PATH,
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }
    actual_tracked = set(
        run(["git", "diff", "--name-only"], display=False).splitlines()
    )
    if actual_tracked != tracked_allowlist:
        fail(
            "Control Center tracked-path allowlist mismatch: "
            f"{sorted(actual_tracked)}"
        )
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

    untracked = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            display=False,
        ).splitlines()
    )
    snapshot_candidates = [
        item
        for item in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
            item,
        )
    ]
    if (
        len(snapshot_candidates) != 1
        or untracked.count(B4_COMPLETION_EVIDENCE_PATH) != 1
        or len(untracked) != 2
    ):
        fail(
            "expected exactly one Control Center snapshot plus one B4 completion "
            f"evidence file; found {untracked}"
        )
    snapshot_path = ROOT / snapshot_candidates[0]
    snapshot_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot_data.get("integrity", {}).get("sha256") != controller.calculate_hash(
        snapshot_data
    ):
        fail("Control Center snapshot integrity is invalid")

    stage_paths = sorted(
        tracked_allowlist | {B4_COMPLETION_EVIDENCE_PATH, snapshot_candidates[0]}
    )
    run(["git", "add", "--", *stage_paths])
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"])
    staged = set(
        run(["git", "diff", "--cached", "--name-only"], display=False).splitlines()
    )
    if staged != set(stage_paths):
        fail("staged B4 Control Center transition path allowlist mismatch")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            "chore(control-center): complete BACKEND-001-B4 via controller",
        ],
        capture=False,
    )
    transition_sha = run(["git", "rev-parse", "HEAD"], display=False)
    if run(["git", "rev-parse", "HEAD^"], display=False) != expected_sha:
        fail("Control Center transition commit parent is not the tested source commit")

    run(
        ["git", "push", "origin", f"HEAD:refs/heads/{BRANCH}"],
        capture=False,
    )
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"], display=False)
    if remote_sha != transition_sha:
        fail("canonical branch readback differs from the guarded transition commit")

    remote_state_raw = subprocess.check_output(
        ["git", "show", f"{remote_sha}:{STATE_PATH}"], cwd=ROOT
    )
    remote_state = json.loads(remote_state_raw.decode("utf-8"))
    validate_transition_state(
        remote_state,
        expected_sha=expected_sha,
        run_id=run_id,
    )
    remote_state_blob_sha = run(
        ["git", "rev-parse", f"{remote_sha}:{STATE_PATH}"],
        display=False,
    )
    if remote_state_blob_sha != state_blob_sha:
        fail("remote canonical state blob SHA differs from local Control Center output")

    remote_evidence = run(
        ["git", "show", f"{remote_sha}:{B4_COMPLETION_EVIDENCE_PATH}"],
        display=False,
    )
    for marker in (
        expected_sha,
        run_id,
        ci_evidence["job_id"],
        operator_report["request_fingerprint"],
        impact_report["fingerprint"],
        authorization["authorization_fingerprint"],
        state_blob_sha,
        "BACKEND-001-B4: `DONE`",
        "BACKEND-001-B2-PRODUCTION-BINDING: `CURRENT`",
        "Production disaster-recovery exercise: `NOT_TESTED`",
        "WAL/PITR: `NOT_TESTED`",
    ):
        if marker not in remote_evidence:
            fail(f"remote B4 completion evidence is missing marker: {marker}")
    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        remote_text = run(["git", "show", f"{remote_sha}:{relative}"], display=False)
        for marker in packet_markers:
            if marker not in remote_text:
                fail(f"remote {relative} is missing {marker!r}")

    print(f"B4_SOURCE_COMMIT={expected_sha}")
    print(f"B4_ACTIONS_RUN_ID={run_id}")
    print(f"B4_ACTIONS_ATTEMPT={attempt}")
    print(f"B4_VERIFICATION_JOB_ID={ci_evidence['job_id']}")
    print(f"B4_TRANSITION_COMMIT={transition_sha}")
    print(f"B4_CANONICAL_BRANCH_HEAD={remote_sha}")
    print(f"B4_POST_TRANSITION_STATE_BLOB_SHA={remote_state_blob_sha}")
    print("B4_TEST_AND_ACRL_VERIFICATION=PASS")
    print("B4_MIGRATION_MANIFEST=PASS")
    print("B4_FULL_DATABASE_RECOVERY=PASS")
    print("B4_EIGHT_ACCEPTANCE_CRITERIA=PASS")
    print("B4_T15_T17_T18_AUTHORIZATION=PASS")
    print("B4_CONTROL_CENTER_TRANSITION=PASS")
    print("B4_CANONICAL_REMOTE_READBACK=PASS")
    print("BACKEND-001-B2-PRODUCTION-BINDING=CURRENT")
    print("B4_PRODUCTION_RECOVERY=NOT_TESTED")
    print("B4_PITR=NOT_TESTED")


if __name__ == "__main__":
    main()



