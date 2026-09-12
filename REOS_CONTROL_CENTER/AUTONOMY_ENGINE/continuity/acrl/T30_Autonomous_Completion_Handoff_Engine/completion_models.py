from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from .mission_models import MissionSnapshot

class CompletionState(str, Enum):
    COMPLETED = "COMPLETED"
    HANDOFF_READY = "HANDOFF_READY"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    INVALID_FINALIZATION = "INVALID_FINALIZATION"

class ProofDimension(str, Enum):
    CODE = "CODE"
    TEST = "TEST"
    CONTRACT = "CONTRACT"
    DEPENDENCY = "DEPENDENCY"
    STATE = "STATE"
    EVIDENCE = "EVIDENCE"
    SECURITY = "SECURITY"
    HANDOFF = "HANDOFF"

@dataclass(frozen=True)
class ProofReport:
    passed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()

@dataclass(frozen=True)
class CompletionResult:
    state: CompletionState
    confidence: str
    reason: str
    proof: ProofReport
    residual_work: tuple[str, ...] = ()
    next_mission: str | None = None
    handoff_fingerprint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
