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
STATE_PATH = CONTROL / "data" / "state.json"
PACKET_PATH = CONTROL / "packets" / "NEW_CHAT_PACKET.txt"
HANDOFF_PATH = CONTROL / "REOS_NEXT_CHAT.txt"
SNAPSHOT_DIR = CONTROL / "snapshots"

BASELINE_HEAD = "a82dc7af949e1eaed4468b4c6ff6ca4f220a0f30"
STATE_BLOB_SHA = "6242f63371a725ea99447c218bbbeb46a0c5eddd"
BACKEND_MASTER_BLOB_SHA = "27b43931d1b6db48065ec41fd3574bd2dbc5ae3c"
WORK_PLAN_BLOB_SHA = "e69b5107d21e54ed4920178bd6ec62c95e773bb5"
ARCH039_SNAPSHOT_PATH = (
    "REOS_CONTROL_CENTER/snapshots/"
    "state_before_arch039_transition_repair.json"
)
ARCH039_SNAPSHOT_BLOB_SHA = "9a086a6d7e5caff45468ed4aa4ecbd8f2ffd3f8c"

REPOSITORY = "prajaktaranjane80-sketch/Homio"
OWNER = "prajaktaranjane80-sketch"
BRANCH = "reos-development"
BRANCH_REF = f"refs/heads/{BRANCH}"
APPROVAL_PREFIX = "[CONTROL-CENTER-ACTIVATE-BACKEND-001]"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_AUDIENCE = "homio-control-center-backend-activation"
OIDC_JWKS_URL = (
    "https://token.actions.githubusercontent.com/.well-known/jwks"
)
EXPECTED_OIDC_SUBJECT = (
    f"repo:{REPOSITORY}:ref:{BRANCH_REF}"
)

B0_EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B0-live-repository-audit.md"
)
ACTIVATION_EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "workstream-activation-ci-evidence.md"
)

EXPECTED_ACTIVATION_PATHS = {
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/action.yml",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream.py",
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    "REOS_CONTROL_CENTER/context/phase_projection.py",
    "REOS_CONTROL_CENTER/context/test_phase_projection.py",
    "REOS_CONTROL_CENTER/context/backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/test_backend_workstream_transition.py",
    B0_EVIDENCE_PATH,
    ".github/actions/homio-backend-ci/verification/scripts/"
    "financial_context_tenant.sh",
    ".github/actions/homio-backend-ci/verification/scripts/"
    "wiring_tests.sh",
    "REOS_CONTROL_CENTER/context/test_backend_activation_import_bootstrap.py",
}
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from REOS_CONTROL_CENTER import reos_control_center as controller  # noqa: E402

from REOS_CONTROL_CENTER.context.backend_workstream_transition import (  # noqa: E402
    activate_backend_workstream_state,
)
from REOS_CONTROL_CENTER.context.phase_projection import (  # noqa: E402
    is_phase_coherent,
)

