"""Deal-specific contextual authorization boundary. CORE-001 remains authority."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
class DealAuthorizationError(PermissionError): pass
class DealAuthorizationDenied(DealAuthorizationError): pass
class DealOperation(str,Enum):
    READ="DEAL_READ"; TRANSITION="DEAL_TRANSITION"; OFFER="DEAL_OFFER"; NEGOTIATE="DEAL_NEGOTIATE"; BOOK="DEAL_BOOK"; AGREEMENT="DEAL_AGREEMENT"; REGISTRATION="DEAL_REGISTRATION"; COMPLETE="DEAL_COMPLETE"; CANCEL="DEAL_CANCEL"; DISPUTE="DEAL_DISPUTE"; FRAUD_BLOCK="DEAL_FRAUD_BLOCK"; EXPORT="DEAL_EXPORT"
@dataclass(frozen=True)
class DealAuthorizationContext:
    subject_id:str; tenant_id:str; roles:frozenset[str]=frozenset(); permissions:frozenset[str]=frozenset(); approvals:frozenset[str]=frozenset(); attributes:Mapping[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class DealAuthorizationDecision:
    allowed:bool; operation:DealOperation; reason:str; required_permission:str; required_approval:str|None=None
_SENSITIVE_APPROVALS={DealOperation.BOOK:"APPROVAL_DEAL_BOOKING",DealOperation.AGREEMENT:"APPROVAL_DEAL_AGREEMENT",DealOperation.REGISTRATION:"APPROVAL_DEAL_REGISTRATION",DealOperation.COMPLETE:"APPROVAL_DEAL_COMPLETION",DealOperation.DISPUTE:"APPROVAL_DEAL_DISPUTE",DealOperation.FRAUD_BLOCK:"APPROVAL_DEAL_FRAUD_BLOCK",DealOperation.EXPORT:"APPROVAL_DEAL_SENSITIVE_EXPORT"}
def authorize_deal_operation(deal:Any,context:DealAuthorizationContext,operation:DealOperation)->DealAuthorizationDecision:
    op=DealOperation(operation); required=op.value
    if context.tenant_id!=deal.tenant_id: return DealAuthorizationDecision(False,op,"Tenant mismatch; authorization denied.",required)
    if not context.subject_id.strip(): return DealAuthorizationDecision(False,op,"Missing authenticated subject; authorization denied.",required)
    if required not in context.permissions: return DealAuthorizationDecision(False,op,"Required permission is absent; authorization denied.",required)
    approval=_SENSITIVE_APPROVALS.get(op)
    if approval and approval not in context.approvals: return DealAuthorizationDecision(False,op,"Required high-risk approval is absent; authorization denied.",required,approval)
    current=getattr(deal.status,"value",deal.status)
    state_requirements={DealOperation.BOOK:"BOOKING_PENDING",DealOperation.COMPLETE:"COMPLETION_PENDING"}
    expected=state_requirements.get(op)
    if expected and current!=expected: return DealAuthorizationDecision(False,op,f"{op.value} is invalid outside {expected}.",required,approval)
    return DealAuthorizationDecision(True,op,"Explicit Deal authorization requirements satisfied.",required,approval)
def require_deal_authorization(deal:Any,context:DealAuthorizationContext,operation:DealOperation)->DealAuthorizationDecision:
    d=authorize_deal_operation(deal,context,operation)
    if not d.allowed: raise DealAuthorizationDenied(d.reason)
    return d
__all__=["DealAuthorizationContext","DealAuthorizationDecision","DealAuthorizationDenied","DealAuthorizationError","DealOperation","authorize_deal_operation","require_deal_authorization"]
