from __future__ import annotations

import copy
from typing import Any


BACKEND_GATE_ID = "BACKEND-001"
BACKEND_CHANGE_REQUEST_ID = "CR-BACKEND-001"

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
        "B2",
        "API security and trusted context",
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
    """Raised when a backend workstream activation is unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BackendWorkstreamTransitionError(message)


def _build_backend_gate_plan(
    *,
    timestamp: str,
    baseline_sha: str,
    evidence_path: str,
) -> dict[str, Any]:
    subtasks: list[dict[str, Any]] = []

    for index, (stage_id, title, priority) in enumerate(BACKEND_STAGES):
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
            "the B0-B10 sequence in HOMIO_Backend_Structure."
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
        "technical_sequence": "B0-B10",
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
    _require(len(baseline_sha) == 40, "Invalid baseline commit SHA.")
    _require(len(master_blob_sha) == 40, "Invalid backend master blob SHA.")
    _require(len(work_plan_blob_sha) == 40, "Invalid work-plan blob SHA.")

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

    gates = [
        item.get("gate")
        for item in sequence
        if isinstance(item, dict)
    ]
    _require(
        "AI-001" in gates and "APP-001" in gates,
        "AI-001 or APP-001 is missing from the authoritative sequence.",
    )
    _require(
        "BACKEND-001" not in gates,
        "BACKEND-001 already exists in the authoritative sequence.",
    )

    ai_index = gates.index("AI-001")
    app_index = gates.index("APP-001")
    _require(
        app_index == ai_index + 1,
        "AI-001 and APP-001 order changed; impact must be reassessed.",
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
        approval_record.get("source_commit"),
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

    existing_requests = state.setdefault("change_requests", [])
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
            "sequence": "B0-B10",
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
