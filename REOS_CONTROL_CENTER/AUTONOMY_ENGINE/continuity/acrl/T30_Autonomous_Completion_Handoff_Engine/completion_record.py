from dataclasses import dataclass
from .completion_models import CompletionState

@dataclass(frozen=True)
class CompletionRecord:
    mission_id: str
    state: CompletionState
    fingerprint: str
    reason: str
