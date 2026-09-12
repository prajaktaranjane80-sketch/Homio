from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class MissionSnapshot:
    mission_id: str
    objective: str
    required_dimensions: tuple[str, ...] = ()
    completed_nodes: tuple[str, ...] = ()
    unresolved_nodes: tuple[str, ...] = ()
    blocked_nodes: tuple[str, ...] = ()
    rejected_human_decision: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
