from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class HandoffCapsule:
    mission_id: str
    state: str
    summary: str
    completed: tuple[str, ...]
    residual_work: tuple[str, ...]
    next_mission: str | None
    recovery_mode: str
    fingerprint: str
    metadata: dict[str, Any]
