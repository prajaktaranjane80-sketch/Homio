from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data" / "state.json"
PACKET = CONTROL / "packets" / "NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
APPROVAL_PREFIX = "[CONTROL-CENTER-COMPLETE-BACKEND-001-B3]"
OIDC_AUDIENCE = "homio-control-center-backend-b3-completion"
OIDC_JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"

BASELINE_HEAD = "b0d6b8c2cf0d9e5c32c719d20915fe1d24e2fd3c"
BASELINE_STATE_BLOB_SHA = "19a40749611c98bab182b9853ed6a25c986d2eb8"
BASELINE_MASTER_BLOB_SHA = "f8d9cd456568cc6c8eaae0caf764123a7e859ba6"
BASELINE_CONTRACT_BLOB_SHA = "76b24db805c8105a85b5c141037485f01d19c757"

STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
MASTER_PATH = (
    "REOS_CONTROL_CENTER/architecture/backend/plans/"
    "HOMIO_Backend_Structure"
)
CONTRACT_PATH = (
    "REOS_CONTROL_CENTER/backend/contracts/python-runtime/v1/contract.json"
)
OWNER_REQUEST_PATH = "REOS_CONTROL_CENTER/evidence/BACKEND-001/B3-completion-request.md"
EVIDENCE_PATH = "REOS_CONTROL_CENTER/evidence/BACKEND-001/B3-completion-ci-evidence.md"
RUNTIME_TEST_PATH = (
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/"
    "tests/test_b3_read_only_boundary.py"
)
ACTION_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b3-completion/action.yml"
)
GUARD_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b3-completion/scripts/guarded_transition.py"
)
GUARD_TEST_PATH = (
    ".github/actions/homio-backend-ci/transitions/"
    "backend-b3-completion/scripts/test_guarded_transition.py"
)
REUSABLE_WORKFLOW_PATH = ".github/workflows/reusable-backend-b3-completion.yml"
WORKFLOW_PATH = ".github/workflows/backend-ci.yml"

EXPECTED_SOURCE_PATHS = {
    WORKFLOW_PATH,
    REUSABLE_WORKFLOW_PATH,
    ACTION_PATH,
    GUARD_PATH,
    GUARD_TEST_PATH,
    RUNTIME_TEST_PATH,
    OWNER_REQUEST_PATH,
}

# The bridge and contract are existing owners. B3 may add focused regressions,
# but must not silently rewrite or duplicate the authenticated transport.
EXPECTED_B3_SOURCE_BLOBS = {
    "REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/client.ts": (
        "f7791f5c330c0237cec4c710d1f41c6dcc0d0ef8"
    ),
    "REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/contracts.ts": (
        "1bb86d28790f3a606f242603e2c06ad8ac0b6e79"
    ),
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/protocol.py": (
        "20ba424574b08452abd25d2923e719e88408b0d8"
    ),
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/worker.py": (
        "b642542ce7b9768cb3913ae9661c33d4955a9ed7"
    ),
    CONTRACT_PATH: BASELINE_CONTRACT_BLOB_SHA,
    "REOS_CONTROL_CENTER/backend/tests/integration/python-runtime-client.test.ts": (
        "4cb3834b6b12a22b094be1845a1d6020c48f9b18"
    ),
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/tests/test_protocol.py": (
        "f9fd89eb8d8d5371e8a226b234da22a6c39ca879"
    ),
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/tests/test_protocol_hardening.py": (
        "610158bbf25a24335e0ad994a0ca033ad849fd11"
    ),
    "REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/tests/fixtures/probe_owners.py": (
        "355b1a80bfbedc5e4e97b2b9c59cd5f7f688bcf0"
    ),
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
from homio_python_runtime import protocol  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"BACKEND-001-B3 COMPLETION BLOCKED: {message}")


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


def assert_exact_branch(expected_sha: str) -> None:
    if run(["git", "rev-parse", "HEAD"], display=False) != expected_sha:
        fail("checked-out HEAD differs from the exact verified source commit")
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("canonical branch moved; refusing a stale B3 transition")


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
        fail("only the immutable repository owner may authorize B3 completion")
    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("B3 completion requires an owner push, not PR or manual dispatch")
    if os.environ["GITHUB_REF"] != BRANCH_REF:
        fail("B3 transition is restricted to reos-development")
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
        fail("owner commit lacks the exact B3 completion approval prefix")
    return event


