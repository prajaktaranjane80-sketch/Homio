from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"

STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
PACKET_PATH = "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
HANDOFF_PATH = "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt"
MASTER_PATH = (
    "REOS_CONTROL_CENTER/architecture/backend/plans/"
    "HOMIO_Backend_Structure"
)
REQUEST_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B2-core001-resource-action-decision-change-request.md"
)
EVIDENCE_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B2-core001-authorization-approval-evidence.md"
)
APPROVAL_RECORD_PATH = (
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B2-core001-authorization-owner-approval.md"
)

BASELINE_HEAD = "ae9e2e24344c391a116cc85b8d358b80bfcaa8e4"
BASELINE_STATE_BLOB_SHA = (
    "3482877a8e321f9d81782270bb44cfaeec297496"
)
BASELINE_MASTER_BLOB_SHA = (
    "f8d9cd456568cc6c8eaae0caf764123a7e859ba6"
)
BASELINE_REQUEST_BLOB_SHA = (
    "d0d24b4bd52549930bcac07d439d3ca8796e0800"
)

OWNER = "prajaktaranjane80-sketch"
REPOSITORY = "prajaktaranjane80-sketch/Homio"
BRANCH = "reos-development"
BRANCH_REF = f"refs/heads/{BRANCH}"

CHANGE_REQUEST_ID = "B2-CORE001-AUTHZ-001"
APPROVAL_PREFIX = (
    "[CONTROL-CENTER-APPROVE-BACKEND-001-B2-CORE001-AUTHZ]"
)
OIDC_AUDIENCE = "homio-control-center-b2-core001-authorization-approval"

# This exact record is the only source file that may be changed by the
# owner-approval commit. The repository owner must create/save it only when
# explicitly choosing to approve the bounded change request.
#
# The GitHub Actions owner identity, OIDC principal, exact commit path,
# immutable state/master/request baselines and T15/T17/T18 checks are
# independently verified. The record cannot authorize production routes
# or completion of B2.
APPROVAL_RECORD_CONTENT = """# B2 CORE-001 Owner Approval

- Change request: `B2-CORE001-AUTHZ-001`
- Decision: `APPROVE`
- Approval scope: `Bounded owner-extension request only`
- Repository: `prajaktaranjane80-sketch/Homio`
- Branch: `reos-development`

I, the repository owner, explicitly approve only the bounded changes described in `B2-core001-resource-action-decision-change-request.md`.

This approval covers the T01 identity/account-resolution extension, the authenticated B3 trusted-context and private authorization operation, one resource/action decision owner within existing CORE-001, default-deny behavior, approved assurance and attribute sources, role-isolation fixtures, and the regression coverage defined by that request.

This approval does not authorize production customer routes, B2 completion, backend acceptance-criteria completion, production release, manual `state.json` edits, frontend changes, or any work outside the referenced request.
"""

# Owner approval must be a dedicated one-file commit. This intentionally
# replaces the previous five-infrastructure-files-in-one-commit requirement,
# which is incompatible with normal GitHub Web Editor saves.
EXPECTED_SOURCE_PATHS = {
    APPROVAL_RECORD_PATH,
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
    BACKEND_GATE_ID,
    BACKEND_STAGES,
    BACKEND_ACCEPTANCE_CRITERIA,
    B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA,
    _validate_owner_approval_record,
)
from REOS_CONTROL_CENTER.context.github_actions_identity import (  # noqa: E402
    EXPECTED_OIDC_SUBJECT,
    OIDC_ISSUER,
    OWNER_ID,
    REPOSITORY_ID,
)


class GuardedTransitionError(RuntimeError):
    """Raised when the B2 CORE-001 approval transition is unsafe."""


def fail(message: str) -> None:
    raise GuardedTransitionError(
        f"B2 CORE-001 approval blocked: {message}"
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def valid_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    )


def valid_fingerprint(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    )


def run(
    command: list[str],
    *,
    capture: bool = True,
    display: bool = True,
) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )

    output = completed.stdout or "" if capture else ""

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


def file_blob_sha(path: str, ref: str = "HEAD") -> str:
    return run(
        ["git", "rev-parse", f"{ref}:{path}"],
        display=False,
    )


def changed_paths_for_commit(source_sha: str) -> list[str]:
    """
    Return only the paths changed by the exact owner source commit.

    The historical reviewed baseline remains an ancestry and trust anchor.
    It is deliberately not used as the diff base because unrelated,
    previously verified commits may exist between that baseline and the
    current owner approval commit.
    """
    require(
        valid_sha(source_sha),
        "Owner source commit SHA is invalid.",
    )

    parent_sha = run(
        ["git", "rev-parse", f"{source_sha}^"],
        display=False,
    )
    require(
        valid_sha(parent_sha),
        "Owner source commit parent SHA is invalid.",
    )

    changed_paths = run(
        [
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            parent_sha,
            source_sha,
        ],
        display=False,
    ).splitlines()

    require(
        len(changed_paths) == len(set(changed_paths)),
        "Owner source commit returned duplicate changed paths.",
    )

    return sorted(changed_paths)


