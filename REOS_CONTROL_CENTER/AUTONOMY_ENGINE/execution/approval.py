from dataclasses import dataclass
@dataclass(frozen=True)
class ApprovalState:
    action_id:str; status:str; approver:str|None; reason:str|None
class ApprovalGate:
    def __init__(self): self._states={}
    def record_external_approval(self,action_id,approver,reason):
        if not approver.strip(): raise ValueError("Approver is required.")
        self._states[action_id]=ApprovalState(action_id,"APPROVED",approver,reason)
    def check(self,action_id): return bool(self._states.get(action_id) and self._states[action_id].status=="APPROVED")
