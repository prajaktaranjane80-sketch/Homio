from __future__ import annotations

import copy
import re
from typing import Any


BACKEND_GATE_ID = "BACKEND-001"
BACKEND_CHANGE_REQUEST_ID = "CR-BACKEND-001"
BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID = (
    "CR-BACKEND-001-B2-DEPENDENCY"
)

BACKEND_TECHNICAL_SEQUENCE = (
    "B0 -> B1 -> B2-FOUNDATION -> B3 -> B4 -> "
    "B2-PRODUCTION-BINDING -> B5 -> B6 -> B7 -> B8 -> B9 -> B10"
)

BACKEND_STAGES = (
    (
        "B0",
        "Live repository audit and ownership verification",
        "CRITICAL",
    ),
    (
        "B1",
        "Backend application foundation",
        "CRITICAL",
    ),
    (
        "B2-FOUNDATION",
        "API security and trusted context — foundation",
        "CRITICAL",
    ),
    (
        "B3",
        "Python domain-runtime bridge",
        "CRITICAL",
    ),
    (
        "B4",
        "PostgreSQL integration",
        "CRITICAL",
    ),
    (
        "B2-PRODUCTION-BINDING",
        "API security and trusted context — production binding",
        "CRITICAL",
    ),
    (
        "B5",
        "Domain API adapters",
        "CRITICAL",
    ),
    (
        "B6",
        "Event and durable workflow integration",
        "HIGH",
    ),
    (
        "B7",
        "Search, AI and provider integration",
        "HIGH",
    ),
    (
        "B8",
        "Complete customer and business journeys",
        "CRITICAL",
    ),
    (
        "B9",
        "Production operations",
        "CRITICAL",
    ),
    (
        "B10",
        "Release verification and final freeze approval",
        "CRITICAL",
    ),
)

B1_ACCEPTANCE_CRITERIA = [
    "Build is reproducible.",
    "Invalid runtime configuration fails safely.",
    "Health and readiness semantics are tested.",
    "Graceful shutdown is tested.",
    "No duplicate public API application exists.",
]

B2_FOUNDATION_ACCEPTANCE_CRITERIA = [
    "One Fastify /api/v1 ingress security boundary is used.",
    "Bearer authentication is verified before protected handlers.",
    "Trusted principal and tenant context are server-derived and minimized.",
    "Protected routes declare valid security metadata and mutation schemas.",
    "All six security adapter ports are mandatory and fail closed when absent.",
    "Protected mutations are reauthorized immediately before handlers.",
    "Security boundary tests cover invalid credentials, missing adapters, "
    "authorization failures, rate-limit ordering and audit ordering.",
]

B3_ACCEPTANCE_CRITERIA = [
    "Private TypeScript-to-Python runtime transport is authenticated.",
    "Request and response contracts are versioned and validated.",
    "Trusted actor, tenant and correlation context are preserved.",
    "Timeout, cancellation and failure classification are tested.",
    "Ambiguous mutation outcomes use durable idempotency identity.",
    "No Python business logic is copied into TypeScript.",
    "No second public Python API is exposed.",
]

B4_ACCEPTANCE_CRITERIA = [
    "Only the approved ARCH-037 schema and canonical owners are used.",
    "Migrations have deterministic ordering and integrity checks.",
    "Tenant access is enforced by the target persistence boundary.",
    "Repositories and transaction boundaries have explicit write ownership.",
    "Durable session and revocation storage is supported.",
    "Shared rate-limit state and minimized audit persistence are supported.",
    "Migration, concurrency, backup and recovery tests pass.",
    "No second schema or persistence authority is introduced.",
]

B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA = [
    "The approved OIDC verifier is connected through the authenticated B3 boundary.",
    "Durable session and revocation validation is connected through B4.",
    "Trusted identity, tenant and active membership are resolved through CORE-001.",
    "One contract-governed CORE-001 resource/action decision owner is used; "
    "the T03 membership data contract remains data-only.",
    "Shared/distributed rate limiting is connected through B4.",
    "Durable PII-minimized security audit persistence is connected through B4.",
    "Buyer, broker, builder and privileged-role isolation tests pass.",
    "Cross-tenant, revoked-session and unauthorized-action tests pass.",
    "Mutation authorization is revalidated immediately before protected handlers.",
    "Rate-limit enforcement works across instances.",
    "Audit persistence occurs before protected handlers.",
    "Invalid credentials and dependency outages fail closed.",
    "No frontend cookie is accepted as an API identity credential.",
    "No production mock, no-op adapter or in-process-only security store remains.",
]