def load_existing_b2_guard():
    """
    Reuse the existing B2 T15/T17/T18 and OIDC implementation.

    This module is loaded only as a library. Its original transition
    main() is never invoked by this approval workflow.
    """
    path = (
        ROOT
        / ".github/actions/homio-backend-ci/transitions/"
        "backend-b2-dependency-correction/scripts/guarded_transition.py"
    )

    require(path.is_file(), "Existing B2 T15/T17/T18 guard is missing.")

    spec = importlib.util.spec_from_file_location(
        "homio_existing_b2_guard_for_core001_approval",
        path,
    )

    require(
        spec is not None and spec.loader is not None,
        "Could not load the existing B2 authorization implementation.",
    )

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    module.APPROVAL_PREFIX = APPROVAL_PREFIX
    module.OIDC_AUDIENCE = OIDC_AUDIENCE

    return module


EXISTING_B2_GUARD = load_existing_b2_guard()


def assert_exact_branch(expected_sha: str) -> None:
    require(valid_sha(expected_sha), "Triggering source SHA is invalid.")

    actual = run(["git", "rev-parse", "HEAD"], display=False)
    require(
        actual == expected_sha,
        "Checked-out HEAD differs from the triggering source SHA.",
    )

    run(
        ["git", "fetch", "--no-tags", "origin", BRANCH_REF],
        capture=False,
    )

    remote_sha = run(
        ["git", "rev-parse", "FETCH_HEAD"],
        display=False,
    )
    require(
        remote_sha == expected_sha,
        "Canonical branch moved; refusing a stale approval transition.",
    )


def verify_owner_push(expected_sha: str) -> dict:
    required = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
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
        for name in required
        if not os.environ.get(name)
    ]
    require(not missing, f"Missing GitHub Actions environment: {missing}")

    require(
        os.environ["GITHUB_ACTOR"] == OWNER,
        "Only the immutable repository owner can approve this request.",
    )
    require(
        os.environ["GITHUB_EVENT_NAME"] == "push",
        "Approval requires an owner push event.",
    )
    require(
        os.environ["GITHUB_REF"] == BRANCH_REF,
        "Approval is restricted to reos-development.",
    )
    require(
        os.environ["GITHUB_REPOSITORY"] == REPOSITORY,
        "Unexpected repository identity.",
    )
    require(
        os.environ["ACTIONS_REPOSITORY"] == REPOSITORY,
        "Unexpected Actions repository identity.",
    )
    require(
        os.environ["EXPECTED_SHA"] == expected_sha,
        "EXPECTED_SHA differs from the triggering commit.",
    )
    require(
        os.environ["VERIFIED_CODE_SHA"] == expected_sha,
        "Verified code SHA differs from the triggering commit.",
    )

    return EXISTING_B2_GUARD.verify_owner_push(expected_sha)


def verify_request_document(expected_sha: str) -> None:
    content = run(
        ["git", "show", f"{expected_sha}:{REQUEST_PATH}"],
        display=False,
    )

    required = (
        "B2-CORE001-AUTHZ-001",
        "Status:** PROPOSED — NOT APPROVED",
        "Production authorization:** NOT AUTHORIZED BY THIS DOCUMENT",
        "The CORE-001 owner must review and approve:",
        "The T01 account-resolution extension and account-cardinality behavior.",
        "The B3 trusted-context and private authorization-operation extension.",
        "The resource/action decision owner within existing CORE-001.",
        "The absence of an explicit-deny model in this scope.",
    )

    for marker in required:
        require(
            marker in content,
            f"Change request document is missing required scope: {marker}",
        )

    require(
        file_blob_sha(REQUEST_PATH, expected_sha)
        == BASELINE_REQUEST_BLOB_SHA,
        "The proposal document differs from its reviewed baseline.",
    )


def verify_owner_approval_record(expected_sha: str) -> None:
    """
    Require the exact owner-attestation text from the triggering commit.

    The dedicated file is deliberately separate from the proposed change
    request, which remains immutable and NOT APPROVED until the guarded
    transition records the decision.
    """
    require(
        valid_sha(expected_sha),
        "Owner approval source SHA is invalid.",
    )

    content = run(
        ["git", "show", f"{expected_sha}:{APPROVAL_RECORD_PATH}"],
        display=False,
    )

    normalized_content = content.replace("\r\n", "\n").strip()
    expected_content = APPROVAL_RECORD_CONTENT.replace(
        "\r\n",
        "\n",
    ).strip()

    require(
        normalized_content == expected_content,
        (
            "Owner approval record does not exactly match the "
            "approved CORE-001 change-request scope."
        ),
    )


