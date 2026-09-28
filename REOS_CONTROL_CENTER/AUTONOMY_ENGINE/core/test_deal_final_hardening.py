from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pytest
from AUTONOMY_ENGINE.core.deal_transaction_events import DealTransactionEvent
from AUTONOMY_ENGINE.core.deal_transaction_replay import verify_transaction_replay
from AUTONOMY_ENGINE.core.deal_concurrency import DealConcurrencyGuard, DealStaleWriteError
from AUTONOMY_ENGINE.core.deal_consistency import validate_deal_consistency
from AUTONOMY_ENGINE.core.deal_authorization import DealAuthorizationContext, DealOperation, authorize_deal_operation
from AUTONOMY_ENGINE.core.deal_transaction_workflow import build_deal_workflow
from AUTONOMY_ENGINE.core.deal_integrity import hash_deal, validate_deal_integrity
from AUTONOMY_ENGINE.core.deal_freeze import verify_deal_core_freeze
from AUTONOMY_ENGINE.core.deal_external_contracts import DealExternalAuthority, DealExternalReference, DealExternalDecision, DealExternalContractError
@dataclass(frozen=True)
class Milestone:
    milestone_id:str; deal_id:str; tenant_id:str; from_status:str; to_status:str; deal_version:int; sequence:int; occurred_at:str; reference_id:str|None=None
@dataclass(frozen=True)
class DealStub:
    deal_id:str; tenant_id:str; customer_id:str="customer-1"; broker_id:str="broker-1"; version:int=3; status:str="BOOKING_PENDING"; source_of_truth:str="deal"; history:tuple=(); milestones:tuple=(); ownership_binding:object|None=None; evidence:tuple=(); audit_log:tuple=()
    def to_dict(self): return {"deal_id":self.deal_id,"tenant_id":self.tenant_id,"customer_id":self.customer_id,"broker_id":self.broker_id,"version":self.version,"status":self.status,"source_of_truth":self.source_of_truth,"history":[],"milestones":[],"evidence":[],"audit_log":[]}
AT="2026-09-24T10:00:00+00:00"
def milestones(): return (Milestone("m1","d1","t1","OFFERED","BOOKING_PENDING",5,1,AT),Milestone("m2","d1","t1","BOOKING_PENDING","BOOKED",6,2,AT))
def test_replay_is_deterministic_and_detects_scope():
    result=verify_transaction_replay(milestones(),deal_id="d1",tenant_id="t1",initial_status="OFFERED"); assert result.valid; assert result.reconstructed_status=="BOOKED"
    bad=verify_transaction_replay(milestones(),deal_id="d2",tenant_id="t1",initial_status="OFFERED"); assert not bad.valid; assert any(v.code=="DEAL_SCOPE" for v in bad.violations)
def test_concurrency_fails_closed():
    deal=DealStub("d1","t1"); assert DealConcurrencyGuard().assert_current(deal,tenant_id="t1",expected_version=3).is_current
    with pytest.raises(DealStaleWriteError): DealConcurrencyGuard().assert_current(deal,tenant_id="t1",expected_version=2)
def test_authorization_is_contextual_and_default_deny():
    deal=DealStub("d1","t1")
    denied=authorize_deal_operation(deal,DealAuthorizationContext("user-1","t1"),DealOperation.BOOK); assert not denied.allowed
    allowed=authorize_deal_operation(deal,DealAuthorizationContext("user-1","t1",permissions=frozenset({"DEAL_BOOK"}),approvals=frozenset({"APPROVAL_DEAL_BOOKING"})),DealOperation.BOOK); assert allowed.allowed
def test_consistency_validates_tenant_and_milestone_chain():
    deal=DealStub("d1","t1",version=6,milestones=milestones()); assert validate_deal_consistency(deal,tenant_id="t1").valid; assert not validate_deal_consistency(deal,tenant_id="t2").valid
def test_workflow_never_changes_authoritative_state():
    deal=DealStub("d1","t1"); s=build_deal_workflow(deal); assert s.next_step is not None; assert "BOOKED" in s.next_step.allowed_next_statuses; assert deal.status=="BOOKING_PENDING"
def test_integrity_hash_is_stable():
    deal=DealStub("d1","t1"); digest=hash_deal(deal); report=validate_deal_integrity(deal,tenant_id="t1",expected_hash=digest); assert report.valid and report.canonical_hash==digest
def test_event_idempotency_is_authoritative():
    event=DealTransactionEvent.from_milestone(milestones()[0]); assert event.event_id=="m1"; assert event.idempotency_key=="m1"; assert event.source_of_truth=="deal_transaction_milestone"; assert event.payload_hash
def test_external_authority_contract_is_scope_bound():
    ref=DealExternalReference("d1","t1",DealExternalAuthority.COMMISSION,"c1","COMMISSION_LINK","1.0",AT)
    ref.assert_scope(deal_id="d1",tenant_id="t1")
    decision=DealExternalDecision("x1","d1","t1",DealExternalAuthority.FRAUD,"REVIEW","7","1", "fingerprint")
    decision.assert_scope(deal_id="d1",tenant_id="t1")
    with pytest.raises(DealExternalContractError): ref.assert_scope(deal_id="d2",tenant_id="t1")

def test_freeze_verifier_requires_full_capability_surface(tmp_path:Path):
    for module in ("deal.py","deal_offer_negotiation.py","deal_transaction_milestones.py","deal_ownership_integration.py","deal_evidence_audit.py","deal_transaction_events.py","deal_transaction_replay.py","deal_concurrency.py","deal_consistency.py","deal_authorization.py","deal_transaction_workflow.py","deal_integrity.py","deal_external_contracts.py","deal_freeze.py"): (tmp_path/module).write_text("",encoding="utf-8")
    report=verify_deal_core_freeze(tmp_path); assert report.ready and not report.missing_modules
