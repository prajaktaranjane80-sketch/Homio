
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"

STATE = CONTROL / "data" / "state.json"
PACKET = CONTROL / "packets" / "NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
SNAPSHOT_DIR = CONTROL / "snapshots"

MASTER_PATH = (
    "REOS_CONTROL_CENTER/architecture/backend/plans/"
    "HOMIO_Backend_Structure"
)
STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
AUDIT_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B2-security-integration-readiness-audit.md"
)
EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B2-dependency-correction-ci-evidence.md"
)

BASELINE_HEAD = "13a056fdd5fd239e4c5aa25d23dc60414baffb2b"
BASELINE_STATE_BLOB_SHA = (
    "dd9c4684698270adf19a9380256c94396608a27a"
)
BASELINE_MASTER_BLOB_SHA = (
    "27b43931d1b6db48065ec41fd3574bd2dbc5ae3c"
)

OWNER = "prajaktaranjane80-sketch"
REPOSITORY = "prajaktaranjane80-sketch/Homio"
BRANCH = "reos-development"
BRANCH_REF = f"refs/heads/{BRANCH}"

APPROVAL_PREFIX = (
    "[CONTROL-CENTER-CORRECT-BACKEND-001-B2-DEPENDENCIES]"
)
OIDC_AUDIENCE = (
    "homio-control-center-backend-b2-dependency-correction"
)
OIDC_JWKS_URL = (
    "https://token.actions.githubusercontent.com/.well-known/jwks"
)

EXPECTED_MASTER_SEQUENCE = (
    "B0 → B1 → B2-FOUNDATION → B3 → B4 → "
    "B2-PRODUCTION-BINDING → B5 → B6 → B7 → B8 → B9 → B10"
)

# This is an exact, reviewed source inventory from BASELINE_HEAD through the
# B2 dependency-correction candidate. The T17 preflight test independently
# compares this set with `git diff BASELINE_HEAD HEAD` before the owner
# transition can execute.
EXPECTED_SOURCE_PATHS = {
    MASTER_PATH,
    "REOS_CONTROL_CENTER/context/backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/test_backend_workstream_transition.py",
    (
        ".github/actions/homio-backend-ci/verification/tests/"
        "test_backend_b1_completion_transition.py"
    ),
    (
        ".github/actions/homio-backend-ci/verification/tests/"
        "test_pull_request_governance.py"
    ),
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    (
        ".github/actions/homio-backend-ci/transitions/"
        "backend-b2-dependency-correction/action.yml"
    ),
    (
        ".github/actions/homio-backend-ci/transitions/"
        "backend-b2-dependency-correction/scripts/guarded_transition.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/impact_models.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py"
    ),
    "REOS_CONTROL_CENTER/backend/src/security/api-security.ts",
    "REOS_CONTROL_CENTER/backend/tests/unit/api-security.test.ts",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/security/"
        "authentication/oidc_verifier.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/security/"
        "authentication/test_oidc_verifier.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/authorization_validation.py"
    ),
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/test_authenticated_approval_binding.py"
    ),
}

for import_root in (ROOT, CONTROL):
    value = str(import_root)
    if value in sys.path:
        sys.path.remove(value)
    sys.path.insert(0, value)

os.chdir(ROOT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True


from REOS_CONTROL_CENTER import reos_control_center as controller  # noqa: E402

from REOS_CONTROL_CENTER.context.backend_workstream_transition import (  # noqa: E402
    BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID,
    BACKEND_GATE_ID,
    BACKEND_STAGES,
    BACKEND_TECHNICAL_SEQUENCE,
    B2_FOUNDATION_ACCEPTANCE_CRITERIA,
    B3_ACCEPTANCE_CRITERIA,
    correct_backend_b2_dependency_state,
)

from REOS_CONTROL_CENTER.context.github_actions_identity import (  # noqa: E402
    BRANCH,
    BRANCH_REF,
    EXPECTED_OIDC_SUBJECT,
    OIDC_ISSUER,
    OWNER,
    OWNER_ID,
    REPOSITORY,
    REPOSITORY_ID,
    GitHubActionsIdentityError,
    validate_github_actions_identity_claims,
)

from REOS_CONTROL_CENTER.context.phase_projection import (  # noqa: E402
    is_phase_coherent,
)

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

from AUTONOMY_ENGINE.security.authentication.oidc_config import (  # noqa: E402
    OIDCSettings,
)
from AUTONOMY_ENGINE.security.authentication.oidc_verifier import (  # noqa: E402
    AuthenticatedIdentityPrincipal,
    AuthenticationError,
    OIDCVerifier,
)


def fail(message: str) -> None:
    raise SystemExit(
        f"BACKEND-001-B2 DEPENDENCY CORRECTION BLOCKED: {message}"
    )


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

    output = (
        completed.stdout or ""
        if capture
        else ""
    )

    if output and display:
        print(
            output,
            end="" if output.endswith("\n") else "\n",
        )

    if completed.returncode != 0:
        fail(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def file_blob_sha(
    path: str,
    ref: str = "HEAD",
) -> str:
    return run(
        ["git", "rev-parse", f"{ref}:{path}"],
        display=False,
    )


def assert_exact_branch(expected_sha: str) -> None:
    actual = run(["git", "rev-parse", "HEAD"])

    if actual != expected_sha:
        fail("checked-out HEAD differs from the triggering source commit")

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            BRANCH_REF,
        ],
        capture=False,
    )

    remote_sha = run(
        ["git", "rev-parse", "FETCH_HEAD"],
        display=False,
    )

    if remote_sha != expected_sha:
        fail(
            "canonical branch moved; refusing a stale transition"
        )