def verify_source_baseline(expected_sha: str) -> list[str]:
    assert_exact_branch(expected_sha)

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
    require(
        ancestor.returncode == 0,
        "The exact reviewed source baseline is not an ancestor.",
    )

    dirty = run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        display=False,
    )
    require(not dirty, "Source checkout is not clean before transition.")

    require(
        file_blob_sha(STATE_PATH, BASELINE_HEAD)
        == BASELINE_STATE_BLOB_SHA,
        "Reviewed canonical state baseline changed.",
    )
    require(
        file_blob_sha(MASTER_PATH, BASELINE_HEAD)
        == BASELINE_MASTER_BLOB_SHA,
        "Reviewed backend master baseline changed.",
    )
    require(
        file_blob_sha(REQUEST_PATH, BASELINE_HEAD)
        == BASELINE_REQUEST_BLOB_SHA,
        "Reviewed CORE-001 request baseline changed.",
    )

    require(
        file_blob_sha(STATE_PATH, expected_sha)
        == BASELINE_STATE_BLOB_SHA,
        "Owner source commit must not modify canonical state.json.",
    )
    require(
        file_blob_sha(MASTER_PATH, expected_sha)
        == BASELINE_MASTER_BLOB_SHA,
        "Owner source commit unexpectedly changes the backend master.",
    )
    require(
        file_blob_sha(REQUEST_PATH, expected_sha)
        == BASELINE_REQUEST_BLOB_SHA,
        "Owner source commit unexpectedly changes the approval request.",
    )

    changed_paths = changed_paths_for_commit(expected_sha)
    actual_paths = set(changed_paths)

    require(
        actual_paths == EXPECTED_SOURCE_PATHS,
        (
            "Exact owner approval path inventory mismatch; "
            f"missing={sorted(EXPECTED_SOURCE_PATHS - actual_paths)}; "
            f"unexpected={sorted(actual_paths - EXPECTED_SOURCE_PATHS)}"
        ),
    )

    verify_request_document(expected_sha)
    verify_owner_approval_record(expected_sha)

    return sorted(actual_paths)


def expected_stage_statuses() -> dict[str, str]:
    result = {}

    for stage_id, _, _ in BACKEND_STAGES:
        if stage_id in {
            "B0",
            "B1",
            "B2-FOUNDATION",
            "B3",
            "B4",
        }:
            status = "DONE"
        elif stage_id == "B2-PRODUCTION-BINDING":
            status = "CURRENT"
        else:
            status = "PENDING"

        result[f"BACKEND-001-{stage_id}"] = status

    return result


def verify_current_state(state: dict) -> None:
    require(
        isinstance(state, dict),
        "Canonical state root must be an object.",
    )
    require(
        state.get("integrity", {}).get("sha256")
        == controller.calculate_hash(state),
        "Canonical state integrity hash is invalid.",
    )

    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get(BACKEND_GATE_ID, {})

    require(
        execution.get("current_gate") == BACKEND_GATE_ID,
        "BACKEND-001 is not the current gate.",
    )
    require(
        execution.get("current_subtask")
        == "BACKEND-001-B2-PRODUCTION-BINDING",
        "B2 Production Binding is not the current execution task.",
    )
    require(
        execution.get("status") == "CONTROL_CENTER_DRIVEN",
        "Execution is not Control Center driven.",
    )
    require(
        gate.get("status") == "CURRENT",
        "BACKEND-001 gate is not CURRENT.",
    )
    require(
        gate.get("current_subtask")
        == "BACKEND-001-B2-PRODUCTION-BINDING",
        "Backend gate projection does not point to B2 Production Binding.",
    )
    require(
        execution.get("current_acceptance_criteria")
        == B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA,
        "Current B2 acceptance-criteria projection changed.",
    )

    subtasks = gate.get("subtasks")
    require(isinstance(subtasks, list), "Backend subtask list is missing.")

    actual_statuses = {
        item.get("id"): item.get("status")
        for item in subtasks
        if isinstance(item, dict)
    }
    require(
        actual_statuses == expected_stage_statuses(),
        "Backend stage sequence/statuses differ from current authority.",
    )

    criteria_state = gate.get("criteria_state")
    require(
        isinstance(criteria_state, list) and len(criteria_state) == 10,
        "Backend AC01-AC10 inventory is invalid.",
    )
    require(
        all(
            isinstance(item, dict)
            and item.get("status") == "PENDING"
            and item.get("evidence") is None
            and item.get("verified_at") is None
            for item in criteria_state
        ),
        "Gate-level acceptance criteria must remain entirely PENDING.",
    )

    request_list = state.get("change_requests")
    require(
        isinstance(request_list, list),
        "Canonical change_requests list is missing.",
    )
    require(
        not any(
            isinstance(item, dict)
            and item.get("id") == CHANGE_REQUEST_ID
            for item in request_list
        ),
        "CORE-001 authorization request is already recorded.",
    )


