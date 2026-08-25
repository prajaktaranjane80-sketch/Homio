
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

FactStatus = Literal[
    "PROVEN", "VERIFIED", "SUPPORTED", "LIKELY",
    "UNVERIFIED", "UNKNOWN", "CONTRADICTED"
]

@dataclass(frozen=True)
class Fact:
    fact_id: str
    claim: str
    status: FactStatus
    source: str
    value: Any = None
    semantic_owner: str | None = None
    command: str | None = None

@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: Literal["PASS", "WARN", "BLOCK"]
    message: str
    facts: tuple[Fact, ...] = ()

@dataclass
class ContextSnapshot:
    generated_at: str
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    gate_status: str | None
    criteria_total: int
    criteria_verified: int
    criteria_pending: int
    plan_current_gate: str | None
    next_gate: str | None
    state_integrity: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
