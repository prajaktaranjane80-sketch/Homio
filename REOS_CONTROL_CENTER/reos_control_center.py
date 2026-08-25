#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "data" / "state.json"
TEMPLATES = ROOT / "GATE_TEMPLATES.json"
PACKETS = ROOT / "packets"
SNAPSHOTS = ROOT / "snapshots"
LOGS = ROOT / "logs"
VERSION = "7.0"

for folder in (PACKETS, SNAPSHOTS, LOGS):
    folder.mkdir(parents=True, exist_ok=True)

FALLBACK_TEMPLATES: dict[str, dict[str, Any]] = {
    "ARCH-037": {
        "name": "Database Final Schema Design v1.0",
        "objective": "Finalize the production-grade database schema from the approved Database DNA.",
        "subtasks": [
            ["T01", "Inventory canonical entities and bounded contexts", "CRITICAL"],
            ["T02", "Define final tables and source-of-truth ownership", "CRITICAL"],
            ["T03", "Define keys relationships and referential rules", "CRITICAL"],
            ["T04", "Define tenant isolation and authorization fields", "CRITICAL"],
            ["T05", "Define indexes uniqueness and critical constraints", "HIGH"],
            ["T06", "Define event and audit persistence model", "HIGH"],
            ["T07", "Define retention archival and recovery rules", "HIGH"],
            ["T08", "Define schema migration and versioning strategy", "HIGH"],
            ["T09", "Run normalization and duplication review", "CRITICAL"],
            ["T10", "Run security privacy and performance review", "CRITICAL"],
            ["T11", "Final schema freeze approval", "CRITICAL"],
        ],
        "criteria": [
            "Every canonical business entity has one authoritative source of truth.",
            "Lead, deal, inventory, trust, fraud, governance and commission relationships are traceable.",
            "Tenant isolation is enforceable at database level.",
            "Critical uniqueness and referential constraints are explicit.",
            "Event and audit history preserves historical truth.",
            "Migration and versioning supports safe production evolution.",
            "Critical access paths have intentional indexes.",
            "Sensitive data boundaries are explicitly defined.",
            "Schema supports all approved operating modes.",
            "No duplicate responsibility exists across services.",
            "Security, performance and consistency review passes.",
        ],
    },
    "ARCH-038": {
        "name": "Technology Stack Lock v1.0",
        "objective": "Freeze the implementation technology stack with explicit reasons and no unnecessary complexity.",
        "subtasks": [
            ["T01", "Define frontend and runtime stack", "CRITICAL"],
            ["T02", "Define backend and service runtime stack", "CRITICAL"],
            ["T03", "Define database and data infrastructure", "CRITICAL"],
            ["T04", "Define event bus cache and background jobs", "HIGH"],
            ["T05", "Define search vector and AI infrastructure", "HIGH"],
            ["T06", "Define cloud deployment and container strategy", "HIGH"],
            ["T07", "Define observability and security tooling", "HIGH"],
            ["T08", "Run cost scalability and vendor-lock review", "CRITICAL"],
            ["T09", "Freeze technology decision record", "CRITICAL"],
        ],
        "criteria": [
            "Every production component has a defined purpose and owner.",
            "Stack supports multi-tenancy and event-driven services.",
            "Stack supports search and AI infrastructure.",
            "Security, observability, backup and recovery requirements are covered.",
            "Development, staging and production environments are supported.",
            "Alternatives and reasons are recorded.",
            "Cost and scale assumptions are recorded.",
            "No unnecessary technology is introduced.",
            "Technology stack is explicitly approved and frozen.",
        ],
    },
    "ARCH-039": {
        "name": "Master Blueprint v1.0",
        "objective": "Assemble all approved architecture into one machine-readable implementation contract.",
        "subtasks": [
            ["T01", "Assemble business architecture registry", "CRITICAL"],
            ["T02", "Assemble technical architecture registry", "CRITICAL"],
            ["T03", "Assemble database event and API contracts", "CRITICAL"],
            ["T04", "Assemble security governance and approval rules", "CRITICAL"],
            ["T05", "Assemble implementation dependency graph", "CRITICAL"],
            ["T06", "Run architecture consistency and duplicate review", "CRITICAL"],
            ["T07", "Generate repository implementation map", "CRITICAL"],
            ["T08", "Freeze Master Blueprint", "CRITICAL"],
        ],
        "criteria": [
            "All approved architecture gates are represented.",
            "No unresolved architecture conflicts remain.",
            "Dependencies and execution order are machine-readable.",
            "Security and governance controls are preserved.",
            "Coding tasks derive from the blueprint.",
            "Master Blueprint is versioned and frozen.",
        ],
    },
}


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load_state() -> dict[str, Any]:
    if not STATE.exists():
        raise SystemExit(f"Canonical state missing: {STATE}")
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid state.json: {exc}") from exc
    state.setdefault("events", [])
    state.setdefault("checkpoints", [])
    state.setdefault("gate_plans", {})
    state.setdefault("session", {})
    state.setdefault("integrity", {"sha256": None})
    return state