def authorize_change_request(
    *,
    expected_sha: str,
    state_blob_sha: str,
    master_blob_sha: str,
    request_blob_sha: str,
    changed_paths: list[str],
    owner_event: dict,
) -> tuple[dict, dict, dict, dict]:
    token = EXISTING_B2_GUARD.request_github_oidc_token()

    principal_verifier = (
        EXISTING_B2_GUARD.GitHubActionsPrincipalVerifier(expected_sha)
    )

    try:
        claims = principal_verifier.verify_identity_token(token)
    except EXISTING_B2_GUARD.AuthenticationError as exc:
        fail(f"GitHub Actions OIDC identity verification failed: {exc.code}")

    context = EXISTING_B2_GUARD.OperatorContext(
        gate="BACKEND-001",
        subtask="BACKEND-001-B2-PRODUCTION-BINDING",
        task=(
            "Approve only the bounded B2 CORE-001 resource/action "
            "authorization change request. Do not implement the proposed "
            "domain changes, complete B2, or activate protected routes."
        ),
        state_available=True,
        state_valid=True,
        architecture_stable=True,
        authority_valid=True,
        integrity_valid=True,
        evidence_available=True,
        metadata={
            "baseline_head": BASELINE_HEAD,
            "source_commit": expected_sha,
            "state_blob_sha": state_blob_sha,
            "master_blob_sha": master_blob_sha,
            "request_blob_sha": request_blob_sha,
            "change_request_id": CHANGE_REQUEST_ID,
            "current_subtask": "BACKEND-001-B2-PRODUCTION-BINDING",
            "production_routes_enabled": False,
            "task_completion_authorized": False,
        },
    )

    operator_request = EXISTING_B2_GUARD.OperatorRequest(
        context=context,
        requested_action=(
            EXISTING_B2_GUARD.OperatorActionType.PROPOSE_CHANGE
        ),
        objective=(
            "Record owner approval for the exact CORE-001 account "
            "resolution, B3 trusted-context, resource/action decision "
            "owner, default-deny, assurance/attribute and role-isolation "
            "scope described in B2-CORE001-AUTHZ-001. This approval is "
            "limited to that proposal and does not authorize production "
            "activation or backend task completion."
        ),
        evidence=(
            f"baseline_head={BASELINE_HEAD}",
            f"owner_source_commit={expected_sha}",
            f"state_blob_sha={state_blob_sha}",
            f"backend_master_blob_sha={master_blob_sha}",
            f"change_request_blob_sha={request_blob_sha}",
            f"change_request_id={CHANGE_REQUEST_ID}",
            f"owner_id={OWNER_ID}",
            f"repository_id={REPOSITORY_ID}",
            f"oidc_subject={EXPECTED_OIDC_SUBJECT}",
            f"changed_path_count={len(changed_paths)}",
        ),
        metadata={
            "change_request_id": CHANGE_REQUEST_ID,
            "approved_scope": "B2-CORE001-AUTHZ-001 only",
            "production_customer_routes": False,
            "B2_completion": False,
            "backend_acceptance_criteria_completion": False,
        },
    )

    operator_report = (
        EXISTING_B2_GUARD.OperatorAutonomyEngine.operate(
            operator_request
        )
    )

    require(
        operator_report.decision.value == "PROPOSE",
        (
            "T15 did not produce PROPOSE: "
            f"{operator_report.decision.value}"
        ),
    )

    analyzer = EXISTING_B2_GUARD.ChangeImpactAnalyzer(ROOT)
    impact_report = analyzer.analyze(changed_paths)
    analyzer.validate_report(impact_report)

    require(
        impact_report.ready_for_handoff,
        "T17 report is not ready for authorization handoff.",
    )
    require(
        not impact_report.unknown_paths,
        f"T17 found unknown paths: {list(impact_report.unknown_paths)}",
    )
    require(
        not impact_report.protected_paths,
        f"T17 found protected paths: {list(impact_report.protected_paths)}",
    )

    nonce = (
        f"{os.environ['ACTIONS_RUN_ID']}:"
        f"{os.environ['ACTIONS_RUN_ATTEMPT']}:"
        f"{expected_sha}:{request_blob_sha}"
    )

    base_request = EXISTING_B2_GUARD.AuthorizationRequest(
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
        f"Change request ID: {CHANGE_REQUEST_ID}",
        f"Change request blob SHA: {request_blob_sha}",
    )

    approval = EXISTING_B2_GUARD.HumanApproval(
        approval_id=f"GH-OWNER-PUSH:{expected_sha}",
        authority="GITHUB_REPOSITORY_OWNER",
        approved=True,
        scope_fingerprint=(
            EXISTING_B2_GUARD.approval_scope_fingerprint(base_request)
        ),
        evidence=approval_evidence,
        principal_issuer=str(claims["iss"]),
        principal_subject=str(claims["sub"]),
        authentication_token=token,
    )

    authorization_request = EXISTING_B2_GUARD.AuthorizationRequest(
        operator_report=operator_report,
        impact_report=impact_report,
        approval=approval,
        nonce=nonce,
    )

    policy = EXISTING_B2_GUARD.SafeAuthorizationPolicy(
        maximum_risk=EXISTING_B2_GUARD.OperatorRisk.MEDIUM,
        trusted_approver_principals=(
            (OIDC_ISSUER, EXPECTED_OIDC_SUBJECT),
        ),
    )

    authorization = (
        EXISTING_B2_GUARD.ExecutionAuthorizationGuard(
            policy,
            principal_verifier=principal_verifier,
        ).authorize(authorization_request)
    )

    require(
        authorization.decision.value == "AUTHORIZE"
        and authorization.execution_authorized is True
        and authorization.state_mutated is False
        and authorization.requires_external_executor is True,
        (
            "T18 did not authorize the bounded external transition: "
            f"{authorization.decision.value}/"
            f"{authorization.reason.value}"
        ),
    )

    approval_record = {
        "actor": claims["actor"],
        "actor_id": str(claims["actor_id"]),
        "owner_id": OWNER_ID,
        "repository_id": REPOSITORY_ID,
        "source_commit": expected_sha,
        "state_blob_sha": state_blob_sha,
        "oidc_issuer": str(claims["iss"]),
        "oidc_subject": str(claims["sub"]),
        "actions_run_id": os.environ["ACTIONS_RUN_ID"],
    }

    return (
        operator_report.to_dict(),
        impact_report.to_dict(),
        authorization.to_dict(),
        approval_record,
    )