def verify_source_baseline(expected_sha: str) -> list[str]:
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("remote branch moved before B3 completion preflight")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASELINE_HEAD, expected_sha],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail("the exact audited B3 baseline is not an ancestor of this change")
    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("source checkout is not clean before the guarded transition")
    if file_blob_sha(STATE_PATH, BASELINE_HEAD) != BASELINE_STATE_BLOB_SHA:
        fail("audited baseline state blob differs from the pinned SHA")
    if file_blob_sha(MASTER_PATH, BASELINE_HEAD) != BASELINE_MASTER_BLOB_SHA:
        fail("audited baseline backend master differs from the pinned SHA")
    if file_blob_sha(STATE_PATH, expected_sha) != BASELINE_STATE_BLOB_SHA:
        fail("owner source changes must not modify canonical state.json")
    if file_blob_sha(MASTER_PATH, expected_sha) != BASELINE_MASTER_BLOB_SHA:
        fail("B3 owner commit must not silently edit the technical master")

    changed = run(["git", "diff", "--name-only", BASELINE_HEAD, expected_sha]).splitlines()
    if set(changed) != EXPECTED_SOURCE_PATHS:
        missing = sorted(EXPECTED_SOURCE_PATHS - set(changed))
        unexpected = sorted(set(changed) - EXPECTED_SOURCE_PATHS)
        fail(f"exact B3 source-path allowlist mismatch; missing={missing}; unexpected={unexpected}")

    for path, expected_blob in EXPECTED_B3_SOURCE_BLOBS.items():
        if file_blob_sha(path, expected_sha) != expected_blob:
            fail(f"existing B3 owner changed unexpectedly: {path}")
    if not (ROOT / OWNER_REQUEST_PATH).is_file():
        fail("explicit B3 owner completion request is missing")
    if (ROOT / EVIDENCE_PATH).exists():
        fail("B3 completion evidence already exists; duplicate transition is forbidden")
    return sorted(changed)


def verify_master_contract(expected_sha: str) -> str:
    master = run(["git", "show", f"{expected_sha}:{MASTER_PATH}"], display=False)
    markers = (
        "### B3 — Python domain-runtime bridge",
        "### B4 — PostgreSQL integration",
        "### B2-PRODUCTION-BINDING — API security and trusted context production binding",
    )
    for marker in markers:
        if marker not in master:
            fail(f"technical master is missing required stage: {marker}")
    if master.index(markers[0]) > master.index(markers[1]):
        fail("technical master no longer places B3 before B4")
    if master.index(markers[1]) > master.index(markers[2]):
        fail("technical master no longer places B4 before B2 production binding")
    return file_blob_sha(MASTER_PATH, expected_sha)


def verify_contract() -> dict:
    try:
        contract = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("versioned Python runtime contract is missing or invalid JSON")
    meta = contract.get("contract", {})
    mutation = contract.get("mutation_policy", {})
    composition = contract.get("owner_composition", {})
    if meta.get("protocol") != protocol.PROTOCOL_NAME or meta.get("version") != protocol.PROTOCOL_VERSION:
        fail("Python and published B3 protocol version disagree")
    if meta.get("status") != "ACTIVE_READ_ONLY_FOUNDATION":
        fail("B3 protocol must remain an explicitly read-only foundation")
    if meta.get("public_network_listener") is not False:
        fail("B3 must not expose a public Python network listener")
    if not str(meta.get("transport", "")).startswith("Node-managed child-process"):
        fail("B3 transport differs from the approved private IPC boundary")
    if set(contract.get("operations", {})) != set(protocol.ALLOWED_OPERATIONS):
        fail("published operation allowlist differs from the Python protocol")
    if mutation.get("enabled") is not False:
        fail("mutations must remain disabled until B4 durable persistence exists")
    if mutation.get("idempotency_field") is not None:
        fail("B3 cannot define a second idempotency owner")
    if mutation.get("non_null_idempotency") != "reject with MUTATION_NOT_ENABLED":
        fail("B3 must reject mutation envelopes until B4 idempotency is bound")
    if mutation.get("automatic_mutation_retry") is not False:
        fail("B3 must never automatically retry mutations")
    future_requirements = set(mutation.get("required_before_enablement", []))
    required = {
        "B4 durable idempotency identity bound to tenant and operation",
        "canonical payload fingerprint",
        "durable result or outcome reconciliation",
        "same-key/different-payload conflict detection",
        "crash-after-commit-before-response recovery test",
    }
    if not required.issubset(future_requirements):
        fail("B3 contract is missing one or more B4 mutation-safety prerequisites")
    if composition.get("factory_required") is not True:
        fail("Python worker must require explicit canonical owner composition")
    if "AUTONOMY_ENGINE.continuity.acrl" not in composition.get("forbidden_production_namespaces", []):
        fail("production worker composition must explicitly forbid ACRL")
    return contract


