from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class RiskDecision:
    level:str; score:int; reasons:tuple[str,...]; requires_approval:bool; allowed:bool
class RiskEngine:
    def assess(self, *, mutation:bool, touches_frozen_architecture:bool, touches_tenant_boundary:bool, production:bool, financial:bool, destructive:bool, evidence_complete:bool)->RiskDecision:
        score=0; r=[]
        for flag,pts,name in [(mutation,20,"mutation"),(touches_frozen_architecture,50,"frozen-architecture"),(touches_tenant_boundary,35,"tenant-boundary"),(production,40,"production"),(financial,45,"financial"),(destructive,40,"destructive")]:
            if flag: score+=pts; r.append(name)
        if not evidence_complete: score+=30; r.append("evidence-incomplete")
        level="CRITICAL" if score>=80 else "HIGH" if score>=55 else "MEDIUM" if score>=25 else "LOW"
        return RiskDecision(level,score,tuple(r),level in {"HIGH","CRITICAL"},not(level=="CRITICAL" and not evidence_complete))