def build_approved_state(
    state: dict,
    *,
    timestamp: str,
    baseline_sha: str,
    source_sha: str,
    state_blob_sha: str,
    master_blob_sha: str,
    request_blob_sha: str,
    t15_report: dict,
    t17_report: dict,
    authorization: dict,
    approval_record: dict,
) -> dict:
    """
    Build an immutable candidate state.

    Only the bounded request is approved. No task status, execution
    projection, gate criterion or production switch is changed.
    """
    verify_current_state(state)

    require(bool(timestamp), "Transition timestamp is required.")
    require(valid_sha(baseline_sha), "Baseline SHA is invalid.")
    require(valid_sha(source_sha), "Owner source SHA is invalid.")
    require(valid_sha(state_blob_sha), "State blob SHA is invalid.")
    require(valid_sha(master_blob_sha), "Backend master blob SHA is invalid.")
    require(valid_sha(request_blob_sha), "Request document blob SHA is invalid.")

    _validate_owner_approval_record(
        approval_record,
        transition_name="B2 CORE-001 authorization approval",
    )

    require(
        isinstance(t15_report, dict)
        and t15_report.get("decision") == "PROPOSE"
        and t15_report.get("execution_authorized") is False
        and valid_fingerprint(t15_report.get("request_fingerprint"))
        and isinstance(t15_report.get("proposal"), dict),
        "T15 bounded proposal report is invalid.",
    )

    require(
        isinstance(t17_report, dict)
        and t17_report.get("decision") == "ANALYZE"
        and t17_report.get("ready_for_handoff") is True
        and not t17_report.get("unknown_paths")
        and not t17_report.get("protected_paths")
        and valid_fingerprint(t17_report.get("fingerprint"))
        and isinstance(t17_report.get("changed_paths"), (list, tuple))
        and bool(t17_report.get("changed_paths")),
        "T17 exact-path impact report is invalid.",
    )

    normalized_t17_paths = {
        str(path).casefold()
        for path in t17_report["changed_paths"]
    }
    normalized_expected_paths = {
        path.casefold()
        for path in EXPECTED_SOURCE_PATHS
    }
    require(
        normalized_t17_paths == normalized_expected_paths,
        "T17 analyzed paths differ from the exact owner approval record path.",
    )

    require(
        isinstance(authorization, dict)
        and authorization.get("decision") == "AUTHORIZE"
        and authorization.get("execution_authorized") is True
        and authorization.get("state_mutated") is False
        and authorization.get("requires_external_executor") is True
        and valid_fingerprint(
            authorization.get("authorization_fingerprint")
        )
        and valid_fingerprint(authorization.get("request_fingerprint")),
        "T18 external-executor authorization is invalid.",
    )

    candidate = copy.deepcopy(state)
    change_requests = candidate.get("change_requests")

    require(
        isinstance(change_requests, list),
        "Canonical change_requests list is invalid.",
    )
    require(
        not any(
            isinstance(item, dict)
            and item.get("id") == CHANGE_REQUEST_ID
            for item in change_requests
        ),
        "CORE-001 approval request already exists; duplicate approval denied.",
    )

    change_request = {
        "id": CHANGE_REQUEST_ID,
        "type": "CORE001_AUTHORIZATION_OWNER_EXTENSION",
        "title": (
            "Approve bounded CORE-001 identity and resource/action "
            "authorization owner extension"
        ),
        "status": "APPROVED",
        "requested_at": timestamp,
        "approved_at": timestamp,
        "requested_by": approval_record["actor"],
        "approved_by": approval_record["actor"],
        "scope": {
            "gate": "BACKEND-001",
            "task": "BACKEND-001-B2-PRODUCTION-BINDING",
            "request_document": REQUEST_PATH,
            "request_id": CHANGE_REQUEST_ID,
            "approved_items": [
                "T01 canonical identity/account resolution and explicit cardinality.",
                "B3 trusted-context and private resource/action authorization operation.",
                "One resource/action decision owner inside existing CORE-001.",
                "Default-deny behavior based on complete canonical grants and prerequisites.",
                "No explicit-deny model added to the T03 membership data contract.",
                "Approved trusted assurance and attribute sources.",
                "Canonical role-isolation fixtures and adversarial regression tests.",
                "Exact source paths, contract updates and test coverage in the request.",
                "A separate guarded approval boundary using existing T15/T17/T18.",
            ],
            "production_customer_routes_enabled": False,
            "b2_task_completed": False,
            "backend_acceptance_criteria_completed": False,
        },
        "source_baseline": {
            "repository_head": baseline_sha,
            "owner_source_commit": source_sha,
            "state_blob_sha": state_blob_sha,
            "backend_master_blob_sha": master_blob_sha,
            "request_document_blob_sha": request_blob_sha,
        },
        "operator_proposal": {
            "decision": t15_report["decision"],
            "request_fingerprint": t15_report["request_fingerprint"],
            "proposal": t15_report["proposal"],
        },
        "impact_review": {
            "decision": t17_report["decision"],
            "fingerprint": t17_report["fingerprint"],
            "changed_paths": list(t17_report["changed_paths"]),
            "unknown_paths": list(t17_report["unknown_paths"]),
            "protected_paths": list(t17_report["protected_paths"]),
        },
        "execution_authorization": {
            "decision": authorization["decision"],
            "authorization_fingerprint": (
                authorization["authorization_fingerprint"]
            ),
            "request_fingerprint": authorization["request_fingerprint"],
            "external_executor_required": True,
            "state_mutated_by_guard": False,
        },
        "owner_approval": {
            "method": "GitHub Actions OIDC + repository-owner push",
            "actor": approval_record["actor"],
            "actor_id": approval_record["actor_id"],
            "owner_id": approval_record["owner_id"],
            "repository_id": approval_record["repository_id"],
            "source_commit": approval_record["source_commit"],
            "commit_prefix": APPROVAL_PREFIX,
            "oidc_issuer": approval_record["oidc_issuer"],
            "oidc_subject": approval_record["oidc_subject"],
            "actions_run_id": approval_record["actions_run_id"],
            "bearer_token_persisted": False,
        },
    }

    change_requests.append(change_request)
    return candidate