def verify_owner_approval_context() -> str:
    content = (ROOT / OWNER_REQUEST_PATH).read_text(encoding="utf-8")
    required = (
        "APPROVAL: AUTHORIZE BACKEND-001-B3 COMPLETION",
        "SCOPE: BACKEND-001-B3 only",
        BASELINE_HEAD,
        BASELINE_STATE_BLOB_SHA,
        BASELINE_MASTER_BLOB_SHA,
        BASELINE_CONTRACT_BLOB_SHA,
        "[CONTROL-CENTER-COMPLETE-BACKEND-001-B3]",
        "B3 remains a private, authenticated, read-only IPC foundation.",
        "Mutation operations remain disabled until B4 supplies the durable idempotency and transaction owner.",
        "BACKEND-001-AC01 through BACKEND-001-AC10 remain PENDING.",
        "Manual `state.json` editing is prohibited.",
    )
    for marker in required:
        if marker not in content:
            fail(f"B3 owner request does not contain required scope/evidence: {marker}")
    return content


def request_github_oidc_token() -> str:
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not request_url or not request_token:
        fail("GitHub OIDC token request unavailable; id-token: write is required")
    parts = urlsplit(request_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["audience"] = OIDC_AUDIENCE
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    request = Request(
        url,
        headers={"Authorization": f"Bearer {request_token}", "Accept": "application/json"},
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
            validate_github_actions_identity_claims(claims, expected_sha=self.expected_sha)
        except GitHubActionsIdentityError as exc:
            raise AuthenticationError("invalid_github_actions_identity") from exc
        if claims.get("iss") != OIDC_ISSUER or claims.get("sub") != EXPECTED_OIDC_SUBJECT:
            raise AuthenticationError("unexpected_identity_subject")
        if claims.get("actor_id") != OWNER_ID or claims.get("repository_id") != REPOSITORY_ID:
            raise AuthenticationError("unexpected_identity_actor")
        audience = claims.get("aud")
        audiences = (audience,) if isinstance(audience, str) else tuple(audience) if isinstance(audience, list) else ()
        if OIDC_AUDIENCE not in audiences:
            raise AuthenticationError("unexpected_identity_audience")
        self.claims = dict(claims)
        return self.claims

    def verify_access_token(self, token: str) -> AuthenticatedIdentityPrincipal:
        claims = self.verify_identity_token(token)
        issuer = claims.get("iss")
        subject = claims.get("sub")
        audience = claims.get("aud")
        audiences = (audience,) if isinstance(audience, str) else tuple(audience) if isinstance(audience, list) else ()
        if not isinstance(issuer, str) or not isinstance(subject, str) or not audiences:
            raise AuthenticationError("invalid_verified_identity")
        return AuthenticatedIdentityPrincipal(issuer=issuer, subject=subject, audiences=audiences)


def authorize_b3_completion(
    *,
    expected_sha: str,
    changed_paths: list[str],
    owner_event: dict,
    master_blob_sha: str,
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
        subtask="BACKEND-001-B3",
        task="Complete only the existing authenticated, private, read-only Python domain-runtime IPC foundation after exact-SHA verification.",
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
            "current_subtask": "BACKEND-001-B3",
            "mutations_enabled": False,
            "next_subtask": "BACKEND-001-B4",
        },
    )
    operator_request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.PROPOSE_CHANGE,
        objective=(
            "Record the exact-SHA verified completion of the existing B3 private Python IPC foundation only. "
            "Preserve its authenticated child-process transport, versioned schemas, trusted context, timeout, "
            "cancellation and failure behavior. Keep mutation execution disabled until B4 durable idempotency "
            "and transaction ownership are implemented. Do not introduce a public Python API or new domain owner."
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
            f"actions_run_id={os.environ['ACTIONS_RUN_ID']}",
        ),
        metadata={"workstream": "BACKEND", "subtask": "BACKEND-001-B3", "scope": "B3_ONLY"},
    )
    operator_report = OperatorAutonomyEngine.operate(operator_request)
    if operator_report.decision.value != "PROPOSE":
        fail(f"T15 did not produce PROPOSE: {operator_report.decision.value}")

    analyzer = ChangeImpactAnalyzer(ROOT)
    impact_report = analyzer.analyze(changed_paths)
    analyzer.validate_report(impact_report)
    if not impact_report.ready_for_handoff or impact_report.unknown_paths or impact_report.protected_paths:
        fail(
            "T17 exact-path impact analysis is not clear: "
            f"unknown={list(impact_report.unknown_paths)}, protected={list(impact_report.protected_paths)}"
        )

    nonce = f"{os.environ['ACTIONS_RUN_ID']}:{os.environ['ACTIONS_RUN_ATTEMPT']}:{expected_sha}"
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
    }
    # The bearer token is held only in memory for T18 verification and is never returned or persisted.
    return operator_report.to_dict(), impact_report.to_dict(), authorization.to_dict(), approval_record


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
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        fail("BACKEND-001 subtask identifiers are missing or duplicated")
    return {item["id"]: item for item in raw}


