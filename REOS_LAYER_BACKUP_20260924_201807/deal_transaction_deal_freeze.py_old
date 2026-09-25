"""CORE-006 final-freeze capability verifier; read-only and fail-closed."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
REQUIRED_MODULES=("deal.py","deal_offer_negotiation.py","deal_transaction_milestones.py","deal_ownership_integration.py","deal_evidence_audit.py","deal_transaction_events.py","deal_transaction_replay.py","deal_concurrency.py","deal_consistency.py","deal_authorization.py","deal_transaction_workflow.py","deal_integrity.py","deal_external_contracts.py","deal_freeze.py")
@dataclass(frozen=True)
class DealFreezeReport:
    ready:bool; required_modules:tuple[str,...]; present_modules:tuple[str,...]; missing_modules:tuple[str,...]; reasons:tuple[str,...]
    def require_ready(self):
        if not self.ready: raise ValueError("; ".join(self.reasons))
        return self
def verify_deal_core_freeze(core_root:Path)->DealFreezeReport:
    present=tuple(name for name in REQUIRED_MODULES if (core_root/name).is_file()); missing=tuple(name for name in REQUIRED_MODULES if not (core_root/name).is_file())
    reasons=("Missing required CORE-006 capability modules: "+", ".join(missing),) if missing else ()
    return DealFreezeReport(not missing,REQUIRED_MODULES,present,missing,reasons)
__all__=["DealFreezeReport","REQUIRED_MODULES","verify_deal_core_freeze"]