def canonical_without_hash(state: dict[str, Any]) -> bytes:
    clone = copy.deepcopy(state)
    clone.setdefault("integrity", {})["sha256"] = None
    return json.dumps(clone, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def calculate_hash(state: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_without_hash(state)).hexdigest()


def save_state(state: dict[str, Any], *, create_snapshot: bool = True) -> None:
    state.setdefault("meta", {})["updated_at"] = now()
    state.setdefault("integrity", {})["sha256"] = calculate_hash(state)

    if create_snapshot and STATE.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        shutil.copy2(STATE, SNAPSHOTS / f"state_{stamp}.json")

    fd, tmp_name = tempfile.mkstemp(dir=STATE.parent, prefix=".reos-", suffix=".tmp")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, STATE)
    finally:
        tmp.unlink(missing_ok=True)


def emit(state: dict[str, Any], event_type: str, payload: dict[str, Any]) -> None:
    state["events"].append({
        "id": str(uuid.uuid4()),
        "time": now(),
        "type": event_type,
        "payload": payload,
    })


def current_gate_id(state: dict[str, Any]) -> str:
    return state["execution"]["current_gate"]


def load_templates() -> dict[str, Any]:
    templates = copy.deepcopy(FALLBACK_TEMPLATES)
    if TEMPLATES.exists():
        try:
            external = json.loads(TEMPLATES.read_text(encoding="utf-8"))
            if isinstance(external, dict):
                templates.update(external)
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Invalid GATE_TEMPLATES.json: {exc}") from exc
    return templates


def materialize_current_gate(state: dict[str, Any], persist: bool = True) -> dict[str, Any]:
    gate_id = current_gate_id(state)
    existing = state["gate_plans"].get(gate_id)
    if existing:
        return existing

    template = load_templates().get(gate_id)
    if not template:
        raise SystemExit(f"No template available for current gate: {gate_id}")

    subtasks = template["subtasks"]
    gate = {
        "id": gate_id,
        "name": template["name"],
        "objective": template["objective"],
        "status": "CURRENT",
        "current_subtask": f"{gate_id}-{subtasks[0][0]}",
        "subtasks": [
            {
                "id": f"{gate_id}-{sid}",
                "title": title,
                "priority": priority,
                "status": "CURRENT" if index == 0 else "PENDING",
            }
            for index, (sid, title, priority) in enumerate(subtasks)
        ],
        "acceptance_criteria": template["criteria"],
        "criteria_state": [
            {
                "id": f"{gate_id}-AC{index:02d}",
                "criterion": criterion,
                "status": "PENDING",
                "evidence": None,
                "verified_at": None,
            }
            for index, criterion in enumerate(template["criteria"], start=1)
        ],
        "completion_policy": "All blocking subtasks DONE + all criteria VERIFIED + explicit approval.",
        "created_at": now(),
    }
    state["gate_plans"][gate_id] = gate
    emit(state, "GATE_AUTO_MATERIALIZED", {"gate": gate_id})
    if persist:
        save_state(state)
    return gate


def is_approval_subtask(subtask: dict[str, Any]) -> bool:
    title = subtask.get("title", "").lower()
    return "approve" in title or "freeze" in title


