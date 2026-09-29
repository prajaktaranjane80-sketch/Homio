"""Read-only cross-capability consistency validation for CORE-006."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class DealConsistencyViolation:
    code: str; message: str
@dataclass(frozen=True)
class DealConsistencyResult:
    valid: bool; checked: tuple[str,...]; violations: tuple[DealConsistencyViolation,...]
    def require_valid(self):
        if not self.valid: raise ValueError("; ".join(v.message for v in self.violations))
        return self
def _scope_errors(value:Any, *, deal_id:str, tenant_id:str, prefix:str):
    if value is None: return []
    errors=[]
    if getattr(value,"deal_id",deal_id)!=deal_id: errors.append(DealConsistencyViolation(f"{prefix}_DEAL_SCOPE",f"{prefix} belongs to a different deal."))
    if getattr(value,"tenant_id",tenant_id)!=tenant_id: errors.append(DealConsistencyViolation(f"{prefix}_TENANT_SCOPE",f"{prefix} belongs to a different tenant."))
    return errors
def validate_deal_consistency(deal:Any, *, tenant_id:str)->DealConsistencyResult:
    violations=[]
    checked=("tenant","identity","version","history","milestones","ownership_binding","evidence","audit_log")
    if deal.tenant_id!=tenant_id: violations.append(DealConsistencyViolation("TENANT_SCOPE","Deal tenant mismatch."))
    if not deal.deal_id or not deal.customer_id or not deal.broker_id: violations.append(DealConsistencyViolation("IDENTITY","Deal identity is incomplete."))
    if not isinstance(deal.version,int) or deal.version<1: violations.append(DealConsistencyViolation("VERSION","Deal version must be an integer >= 1."))
    history=tuple(getattr(deal,"history",()) or ())
    previous_version=0
    for entry in history:
        if entry.version<=previous_version: violations.append(DealConsistencyViolation("HISTORY_VERSION_ORDER","Deal history versions must strictly increase.")); break
        previous_version=entry.version
    milestones=tuple(getattr(deal,"milestones",()) or ())
    expected_sequence=1; previous_version=0; previous_status=None
    for m in sorted(milestones,key=lambda x:x.sequence):
        fs=getattr(m.from_status,"value",m.from_status); ts=getattr(m.to_status,"value",m.to_status)
        if m.sequence!=expected_sequence: violations.append(DealConsistencyViolation("MILESTONE_SEQUENCE",f"Expected milestone sequence {expected_sequence}, got {m.sequence}."))
        if m.deal_version<=previous_version: violations.append(DealConsistencyViolation("MILESTONE_VERSION","Milestone deal_version must strictly increase."))
        if previous_status is not None and fs!=previous_status: violations.append(DealConsistencyViolation("MILESTONE_STATUS_CHAIN","Milestone status chain is inconsistent."))
        violations.extend(_scope_errors(m,deal_id=deal.deal_id,tenant_id=deal.tenant_id,prefix="MILESTONE"))
        expected_sequence+=1; previous_version=m.deal_version; previous_status=ts
    violations.extend(_scope_errors(getattr(deal,"ownership_binding",None),deal_id=deal.deal_id,tenant_id=deal.tenant_id,prefix="OWNERSHIP"))
    for e in tuple(getattr(deal,"evidence",()) or ()): violations.extend(_scope_errors(e,deal_id=deal.deal_id,tenant_id=deal.tenant_id,prefix="EVIDENCE"))
    for a in tuple(getattr(deal,"audit_log",()) or ()): violations.extend(_scope_errors(a,deal_id=deal.deal_id,tenant_id=deal.tenant_id,prefix="AUDIT"))
    return DealConsistencyResult(not violations,checked,tuple(violations))
__all__=["DealConsistencyResult","DealConsistencyViolation","validate_deal_consistency"]