BACKEND_ACCEPTANCE_CRITERIA = [
    "One reproducible public Fastify API application exists.",
    "Protected routes enforce trusted identity and tenant context.",
    "Python integration uses one authenticated private runtime boundary.",
    "Persistence follows approved schema and one write owner per aggregate.",
    "Adapters preserve canonical CORE domain ownership.",
    "Events and durable workflows have tested retry and recovery behavior.",
    "Search and AI integrations preserve authorization and source provenance.",
    "Critical customer and business journeys pass end-to-end.",
    "Production operational controls have current evidence.",
    "Release verification and accountable approval are complete.",
]


class BackendWorkstreamTransitionError(ValueError):
    """Raised when a backend workstream transition is unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BackendWorkstreamTransitionError(message)


def _valid_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{40}", value) is not None
    )


def _valid_fingerprint(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    )


def _build_backend_gate_plan(
    *,
    timestamp: str,
    baseline_sha: str,
    evidence_path: str,
) -> dict[str, Any]:
    stage_acceptance = {
        "B1": B1_ACCEPTANCE_CRITERIA,
        "B2-FOUNDATION": B2_FOUNDATION_ACCEPTANCE_CRITERIA,
        "B3": B3_ACCEPTANCE_CRITERIA,
        "B4": B4_ACCEPTANCE_CRITERIA,
        "B2-PRODUCTION-BINDING": (
            B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
        ),
    }

    subtasks: list[dict[str, Any]] = []

    for stage_id, title, priority in BACKEND_STAGES:
        status = "PENDING"

        if stage_id == "B0":
            status = "DONE"
        elif stage_id == "B1":
            status = "CURRENT"

        item: dict[str, Any] = {
            "id": f"{BACKEND_GATE_ID}-{stage_id}",
            "title": title,
            "priority": priority,
            "status": status,
        }

        if stage_id == "B0":
            item["completed_at"] = timestamp
            item["note"] = (
                "Read-only B0 audit recorded in "
                f"{evidence_path}; baseline {baseline_sha}. "
                "No backend source code was modified during B0."
            )

        if stage_id in stage_acceptance:
            item["acceptance_criteria"] = list(
                stage_acceptance[stage_id]
            )

        subtasks.append(item)

    criteria_state = [
        {
            "id": f"{BACKEND_GATE_ID}-AC{index:02d}",
            "criterion": criterion,
            "status": "PENDING",
            "evidence": None,
            "verified_at": None,
        }
        for index, criterion in enumerate(
            BACKEND_ACCEPTANCE_CRITERIA,
            start=1,
        )
    ]

    return {
        "id": BACKEND_GATE_ID,
        "name": "Unified HOMIO / REOS Backend",
        "objective": (
            "Establish and verify one unified public backend through "
            "the guarded B0-B10 sequence and B2 production dependency "
            "correction in HOMIO_Backend_Structure."
        ),
        "status": "CURRENT",
        "current_subtask": f"{BACKEND_GATE_ID}-B1",
        "subtasks": subtasks,
        "acceptance_criteria": list(BACKEND_ACCEPTANCE_CRITERIA),
        "criteria_state": criteria_state,
        "completion_policy": (
            "All blocking subtasks DONE + all criteria VERIFIED "
            "+ explicit approval."
        ),
        "created_at": timestamp,
        "technical_master": (
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "HOMIO_Backend_Structure"
        ),
        "technical_sequence": BACKEND_TECHNICAL_SEQUENCE,
        "workstream": "BACKEND",
        "baseline": {
            "repository_head": baseline_sha,
            "b0_evidence": evidence_path,
        },
    }


def activate_backend_workstream_state(
    state: dict[str, Any],
    *,
    timestamp: str,
    baseline_sha: str,
    master_blob_sha: str,
    work_plan_blob_sha: str,
    b0_evidence_path: str,
    approval_record: dict[str, Any],
    t15_report: dict[str, Any],
    t17_report: dict[str, Any],
    authorization: dict[str, Any],
) -> dict[str, Any]:
    """Return a validated new state with BACKEND-001 selected.

    This function does not write files or persist state. The existing
    Control Center remains the only persistence owner.
    """
    _require(isinstance(state, dict), "Canonical state must be an object.")
    _require(bool(timestamp), "Transition timestamp is required.")
    _require(_valid_sha(baseline_sha), "Invalid baseline commit SHA.")
    _require(_valid_sha(master_blob_sha), "Invalid backend master blob SHA.")
    _require(_valid_sha(work_plan_blob_sha), "Invalid work-plan blob SHA.")

    execution = state.get("execution")
    _require(isinstance(execution, dict), "Canonical execution object missing.")
    _require(
        execution.get("current_gate") == "APP-001",
        "APP-001 must be the current gate before backend activation.",
    )
    _require(
        execution.get("current_subtask") == "APP-001-T01",
        "APP-001-T01 must remain the active frontend subtask before activation.",
    )
    _require(
        execution.get("status") == "CONTROL_CENTER_DRIVEN",
        "Unexpected execution status; refusing workstream transition.",
    )

    gate_plans = state.get("gate_plans")
    _require(isinstance(gate_plans, dict), "Canonical gate_plans missing.")
    app_gate = gate_plans.get("APP-001")
    _require(isinstance(app_gate, dict), "APP-001 gate plan missing.")
    _require(
        app_gate.get("status") == "CURRENT",
        "APP-001 gate must be CURRENT before backend activation.",
    )
    _require(
        app_gate.get("current_subtask") == "APP-001-T01",
        "APP-001-T01 cannot be reconstructed safely.",
    )

    app_subtasks = {
        item.get("id"): item
        for item in app_gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    _require(
        app_subtasks.get("APP-001-T01", {}).get("status") == "CURRENT",
        "APP-001-T01 is not CURRENT in its gate plan.",
    )

    _require(
        BACKEND_GATE_ID not in gate_plans,
        "BACKEND-001 already exists; duplicate activation is forbidden.",
    )

    architecture = state.get("architecture")
    _require(isinstance(architecture, dict), "Architecture registry missing.")
    _require(
        architecture.get("locked") is False,
        "Architecture lock is not in the expected pre-transition state.",
    )

    pending = architecture.get("pending")
    approved = architecture.get("approved")
    _require(isinstance(pending, list), "Architecture pending registry missing.")
    _require(isinstance(approved, list), "Architecture approved registry missing.")

    arch039_pending = [
        item
        for item in pending
        if isinstance(item, dict) and item.get("id") == "ARCH-039"
    ]
    _require(
        len(arch039_pending) == 1,
        "ARCH-039 must exist exactly once in architecture.pending.",
    )
    _require(
        arch039_pending[0].get("status") == "PENDING",
        "ARCH-039 pending status differs from the audited baseline.",
    )
    _require(
        not any(
            isinstance(item, dict) and item.get("id") == "ARCH-039"
            for item in approved
        ),
        "ARCH-039 is already approved; reconciliation is not applicable.",
    )

    execution_plan = state.get("execution_plan")
    _require(isinstance(execution_plan, dict), "Execution plan missing.")
    sequence = execution_plan.get("authoritative_sequence")
    _require(isinstance(sequence, list), "Authoritative sequence missing.")

    _require(
        all(
            isinstance(item, dict)
            and isinstance(item.get("gate"), str)
            and bool(item.get("gate"))
            for item in sequence
        ),
        "Authoritative sequence contains an invalid gate entry.",
    )
    gates = [item["gate"] for item in sequence]
    _require(
        len(gates) == len(set(gates)),
        "Authoritative sequence contains duplicate gate identifiers.",
    )
    _require(
        "AI-001" in gates and "APP-001" in gates,
        "AI-001 or APP-001 is missing from the authoritative sequence.",
    )
    _require(
        BACKEND_GATE_ID not in gates,
        "BACKEND-001 already exists in the authoritative sequence.",
    )

    ai_index = gates.index("AI-001")
    app_index = gates.index("APP-001")
    _require(
        app_index == ai_index + 1,
        "AI-001 and APP-001 order changed; impact must be reassessed.",
    )

    dependencies = state.get("dependencies")
    _require(
        isinstance(dependencies, dict),
        "Canonical dependencies graph missing.",
    )
    dependency_nodes = dependencies.get("nodes")
    dependency_edges = dependencies.get("edges")
    _require(
        isinstance(dependency_nodes, list),
        "Canonical dependency nodes must be a list.",
    )
    _require(
        isinstance(dependency_edges, list),
        "Canonical dependency edges must be a list.",
    )

    node_ids: list[str] = []
    for node in dependency_nodes:
        _require(
            isinstance(node, dict)
            and isinstance(node.get("id"), str)
            and bool(node.get("id")),
            "Dependency graph contains an invalid node.",
        )
        node_ids.append(node["id"])

    _require(
        len(node_ids) == len(set(node_ids)),
        "Dependency graph contains duplicate nodes.",
    )
    _require(
        set(node_ids) == set(gates),
        "Dependency graph node inventory differs from the authoritative sequence.",
    )

    normalized_edges: list[tuple[str, str]] = []
    for edge in dependency_edges:
        _require(
            isinstance(edge, list)
            and len(edge) == 2
            and all(isinstance(part, str) and part for part in edge),
            "Dependency graph contains an invalid edge.",
        )
        normalized_edges.append((edge[0], edge[1]))

    expected_edges = list(zip(gates, gates[1:]))
    _require(
        len(normalized_edges) == len(set(normalized_edges)),
        "Dependency graph contains duplicate edges.",
    )
    _require(
        normalized_edges == expected_edges,
        "Dependency graph edges do not match the authoritative sequence.",
    )

    ai_item = sequence[ai_index]
    app_item = sequence[app_index]
    _require(
        ai_item.get("status") == "COMPLETE",
        "AI-001 must remain COMPLETE.",
    )
    _require(
        app_item.get("status") == "CURRENT",
        "APP-001 must remain CURRENT before activation.",
    )

    for gate_id in ("REL-001", "SCALE-001"):
        item = next(
            (
                entry
                for entry in sequence
                if isinstance(entry, dict)
                and entry.get("gate") == gate_id
            ),
            None,
        )
        _require(
            isinstance(item, dict) and item.get("status") == "FUTURE",
            f"{gate_id} must remain FUTURE.",
        )

    _require(
        isinstance(approval_record, dict),
        "Owner approval record is missing.",
    )
    _require(
        approval_record.get("actor") == "prajaktaranjane80-sketch",
        "Approval actor is not the repository owner.",
    )
    _require(
        bool(approval_record.get("source_commit")),
        "Owner approval source commit is missing.",
    )
    _require(
        isinstance(t15_report, dict)
        and t15_report.get("decision") == "PROPOSE"
        and t15_report.get("execution_authorized") is False,
        "T15 proposal is invalid or already execution-authorized.",
    )
    _require(
        isinstance(t17_report, dict)
        and t17_report.get("decision") == "ANALYZE"
        and not t17_report.get("unknown_paths")
        and not t17_report.get("protected_paths"),
        "T17 impact report is not clear for this change.",
    )
    _require(
        isinstance(authorization, dict)
        and authorization.get("decision") == "AUTHORIZE"
        and authorization.get("execution_authorized") is True
        and authorization.get("state_mutated") is False
        and authorization.get("requires_external_executor") is True,
        "T18 did not authorize the external Control Center transition.",
    )

    existing_requests = state.get("change_requests", [])
    _require(
        isinstance(existing_requests, list),
        "Canonical change_requests must be a list.",
    )
    _require(
        not any(
            isinstance(item, dict)
            and item.get("id") == BACKEND_CHANGE_REQUEST_ID
            for item in existing_requests
        ),
        "Backend activation change request already exists.",
    )

    candidate = copy.deepcopy(state)
    candidate.setdefault("change_requests", [])

    # Reconcile the previously validated ARCH-039 snapshot using the
    # owner approval and guarded T15/T17/T18 evidence from this transition.
    candidate_architecture = candidate["architecture"]
    arch039 = next(
        item
        for item in candidate_architecture["pending"]
        if item.get("id") == "ARCH-039"
    )
    candidate_architecture["pending"].remove(arch039)

    approved_arch039 = dict(arch039)
    approved_arch039["status"] = "APPROVED"
    approved_arch039["approved_at"] = timestamp
    approved_arch039["approval_evidence"] = {
        "source": "guarded backend workstream activation",
        "owner": approval_record["actor"],
        "source_commit": approval_record["source_commit"],
        "authorization_fingerprint": authorization[
            "authorization_fingerprint"
        ],
    }
    candidate_architecture["approved"].append(approved_arch039)
    candidate_architecture["locked"] = True

    # Insert the backend workstream immediately after AI-001 and before
    # APP-001. Existing APP-001-T01 remains intact and is resumed later.
    new_sequence = copy.deepcopy(
        candidate["execution_plan"]["authoritative_sequence"]
    )
    app_index = next(
        index
        for index, item in enumerate(new_sequence)
        if item.get("gate") == "APP-001"
    )
    new_sequence.insert(
        app_index,
        {
            "id": "PLAN-016",
            "gate": BACKEND_GATE_ID,
            "name": "Unified HOMIO / REOS Backend",
            "status": "CURRENT",
        },
    )

    for index, item in enumerate(new_sequence, start=1):
        item["id"] = f"PLAN-{index:03d}"
        if item.get("gate") == BACKEND_GATE_ID:
            item["status"] = "CURRENT"
        elif item.get("gate") == "APP-001":
            item["status"] = "FUTURE"

    candidate["execution_plan"]["authoritative_sequence"] = new_sequence

    # Synchronize gate-plan and dependency-graph projections from the
    # authoritative sequence. APP-001-T01 remains CURRENT for later resume.
    candidate["gate_plans"]["APP-001"]["status"] = "FUTURE"

    dependency_nodes_by_id = {
        item["id"]: dict(item)
        for item in candidate["dependencies"]["nodes"]
    }
    dependency_nodes_by_id[BACKEND_GATE_ID] = {
        "id": BACKEND_GATE_ID,
        "status": "CURRENT",
    }
    candidate["dependencies"]["nodes"] = [
        {
            **dependency_nodes_by_id[item["gate"]],
            "status": item["status"],
        }
        for item in new_sequence
    ]
    candidate["dependencies"]["edges"] = [
        [left["gate"], right["gate"]]
        for left, right in zip(new_sequence, new_sequence[1:])
    ]

    candidate["gate_plans"][BACKEND_GATE_ID] = _build_backend_gate_plan(
        timestamp=timestamp,
        baseline_sha=baseline_sha,
        evidence_path=b0_evidence_path,
    )

    candidate["execution"]["current_gate"] = BACKEND_GATE_ID
    candidate["execution"]["current_subtask"] = (
        f"{BACKEND_GATE_ID}-B1"
    )
    candidate["execution"]["current_task"] = (
        f"{BACKEND_GATE_ID}-B1: Backend application foundation."
    )
    candidate["execution"]["status"] = "CONTROL_CENTER_DRIVEN"
    candidate["execution"]["current_acceptance_criteria"] = list(
        B1_ACCEPTANCE_CRITERIA
    )

    change_request = {
        "id": BACKEND_CHANGE_REQUEST_ID,
        "type": "WORKSTREAM_ACTIVATION",
        "title": "Activate unified HOMIO / REOS backend execution",
        "status": "APPROVED",
        "requested_at": timestamp,
        "approved_at": timestamp,
        "requested_by": approval_record["actor"],
        "approved_by": approval_record["actor"],
        "scope": {
            "workstream": "BACKEND",
            "gate": BACKEND_GATE_ID,
            "first_subtask": f"{BACKEND_GATE_ID}-B1",
            "technical_master": (
                "REOS_CONTROL_CENTER/architecture/backend/plans/"
                "HOMIO_Backend_Structure"
            ),
            "delivery_contract": "REOS_CONTROL_CENTER/plan for work",
            "sequence": BACKEND_TECHNICAL_SEQUENCE,
            "architecture_reconciliation": "ARCH-039",
        },
        "source_baseline": {
            "repository_head": baseline_sha,
            "state_blob_sha": approval_record["state_blob_sha"],
            "backend_master_blob_sha": master_blob_sha,
            "work_plan_blob_sha": work_plan_blob_sha,
            "b0_evidence_path": b0_evidence_path,
        },
        "impact_review": {
            "decision": t17_report["decision"],
            "fingerprint": t17_report["fingerprint"],
            "changed_paths": list(t17_report["changed_paths"]),
            "unknown_paths": list(t17_report["unknown_paths"]),
            "protected_paths": list(t17_report["protected_paths"]),
        },
        "operator_proposal": {
            "decision": t15_report["decision"],
            "request_fingerprint": t15_report["request_fingerprint"],
            "proposal": t15_report["proposal"],
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
            "source_commit": approval_record["source_commit"],
            "commit_prefix": (
                "[CONTROL-CENTER-ACTIVATE-BACKEND-001]"
            ),
            "oidc_issuer": approval_record["oidc_issuer"],
            "oidc_subject": approval_record["oidc_subject"],
            "actions_run_id": approval_record["actions_run_id"],
        },
        "preserved_work": {
            "gate": "APP-001",
            "subtask": "APP-001-T01",
            "status": "PRESERVED_FOR_RESUMPTION",
            "resume_after": BACKEND_GATE_ID,
        },
    }

    candidate["change_requests"].append(change_request)

    return candidate


def correct_backend_b2_dependency_state(
    state: dict[str, Any],
    *,
    timestamp: str,
    baseline_sha: str,
    master_blob_sha: str,
    approval_record: dict[str, Any],
    t15_report: dict[str, Any],
    t17_report: dict[str, Any],
    authorization: dict[str, Any],
) -> dict[str, Any]:
    """Return a new, validated state with the corrected B2 dependency order.

    The existing Control Center remains the only persistence owner.
    This function is deterministic and does not mutate the input state.
    The guarded runner separately completes B2-FOUNDATION through the
    Control Center after the exact-SHA verification job succeeds.
    """
    _require(isinstance(state, dict), "Canonical state must be an object.")
    _require(bool(timestamp), "Transition timestamp is required.")
    _require(_valid_sha(baseline_sha), "Invalid source baseline SHA.")
    _require(_valid_sha(master_blob_sha), "Invalid corrected master blob SHA.")

    execution = state.get("execution")
    _require(isinstance(execution, dict), "Canonical execution object missing.")
    _require(
        execution.get("current_gate") == BACKEND_GATE_ID,
        "BACKEND-001 must remain the current gate.",
    )
    _require(
        execution.get("current_subtask") == f"{BACKEND_GATE_ID}-B2",
        "Only the currently active original B2 can be re-sequenced.",
    )
    _require(
        execution.get("status") == "CONTROL_CENTER_DRIVEN",
        "Unexpected execution status; refusing dependency correction.",
    )

    gate_plans = state.get("gate_plans")
    _require(isinstance(gate_plans, dict), "Canonical gate_plans missing.")

    gate = gate_plans.get(BACKEND_GATE_ID)
    _require(isinstance(gate, dict), "BACKEND-001 gate plan is missing.")
    _require(
        gate.get("status") == "CURRENT",
        "BACKEND-001 gate must remain CURRENT.",
    )
    _require(
        gate.get("current_subtask") == f"{BACKEND_GATE_ID}-B2",
        "Gate current_subtask does not match the active B2 task.",
    )

    raw_subtasks = gate.get("subtasks")
    _require(isinstance(raw_subtasks, list), "Backend subtasks must be a list.")
    _require(
        all(isinstance(item, dict) for item in raw_subtasks),
        "Backend subtasks contain a malformed entry.",
    )

    subtask_ids = [item.get("id") for item in raw_subtasks]
    _require(
        all(isinstance(value, str) and value for value in subtask_ids),
        "Backend subtask IDs must be non-empty strings.",
    )
    _require(
        len(subtask_ids) == len(set(subtask_ids)),
        "Backend subtasks contain duplicate identifiers.",
    )

    legacy_ids = {
        f"{BACKEND_GATE_ID}-B{number}"
        for number in range(0, 11)
    }
    _require(
        set(subtask_ids) == legacy_ids,
        "Backend subtask inventory is not the exact audited B0-B10 baseline.",
    )

    subtasks = {
        item["id"]: item
        for item in raw_subtasks
    }

    expected_statuses = {
        f"{BACKEND_GATE_ID}-B0": "DONE",
        f"{BACKEND_GATE_ID}-B1": "DONE",
        f"{BACKEND_GATE_ID}-B2": "CURRENT",
        **{
            f"{BACKEND_GATE_ID}-B{number}": "PENDING"
            for number in range(3, 11)
        },
    }

    for subtask_id, expected_status in expected_statuses.items():
        _require(
            subtasks[subtask_id].get("status") == expected_status,
            f"{subtask_id} must be {expected_status} before correction.",
        )

    criteria_state = gate.get("criteria_state")
    _require(
        isinstance(criteria_state, list)
        and len(criteria_state) == len(BACKEND_ACCEPTANCE_CRITERIA),
        "Backend gate-level acceptance criteria inventory changed.",
    )
    _require(
        all(
            isinstance(item, dict)
            and item.get("status") == "PENDING"
            and item.get("evidence") is None
            and item.get("verified_at") is None
            for item in criteria_state
        ),
        "Gate-level acceptance criteria must remain entirely PENDING.",
    )

    _require(
        isinstance(approval_record, dict),
        "OIDC-verified owner approval record is missing.",
    )
    _require(
        approval_record.get("actor") == "prajaktaranjane80-sketch",
        "Approval actor is not the repository owner.",
    )
    _require(
        _valid_sha(approval_record.get("source_commit")),
        "Approval source commit is invalid.",
    )
    _require(
        _valid_sha(approval_record.get("state_blob_sha")),
        "Baseline state blob SHA is invalid.",
    )
    _require(
        approval_record.get("oidc_issuer")
        == "https://token.actions.githubusercontent.com",
        "Approval OIDC issuer is invalid.",
    )
    _require(
        isinstance(approval_record.get("oidc_subject"), str)
        and bool(approval_record["oidc_subject"]),
        "Approval OIDC subject is missing.",
    )
    _require(
        isinstance(approval_record.get("actions_run_id"), str)
        and bool(approval_record["actions_run_id"]),
        "Actions run ID is missing from approval evidence.",
    )

    _require(
        isinstance(t15_report, dict)
        and t15_report.get("decision") == "PROPOSE"
        and t15_report.get("execution_authorized") is False
        and _valid_fingerprint(t15_report.get("request_fingerprint")),
        "T15 bounded proposal is missing or invalid.",
    )
    _require(
        isinstance(t17_report, dict)
        and t17_report.get("decision") == "ANALYZE"
        and t17_report.get("ready_for_handoff") is True
        and not t17_report.get("unknown_paths")
        and not t17_report.get("protected_paths")
        and _valid_fingerprint(t17_report.get("fingerprint"))
        and isinstance(t17_report.get("changed_paths"), (list, tuple))
        and bool(t17_report.get("changed_paths")),
        "T17 exact-path impact report is not clear for handoff.",
    )
    _require(
        isinstance(authorization, dict)
        and authorization.get("decision") == "AUTHORIZE"
        and authorization.get("execution_authorized") is True
        and authorization.get("state_mutated") is False
        and authorization.get("requires_external_executor") is True
        and _valid_fingerprint(
            authorization.get("authorization_fingerprint")
        ),
        "T18 has not authorized the bounded external transition.",
    )

    existing_requests = state.get("change_requests", [])
    _require(
        isinstance(existing_requests, list),
        "Canonical change_requests must be a list.",
    )
    _require(
        not any(
            isinstance(item, dict)
            and item.get("id") == BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID
            for item in existing_requests
        ),
        "B2 dependency correction request already exists.",
    )

    foundation = copy.deepcopy(subtasks[f"{BACKEND_GATE_ID}-B2"])
    foundation["id"] = f"{BACKEND_GATE_ID}-B2-FOUNDATION"
    foundation["title"] = (
        "API security and trusted context — foundation"
    )
    foundation["status"] = "CURRENT"
    foundation["acceptance_criteria"] = list(
        B2_FOUNDATION_ACCEPTANCE_CRITERIA
    )

    production_binding: dict[str, Any] = {
        "id": f"{BACKEND_GATE_ID}-B2-PRODUCTION-BINDING",
        "title": (
            "API security and trusted context — production binding"
        ),
        "priority": "CRITICAL",
        "status": "PENDING",
        "acceptance_criteria": list(
            B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
        ),
    }

    candidate = copy.deepcopy(state)
    candidate_gate = candidate["gate_plans"][BACKEND_GATE_ID]

    corrected_subtasks: list[dict[str, Any]] = []

    for original in raw_subtasks:
        stage_id = original["id"].removeprefix(
            f"{BACKEND_GATE_ID}-"
        )

        if stage_id == "B2":
            corrected_subtasks.append(foundation)
            continue

        item = copy.deepcopy(original)

        if stage_id == "B3":
            item["acceptance_criteria"] = list(
                B3_ACCEPTANCE_CRITERIA
            )
        elif stage_id == "B4":
            item["acceptance_criteria"] = list(
                B4_ACCEPTANCE_CRITERIA
            )

        corrected_subtasks.append(item)

        if stage_id == "B4":
            corrected_subtasks.append(
                copy.deepcopy(production_binding)
            )

    expected_order = [
        f"{BACKEND_GATE_ID}-{stage_id}"
        for stage_id, _, _ in BACKEND_STAGES
    ]

    actual_order = [
        item["id"]
        for item in corrected_subtasks
    ]

    _require(
        actual_order == expected_order,
        "Corrected B2 dependency stage order is inconsistent.",
    )

    candidate_gate["subtasks"] = corrected_subtasks
    candidate_gate["current_subtask"] = (
        f"{BACKEND_GATE_ID}-B2-FOUNDATION"
    )
    candidate_gate["technical_sequence"] = (
        BACKEND_TECHNICAL_SEQUENCE
    )

    candidate["execution"]["current_subtask"] = (
        f"{BACKEND_GATE_ID}-B2-FOUNDATION"
    )
    candidate["execution"]["current_task"] = (
        f"{BACKEND_GATE_ID}-B2-FOUNDATION: "
        "API security and trusted context — foundation."
    )
    candidate["execution"]["status"] = "CONTROL_CENTER_DRIVEN"
    candidate["execution"]["current_acceptance_criteria"] = list(
        B2_FOUNDATION_ACCEPTANCE_CRITERIA
    )

    candidate.setdefault("change_requests", [])

    candidate["change_requests"].append(
        {
            "id": BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID,
            "type": "STAGE_DEPENDENCY_CORRECTION",
            "title": (
                "Correct B2 production dependencies without "
                "prematurely enabling protected customer routes"
            ),
            "status": "APPROVED",
            "requested_at": timestamp,
            "approved_at": timestamp,
            "requested_by": approval_record["actor"],
            "approved_by": approval_record["actor"],
            "scope": {
                "gate": BACKEND_GATE_ID,
                "previous_active_subtask": (
                    f"{BACKEND_GATE_ID}-B2"
                ),
                "foundation_subtask": (
                    f"{BACKEND_GATE_ID}-B2-FOUNDATION"
                ),
                "production_binding_subtask": (
                    f"{BACKEND_GATE_ID}-B2-PRODUCTION-BINDING"
                ),
                "production_binding_position": "AFTER_B3_AND_B4",
                "technical_sequence": BACKEND_TECHNICAL_SEQUENCE,
                "customer_protected_routes_enabled": False,
            },
            "source_baseline": {
                "repository_head": baseline_sha,
                "source_commit": approval_record["source_commit"],
                "state_blob_sha": approval_record["state_blob_sha"],
                "corrected_backend_master_blob_sha": master_blob_sha,
            },
            "impact_review": {
                "decision": t17_report["decision"],
                "fingerprint": t17_report["fingerprint"],
                "changed_paths": list(t17_report["changed_paths"]),
                "unknown_paths": list(t17_report["unknown_paths"]),
                "protected_paths": list(t17_report["protected_paths"]),
            },
            "operator_proposal": {
                "decision": t15_report["decision"],
                "request_fingerprint": (
                    t15_report["request_fingerprint"]
                ),
                "proposal": t15_report["proposal"],
            },
            "execution_authorization": {
                "decision": authorization["decision"],
                "authorization_fingerprint": (
                    authorization["authorization_fingerprint"]
                ),
                "request_fingerprint": (
                    authorization["request_fingerprint"]
                ),
                "external_executor_required": True,
                "state_mutated_by_guard": False,
            },
            "owner_approval": {
                "method": "GitHub Actions OIDC + repository-owner push",
                "actor": approval_record["actor"],
                "actor_id": approval_record.get("actor_id"),
                "source_commit": approval_record["source_commit"],
                "repository_id": approval_record.get("repository_id"),
                "owner_id": approval_record.get("owner_id"),
                "oidc_issuer": approval_record["oidc_issuer"],
                "oidc_subject": approval_record["oidc_subject"],
                "actions_run_id": approval_record["actions_run_id"],
                "commit_prefix": (
                    "[CONTROL-CENTER-CORRECT-BACKEND-001-B2-DEPENDENCIES]"
                ),
                "bearer_token_persisted": False,
            },
            "security_ownership_boundary": {
                "oidc_verification": (
                    "Existing AUTONOMY_ENGINE OIDCVerifier"
                ),
                "identity_membership": "Existing CORE-001 owner",
                "membership_t03": (
                    "Remains a grants/prerequisites data contract; "
                    "it is not converted into an authorization decision engine."
                ),
                "resource_action_decisions": (
                    "Must use one contract-governed decision owner "
                    "within the existing CORE-001 authority before "
                    "B2 production binding can pass."
                ),
                "session_rate_limit_audit_persistence": (
                    "Existing B4 persistence boundary"
                ),
                "acrl_runtime_use": False,
            },
        }
    )

    return candidate
