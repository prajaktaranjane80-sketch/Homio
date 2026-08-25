from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
@dataclass(frozen=True)
class ActionCandidate:
    action_id: str; description: str; risk: str; requires_mutation: bool; evidence_required: tuple[str, ...] = ()
@dataclass(frozen=True)
class ActionPlan:
    status: str; selected: ActionCandidate | None; blockers: tuple[str, ...]; rationale: str
class ActionPlanner:
    RISK_ORDER = {"LOW":0,"MEDIUM":1,"HIGH":2,"CRITICAL":3}
    def choose(self, candidates: Iterable[ActionCandidate], *, blockers=(), proven_evidence=()):
        blockers=tuple(blockers)
        if blockers: return ActionPlan("BLOCKED",None,blockers,"Existing blockers prevent safe action selection.")
        proven=set(proven_evidence)
        eligible=[c for c in candidates if all(e in proven for e in c.evidence_required)]
        if not eligible: return ActionPlan("NO_SAFE_ACTION",None,(),"No candidate has sufficient evidence.")
        s=sorted(eligible,key=lambda c:(self.RISK_ORDER.get(c.risk,99),c.requires_mutation,c.action_id))[0]
        return ActionPlan("READY",s,(),"Selected the smallest-risk eligible action with required evidence.")