def expected_subtask_statuses(transitioned: bool) -> dict[str, str]:
    statuses = {
        "BACKEND-001-B0": "DONE",
        "BACKEND-001-B1": "DONE",
        "BACKEND-001-B2-FOUNDATION": "DONE",
        "BACKEND-001-B3": "DONE" if transitioned else "CURRENT",
        "BACKEND-001-B4": "CURRENT" if transitioned else "PENDING",
        "BACKEND-001-B2-PRODUCTION-BINDING": "PENDING",
    }
    statuses.update({f"BACKEND-001-B{n}": "PENDING" for n in range(5, 11)})
    return statuses


def validate_state(state: dict, *, transitioned: bool, expected_sha: str | None = None, run_id: str | None = None) -> None:
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
    actual_ids = [item.get("id") for item in gate.get("subtasks", []) if isinstance(item, dict)]
    expected_order = [f"BACKEND-001-{stage_id}" for stage_id, _, _ in BACKEND_STAGES]
    if actual_ids != expected_order:
        fail("canonical backend subtask order or identifier inventory changed")
    subtasks = _subtasks_by_id(gate)
    wanted = expected_subtask_statuses(transitioned)
    if set(subtasks) != set(wanted):
        fail("canonical backend subtask inventory differs from the exact B0-B10 contract")
    for subtask_id, status in wanted.items():
        if subtasks[subtask_id].get("status") != status:
            fail(f"{subtask_id} must be {status}; found {subtasks[subtask_id].get('status')!r}")

    current = "BACKEND-001-B4" if transitioned else "BACKEND-001-B3"
    if gate.get("current_subtask") != current or execution.get("current_subtask") != current:
        fail(f"Control Center current subtask must be {current}")
    if execution.get("current_acceptance_criteria") != (B4_ACCEPTANCE_CRITERIA if transitioned else B3_ACCEPTANCE_CRITERIA):
        fail("execution acceptance-criteria projection does not match the current backend subtask")

    b3 = subtasks["BACKEND-001-B3"]
    if b3.get("acceptance_criteria") != B3_ACCEPTANCE_CRITERIA:
        fail("B3 acceptance-criteria contract has changed")
    if subtasks["BACKEND-001-B4"].get("acceptance_criteria") != B4_ACCEPTANCE_CRITERIA:
        fail("B4 acceptance-criteria contract has changed")

    criteria = gate.get("criteria_state", [])
    if not isinstance(criteria, list) or len(criteria) != 10:
        fail("backend gate-level AC01-AC10 inventory has changed")
    expected_criteria_ids = {f"BACKEND-001-AC{number:02d}" for number in range(1, 11)}
    actual_criteria_ids = {item.get("id") for item in criteria if isinstance(item, dict)}
    if actual_criteria_ids != expected_criteria_ids:
        fail("backend gate-level acceptance criterion identifiers changed")
    if any(not isinstance(item, dict) or item.get("status") != "PENDING" or item.get("evidence") is not None or item.get("verified_at") is not None for item in criteria):
        fail("B3 transition must leave all BACKEND-001-AC01 through AC10 PENDING")
    if state.get("session", {}).get("last_handoff") != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt":
        fail("Control Center handoff path is not repository-relative")
    if not is_phase_coherent(state):
        fail("canonical Control Center phase projection is not coherent")

    if transitioned:
        note = b3.get("note", "")
        if not isinstance(note, str) or not expected_sha or expected_sha not in note:
            fail("B3 completion note is not bound to the verified source SHA")
        if not run_id or run_id not in note:
            fail("B3 completion note is not bound to the Actions run ID")
        if "mutations remain disabled" not in note.lower():
            fail("B3 completion note does not preserve the read-only mutation boundary")