from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_autonomy import (  # noqa: E402
    OperatorAutonomyEngine,
    OperatorRequest,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_policy import (  # noqa: E402
    OperatorActionType,
    OperatorRisk,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T15_AI_Operator_Autonomy.operator_validation import (  # noqa: E402
    OperatorContext,
)

from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T17_Change_Impact_Dependency_Analysis.change_impact_analysis import (  # noqa: E402
    ChangeImpactAnalyzer,
)

from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_identity import (  # noqa: E402
    approval_scope_fingerprint,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (  # noqa: E402
    AuthorizationRequest,
    HumanApproval,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_policy import (  # noqa: E402
    SafeAuthorizationPolicy,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.execution_authorization import (  # noqa: E402
    ExecutionAuthorizationGuard,
)

from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.security.authentication.oidc_config import (  # noqa: E402
    OIDCSettings,
)
from REOS_CONTROL_CENTER.AUTONOMY_ENGINE.security.authentication.oidc_verifier import (  # noqa: E402
    AuthenticatedPrincipal,
    OIDCVerifier,
)

import jwt  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"BACKEND-001 ACTIVATION BLOCKED: {message}")


def run(
    command: list[str],
    *,
    capture: bool = True,
    check: bool = True,
) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    output = result.stdout or "" if capture else ""

    if output:
        print(output, end="" if output.endswith("\n") else "\n")

    if check and result.returncode != 0:
        fail(
            f"command failed ({result.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def file_blob_sha(path: str, ref: str = "HEAD") -> str:
    return run(["git", "rev-parse", f"{ref}:{path}"])


def verify_owner_push(expected_sha: str) -> dict:
    required_env = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
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
        fail("only the repository owner may activate BACKEND-001")

    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("activation is permitted only from a guarded push")

    if os.environ["GITHUB_REF"] != BRANCH_REF:
        fail("activation is restricted to reos-development")

    if os.environ["GITHUB_REPOSITORY"] != REPOSITORY:
        fail("unexpected repository identity")

    if os.environ["ACTIONS_REPOSITORY"] != REPOSITORY:
        fail("unexpected Actions repository identity")

    if os.environ["EXPECTED_SHA"] != expected_sha:
        fail("EXPECTED_SHA does not match the requested source SHA")

    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out source differs from the triggering SHA")

    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    if not event_path.is_file():
        fail("GitHub push event payload is missing")

    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"GitHub push event payload is invalid: {exc}")

    if event.get("ref") != BRANCH_REF:
        fail("push event ref differs from reos-development")

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
    if not isinstance(message, str) or not message.startswith(
        APPROVAL_PREFIX
    ):
        fail("owner commit lacks the required activation prefix")

    return event


def verify_repository_baseline(expected_sha: str) -> list[str]:
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

    remote_before = run(["git", "rev-parse", "FETCH_HEAD"])
    if remote_before != expected_sha:
        fail("remote branch moved before activation")

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
        fail("the audited baseline is not an ancestor of this activation")

    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("source checkout is not clean before activation")

    expected_blobs = (
        (
            "REOS_CONTROL_CENTER/data/state.json",
            STATE_BLOB_SHA,
        ),
        (
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "HOMIO_Backend_Structure",
            BACKEND_MASTER_BLOB_SHA,
        ),
        (
            "REOS_CONTROL_CENTER/plan for work",
            WORK_PLAN_BLOB_SHA,
        ),
        (
            ARCH039_SNAPSHOT_PATH,
            ARCH039_SNAPSHOT_BLOB_SHA,
        ),
    )

    for path, expected_blob in expected_blobs:
        actual_blob = file_blob_sha(path)
        if actual_blob != expected_blob:
            fail(
                f"baseline file changed unexpectedly: {path}; "
                f"expected {expected_blob}, received {actual_blob}"
            )

    changed_paths = run(
        [
            "git",
            "diff",
            "--name-only",
            BASELINE_HEAD,
            expected_sha,
        ]
    ).splitlines()

    actual = set(changed_paths)
    if actual != EXPECTED_ACTIVATION_PATHS:
        missing = sorted(EXPECTED_ACTIVATION_PATHS - actual)
        unexpected = sorted(actual - EXPECTED_ACTIVATION_PATHS)
        fail(
            "activation source path allowlist mismatch; "
            f"missing={missing}; unexpected={unexpected}"
        )

    return sorted(actual)


def verify_b0_evidence() -> None:
    path = ROOT / B0_EVIDENCE_PATH
    if not path.is_file():
        fail("B0 read-only audit evidence file is missing")

    content = path.read_text(encoding="utf-8")
    required_markers = (
        "B0 AUDIT RESULT: COMPLETE (READ-ONLY)",
        f"BASELINE HEAD: `{BASELINE_HEAD}`",
        f"STATE BLOB SHA: `{STATE_BLOB_SHA}`",
        f"BACKEND MASTER BLOB SHA: `{BACKEND_MASTER_BLOB_SHA}`",
        f"WORK PLAN BLOB SHA: `{WORK_PLAN_BLOB_SHA}`",
        "PUBLIC FASTIFY APPLICATION: ABSENT",
        "NO BACKEND SOURCE FILES MODIFIED DURING B0",
        "B0 EXIT CONDITION: SATISFIED",
        "PRODUCTION READINESS: NOT CLAIMED",
    )

    for marker in required_markers:
        if marker not in content:
            fail(f"B0 evidence is missing required marker: {marker}")


def verify_arch039_snapshot() -> None:
    raw = subprocess.check_output(
        ["git", "show", f"HEAD:{ARCH039_SNAPSHOT_PATH}"],
        cwd=ROOT,
    )

    try:
        snapshot = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        fail(f"ARCH-039 validation snapshot is invalid: {exc}")

    stored_hash = snapshot.get("integrity", {}).get("sha256")
    if stored_hash != controller.calculate_hash(snapshot):
        fail("ARCH-039 snapshot integrity verification failed")

    gate = snapshot.get("gate_plans", {}).get("ARCH-039", {})
    if gate.get("status") != "VALIDATED":
        fail("historical ARCH-039 gate is not VALIDATED")

    if gate.get("current_subtask") != "ARCH-039-T08":
        fail("historical ARCH-039 approval subtask is not T08")

    subtasks = {
        item.get("id"): item
        for item in gate.get("subtasks", [])
        if isinstance(item, dict)
    }

    for index in range(1, 8):
        task_id = f"ARCH-039-T{index:02d}"
        if subtasks.get(task_id, {}).get("status") != "DONE":
            fail(f"ARCH-039 historical evidence does not prove {task_id}=DONE")

    if (
        subtasks.get("ARCH-039-T08", {}).get("status")
        != "READY_FOR_APPROVAL"
    ):
        fail("ARCH-039-T08 was not ready for approval in the snapshot")

    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
        if isinstance(item, dict)
    }

    expected_criteria = {
        f"ARCH-039-AC{index:02d}"
        for index in range(1, 7)
    }

    if set(criteria) != expected_criteria:
        fail("ARCH-039 snapshot acceptance criteria inventory is invalid")

    if any(
        criteria.get(criterion_id) != "VERIFIED"
        for criterion_id in expected_criteria
    ):
        fail("ARCH-039 snapshot contains unverified acceptance criteria")

    if snapshot.get("execution", {}).get("status") != "READY_FOR_APPROVAL":
        fail("ARCH-039 snapshot was not ready for approval")


def verify_current_state(state: dict) -> None:
    if state.get("integrity", {}).get("sha256") != (
        controller.calculate_hash(state)
    ):
        fail("canonical state integrity hash is invalid")

    execution = state.get("execution", {})
    if execution.get("current_gate") != "APP-001":
        fail("canonical current gate is no longer APP-001")

    if execution.get("current_subtask") != "APP-001-T01":
        fail("canonical current task is no longer APP-001-T01")

    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("canonical execution status has changed")

    sequence = state.get("execution_plan", {}).get(
        "authoritative_sequence",
        [],
    )
    by_gate = {
        item.get("gate"): item
        for item in sequence
        if isinstance(item, dict)
    }

    if by_gate.get("AI-001", {}).get("status") != "COMPLETE":
        fail("AI-001 is not COMPLETE in the authoritative sequence")

    if by_gate.get("APP-001", {}).get("status") != "CURRENT":
        fail("APP-001 is not CURRENT in the authoritative sequence")

    app_gate = state.get("gate_plans", {}).get("APP-001", {})
    if app_gate.get("current_subtask") != "APP-001-T01":
        fail("APP-001-T01 is not preserved in its gate plan")

    arch = state.get("architecture", {})
    if arch.get("locked") is not False:
        fail("architecture lock differs from the audited baseline")

    pending_arch039 = [
        item
        for item in arch.get("pending", [])
        if isinstance(item, dict)
        and item.get("id") == "ARCH-039"
    ]
    if len(pending_arch039) != 1:
        fail("ARCH-039 pending registry differs from the audited baseline")

    if pending_arch039[0].get("status") != "PENDING":
        fail("ARCH-039 is not in the audited PENDING state")

    if any(
        isinstance(item, dict) and item.get("id") == "ARCH-039"
        for item in arch.get("approved", [])
    ):
        fail("ARCH-039 already appears in the approved registry")

    arch039_plan = by_gate.get("ARCH-039", {})
    if arch039_plan.get("status") != "COMPLETE":
        fail("ARCH-039 execution-plan status differs from the audited baseline")

    if "ARCH-039" in state.get("gate_plans", {}):
        fail(
            "ARCH-039 gate plan unexpectedly exists; "
            "manual reconciliation is not permitted"
        )

    if state.get("change_requests") != []:
        fail(
            "Canonical change_requests changed since the audited baseline"
        )

    if "BACKEND-001" in state.get("gate_plans", {}):
        fail("BACKEND-001 is already materialized")


def request_github_oidc_token() -> str:
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")

    if not request_url or not request_token:
        fail(
            "GitHub OIDC token request is unavailable; "
            "check id-token: write permission"
        )

    parts = urlsplit(request_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
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
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        fail("GitHub OIDC token request failed")

    token = payload.get("value")
    if not isinstance(token, str) or not token:
        fail("GitHub OIDC endpoint returned no identity token")

    return token


class GitHubActionsPrincipalVerifier:
    """Verify GitHub's signed OIDC identity and bind the owner actor.

    The existing HOMIO OIDCVerifier performs signature, issuer, audience,
    expiry and subject verification. The additional claims are read from
    that same already-verified token to bind the repository owner, ref and
    source commit to the human approval event.
    """

    def __init__(self, expected_sha: str) -> None:
        self.expected_sha = expected_sha
        self.settings = OIDCSettings(
            issuer=OIDC_ISSUER,
            audience=OIDC_AUDIENCE,
            jwks_url=OIDC_JWKS_URL,
        )
        self.verifier = OIDCVerifier(self.settings)
        self.claims: dict[str, object] = {}

    def verify_access_token(
        self,
        token: str,
    ) -> AuthenticatedPrincipal:
        principal = self.verifier.verify_access_token(token)

        try:
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_aud": False,
                    "verify_iss": False,
                    "verify_nbf": False,
                },
                algorithms=["RS256", "ES256"],
            )
        except Exception:
            fail("Verified GitHub OIDC token claims could not be read")

        expected_claims = {
            "iss": OIDC_ISSUER,
            "sub": EXPECTED_OIDC_SUBJECT,
            "repository": REPOSITORY,
            "repository_owner": OWNER,
            "actor": OWNER,
            "ref": BRANCH_REF,
            "sha": self.expected_sha,
            "event_name": "push",
        }

        for name, expected in expected_claims.items():
            if claims.get(name) != expected:
                fail(
                    "GitHub OIDC token scope mismatch for claim "
                    f"{name!r}"
                )

        actor_id = claims.get("actor_id")
        if not isinstance(actor_id, (str, int)) or not str(actor_id):
            fail("GitHub OIDC actor identity is incomplete")

        if principal.issuer != OIDC_ISSUER:
            fail("OIDC verifier returned an unexpected issuer")

        if principal.subject != EXPECTED_OIDC_SUBJECT:
            fail("OIDC verifier returned an unexpected subject")

        if OIDC_AUDIENCE not in principal.audiences:
            fail("OIDC verifier returned an unexpected audience")

        self.claims = claims
        return principal


def authorize_activation(
    *,
    expected_sha: str,
    state: dict,
    changed_paths: list[str],
    owner_event: dict,
) -> tuple[dict, dict, dict, dict]:
    token = request_github_oidc_token()
    principal_verifier = GitHubActionsPrincipalVerifier(expected_sha)
    principal = principal_verifier.verify_access_token(token)
    claims = principal_verifier.claims

    context = OperatorContext(
        gate="APP-001",
        subtask="APP-001-T01",
        task=(
            "Owner-approved insertion of the unified backend workstream "
            "between AI-001 and APP-001, including ARCH-039 status reconciliation."
        ),
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
        metadata={
            "baseline_head": BASELINE_HEAD,
            "state_blob_sha": STATE_BLOB_SHA,
            "backend_master_blob_sha": BACKEND_MASTER_BLOB_SHA,
            "work_plan_blob_sha": WORK_PLAN_BLOB_SHA,
            "arch039_snapshot_blob_sha": ARCH039_SNAPSHOT_BLOB_SHA,
            "owner_commit_sha": expected_sha,
        },
    )

    operator_request = OperatorRequest(
        context=context,
        requested_action=OperatorActionType.PROPOSE_CHANGE,
        objective=(
            "Activate BACKEND-001 after B0 audit, preserve APP-001-T01, "
            "reconcile previously validated ARCH-039, and insert B0-B10 "
            "into the authoritative execution sequence."
        ),
        evidence=(
            f"baseline_head={BASELINE_HEAD}",
            f"state_blob_sha={STATE_BLOB_SHA}",
            f"backend_master_blob_sha={BACKEND_MASTER_BLOB_SHA}",
            f"work_plan_blob_sha={WORK_PLAN_BLOB_SHA}",
            f"arch039_snapshot_blob_sha={ARCH039_SNAPSHOT_BLOB_SHA}",
            f"owner_source_commit={expected_sha}",
        ),
        metadata={
            "workstream": "BACKEND",
            "gate": "BACKEND-001",
            "first_subtask": "BACKEND-001-B1",
            "preserved_subtask": "APP-001-T01",
        },
    )

    operator_report = OperatorAutonomyEngine.operate(operator_request)
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

    if impact_report.protected_paths or impact_report.unknown_paths:
        fail(
            "T17 found protected or unknown impacts: "
            f"protected={list(impact_report.protected_paths)}, "
            f"unknown={list(impact_report.unknown_paths)}"
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
        f"GitHub actor: {claims['actor']}",
        f"GitHub actor ID: {claims['actor_id']}",
        f"Repository: {REPOSITORY}",
        f"Branch: {BRANCH}",
        f"Owner-approved source commit: {expected_sha}",
        f"Required commit prefix: {APPROVAL_PREFIX}",
        f"Push event sender: {owner_event['sender']['login']}",
        f"Actions run ID: {os.environ['ACTIONS_RUN_ID']}",
    )

    approval = HumanApproval(
        approval_id=f"GH-OWNER-PUSH:{expected_sha}",
        authority="GITHUB_REPOSITORY_OWNER",
        approved=True,
        scope_fingerprint=approval_scope_fingerprint(base_request),
        evidence=approval_evidence,
        principal_issuer=principal.issuer,
        principal_subject=principal.subject,
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
            "T18 did not authorize the external Control Center executor: "
            f"{authorization.decision.value}/{authorization.reason.value}"
        )

    # Persist only safe report metadata. Never persist the OIDC token.
    approval_record = {
        "actor": claims["actor"],
        "actor_id": str(claims["actor_id"]),
        "source_commit": expected_sha,
        "state_blob_sha": STATE_BLOB_SHA,
        "oidc_issuer": principal.issuer,
        "oidc_subject": principal.subject,
        "actions_run_id": os.environ["ACTIONS_RUN_ID"],
    }

    return (
        operator_report.to_dict(),
        impact_report.to_dict(),
        authorization.to_dict(),
        approval_record,
    )


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
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def verify_transition_state(state: dict) -> None:
    execution = state.get("execution", {})

    if execution.get("current_gate") != "BACKEND-001":
        fail("Control Center did not select BACKEND-001")

    if execution.get("current_subtask") != "BACKEND-001-B1":
        fail("Control Center did not select BACKEND-001-B1")

    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution status is not CONTROL_CENTER_DRIVEN")

    backend_gate = state.get("gate_plans", {}).get("BACKEND-001", {})
    if backend_gate.get("status") != "CURRENT":
        fail("BACKEND-001 gate plan is not CURRENT")

    subtasks = {
        item.get("id"): item
        for item in backend_gate.get("subtasks", [])
        if isinstance(item, dict)
    }

    if subtasks.get("BACKEND-001-B0", {}).get("status") != "DONE":
        fail("B0 audit is not recorded as DONE")

    if subtasks.get("BACKEND-001-B1", {}).get("status") != "CURRENT":
        fail("B1 backend foundation is not CURRENT")

    app_gate = state.get("gate_plans", {}).get("APP-001", {})
    if app_gate.get("current_subtask") != "APP-001-T01":
        fail("APP-001-T01 was not preserved")

    app_subtasks = {
        item.get("id"): item
        for item in app_gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    if app_subtasks.get("APP-001-T01", {}).get("status") != "CURRENT":
        fail("APP-001-T01 is not preserved as CURRENT")

    sequence = {
        item.get("gate"): item.get("status")
        for item in state.get("execution_plan", {}).get(
            "authoritative_sequence",
            [],
        )
        if isinstance(item, dict)
    }

    expected = {
        "AI-001": "COMPLETE",
        "BACKEND-001": "CURRENT",
        "APP-001": "FUTURE",
        "REL-001": "FUTURE",
        "SCALE-001": "FUTURE",
    }

    for gate_id, status in expected.items():
        if sequence.get(gate_id) != status:
            fail(
                f"authoritative sequence mismatch for {gate_id}: "
                f"{sequence.get(gate_id)!r}"
            )

    architecture = state.get("architecture", {})
    if architecture.get("locked") is not True:
        fail("ARCH-039 reconciliation did not restore the architecture lock")

    if not any(
        item.get("id") == "ARCH-039"
        and item.get("status") == "APPROVED"
        for item in architecture.get("approved", [])
        if isinstance(item, dict)
    ):
        fail("ARCH-039 is not present in the approved architecture registry")

    if any(
        item.get("id") == "ARCH-039"
        for item in architecture.get("pending", [])
        if isinstance(item, dict)
    ):
        fail("ARCH-039 remains in the pending architecture registry")

    if not any(
        item.get("id") == "CR-BACKEND-001"
        and item.get("status") == "APPROVED"
        for item in state.get("change_requests", [])
        if isinstance(item, dict)
    ):
        fail("Approved backend activation change request is missing")

    if not is_phase_coherent(state):
        fail("Canonical gate and phase projection are not coherent")

    if state.get("integrity", {}).get("sha256") != (
        controller.calculate_hash(state)
    ):
        fail("post-transition state integrity verification failed")


def write_activation_evidence(
    *,
    source_sha: str,
    state_blob_sha: str,
    operator_report: dict,
    impact_report: dict,
    authorization: dict,
    approval_record: dict,
) -> None:
    path = ROOT / ACTIVATION_EVIDENCE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    run_id = os.environ["ACTIONS_RUN_ID"]
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/{run_id}"
    )

    lines = [
        "# BACKEND-001 — Guarded Workstream Activation Evidence",
        "",
        f"- Repository: `{REPOSITORY}`",
        f"- Branch: `{BRANCH}`",
        f"- Owner actor: `{approval_record['actor']}`",
        f"- Owner actor ID: `{approval_record['actor_id']}`",
        f"- Owner-approved source commit: `{source_sha}`",
        f"- GitHub Actions run: [{run_id}]({run_url})",
        "",
        "## Authorization chain",
        "",
        f"- T15 decision: `{operator_report['decision']}`",
        f"- T15 request fingerprint: `{operator_report['request_fingerprint']}`",
        f"- T17 decision: `{impact_report['decision']}`",
        f"- T17 fingerprint: `{impact_report['fingerprint']}`",
        f"- T17 changed paths: `{len(impact_report['changed_paths'])}`",
        f"- T17 unknown paths: `{len(impact_report['unknown_paths'])}`",
        f"- T17 protected paths: `{len(impact_report['protected_paths'])}`",
        f"- T18 decision: `{authorization['decision']}`",
        (
            "- T18 authorization fingerprint: "
            f"`{authorization['authorization_fingerprint']}`"
        ),
        f"- OIDC issuer: `{approval_record['oidc_issuer']}`",
        f"- OIDC subject: `{approval_record['oidc_subject']}`",
        "- OIDC bearer token: not persisted",
        "",
        "## ARCH-039 reconciliation",
        "",
        f"- Verified source snapshot: `{ARCH039_SNAPSHOT_PATH}`",
        f"- Snapshot blob SHA: `{ARCH039_SNAPSHOT_BLOB_SHA}`",
        "- Historical gate status: `VALIDATED`",
        "- T01-T07: `DONE`",
        "- T08: `READY_FOR_APPROVAL`",
        "- AC01-AC06: `VERIFIED`",
        "- Owner-approved final freeze: `APPROVED`",
        "- Architecture lock: `true`",
        "",
        "## Backend activation",
        "",
        "- B0: `DONE`",
        "- B1: `CURRENT`",
        "- B2-B10: `PENDING`",
        "- Current task: `BACKEND-001-B1`",
        "- Preserved frontend task: `APP-001-T01`",
        "- Next frontend gate status: `FUTURE` in the authoritative sequence",
        f"- Post-transition state blob SHA: `{state_blob_sha}`",
        "",
        "This evidence proves only the guarded workstream activation. It does not "
        "claim that B1 is complete, that the backend is production-ready, or "
        "that any production release has been approved.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    expected_sha = os.environ.get("EXPECTED_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        fail("EXPECTED_SHA is not a valid commit SHA")

    owner_event = verify_owner_push(expected_sha)
    changed_paths = verify_repository_baseline(expected_sha)
    verify_b0_evidence()
    verify_arch039_snapshot()

    state = controller.load_state()
    verify_current_state(state)

    (
        operator_report,
        impact_report,
        authorization,
        approval_record,
    ) = authorize_activation(
        expected_sha=expected_sha,
        state=state,
        changed_paths=changed_paths,
        owner_event=owner_event,
    )

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    new_state = activate_backend_workstream_state(
        state,
        timestamp=timestamp,
        baseline_sha=BASELINE_HEAD,
        master_blob_sha=BACKEND_MASTER_BLOB_SHA,
        work_plan_blob_sha=WORK_PLAN_BLOB_SHA,
        b0_evidence_path=B0_EVIDENCE_PATH,
        approval_record=approval_record,
        t15_report=operator_report,
        t17_report=impact_report,
        authorization=authorization,
    )

    controller.emit(
        new_state,
        "GATE_APPROVED_AND_FROZEN",
        {
            "gate": "ARCH-039",
            "source_snapshot_blob_sha": ARCH039_SNAPSHOT_BLOB_SHA,
            "authorization_fingerprint": (
                authorization["authorization_fingerprint"]
            ),
            "approved_by": approval_record["actor"],
        },
    )

    controller.emit(
        new_state,
        "CHANGE_REQUEST_APPROVED",
        {
            "id": "CR-BACKEND-001",
            "approved_by": approval_record["actor"],
            "authorization_fingerprint": (
                authorization["authorization_fingerprint"]
            ),
        },
    )

    controller.emit(
        new_state,
        "WORKSTREAM_ACTIVATED",
        {
            "gate": "BACKEND-001",
            "subtask": "BACKEND-001-B1",
            "preserved_gate": "APP-001",
            "preserved_subtask": "APP-001-T01",
            "source_commit": expected_sha,
        },
    )

    controller.build_handoff_packet(new_state)
    controller.save_state(new_state)

    for path in (STATE_PATH, PACKET_PATH, HANDOFF_PATH):
        preserve_line_endings(path)

    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )

    verified_state = controller.load_state()
    verify_transition_state(verified_state)

    state_blob_sha = run(["git", "hash-object", str(STATE_PATH)])

    write_activation_evidence(
        source_sha=expected_sha,
        state_blob_sha=state_blob_sha,
        operator_report=operator_report,
        impact_report=impact_report,
        authorization=authorization,
        approval_record=approval_record,
    )

    untracked = sorted(
        run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
            ]
        ).splitlines()
    )

    snapshot_files = [
        item
        for item in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/"
            r"state_\d{8}_\d{6}_\d{6}\.json",
            item,
        )
    ]

    expected_untracked = {
        *snapshot_files,
        ACTIVATION_EVIDENCE_PATH,
    }

    if len(snapshot_files) != 1 or set(untracked) != expected_untracked:
        fail(
            "unexpected untracked files after Control Center transition: "
            f"{untracked}"
        )

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }

    actual_tracked = set(
        run(["git", "diff", "--name-only"]).splitlines()
    )

    if actual_tracked != expected_tracked:
        fail(
            "unexpected Control Center tracked modifications: "
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

    staged_paths = sorted(expected_tracked | expected_untracked)
    run(["git", "add", "--", *staged_paths])

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
        run(["git", "diff", "--cached", "--name-only"]).splitlines()
    )

    if actual_staged != set(staged_paths):
        fail(
            "staged path allowlist mismatch: "
            f"{sorted(actual_staged)}"
        )

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
                "chore(control-center): activate BACKEND-001 "
                "through guarded owner approval"
            ),
        ],
        capture=False,
    )

    transition_commit = run(["git", "rev-parse", "HEAD"])

    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("transition commit parent is not the verified source commit")

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
        fail("canonical branch changed before transition publication")

    push_result = subprocess.run(
        [
            "git",
            "push",
            "origin",
            f"HEAD:{BRANCH_REF}",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if push_result.stdout:
        print(
            push_result.stdout,
            end=(
                ""
                if push_result.stdout.endswith("\n")
                else "\n"
            ),
        )

    # If a network error makes push outcome ambiguous, reconcile by readback.
    # Never blindly retry an ambiguous write.
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

    remote_head = run(["git", "rev-parse", "FETCH_HEAD"])
    if remote_head != transition_commit:
        fail(
            "remote readback does not confirm the activation commit; "
            f"push return code={push_result.returncode}, "
            f"remote HEAD={remote_head}"
        )

    local_state_blob = file_blob_sha(
        "REOS_CONTROL_CENTER/data/state.json",
        ref="HEAD",
    )
    remote_state_blob = file_blob_sha(
        "REOS_CONTROL_CENTER/data/state.json",
        ref="FETCH_HEAD",
    )

    if local_state_blob != remote_state_blob:
        fail("remote state blob differs from the verified local transition")

    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("transition checkout is not clean after publication")

    print("=" * 72)
    print("BACKEND-001 WORKSTREAM ACTIVATED")
    print("Source commit:", expected_sha)
    print("Transition commit:", transition_commit)
    print("Remote HEAD:", remote_head)
    print("State blob SHA:", remote_state_blob)
    print("Current gate: BACKEND-001")
    print("Current subtask: BACKEND-001-B1")
    print("Preserved frontend subtask: APP-001-T01")
    print("T15: PROPOSE")
    print("T17: ANALYZE")
    print("T18: AUTHORIZE")
    print("ARCH-039: APPROVED AND LOCKED")
    print("=" * 72)


if __name__ == "__main__":
    main()
