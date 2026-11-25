from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data" / "state.json"
PACKET = CONTROL / "packets" / "NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"

APPROVAL_PREFIX = "[CONTROL-CENTER-COMPLETE-BACKEND-001-B4]"
OIDC_AUDIENCE = "homio-control-center-backend-b4-completion"
OIDC_JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"

# This checkpoint is the live branch HEAD after the owner saved the B4
# target-backup/restore evidence. It is a baseline, not an execution result.
BASELINE_HEAD = "8a15cfa03631198b6bdcfa768ce1372c9e74beec"
BASELINE_STATE_BLOB_SHA = "5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b"
BASELINE_MASTER_BLOB_SHA = "f8d9cd456568cc6c8eaae0caf764123a7e859ba6"
BASELINE_PLAN_BLOB_SHA = "84c94c82ac5b0fde7c7bdf94acca235402c465ab"
BASELINE_REGISTER_BLOB_SHA = "fe1deafb694534743447d9113ae52930d8b68d02"
BASELINE_ENTRYPOINT_BLOB_SHA = "2e1d66cec0a8ca17b24ccf285d3133ff16ca2834"
BASELINE_SCHEMA_MANIFEST_BLOB_SHA = "377fa5699f774769693b5363d2a10058d20c860c"
BASELINE_TARGET_RECOVERY_BLOB_SHA = "5009cf707eb860ef8e8417e81a7199dbef4bece5"

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

EXPECTED_SOURCE_PATHS = {
    WORKFLOW_PATH,
    REUSABLE_WORKFLOW_PATH,
    ACTION_PATH,
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

# Existing owners and evidence are pinned at the B4 checkpoint. The completion
# change may add only the four B4 guard files and the existing CI workflow wiring.
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

# Git blob hashes are pinned independently from the SQL-content SHA-256
# values. This detects both byte-level content drift and Git-object replacement.
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
        fail("GitHub push event payload missing or malformed etc.