def verify_current_state_projection_only(state: dict) -> None:
    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get(BACKEND_GATE_ID, {})

    require(
        execution.get("current_gate") == BACKEND_GATE_ID
        and execution.get("current_subtask")
        == "BACKEND-001-B2-PRODUCTION-BINDING"
        and execution.get("status") == "CONTROL_CENTER_DRIVEN",
        "Approval transition changed the current execution task.",
    )
    require(
        gate.get("status") == "CURRENT"
        and gate.get("current_subtask")
        == "BACKEND-001-B2-PRODUCTION-BINDING",
        "Approval transition changed the backend gate projection.",
    )

    subtasks = gate.get("subtasks", [])
    statuses = {
        item.get("id"): item.get("status")
        for item in subtasks
        if isinstance(item, dict)
    }
    require(
        statuses == expected_stage_statuses(),
        "Approval transition changed one or more backend stage statuses.",
    )
    require(
        all(
            item.get("status") == "PENDING"
            for item in gate.get("criteria_state", [])
        ),
        "Approval transition changed backend acceptance criteria.",
    )


def validate_approved_state(state: dict, *, expected_source_sha: str) -> None:
    require(
        state.get("integrity", {}).get("sha256")
        == controller.calculate_hash(state),
        "Post-transition canonical state integrity is invalid.",
    )

    verify_current_state_projection_only(state)

    matches = [
        item
        for item in state.get("change_requests", [])
        if isinstance(item, dict)
        and item.get("id") == CHANGE_REQUEST_ID
    ]
    require(
        len(matches) == 1 and matches[0].get("status") == "APPROVED",
        "CORE-001 change-request approval was not persisted exactly once.",
    )

    approval = matches[0].get("owner_approval", {})
    require(
        approval.get("source_commit") == expected_source_sha,
        "Persisted owner approval source SHA differs from verified SHA.",
    )
    require(
        approval.get("commit_prefix") == APPROVAL_PREFIX,
        "Persisted owner approval prefix is invalid.",
    )
    require(
        approval.get("bearer_token_persisted") is False,
        "OIDC bearer token persistence boundary was violated.",
    )


