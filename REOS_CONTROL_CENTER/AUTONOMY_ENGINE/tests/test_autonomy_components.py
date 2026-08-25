from pathlib import Path
from core.action_planner import ActionCandidate,ActionPlanner
from core.context_compiler import ContextCompiler
from core.risk_engine import RiskEngine
from core.workspace_guard import WorkspaceGuard
from execution.approval import ApprovalGate

def test_planner():
    r=ActionPlanner().choose([ActionCandidate("A","inspect","LOW",False,("state",)),ActionCandidate("B","mutate","HIGH",True,("state","approval"))],proven_evidence=["state"])
    assert r.selected and r.selected.action_id=="A"
def test_redact():
    r=ContextCompiler.redact({"token":"abc","nested":{"password":"x"}}); assert r["token"]=="[REDACTED]" and r["nested"]["password"]=="[REDACTED]"
def test_risk():
    d=RiskEngine().assess(mutation=True,touches_frozen_architecture=True,touches_tenant_boundary=True,production=True,financial=False,destructive=True,evidence_complete=False); assert d.level=="CRITICAL" and not d.allowed and d.requires_approval
def test_workspace():
    g=WorkspaceGuard([Path("/tmp/reos-test-root")]); assert g.check(Path("/tmp/reos-test-root/sub")); assert not g.check(Path("/tmp/other"))
def test_approval():
    g=ApprovalGate(); assert not g.check("X"); g.record_external_approval("X","human","approved"); assert g.check("X")
