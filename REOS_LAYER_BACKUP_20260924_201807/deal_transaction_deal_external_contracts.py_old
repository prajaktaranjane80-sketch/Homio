"""External authority contracts for CORE-006.

Deal consumes authoritative references/decisions from other domains; it does
not recreate ownership, evidence, governance, fraud, commission, identity,
event-transport or AI engines.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

class DealExternalAuthority(str, Enum):
    OWNERSHIP = "ARCH-011"
    EVIDENCE = "ARCH-014"
    GOVERNANCE = "ARCH-017"
    POLICY = "ARCH-018"
    EVENT_TRANSPORT = "CORE-002"
    IDENTITY = "CORE-001"
    FRAUD = "CORE-007"
    COMMISSION = "CORE-008"
    AI = "AI"

class DealExternalContractError(ValueError):
    pass

@dataclass(frozen=True)
class DealExternalReference:
    deal_id: str
    tenant_id: str
    authority: DealExternalAuthority
    reference_id: str
    reference_type: str
    authority_version: str
    created_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("deal_id", "tenant_id", "reference_id", "reference_type", "authority_version", "created_at"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise DealExternalContractError(f"{name} is required.")

    def assert_scope(self, *, deal_id: str, tenant_id: str) -> None:
        if self.deal_id != deal_id or self.tenant_id != tenant_id:
            raise DealExternalContractError("External reference crosses Deal scope.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "authority": self.authority.value,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "authority_version": self.authority_version,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

@dataclass(frozen=True)
class DealExternalDecision:
    decision_id: str
    deal_id: str
    tenant_id: str
    authority: DealExternalAuthority
    outcome: str
    policy_version: str
    decided_at: str
    input_fingerprint: str
    evidence_reference_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("decision_id", "deal_id", "tenant_id", "outcome", "policy_version", "decided_at", "input_fingerprint"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise DealExternalContractError(f"{name} is required.")

    def assert_scope(self, *, deal_id: str, tenant_id: str) -> None:
        if self.deal_id != deal_id or self.tenant_id != tenant_id:
            raise DealExternalContractError("External decision crosses Deal scope.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "authority": self.authority.value,
            "outcome": self.outcome,
            "policy_version": self.policy_version,
            "decided_at": self.decided_at,
            "input_fingerprint": self.input_fingerprint,
            "evidence_reference_ids": list(self.evidence_reference_ids),
            "metadata": dict(self.metadata),
        }

__all__ = ["DealExternalAuthority", "DealExternalContractError", "DealExternalDecision", "DealExternalReference"]