def verify_owner_push(expected_sha: str) -> dict:
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
    )

    missing = [
        name
        for name in required_env
        if not os.environ.get(name)
    ]

    if missing:
        fail(f"required GitHub environment is missing: {missing}")

    if os.environ["GITHUB_ACTOR"] != OWNER:
        fail("only the repository owner may authorize this transition")

    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("B2 dependency correction requires an owner push")

    if os.environ["GITHUB_REF"] != BRANCH_REF:
        fail("transition is restricted to reos-development")

    if os.environ["GITHUB_REPOSITORY"] != REPOSITORY:
        fail("unexpected GitHub repository identity")

    if os.environ["ACTIONS_REPOSITORY"] != REPOSITORY:
        fail("unexpected Actions repository identity")

    if os.environ["EXPECTED_SHA"] != expected_sha:
        fail("EXPECTED_SHA differs from the triggering source commit")

    if os.environ["VERIFIED_CODE_SHA"] != expected_sha:
        fail("verification SHA differs from the triggering source commit")

    event_path = Path(os.environ["GITHUB_EVENT_PATH"])

    if not event_path.is_file():
        fail("GitHub push event payload is missing")

    try:
        event = json.loads(
            event_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("GitHub push event payload is invalid")

    if event.get("ref") != BRANCH_REF:
        fail("push event ref differs from the canonical branch")

    if event.get("after") != expected_sha:
        fail("push event SHA differs from the workflow SHA")

    repository = event.get("repository", {})

    if repository.get("full_name") != REPOSITORY:
        fail("push event belongs to a different repository")

    sender = event.get("sender", {})

    if sender.get("login") != OWNER:
        fail("push event sender is not the repository owner")

    head_commit = event.get("head_commit")

    if not isinstance(head_commit, dict):
        fail("push event does not contain a head commit")

    message = head_commit.get("message", "")

    if (
        not isinstance(message, str)
        or not message.startswith(APPROVAL_PREFIX)
    ):
        fail("owner commit lacks the exact B2 dependency approval prefix")

    return event


def verify_source_baseline(expected_sha: str) -> list[str]:
    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            BRANCH_REF,
        ],
        capture=False,
    )

    if run(["git", "rev-parse", "FETCH_HEAD"]) != expected_sha:
        fail("remote branch moved before dependency correction")

    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            BASELINE_HEAD,
            expected_sha,
        ],
        cwd=ROOT,
        check=False,
    )

    if ancestor.returncode != 0:
        fail("the exact audited baseline is not an ancestor of this change")

    if run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ]
    ):
        fail("source checkout is not clean before the transition")

    if file_blob_sha(STATE_PATH, BASELINE_HEAD) != (
        BASELINE_STATE_BLOB_SHA
    ):
        fail("audited baseline state blob differs from the pinned SHA")

    if file_blob_sha(MASTER_PATH, BASELINE_HEAD) != (
        BASELINE_MASTER_BLOB_SHA
    ):
        fail("audited baseline backend master differs from the pinned SHA")

    if file_blob_sha(STATE_PATH, expected_sha) != (
        BASELINE_STATE_BLOB_SHA
    ):
        fail("owner source changes must not modify canonical state.json")

    changed_paths = run(
        [
            "git",
            "diff",
            "--name-only",
            BASELINE_HEAD,
            expected_sha,
        ]
    ).splitlines()

    actual_paths = set(changed_paths)

    if actual_paths != EXPECTED_SOURCE_PATHS:
        missing = sorted(EXPECTED_SOURCE_PATHS - actual_paths)
        unexpected = sorted(actual_paths - EXPECTED_SOURCE_PATHS)

        fail(
            "B2 dependency correction source-path allowlist mismatch; "
            f"missing={missing}; unexpected={unexpected}"
        )

    return sorted(actual_paths)


