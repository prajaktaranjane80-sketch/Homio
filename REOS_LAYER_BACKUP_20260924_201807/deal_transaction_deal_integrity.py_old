"""Canonical integrity and tamper-evidence checks for Deal."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Mapping
@dataclass(frozen=True)
class DealIntegrityReport:
    valid:bool; deal_id:str; tenant_id:str; canonical_hash:str; checks:tuple[str,...]; violations:tuple[str,...]
    def require_valid(self):
        if not self.valid: raise ValueError("; ".join(self.violations))
        return self
def _canonical(value:Mapping[str,Any])->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def hash_deal(deal:Any)->str: return hashlib.sha256(_canonical(deal.to_dict()).encode("utf-8")).hexdigest()
def validate_deal_integrity(deal:Any,*,tenant_id:str,expected_hash:str|None=None)->DealIntegrityReport:
    violations=[]
    if deal.tenant_id!=tenant_id: violations.append("tenant scope mismatch")
    if getattr(deal,"source_of_truth",None)!="deal": violations.append("Deal source_of_truth is not authoritative.")
    if not isinstance(deal.version,int) or deal.version<1: violations.append("Deal version is invalid.")
    digest=hash_deal(deal)
    if expected_hash is not None and digest!=expected_hash: violations.append("Canonical Deal hash mismatch.")
    return DealIntegrityReport(not violations,deal.deal_id,deal.tenant_id,digest,("tenant_scope","source_of_truth","canonical_serialization","version","expected_hash"),tuple(violations))
__all__=["DealIntegrityReport","hash_deal","validate_deal_integrity"]