def build_handoff_packet(state: dict[str, Any]) -> Path:
    gate = materialize_current_gate(state)
    execution = state["execution"]
    lines = [
        "HOMIO / REOS — COMPACT CONTROL PACKET v7.0",
        "=" * 72,
        f"CURRENT_GATE={execution['current_gate']}",
        f"CURRENT_TASK={execution['current_task']}",
        f"STATUS={execution['status']}",
        f"CURRENT_SUBTASK={gate['current_subtask']}",
        "RULE=CONTROL_CENTER_IS_ROADMAP_AUTHORITY",
        "",
        "SUBTASKS:",
    ]
    lines.extend(f"{x['id']}|{x['status']}|{x['title']}" for x in gate["subtasks"])
    lines += ["", "ACCEPTANCE CRITERIA:"]
    lines.extend(f"{x['id']}|{x['status']}|{x['criterion']}" for x in gate["criteria_state"])
    packet = "\n".join(lines)
    path = PACKETS / "NEW_CHAT_PACKET.txt"
    path.write_text(packet, encoding="utf-8")
    (ROOT / "REOS_NEXT_CHAT.txt").write_text(packet, encoding="utf-8")
    state["session"]["last_handoff"] = str(path)
    return path


def cmd_status(state: dict[str, Any]) -> None:
    gate = materialize_current_gate(state)
    e = state["execution"]
    print(f"HOMIO / REOS CONTROL CENTER v{VERSION}")
    print("=" * 72)
    print("Phase:", state.get("phases", {}).get("current", "UNKNOWN"))
    print("Gate:", e.get("current_gate"))
    print("Task:", e.get("current_task"))
    print("Status:", e.get("status"))
    print("Subtask:", gate.get("current_subtask"))
    print("Gate Status:", gate.get("status"))
    print("Subtasks:", len(gate.get("subtasks", [])), "Criteria:", len(gate.get("criteria_state", [])))
    print("Approved:", len(state.get("architecture", {}).get("approved", [])), "Pending:", len(state.get("architecture", {}).get("pending", [])))
    print("State:", STATE)


def cmd_plan(state: dict[str, Any]) -> None:
    plan = state.get("execution_plan", {})
    print("PLAN VERSION:", plan.get("plan_version"))
    print("MODE:", plan.get("mode"))
    for step in plan.get("authoritative_sequence", []):
        print(f"{step['id']} | {step['gate']} | {step['name']} | {step['status']}")


def cmd_gate(state: dict[str, Any]) -> None:
    gate = materialize_current_gate(state)
    print("GATE:", gate["name"])
    print("STATUS:", gate["status"])
    print("CURRENT SUBTASK:", gate["current_subtask"])
    print("SUBTASKS:")
    for subtask in gate["subtasks"]:
        print(f"{subtask['id']} | {subtask['title']} | {subtask['status']} | {subtask['priority']}")
    print("ACCEPTANCE CRITERIA:")
    for criterion in gate["criteria_state"]:
        print(f"{criterion['id']} | {criterion['status']} | {criterion['criterion']}")


def cmd_sync_gate(state: dict[str, Any]) -> None:
    gate = materialize_current_gate(state)
    save_state(state)
    build_handoff_packet(state)
    print("Gate synchronized:", gate["id"])
    print("Current subtask:", gate["current_subtask"])


def cmd_complete_subtask(state: dict[str, Any], subtask_id: str, note: str) -> None:
    gate = materialize_current_gate(state)
    subtask = next((x for x in gate["subtasks"] if x["id"] == subtask_id), None)
    if not subtask:
        raise SystemExit(f"Subtask not found: {subtask_id}")
    if subtask["status"] != "CURRENT":
        raise SystemExit(f"Only CURRENT subtask can be completed. {subtask_id} is {subtask['status']}")
    if is_approval_subtask(subtask):
        raise SystemExit("Approval/freeze subtask is controlled by approve-gate, not complete-subtask.")

    subtask["status"] = "DONE"
    subtask["completed_at"] = now()
    subtask["note"] = note

    remaining = [
        x for x in gate["subtasks"]
        if x["status"] not in ("DONE", "CLOSED", "READY_FOR_APPROVAL") and not is_approval_subtask(x)
    ]
    if remaining:
        remaining[0]["status"] = "CURRENT"
        gate["current_subtask"] = remaining[0]["id"]
        state["execution"]["current_subtask"] = remaining[0]["id"]
        state["execution"]["current_task"] = f"{remaining[0]['id']}: {remaining[0]['title']}."
    else:
        gate["status"] = "READY_FOR_VALIDATION"
        state["execution"]["current_subtask"] = next((x["id"] for x in gate["subtasks"] if is_approval_subtask(x)), None)
        state["execution"]["current_task"] = f"{current_gate_id(state)}: Validate acceptance criteria."

    emit(state, "SUBTASK_COMPLETED", {"id": subtask_id, "note": note})
    save_state(state)
    build_handoff_packet(state)
    print("COMPLETED:", subtask_id)
    print("NEXT:", state["execution"]["current_task"])