def verify_master_dependency_contract(expected_sha: str) -> str:
    content = run(
        [
            "git",
            "show",
            f"{expected_sha}:{MASTER_PATH}",
        ],
        display=False,
    )

    required_markers = (
        "### B2-FOUNDATION — API security and trusted context foundation",
        "### B3 — Python domain-runtime bridge",
        "### B4 — PostgreSQL integration",
        (
            "### B2-PRODUCTION-BINDING — API security and trusted "
            "context production binding"
        ),
    )

    for marker in required_markers:
        if marker not in content:
            fail(
                "corrected backend master is missing required section: "
                f"{marker}"
            )

    try:
        dependency_section = content.split(
            "## 21.6 Stage dependencies",
            1,
        )[1].split(
            "## 21.7",
            1,
        )[0]
    except IndexError:
        fail("backend master dependency section boundaries are invalid")

    if EXPECTED_MASTER_SEQUENCE not in dependency_section:
        fail("backend master does not contain the exact corrected sequence")

    current_master_blob_sha = file_blob_sha(
        MASTER_PATH,
        expected_sha,
    )

    return current_master_blob_sha


def verify_owner_approval_context(expected_sha: str) -> None:
    content = run(
        [
            "git",
            "show",
            f"{expected_sha}:{AUDIT_PATH}",
        ],
        display=False,
    )

    required = (
        "APPROVE B2 DEPENDENCY CORRECTION",
        "T15 must produce a bounded proposal.",
        "T17 must analyze the actual changed repository paths",
        "T18 must authorize the exact scope",
        "Manual `state.json` editing is prohibited.",
    )

    for marker in required:
        if marker not in content:
            fail(
                "existing B2 owner-approval audit lacks required scope: "
                f"{marker}"
            )


def request_github_oidc_token() -> str:
    request_url = os.environ.get(
        "ACTIONS_ID_TOKEN_REQUEST_URL",
        "",
    )
    request_token = os.environ.get(
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
        "",
    )

    if not request_url or not request_token:
        fail(
            "GitHub OIDC token request is unavailable; "
            "check id-token: write permission"
        )

    parts = urlsplit(request_url)
    query = dict(
        parse_qsl(parts.query, keep_blank_values=True)
    )
    query["audience"] = OIDC_AUDIENCE

    url = urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
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
            payload = json.loads(
                response.read().decode("utf-8")
            )
    except Exception:
        fail("GitHub OIDC token request failed")

    token = payload.get("value")

    if not isinstance(token, str) or not token:
        fail("GitHub OIDC endpoint returned no identity token")

    return token


class GitHubActionsPrincipalVerifier:
    """Verify GitHub Actions OIDC workload identity for T18 approval.

    The Actions identity JWT is a workload identity, not an RFC 9068 API
    access token. Signature, issuer, audience, expiry and JWT profile are
    checked by the existing OIDCVerifier identity-token method. Immutable
    repository, owner, actor, ref, event and exact-SHA claims are then
    checked by the existing HOMIO GitHub identity contract.
    """

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

    def verify_identity_token(
        self,
        token: str,
    ) -> dict[str, object]:
        try:
            claims = self.verifier.verify_identity_token(token)
        except AuthenticationError:
            raise

        try:
            validate_github_actions_identity_claims(
                claims,
                expected_sha=self.expected_sha,
            )
        except GitHubActionsIdentityError as exc:
            raise AuthenticationError(
                "invalid_github_actions_identity"
            ) from exc

        issuer = claims.get("iss")
        subject = claims.get("sub")
        actor_id = claims.get("actor_id")

        if issuer != OIDC_ISSUER:
            raise AuthenticationError("unexpected_identity_issuer")

        if subject != EXPECTED_OIDC_SUBJECT:
            raise AuthenticationError("unexpected_identity_subject")

        if actor_id != OWNER_ID:
            raise AuthenticationError("unexpected_identity_actor")

        raw_audience = claims.get("aud")

        if isinstance(raw_audience, str):
            audiences = (raw_audience,)
        elif (
            isinstance(raw_audience, list)
            and raw_audience
            and all(
                isinstance(item, str)
                and item.strip() == item
                for item in raw_audience
            )
        ):
            audiences = tuple(raw_audience)
        else:
            raise AuthenticationError("invalid_identity_audience")

        if OIDC_AUDIENCE not in audiences:
            raise AuthenticationError("unexpected_identity_audience")

        self.claims = claims
        return claims

    def verify_access_token(
        self,
        token: str,
    ) -> AuthenticatedIdentityPrincipal:
        # T18's established verifier protocol consumes a verified principal.
        # This adapter returns a distinct workload-identity type, never an
        # API access principal or fabricated OAuth client_id/jti.
        claims = self.verify_identity_token(token)

        issuer = claims.get("iss")
        subject = claims.get("sub")
        raw_audience = claims.get("aud")

        if not isinstance(issuer, str) or not isinstance(subject, str):
            raise AuthenticationError("invalid_verified_identity")

        if isinstance(raw_audience, str):
            audiences = (raw_audience,)
        elif (
            isinstance(raw_audience, list)
            and raw_audience
            and all(
                isinstance(item, str)
                and item.strip() == item
                for item in raw_audience
            )
        ):
            audiences = tuple(raw_audience)
        else:
            raise AuthenticationError("invalid_verified_identity_audience")

        return AuthenticatedIdentityPrincipal(
            issuer=issuer,
            subject=subject,
            audiences=audiences,
        )


