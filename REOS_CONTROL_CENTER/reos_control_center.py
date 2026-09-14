#!/usr/bin/env python3
from **future** import annotations

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

ROOT = Path(**file**).resolve().parent
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
"""
Load the canonical REOS Control Center state.

```
Canonical authority:
    REOS_CONTROL_CENTER/data/state.json

L3 guarantees:
    - state.json remains the single source of truth.
    - integrity is verified before state is trusted.
    - missing integrity metadata fails closed.
    - missing SHA-256 fails closed.
    - tampered state fails closed.
    - no duplicate state authority is created.
"""
if not STATE.exists():
    raise SystemExit(f"Canonical state missing: {STATE}")

try:
    state = json.loads(STATE.read_text(encoding="utf-8"))
except OSError as exc:
    raise SystemExit(
        f"CANONICAL STATE READ FAILURE: {exc}"
    ) from exc
except json.JSONDecodeError as exc:
    raise SystemExit(
        f"Invalid state.json: {exc}"
    ) from exc

if not isinstance(state, dict):
    raise SystemExit(
        "CANONICAL STATE INTEGRITY FAILURE: "
        "state.json root must be an object"
    )

integrity = state.get("integrity")

if not isinstance(integrity, dict):
    raise SystemExit(
        "CANONICAL STATE INTEGRITY FAILURE: "
        "integrity metadata missing"
    )

stored_hash = integrity.get("sha256")

if not isinstance(stored_hash, str) or not stored_hash.strip():
    raise SystemExit(
        "CANONICAL STATE INTEGRITY FAILURE: "
        "SHA-256 missing"
    )

calculated_hash = calculate_hash(state)

if stored_hash != calculated_hash:
    raise SystemExit(
        "CANONICAL STATE INTEGRITY FAILURE: "
        "stored SHA-256 does not match canonical state"
    )

# Compatibility defaults are applied only AFTER
# canonical integrity has been verified.
state.setdefault("events", [])
state.setdefault("checkpoints", [])
state.setdefault("gate_plans", {})
state.setdefault("session", {})

return state
```

def canonical_without_hash(state: dict[str, Any]) -> bytes:
clone = copy.deepcopy(state)
clone.setdefault("integrity", {})["sha256"] = None
return json.dumps(
clone,
sort_keys=True,
ensure_ascii=False,
separators=(",", ":"),
).encode("utf-8")

def calculate_hash(state: dict[str, Any]) -> str:
return hashlib.sha256(canonical_without_hash(state)).hexdigest()

def save_state(state: dict[str, Any], *, create_snapshot: bool = True) -> None:
state.setdefault("meta", {})["updated_at"] = now()
state.setdefault("integrity", {})["sha256"] = calculate_hash(state)

```
if create_snapshot and STATE.exists():
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    shutil.copy2(STATE, SNAPSHOTS / f"state_{stamp}.json")

fd, tmp_name = tempfile.mkstemp(
    dir=STATE.parent,
    prefix=".reos-",
    suffix=".tmp",
)
os.close(fd)
tm
```