def cmd_verify_criterion(state: dict[str, Any], criterion_id: str, evidence: str) -> None:
    gate = materialize_current_gate(state)
    criterion = next((x for x in gate["criteria_state"] if x["id"] == criterion_id), None)
    if not criterion:
        raise SystemExit(f"Criterion not found: {criterion_id}")
    criterion["status"] = "VERIFIED"
    criterion["evidence"] = evidence
    criterion["verified_at"] = now()
    emit(state, "CRITERION_VERIFIED", {"id": criterion_id, "evidence": evidence})
    save_state(state)
    build_handoff_packet(state)
    print("VERIFIED:", criterion_id)


def cmd_verify_all(state: dict[str, Any]) -> None:
    gate = materialize_current_gate(state)
    evidence = "Final review completed by current gate execution."
    for criterion in gate["criteria_state"]:
        criterion["status"] = "VERIFIED"
        criterion["evidence"] = evidence
        criterion["verified_at"] = now()
    emit(state, "CRITERIA_BULK_VERIFIED", {"gate": current_gate_id(state)})
    save_state(state)
    build_handoff_packet(state)
    print("VERIFIED CRITERIA:", len(gate["criteria_state"]))


def cmd_validate_gate(state: dict[str, Any]) -> bool:
    gate = materialize_current_gate(state)
    approval_subtask = next((x for x in gate["subtasks"] if is_approval_subtask(x)), None)
    unfinished = [
        x["id"] for x in gate["subtasks"]
        if x is not approval_subtask and x["status"] not in ("DONE", "CLOSED")
    ]
    unverified = [x["id"] for x in gate["criteria_state"] if x["status"] != "VERIFIED"]

    if unfinished or unverified:
        print("VALIDATION BLOCKED")
        print("Unfinished subtasks:", unfinished or "None")
        print("Unverified criteria:", unverified or "None")
        return False

    if approval_subtask:
        approval_subtask["status"] = "READY_FOR_APPROVAL"
        gate["current_subtask"] = approval_subtask["id"]
        state["execution"]["current_subtask"] = approval_subtask["id"]
    gate["status"] = "VALIDATED"
    state["execution"]["status"] = "READY_FOR_APPROVAL"
    state["execution"]["current_task"] = f"{current_gate_id(state)}: Approval required."
    emit(state, "GATE_VALIDATED", {"gate": current_gate_id(state)})
    save_state(state)
    build_handoff_packet(state)
    print("GATE VALIDATED:", current_gate_id(state))
    print("APPROVAL READY: run python reos_control_center.py approve-gate")
    return True