def write_evidence(
    *,
    source_sha: str,
    run_id: str,
    run_attempt: str,
    state_blob_sha: str,
    master_blob_sha: str,
    request_blob_sha: str,
    t15_report: dict,
    t17_report: dict,
    authorization: dict,
    approval_record: dict,
) -> None:
    lines = [
        "# B2 CORE-001 Authorization Change-Request Approval Evidence",
        "",
        f"- Change request: `{CHANGE_REQUEST_ID}`",
        "- Approval result: **APPROVED — BOUNDED CHANGE SCOPE ONLY**",
        f"- Owner approval record: `{APPROVAL_RECORD_PATH}`",
        f"- Verified owner source commit: `{source_sha}`",
        f"- GitHub Actions run: `{run_id}`",
        f"- GitHub Actions attempt: `{run_attempt}`",
        f"- State baseline blob SHA: `{state_blob_sha}`",
        f"- Backend master blob SHA: `{master_blob_sha}`",
        f"- Request document blob SHA: `{request_blob_sha}`",
        "",
        "## T15 / T17 / T18",
        "",
        "- T15 decision: `PROPOSE`",
        f"- T15 request fingerprint: `{t15_report['request_fingerprint']}`",
        "- T17 decision: `ANALYZE`",
        f"- T17 impact fingerprint: `{t17_report['fingerprint']}`",
        f"- T17 changed paths: `{len(t17_report['changed_paths'])}`",
        "- T17 unknown paths: `0`",
        "- T17 protected paths: `0`",
        "- T18 decision: `AUTHORIZE`",
        (
            "- T18 authorization fingerprint: "
            f"`{authorization['authorization_fingerprint']}`"
        ),
        f"- OIDC issuer: `{approval_record['oidc_issuer']}`",
        f"- OIDC subject: `{approval_record['oidc_subject']}`",
        "- Repository owner identity: cryptographically verified",
        "- OIDC bearer token persisted: **NO**",
        "",
        "## Preserved execution state",
        "",
        "- BACKEND-001-B0 through B4: `DONE`",
        "- BACKEND-001-B2-PRODUCTION-BINDING: `CURRENT`",
        "- B2 Production Binding: `CURRENT`",
        "- BACKEND-001-B5 through B10: `PENDING`",
        "- BACKEND-001-AC01 through AC10: `PENDING`",
        "- Production customer routes enabled: **NO**",
        "- B2 completion claimed: **NO**",
        "- Production readiness claimed: **NO**",
        "",
        "## State ownership",
        "",
        "- State writer: existing HOMIO Control Center",
        "- Manual state.json editing: **NOT PERFORMED**",
        "- Duplicate identity, authorization or persistence owner: **NOT CREATED**",
        "",
    ]

    evidence = ROOT / EVIDENCE_PATH
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    expected_sha = os.environ.get("EXPECTED_SHA", "")
    require(valid_sha(expected_sha), "EXPECTED_SHA is invalid.")

    owner_event = verify_owner_push(expected_sha)
    changed_paths = verify_source_baseline(expected_sha)

    state = controller.load_state()
    verify_current_state(state)

    state_blob_sha = file_blob_sha(STATE_PATH, expected_sha)
    master_blob_sha = file_blob_sha(MASTER_PATH, expected_sha)
    request_blob_sha = file_blob_sha(REQUEST_PATH, expected_sha)

    t15_report, t17_report, authorization, approval_record = (
        authorize_change_request(
            expected_sha=expected_sha,
            state_blob_sha=state_blob_sha,
            master_blob_sha=master_blob_sha,
            request_blob_sha=request_blob_sha,
            changed_paths=changed_paths,
            owner_event=owner_event,
        )
    )

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    candidate = build_approved_state(
        state,
        timestamp=timestamp,
        baseline_sha=BASELINE_HEAD,
        source_sha=expected_sha,
        state_blob_sha=state_blob_sha,
        master_blob_sha=master_blob_sha,
        request_blob_sha=request_blob_sha,
        t15_report=t15_report,
        t17_report=t17_report,
        authorization=authorization,
        approval_record=approval_record,
    )

    controller.emit(
        candidate,
        "BACKEND_CHANGE_REQUEST_APPROVED",
        {
            "change_request": CHANGE_REQUEST_ID,
            "source_commit": expected_sha,
            "t15_request_fingerprint": (
                t15_report["request_fingerprint"]
            ),
            "t17_fingerprint": t17_report["fingerprint"],
            "t18_authorization_fingerprint": (
                authorization["authorization_fingerprint"]
            ),
            "production_customer_routes_enabled": False,
            "b2_task_completed": False,
        },
    )

    # Existing Control Center is the sole canonical state writer.
    controller.build_handoff_packet(candidate)
    controller.save_state(candidate)

    saved_state_blob_sha = file_blob_sha(STATE_PATH)

    write_evidence(
        source_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
        run_attempt=os.environ["ACTIONS_RUN_ATTEMPT"],
        state_blob_sha=saved_state_blob_sha,
        master_blob_sha=master_blob_sha,
        request_blob_sha=request_blob_sha,
        t15_report=t15_report,
        t17_report=t17_report,
        authorization=authorization,
        approval_record=approval_record,
    )

    expected_tracked = {
        STATE_PATH,
        PACKET_PATH,
        HANDOFF_PATH,
    }
    actual_tracked = set(
        run(["git", "diff", "--name-only"], display=False).splitlines()
    )
    require(
        actual_tracked == expected_tracked,
        (
            "Control Center tracked-path allowlist mismatch: "
            f"{sorted(actual_tracked)}"
        ),
    )

    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

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

    snapshot_candidates = [
        item
        for item in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/"
            r"state_\d{8}_\d{6}_\d{6}\.json",
            item,
        )
    ]

    require(
        len(untracked) == 2
        and len(snapshot_candidates) == 1
        and EVIDENCE_PATH in untracked,
        f"Unexpected Control Center untracked inventory: {untracked}",
    )

    snapshot_data = json.loads(
        (ROOT / snapshot_candidates[0]).read_text(encoding="utf-8")
    )
    require(
        snapshot_data.get("integrity", {}).get("sha256")
        == controller.calculate_hash(snapshot_data),
        "Control Center snapshot integrity is invalid.",
    )

    staged_paths = sorted(
        expected_tracked
        | {
            EVIDENCE_PATH,
            snapshot_candidates[0],
        }
    )

    run(["git", "add", "--", *staged_paths])
    run([
        "git",
        "-c",
        "core.whitespace=cr-at-eol",
        "diff",
        "--cached",
        "--check",
    ])

    actual_staged = set(
        run(
            ["git", "diff", "--cached", "--name-only"],
            display=False,
        ).splitlines()
    )
    require(
        actual_staged == set(staged_paths),
        "Staged Control Center transition path allowlist mismatch.",
    )

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            (
                "user.email="
                "41898282+github-actions[bot]@users.noreply.github.com"
            ),
            "commit",
            "-m",
            (
                "chore(control-center): approve bounded B2 CORE-001 "
                "authorization request"
            ),
        ],
        capture=False,
    )

    transition_sha = run(["git", "rev-parse", "HEAD"], display=False)
    require(
        run(["git", "rev-parse", "HEAD^"], display=False) == expected_sha,
        "Transition commit parent differs from verified owner SHA.",
    )

    run(
        ["git", "push", "origin", f"HEAD:refs/heads/{BRANCH}"],
        capture=False,
    )
    run(
        ["git", "fetch", "--no-tags", "origin", BRANCH_REF],
        capture=False,
    )

    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"], display=False)
    require(
        remote_sha == transition_sha,
        "Canonical branch readback differs from transition commit.",
    )

    remote_state = json.loads(
        run(
            ["git", "show", f"{remote_sha}:{STATE_PATH}"],
            display=False,
        )
    )
    validate_approved_state(
        remote_state,
        expected_source_sha=expected_sha,
    )

    remote_state_blob_sha = run(
        ["git", "rev-parse", f"{remote_sha}:{STATE_PATH}"],
        display=False,
    )
    require(
        remote_state_blob_sha == saved_state_blob_sha,
        "Remote canonical state blob SHA differs from saved state.",
    )

    remote_evidence = run(
        ["git", "show", f"{remote_sha}:{EVIDENCE_PATH}"],
        display=False,
    )
    for marker in (
        CHANGE_REQUEST_ID,
        APPROVAL_RECORD_PATH,
        expected_sha,
        t15_report["request_fingerprint"],
        t17_report["fingerprint"],
        authorization["authorization_fingerprint"],
        saved_state_blob_sha,
        "B2 Production Binding: `CURRENT`",
        "BACKEND-001-AC01 through AC10: `PENDING`",
    ):
        require(
            marker in remote_evidence,
            f"Remote approval evidence is missing marker: {marker}",
        )

    for relative in (PACKET_PATH, HANDOFF_PATH):
        remote_packet = run(
            ["git", "show", f"{remote_sha}:{relative}"],
            display=False,
        )
        require(
            "BACKEND-001-B2-PRODUCTION-BINDING" in remote_packet,
            f"Remote {relative} lost the current B2 task projection.",
        )

    print(f"B2_APPROVAL_SOURCE_COMMIT={expected_sha}")
    print(f"B2_APPROVAL_RUN_ID={os.environ['ACTIONS_RUN_ID']}")
    print(f"B2_APPROVAL_TRANSITION_COMMIT={transition_sha}")
    print(f"B2_APPROVAL_REMOTE_HEAD={remote_sha}")
    print(f"B2_APPROVAL_STATE_BLOB_SHA={remote_state_blob_sha}")
    print("B2_CORE001_T15_T17_T18=PASS")
    print("B2_CORE001_CHANGE_REQUEST=APPROVED")
    print("B2_PRODUCTION_BINDING=REMAINS_CURRENT")
    print("BACKEND_ACCEPTANCE_CRITERIA=REMAINS_PENDING")
    print("PRODUCTION_CUSTOMER_ROUTES=NOT_ENABLED")


if __name__ == "__main__":
    main()