def verify_current_state(state: dict) -> None:
    validate_state(state, transitioned=False)
    if state.get("execution", {}).get("current_subtask") != "BACKEND-001-B3":
        fail("canonical execution position is not BACKEND-001-B3")


def validate_transition_state(state: dict, *, expected_sha: str, run_id: str) -> None:
    validate_state(state, transitioned=True, expected_sha=expected_sha, run_id=run_id)


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    if original.count(b"\n") > 0 and original.count(b"\n") == original.count(b"\r\n"):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def main() -> None:
    required_env = (
        "GITHUB_ACTOR", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "GITHUB_REF",
        "GITHUB_REPOSITORY", "EXPECTED_SHA", "VERIFIED_CODE_SHA", "ACTIONS_RUN_ID",
        "ACTIONS_RUN_ATTEMPT", "ACTIONS_SERVER_URL", "ACTIONS_REPOSITORY", "RUNNER_TEMP",
    )
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        fail(f"required GitHub environment values are missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    if os.environ["VERIFIED_CODE_SHA"] != expected_sha:
        fail("exact source verification SHA mismatch")
    owner_event = verify_owner_push(expected_sha)
    assert_exact_branch(expected_sha)
    changed_paths = verify_source_baseline(expected_sha)
    master_blob_sha = verify_master_contract(expected_sha)
    verify_contract()
    verify_owner_approval_context()

    run([sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"], capture=False)
    state = controller.load_state()
    verify_current_state(state)

    operator_report, impact_report, authorization, approval_record = authorize_b3_completion(
        expected_sha=expected_sha,
        changed_paths=changed_paths,
        owner_event=owner_event,
        master_blob_sha=master_blob_sha,
    )

    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    run_id = os.environ["ACTIONS_RUN_ID"]
    attempt = os.environ["ACTIONS_RUN_ATTEMPT"]
    note = (
        "BACKEND-001-B3 completed through the guarded Control Center after exact-SHA "
        f"backend, Python/TypeScript IPC contract, and complete ACRL verification passed "
        f"for source commit {expected_sha}; GitHub Actions run {run_id}, attempt {attempt}. "
        "The verified scope is the existing authenticated private Node-managed Python "
        "child-process bridge, versioned request/response contract, trusted actor/tenant/" 
        "correlation propagation, strict serialization, bounded timeout/cancellation, "
        "worker lifecycle, replay and failure classification. No Python business logic "
        "was copied into TypeScript and no second public Python API was introduced. "
        "The B3 protocol remains read-only. Mutations remain disabled until B4 supplies "
        "the canonical durable idempotency and transaction owner. Non-null idempotency "
        "envelopes fail closed and automatic mutation retries remain disabled. "
        "B4 is now CURRENT. B2 production binding and later backend stages remain pending. "
        "BACKEND-001-AC01 through AC10 remain PENDING. Production readiness is not claimed."
    )
    controller.cmd_complete_subtask(state, "BACKEND-001-B3", note)

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    run([sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"], capture=False)
    transitioned = controller.load_state()
    validate_transition_state(transitioned, expected_sha=expected_sha, run_id=run_id)

    packet_markers = (
        "CURRENT_SUBTASK=BACKEND-001-B4",
        "BACKEND-001-B3|DONE|Python domain-runtime bridge",
        "BACKEND-001-B4|CURRENT|PostgreSQL integration",
        "BACKEND-001-B2-PRODUCTION-BINDING|PENDING|API security and trusted context — production binding",
    )
    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in packet_markers:
            if marker not in content:
                fail(f"{path.name} is missing expected handoff marker {marker!r}")

    state_blob_sha = run(["git", "hash-object", str(STATE)], display=False)
    run_url = f"{os.environ['ACTIONS_SERVER_URL']}/{REPOSITORY}/actions/runs/{run_id}"
    evidence = [
        "# BACKEND-001 — B3 Python domain-runtime bridge completion evidence",
        "",
        f"- Repository: `{REPOSITORY}`",
        f"- Branch: `{BRANCH}`",
        f"- Verified source commit: `{expected_sha}`",
        f"- Actions run: [{run_id}]({run_url})",
        f"- Actions attempt: `{attempt}`",
        "- Exact-SHA backend and ACRL verification dependency: **PASS**",
        "- Existing TypeScript/Python bridge owner reused: **YES**",
        "- Public Python network listener: **NONE**",
        "- Protocol mode: **ACTIVE_READ_ONLY_FOUNDATION**",
        "- Mutation operations: **DISABLED / FAIL CLOSED**",
        "- Non-null idempotency envelope before B4: **REJECTED**",
        "- Automatic mutation retry: **DISABLED**",
        "- Canonical owner composition: explicit factory required; no in-memory production fallback",
        "- ACRL imported into customer runtime: **NO**",
        "- T15 decision: `PROPOSE`",
        f"- T15 request fingerprint: `{operator_report['request_fingerprint']}`",
        "- T17 decision: `ANALYZE`",
        f"- T17 fingerprint: `{impact_report['fingerprint']}`",
        f"- T17 changed paths: `{len(impact_report['changed_paths'])}`",
        f"- T17 unknown/protected paths: `{len(impact_report['unknown_paths'])}/{len(impact_report['protected_paths'])}`",
        "- T18 decision: `AUTHORIZE`",
        f"- T18 authorization fingerprint: `{authorization['authorization_fingerprint']}`",
        f"- OIDC issuer: `{approval_record['oidc_issuer']}`",
        f"- OIDC subject: `{approval_record['oidc_subject']}`",
        "- OIDC bearer token persisted: **NO**",
        "",
        "## Canonical Control Center result",
        "",
        "- BACKEND-001-B0: `DONE`",
        "- BACKEND-001-B1: `DONE`",
        "- BACKEND-001-B2-FOUNDATION: `DONE`",
        "- BACKEND-001-B3: `DONE`",
        "- BACKEND-001-B4: `CURRENT`",
        "- BACKEND-001-B2-PRODUCTION-BINDING: `PENDING`",
        "- BACKEND-001-B5 through B10: `PENDING`",
        "- BACKEND-001-AC01 through AC10: `PENDING`",
        "",
        "## Read-only and release boundaries",
        "",
        "B3 closes the authenticated IPC foundation only. Mutations remain disabled until B4 provides durable idempotency and transaction ownership. This evidence does not assert B4 completion, production adapter binding, customer route enablement, or production release readiness.",
        "",
        f"- Post-transition state blob SHA: `{state_blob_sha}`",
        f"- Backend master blob SHA: `{master_blob_sha}`",
        f"- Canonical technical sequence: `{BACKEND_TECHNICAL_SEQUENCE}`",
        "- State mutation owner: existing Control Center only",
        "- Manual state.json editing: **NOT PERFORMED**",
        "",
    ]
    evidence_path = ROOT / EVIDENCE_PATH
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("\n".join(evidence), encoding="utf-8", newline="\n")

    tracked_allowlist = {
        STATE_PATH,
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }
    actual_tracked = set(run(["git", "diff", "--name-only"], display=False).splitlines())
    if actual_tracked != tracked_allowlist:
        fail(f"Control Center tracked-path allowlist mismatch: {sorted(actual_tracked)}")
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

    untracked = sorted(run(["git", "ls-files", "--others", "--exclude-standard"], display=False).splitlines())
    snapshot_candidates = [
        item for item in untracked
        if re.fullmatch(r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json", item)
    ]
    if len(snapshot_candidates) != 1 or untracked.count(EVIDENCE_PATH) != 1 or len(untracked) != 2:
        fail(f"expected exactly one snapshot plus one B3 evidence file; found {untracked}")
    snapshot_path = ROOT / snapshot_candidates[0]
    snapshot_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot_data.get("integrity", {}).get("sha256") != controller.calculate_hash(snapshot_data):
        fail("Control Center snapshot integrity is invalid")

    stage_paths = sorted(tracked_allowlist | {EVIDENCE_PATH, snapshot_candidates[0]})
    run(["git", "add", "--", *stage_paths])
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"])
    staged = set(run(["git", "diff", "--cached", "--name-only"], display=False).splitlines())
    if staged != set(stage_paths):
        fail("staged Control Center transition path allowlist mismatch")

    run(
        [
            "git", "-c", "user.name=github-actions[bot]",
            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-m", "chore(control-center): complete BACKEND-001-B3 via controller",
        ],
        capture=False,
    )
    transition_sha = run(["git", "rev-parse", "HEAD"], display=False)
    if run(["git", "rev-parse", "HEAD^"], display=False) != expected_sha:
        fail("Control Center transition commit parent is not the tested source commit")

    run(["git", "push", "origin", f"HEAD:refs/heads/{BRANCH}"], capture=False)
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"], display=False)
    if remote_sha != transition_sha:
        fail("canonical branch readback differs from the guarded transition commit")

    remote_state_raw = subprocess.check_output(["git", "show", f"{remote_sha}:{STATE_PATH}"], cwd=ROOT)
    remote_state = json.loads(remote_state_raw.decode("utf-8"))
    validate_transition_state(remote_state, expected_sha=expected_sha, run_id=run_id)
    remote_state_blob_sha = run(["git", "rev-parse", f"{remote_sha}:{STATE_PATH}"], display=False)
    if remote_state_blob_sha != state_blob_sha:
        fail("remote canonical state blob SHA differs from local Control Center output")
    remote_evidence = run(["git", "show", f"{remote_sha}:{EVIDENCE_PATH}"], display=False)
    for marker in (
        expected_sha,
        run_id,
        operator_report["request_fingerprint"],
        impact_report["fingerprint"],
        authorization["authorization_fingerprint"],
        state_blob_sha,
        "BACKEND-001-B3: `DONE`",
        "BACKEND-001-B4: `CURRENT`",
        "Mutations remain disabled until B4",
    ):
        if marker not in remote_evidence:
            fail(f"remote B3 completion evidence is missing marker: {marker}")
    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        remote_text = run(["git", "show", f"{remote_sha}:{relative}"], display=False)
        for marker in packet_markers:
            if marker not in remote_text:
                fail(f"remote {relative} is missing {marker!r}")

    print(f"B3_SOURCE_COMMIT={expected_sha}")
    print(f"B3_ACTIONS_RUN_ID={run_id}")
    print(f"B3_ACTIONS_ATTEMPT={attempt}")
    print(f"B3_TRANSITION_COMMIT={transition_sha}")
    print(f"B3_CANONICAL_BRANCH_HEAD={remote_sha}")
    print(f"B3_POST_TRANSITION_STATE_BLOB_SHA={remote_state_blob_sha}")
    print("B3_T15_T17_T18_AUTHORIZATION=PASS")
    print("B3_CONTROL_CENTER_TRANSITION=PASS")
    print("B3_CANONICAL_REMOTE_READBACK=PASS")
    print("B3_MUTATIONS=REMAIN_DISABLED_UNTIL_B4")
    print("BACKEND-001-B4=CURRENT")


if __name__ == "__main__":
    main()