def authorize_dependency_correction(
    *,
    expected_sha: str,
    state: dict,
    changed_paths: list[str],
    owner_event: dict,
    master_blob_sha: str,
) -> tuple[dict, dict, dict, dict]:
    token = request_github_oidc_token()

    principal_verifier = GitHubActionsPrincipalVerifier(
        expected_sha
    )
    try:
        principal_verifier.verify_identity_token(token)
    except AuthenticationError as exc:
        fail(
            "GitHub Actions OIDC identity verification failed: "
            f"{exc.code}"
        )

    claims = principal_verifier.claims

    context = OperatorContext(
        gate="BACKEND-001",
        subtask="BACKEND-001-B2",
        task=(
            "Apply the owner-approved B2 dependency correction, "
            "separate the existing Fastify security foundation from "
            "production adapter binding, and preserve the single "
            "Control Center authority."
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
            "baseline_master_blob_sha": BASELINE_MASTER_BLOB_SHA,
            "corrected_master_blob_sha": master_blob_sha,
            "owner_source_commit": expected_sha,
            "owner_id": OWNER_ID,
            "repository_id": REPOSITORY_ID,
            "oidc_subject": EXPECTED_OIDC_SUBJECT,
            "current_subtask": "BACKEND-001-B2",
            "corrected_sequence": BACKEND_TECHNICAL_SEQUENCE,
        },
    )

    operator_request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.PROPOSE_CHANGE,
        objective=(
            "Re-sequence the existing B2 security foundation and "
            "production binding around the B3 authenticated bridge "
            "and B4 durable persistence dependencies. Preserve the "
            "single Fastify ingress, existing OIDC verifier, CORE-001 "
            "ownership, fail-closed behavior and all pending backend "
            "gate-level acceptance criteria."
        ),
        evidence=(
            f"baseline_head={BASELINE_HEAD}",
            f"state_blob_sha={BASELINE_STATE_BLOB_SHA}",
            f"baseline_master_blob_sha={BASELINE_MASTER_BLOB_SHA}",
            f"corrected_master_blob_sha={master_blob_sha}",
            f"owner_source_commit={expected_sha}",
            f"owner_id={OWNER_ID}",
            f"repository_id={REPOSITORY_ID}",
            f"oidc_subject={EXPECTED_OIDC_SUBJECT}",
            f"changed_path_count={len(changed_paths)}",
        ),
        metadata={
            "workstream": "BACKEND",
            "gate": "BACKEND-001",
            "previous_subtask": "BACKEND-001-B2",
            "foundation_subtask": "BACKEND-001-B2-FOUNDATION",
            "production_binding_subtask": (
                "BACKEND-001-B2-PRODUCTION-BINDING"
            ),
            "production_binding_after": ("B3", "B4"),
        },
    )

    operator_report = OperatorAutonomyEngine.operate(
        operator_request
    )

    if operator_report.decision.value != "PROPOSE":
        fail(
            "T15 did not produce a PROPOSE decision: "
            f"{operator_report.decision.value}"
        )

    analyzer = ChangeImpactAnalyzer(ROOT)
    impact_report = analyzer.analyze(changed_paths)
    analyzer.validate_report(impact_report)

    if not impact_report.ready_for_handoff:
        fail("T17 report is not ready for authorization handoff")

    if impact_report.unknown_paths or impact_report.protected_paths:
        fail(
            "T17 found unknown or protected impacts: "
            f"unknown={list(impact_report.unknown_paths)}, "
            f"protected={list(impact_report.protected_paths)}"
        )

    nonce = (
        f"{os.environ['ACTIONS_RUN_ID']}:"
        f"{os.environ['ACTIONS_RUN_ATTEMPT']}:"
        f"{expected_sha}"
    )

    base_request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=None,
        nonce=nonce,
    )

    approval_evidence = (
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
        f"Corrected master blob SHA: {master_blob_sha}",
    )

    approval = HumanApproval(
        approval_id=f"GH-OWNER-PUSH:{expected_sha}",
        authority="GITHUB_REPOSITORY_OWNER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(
            base_request
        ),
        evidence=approval_evidence,
        principal_issuer=str(claims["iss"]),
        principal_subject=str(claims["sub"]),
        authentication_token=token,
    )

    authorization_request = AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce=nonce,
    )

    policy = SafeAuthorizationPolicy(
        maximum_risk=OperatorRisk.MEDIUM,
        trusted_approver_principals=(
            (OIDC_ISSUER, EXPECTED_OIDC_SUBJECT),
        ),
    )

    authorization = ExecutionAuthorizationGuard(
        policy,
        principal_verifier=principal_verifier,
    ).authorize(authorization_request)

    if (
        authorization.decision.value != "AUTHORIZE"
        or authorization.execution_authorized is not True
        or authorization.state_mutated is not False
        or authorization.requires_external_executor is not True
    ):
        fail(
            "T18 did not authorize the external Control Center transition: "
            f"{authorization.decision.value}/"
            f"{authorization.reason.value}"
        )

    # Persist only safe verified identity metadata. Never persist the token.
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

    return (
        operator_report.to_dict(),
        impact_report.to_dict(),
        authorization.to_dict(),
        approval_record,
    )


