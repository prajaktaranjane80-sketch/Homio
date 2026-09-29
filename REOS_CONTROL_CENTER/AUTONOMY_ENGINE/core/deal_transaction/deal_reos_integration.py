from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DealREOSContract:
    contract_version: str
    deal_id: str
    tenant_id: str
    control_center_authoritative: bool
    state_mutation_authorized: bool
    source_of_truth: str
    current_status: str
    current_version: int
    discoverable_tasks: tuple[str, ...]
    verification_contract: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "control_center_authoritative": (
                self.control_center_authoritative
            ),
            "state_mutation_authorized": (
                self.state_mutation_authorized
            ),
            "source_of_truth": self.source_of_truth,
            "current_status": self.current_status,
            "current_version": self.current_version,
            "discoverable_tasks": list(
                self.discoverable_tasks
            ),
            "verification_contract": (
                self.verification_contract
            ),
        }


def build_reos_contract(
    deal: Any,
) -> DealREOSContract:
    return DealREOSContract(
        contract_version="1.0",
        deal_id=deal.deal_id,
        tenant_id=deal.tenant_id,
        control_center_authoritative=True,
        state_mutation_authorized=False,
        source_of_truth="deal",
        current_status=getattr(
            deal.status,
            "value",
            deal.status,
        ),
        current_version=deal.version,
        discoverable_tasks=(
            "CORE-006-T06",
            "CORE-006-T07",
            "CORE-006-T08",
            "CORE-006-T09",
            "CORE-006-T10",
        ),
        verification_contract="REOS_CONTROL_CENTER",
    )
