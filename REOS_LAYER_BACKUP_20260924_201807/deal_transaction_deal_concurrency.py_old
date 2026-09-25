"""Optimistic concurrency boundary for the Deal aggregate."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
class DealConcurrencyError(ValueError): pass
class DealConcurrencyScopeError(DealConcurrencyError): pass
class DealStaleWriteError(DealConcurrencyError): pass
class DealInvalidExpectedVersionError(DealConcurrencyError): pass
class DealConcurrencyOperation(str, Enum):
    READ="READ"; WRITE="WRITE"; TRANSITION="TRANSITION"; EVENT="EVENT"; REPLAY="REPLAY"
@dataclass(frozen=True)
class DealConcurrencyReceipt:
    deal_id: str; tenant_id: str; operation: DealConcurrencyOperation; expected_version: int; current_version: int
    @property
    def is_current(self)->bool: return self.expected_version == self.current_version
    def to_dict(self)->dict[str,Any]: return {"deal_id":self.deal_id,"tenant_id":self.tenant_id,"operation":self.operation.value,"expected_version":self.expected_version,"current_version":self.current_version,"is_current":self.is_current}
@dataclass(frozen=True)
class DealConcurrencyGuard:
    def assert_current(self, deal: Any, *, tenant_id: str, expected_version: int, operation: DealConcurrencyOperation=DealConcurrencyOperation.WRITE)->DealConcurrencyReceipt:
        if tenant_id != deal.tenant_id: raise DealConcurrencyScopeError("Deal concurrency request belongs to a different tenant.")
        if isinstance(expected_version,bool) or not isinstance(expected_version,int) or expected_version<1: raise DealInvalidExpectedVersionError("expected_version must be an integer >= 1.")
        if expected_version != deal.version: raise DealStaleWriteError(f"Deal operation targets stale version: expected {expected_version}, current {deal.version}.")
        return DealConcurrencyReceipt(deal.deal_id, deal.tenant_id, DealConcurrencyOperation(operation), expected_version, deal.version)
def assert_deal_version(deal: Any, *, tenant_id: str, expected_version: int, operation: DealConcurrencyOperation=DealConcurrencyOperation.WRITE)->DealConcurrencyReceipt:
    return DealConcurrencyGuard().assert_current(deal, tenant_id=tenant_id, expected_version=expected_version, operation=operation)
__all__=["DealConcurrencyError","DealConcurrencyGuard","DealConcurrencyOperation","DealConcurrencyReceipt","DealConcurrencyScopeError","DealInvalidExpectedVersionError","DealStaleWriteError","assert_deal_version"]