def verify_current_state(state: dict) -> None:
    if state.get("integrity", {}).get("sha256") != (
        controller.calculate_hash(state)
    ):
        fail("canonical state integrity hash is invalid")

    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get("BACKEND-001", {})

    if execution.get("current_gate") != "BACKEND-001":
        fail("canonical current gate is not BACKEND-001")

    if execution.get("current_subtask") != "BACKEND-001-B2":
        fail("canonical current subtask is not original B2")

    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("canonical execution mode is not CONTROL_CENTER_DRIVEN")

    if gate.get("status") != "CURRENT":
        fail("BACKEND-001 gate is not CURRENT")

    if gate.get("current_subtask") != "BACKEND-001-B2":
        fail("backend gate current subtask differs from original B2")


def validate_transition_state(
    state: dict,
    *,
    expected_sha: str,
    run_id: str,
) -> None:
    if state.get("integrity", {}).get("sha256") != (
        controller.calculate_hash(state)
    ):
        fail("post-transition canonical state integrity is invalid")

    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get("BACKEND-001", {})

    if execution.get("current_gate") != "BACKEND-001":
        fail("Control Center did not preserve BACKEND-001 as current")

    if execution.get("current_subtask") != "BACKEND-001-B3":
        fail("Control Center did not advance execution to B3")

    if gate.get("status") != "CURRENT":
        fail("BACKEND-001 gate is not CURRENT after transition")

    if gate.get("current_subtask") != "BACKEND-001-B3":
        fail("Backend gate current_subtask is not B3")

    if gate.get("technical_sequence") != BACKEND_TECHNICAL_SEQUENCE:
        fail("Corrected technical sequence was not persisted")

    raw_subtasks = gate.get("subtasks", [])

    actual_order = [
        item.get("id")
        for item in raw_subtasks
        if isinstance(item, dict)
    ]

    expected_order = [
        f"BACKEND-001-{stage_id}"
        for stage_id, _, _ in BACKEND_STAGES
    ]

    if actual_order != expected_order:
        fail("Post-transition backend stage order is invalid")

    subtasks = {
        item["id"]: item
        for item in raw_subtasks
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    expected_statuses = {
        "BACKEND-001-B0": "DONE",
        "BACKEND-001-B1": "DONE",
        "BACKEND-001-B2-FOUNDATION": "DONE",
        "BACKEND-001-B3": "CURRENT",
        "BACKEND-001-B4": "PENDING",
        "BACKEND-001-B2-PRODUCTION-BINDING": "PENDING",
        **{
            f"BACKEND-001-B{number}": "PENDING"
            for number in range(5, 11)
        },
    }

    if set(subtasks) != set(expected_statuses):
        fail("Post-transition backend subtask identifiers are invalid")

    for subtask_id, expected_status in expected_statuses.items():
        if subtasks[subtask_id].get("status") != expected_status:
            fail(
                f"{subtask_id} must be {expected_status}; "
                f"found {subtasks[subtask_id].get('status')!r}"
            )

    if "BACKEND-001-B2" in subtasks:
        fail("Legacy ambiguous B2 subtask was not removed")

    foundation_note = subtasks[
        "BACKEND-001-B2-FOUNDATION"
    ].get("note", "")

    if (
        not isinstance(foundation_note, str)
        or expected_sha not in foundation_note
        or run_id not in foundation_note
    ):
        fail("B2 foundation completion note lacks exact-SHA evidence")

    if (
        execution.get("current_acceptance_criteria")
        != B3_ACCEPTANCE_CRITERIA
    ):
        fail("B3 acceptance criteria were not projected by the Control Center")

    criteria_state = gate.get("criteria_state", [])

    if any(
        item.get("status") != "PENDING"
        for item in criteria_state
        if isinstance(item, dict)
    ):
        fail(
            "Backend gate-level acceptance criteria must remain PENDING"
        )

    request = next(
        (
            item
            for item in state.get("change_requests", [])
            if isinstance(item, dict)
            and item.get("id")
            == BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID
        ),
        None,
    )

    if not isinstance(request, dict):
        fail("Approved B2 dependency correction request is missing")

    if request.get("status") != "APPROVED":
        fail("B2 dependency correction request is not APPROVED")

    if (
        request.get("execution_authorization", {}).get("decision")
        != "AUTHORIZE"
    ):
        fail("B2 dependency correction lacks T18 authorization evidence")

    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("Control Center handoff path is not repository-relative")

    if not is_phase_coherent(state):
        fail("Canonical Control Center phase projection is not coherent")


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()

    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
    )

    if (
        original.count(b"\n") > 0
        and original.count(b"\n") == original.count(b"\r\n")
    ):
        normalized = path.read_bytes().replace(
            b"\r\n",
            b"\n",
        )

        path.write_bytes(
            normalized.replace(b"\n", b"\r\n")
        )


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
        "RUNNER_TEMP",
    )

    missing = [
        name
        for name in required_env
        if not os.environ.get(name)
    ]

    if missing:
        fail(f"required GitHub environment values are missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]

    if os.environ["VERIFIED_CODE_SHA"] != expected_sha:
        fail("exact source verification SHA mismatch")

    owner_event = verify_owner_push(expected_sha)

    assert_exact_branch(expected_sha)

    changed_paths = verify_source_baseline(expected_sha)

    master_blob_sha = verify_master_dependency_contract(
        expected_sha
    )

    verify_owner_approval_context(expected_sha)

    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )

    state = controller.load_state()
    verify_current_state(state)

    (
        operator_report,
        impact_report,
        authorization,
        approval_record,
    ) = authorize_dependency_correction(
        expected_sha=expected_sha,
        state=state,
        changed_paths=changed_paths,
        owner_event=owner_event,
        master_blob_sha=master_blob_sha,
    )

    timestamp = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    corrected_state = correct_backend_b2_dependency_state(
        state,
        timestamp=timestamp,
        baseline_sha=BASELINE_HEAD,
        master_blob_sha=master_blob_sha,
        approval_record=approval_record,
        t15_report=operator_report,
        t17_report=impact_report,
        authorization=authorization,
    )

    controller.emit(
        corrected_state,
        "BACKEND_B2_DEPENDENCIES_CORRECTED",
        {
            "change_request": (
                BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID
            ),
            "source_commit": expected_sha,
            "t15_request_fingerprint": (
                operator_report["request_fingerprint"]
            ),
            "t17_fingerprint": impact_report["fingerprint"],
            "t18_authorization_fingerprint": (
                authorization["authorization_fingerprint"]
            ),
            "production_binding_after": ["B3", "B4"],
        },
    )

    # The existing Control Center owns persistence and handoff generation.
    controller.PACKETS = Path(
        "REOS_CONTROL_CENTER/packets"
    )

    note = (
        "BACKEND-001-B2-FOUNDATION completed through the guarded "
        "Control Center after the exact-SHA backend and ACRL verification "
        f"job passed for source commit {expected_sha}; "
        f"GitHub Actions run {os.environ['ACTIONS_RUN_ID']}, "
        f"attempt {os.environ['ACTIONS_RUN_ATTEMPT']}. "
        "The verified scope includes the single Fastify security boundary, "
        "trusted-context contracts, fail-closed adapter requirements, "
        "mutation reauthorization and the existing security-boundary "
        "regression suite. This completes B2-FOUNDATION only. "
        "The six real production adapters are not claimed complete. "
        "B3 is now CURRENT; B4 and B2-PRODUCTION-BINDING remain PENDING. "
        "Backend gate-level AC01 through AC10 remain PENDING."
    )

    controller.cmd_complete_subtask(
        corrected_state,
        "BACKEND-001-B2-FOUNDATION",
        note,
    )

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )

    transitioned_state = controller.load_state()

    validate_transition_state(
        transitioned_state,
        expected_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
    )

    expected_packet_markers = (
        "CURRENT_SUBTASK=BACKEND-001-B3",
        (
            "BACKEND-001-B2-FOUNDATION|DONE|"
            "API security and trusted context — foundation"
        ),
        "BACKEND-001-B3|CURRENT|Python domain-runtime bridge",
        "BACKEND-001-B4|PENDING|PostgreSQL integration",
        (
            "BACKEND-001-B2-PRODUCTION-BINDING|PENDING|"
            "API security and trusted context — production binding"
        ),
    )

    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")

        for marker in expected_packet_markers:
            if marker not in content:
                fail(
                    f"{path.name} is missing expected marker {marker!r}"
                )

    if (ROOT / EVIDENCE_PATH).exists():
        fail("B2 dependency correction evidence file already exists")

    state_blob_sha = run(
        [
            "git",
            "hash-object",
            str(STATE),
        ],
        display=False,
    )

    run_id = os.environ["ACTIONS_RUN_ID"]
    run_attempt = os.environ["ACTIONS_RUN_ATTEMPT"]
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{REPOSITORY}/actions/runs/{run_id}"
    )

    evidence_lines = [
        "# BACKEND-001 — B2 dependency correction evidence",
        "",
        f"- Repository: `{REPOSITORY}`",
        f"- Branch: `{BRANCH}`",
        f"- Source commit SHA: `{expected_sha}`",
        f"- Actions run: [{run_id}]({run_url})",
        f"- Actions attempt: `{run_attempt}`",
        "- Backend/ACRL verification dependency job: **PASS**",
        "- Canonical state mutation: existing Control Center only",
        "- Manual state.json editing: **NOT PERFORMED**",
        "",
        "## Guarded authorization evidence",
        "",
        "- T15 decision: `PROPOSE`",
        (
            "- T15 request fingerprint: "
            f"`{operator_report['request_fingerprint']}`"
        ),
        "- T17 decision: `ANALYZE`",
        f"- T17 fingerprint: `{impact_report['fingerprint']}`",
        f"- T17 changed paths: `{len(impact_report['changed_paths'])}`",
        "- T17 unknown paths: `0`",
        "- T17 protected paths: `0`",
        "- T18 decision: `AUTHORIZE`",
        (
            "- T18 authorization fingerprint: "
            f"`{authorization['authorization_fingerprint']}`"
        ),
        f"- OIDC issuer: `{approval_record['oidc_issuer']}`",
        f"- OIDC subject: `{approval_record['oidc_subject']}`",
        "- Owner identity: cryptographically verified",
        "- OIDC bearer token persisted: **NO**",
        "",
        "## Canonical Control Center result",
        "",
        "- BACKEND-001-B0: `DONE`",
        "- BACKEND-001-B1: `DONE`",
        "- BACKEND-001-B2-FOUNDATION: `DONE`",
        "- BACKEND-001-B3: `CURRENT`",
        "- BACKEND-001-B4: `PENDING`",
        "- BACKEND-001-B2-PRODUCTION-BINDING: `PENDING`",
        "- BACKEND-001-B5 through B10: `PENDING`",
        "- BACKEND-001-AC01 through AC10: `PENDING`",
        "",
        "## State and production boundary",
        "",
        f"- Post-transition state blob SHA: `{state_blob_sha}`",
        f"- Corrected master blob SHA: `{master_blob_sha}`",
        f"- Technical sequence: `{BACKEND_TECHNICAL_SEQUENCE}`",
        "- Six production adapters: **NOT CLAIMED COMPLETE**",
        "- Customer protected routes enabled by this transition: **NO**",
        "- Production readiness: **NOT CLAIMED**",
        "",
    ]

    evidence_path = ROOT / EVIDENCE_PATH
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        "\n".join(evidence_lines),
        encoding="utf-8",
        newline="\n",
    )

    expected_tracked = {
        STATE_PATH,
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }

    actual_tracked = set(
        run(
            ["git", "diff", "--name-only"],
            display=False,
        ).splitlines()
    )

    if actual_tracked != expected_tracked:
        fail(
            "Control Center tracked-path allowlist mismatch: "
            f"{sorted(actual_tracked)}"
        )

    run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "diff",
            "--check",
        ]
    )

    untracked = sorted(
        run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
            ],
            display=False,
        ).splitlines()
    )

    if len(untracked) != 2:
        fail(
            "Expected exactly one state snapshot and one B2 evidence file; "
            f"found {untracked}"
        )

    snapshot_candidates = [
        item
        for item in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/"
            r"state_\d{8}_\d{6}_\d{6}\.json",
            item,
        )
    ]

    evidence_relative = (
        Path(EVIDENCE_PATH).as_posix()
    )

    if len(snapshot_candidates) != 1:
        fail("Control Center snapshot inventory is invalid")

    if evidence_relative not in untracked:
        fail("B2 dependency evidence was not generated")

    snapshot_relative = snapshot_candidates[0]
    snapshot = ROOT / snapshot_relative

    snapshot_data = json.loads(
        snapshot.read_text(encoding="utf-8")
    )

    if (
        snapshot_data.get("integrity", {}).get("sha256")
        != controller.calculate_hash(snapshot_data)
    ):
        fail("Control Center snapshot integrity is invalid")

    staged_paths = sorted(
        expected_tracked
        | {
            evidence_relative,
            snapshot_relative,
        }
    )

    run(
        ["git", "add", "--", *staged_paths]
    )

    run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "diff",
            "--cached",
            "--check",
        ]
    )

    actual_staged = set(
        run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only",
            ],
            display=False,
        ).splitlines()
    )

    if actual_staged != set(staged_paths):
        fail("staged Control Center transition path allowlist mismatch")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            (
                "chore(control-center): correct B2 dependencies "
                "and close verified foundation"
            ),
        ],
        capture=False,
    )

    transition_sha = run(
        ["git", "rev-parse", "HEAD"],
        display=False,
    )

    if run(["git", "rev-parse", "HEAD^"], display=False) != expected_sha:
        fail("transition commit parent differs from verified source SHA")

    run(
        [
            "git",
            "push",
            "origin",
            f"HEAD:refs/heads/{BRANCH}",
        ],
        capture=False,
    )

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            BRANCH_REF,
        ],
        capture=False,
    )

    remote_sha = run(
        ["git", "rev-parse", "FETCH_HEAD"],
        display=False,
    )

    if remote_sha != transition_sha:
        fail("canonical branch readback differs from transition commit")

    readback_raw = subprocess.check_output(
        [
            "git",
            "show",
            f"{remote_sha}:{STATE_PATH}",
        ],
        cwd=ROOT,
    )

    readback_state = json.loads(
        readback_raw.decode("utf-8")
    )

    validate_transition_state(
        readback_state,
        expected_sha=expected_sha,
        run_id=run_id,
    )

    remote_state_blob_sha = run(
        [
            "git",
            "rev-parse",
            f"{remote_sha}:{STATE_PATH}",
        ],
        display=False,
    )

    if remote_state_blob_sha != state_blob_sha:
        fail("remote state blob SHA differs from the generated state")

    remote_evidence = run(
        [
            "git",
            "show",
            f"{remote_sha}:{EVIDENCE_PATH}",
        ],
        display=False,
    )

    for marker in (
        expected_sha,
        run_id,
        operator_report["request_fingerprint"],
        impact_report["fingerprint"],
        authorization["authorization_fingerprint"],
        state_blob_sha,
        "BACKEND-001-B2-FOUNDATION: `DONE`",
        "BACKEND-001-B3: `CURRENT`",
        "B2-PRODUCTION-BINDING: `PENDING`",
    ):
        if marker not in remote_evidence:
            fail(
                "Remote B2 dependency evidence is missing marker: "
                f"{marker}"
            )

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        remote_content = run(
            [
                "git",
                "show",
                f"{remote_sha}:{relative}",
            ],
            display=False,
        )

        for marker in expected_packet_markers:
            if marker not in remote_content:
                fail(
                    f"Remote {relative} is missing {marker!r}"
                )

    print(f"B2_SOURCE_COMMIT={expected_sha}")
    print(f"B2_ACTIONS_RUN_ID={run_id}")
    print(f"B2_ACTIONS_ATTEMPT={run_attempt}")
    print(f"B2_TRANSITION_COMMIT={transition_sha}")
    print(f"B2_CANONICAL_BRANCH_HEAD={remote_sha}")
    print(f"B2_POST_TRANSITION_STATE_BLOB_SHA={remote_state_blob_sha}")
    print("B2_T15_T17_T18_AUTHORIZATION=PASS")
    print("B2_FOUNDATION_CONTROL_CENTER_TRANSITION=PASS")
    print("B2_FOUNDATION_CANONICAL_READBACK=PASS")
    print("B2_PRODUCTION_BINDING=REMAINS_PENDING")
    print("BACKEND-001-B3=CURRENT")


if __name__ == "__main__":
    main()