def cmd_approve_gate(state: dict[str, Any]) -> None:
    gate = materialize_current_gate(state)
    if gate.get("status") != "VALIDATED":
        raise SystemExit("Gate must be VALIDATED before approval. Run: python reos_control_center.py validate-gate")

    gid = current_gate_id(state)
    pending_item = next((x for x in state["architecture"]["pending"] if x["id"] == gid), None)
    if pending_item:
        state["architecture"]["pending"].remove(pending_item)
        pending_item["status"] = "APPROVED"
        pending_item["approved_at"] = now()
        state["architecture"]["approved"].append(pending_item)

    gate["status"] = "APPROVED"
    for subtask in gate["subtasks"]:
        if subtask["status"] in ("CURRENT", "READY_FOR_APPROVAL") or is_approval_subtask(subtask):
            subtask["status"] = "DONE"
            subtask["completed_at"] = now()

    sequence = state.get("execution_plan", {}).get("authoritative_sequence", [])
    current_index = next((i for i, x in enumerate(sequence) if x.get("gate") == gid), None)
    if current_index is None:
        raise SystemExit(f"Current gate {gid} is missing from execution_plan")

    sequence[current_index]["status"] = "COMPLETE"
    next_gate = sequence[current_index + 1]["gate"] if current_index + 1 < len(sequence) else None

    if next_gate:
        sequence[current_index + 1]["status"] = "CURRENT"
        state["execution"]["current_gate"] = next_gate
        state["execution"]["status"] = "CONTROL_CENTER_DRIVEN"
        state["execution"]["current_subtask"] = None
        state["execution"]["current_task"] = next(x["name"] for x in sequence if x["gate"] == next_gate)
        materialize_current_gate(state)
        next_plan = state["gate_plans"][next_gate]
        state["execution"]["current_subtask"] = next_plan["current_subtask"]
        state["execution"]["current_task"] = f"{next_plan['current_subtask']}: {next_plan['subtasks'][0]['title']}."
    else:
        state["execution"]["status"] = "COMPLETE"
        state["execution"]["current_subtask"] = None
        state["execution"]["current_task"] = "All authoritative gates complete."

    emit(state, "GATE_APPROVED_AND_FROZEN", {"gate": gid, "next_gate": next_gate})
    save_state(state)
    build_handoff_packet(state)
    print("GATE APPROVED & FROZEN:", gid)
    print("NEXT GATE:", next_gate or "NONE")


def cmd_checkpoint(state: dict[str, Any], note: str) -> None:
    item = {
        "id": f"CP-{len(state['checkpoints']) + 1:05d}",
        "time": now(),
        "gate": current_gate_id(state),
        "task": state["execution"]["current_task"],
        "note": note,
    }
    state["checkpoints"].append(item)
    state["session"]["last_checkpoint"] = item
    emit(state, "CHECKPOINT", item)
    save_state(state)
    build_handoff_packet(state)
    print(item["id"])


def cmd_verify_state(state: dict[str, Any]) -> None:
    stored = state.get("integrity", {}).get("sha256")
    calculated = calculate_hash(state)
    print("STATE HASH STORED:", stored)
    print("STATE HASH CALCULATED:", calculated)
    print("INTEGRITY:", "PASS" if stored == calculated else "MISMATCH")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reos_control_center.py")
    sub = parser.add_subparsers(dest="cmd")
    for command in (
        "status", "plan", "gate", "handoff", "sync-gate",
        "verify-all", "validate-gate", "approve-gate", "verify-state"
    ):
        sub.add_parser(command)
    p = sub.add_parser("complete-subtask")
    p.add_argument("id")
    p.add_argument("--note", default="")
    p = sub.add_parser("verify-criterion")
    p.add_argument("id")
    p.add_argument("--evidence", required=True)
    p = sub.add_parser("checkpoint")
    p.add_argument("note")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    state = load_state()

    if args.cmd == "status":
        cmd_status(state)
    elif args.cmd == "plan":
        cmd_plan(state)
    elif args.cmd == "gate":
        cmd_gate(state)
    elif args.cmd == "handoff":
        path = build_handoff_packet(state)
        print(path)
    elif args.cmd == "sync-gate":
        cmd_sync_gate = materialize_current_gate(state)
        save_state(state)
        build_handoff_packet(state)
        print("Gate synchronized:", cmd_sync_gate["id"])
        print("Current subtask:", cmd_sync_gate["current_subtask"])
    elif args.cmd == "complete-subtask":
        cmd_complete_subtask(state, args.id, args.note)
    elif args.cmd == "verify-criterion":
        cmd_verify_criterion(state, args.id, args.evidence)
    elif args.cmd == "verify-all":
        cmd_verify_all(state)
    elif args.cmd == "validate-gate":
        cmd_validate_gate(state)
    elif args.cmd == "approve-gate":
        cmd_approve_gate(state)
    elif args.cmd == "checkpoint":
        cmd_checkpoint(state, args.note)
    elif args.cmd == "verify-state":
        cmd_verify_state(state)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
