"""Replay and reconstruction verification for CORE-006 transaction history."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Any
class DealReplayError(ValueError):
    """Base replay verification error."""
@dataclass(frozen=True)
class DealReplayViolation:
    code: str
    message: str
    sequence: int | None = None
    deal_version: int | None = None
@dataclass(frozen=True)
class DealReplayResult:
    valid: bool
    deal_id: str
    tenant_id: str
    reconstructed_status: str | None
    event_count: int
    violations: tuple[DealReplayViolation, ...] = ()
    def require_valid(self) -> "DealReplayResult":
        if not self.valid:
            raise DealReplayError("; ".join(v.message for v in self.violations))
        return self
def verify_transaction_replay(milestones: Iterable[Any], *, deal_id: str, tenant_id: str, initial_status: str | None = None) -> DealReplayResult:
    items = tuple(sorted(tuple(milestones), key=lambda x: (x.sequence, x.deal_version)))
    violations: list[DealReplayViolation] = []
    seen_ids: set[str] = set()
    previous_status = initial_status
    previous_version = 0
    expected_sequence = 1
    for milestone in items:
        fs = getattr(milestone.from_status, "value", milestone.from_status)
        ts = getattr(milestone.to_status, "value", milestone.to_status)
        if milestone.deal_id != deal_id:
            violations.append(DealReplayViolation("DEAL_SCOPE", "Milestone belongs to a different deal.", milestone.sequence, milestone.deal_version))
        if milestone.tenant_id != tenant_id:
            violations.append(DealReplayViolation("TENANT_SCOPE", "Milestone belongs to a different tenant.", milestone.sequence, milestone.deal_version))
        if milestone.milestone_id in seen_ids:
            violations.append(DealReplayViolation("DUPLICATE_MILESTONE_ID", "Duplicate milestone identity detected.", milestone.sequence, milestone.deal_version))
        seen_ids.add(milestone.milestone_id)
        if milestone.sequence != expected_sequence:
            violations.append(DealReplayViolation("SEQUENCE_GAP", f"Expected milestone sequence {expected_sequence}, got {milestone.sequence}.", milestone.sequence, milestone.deal_version))
        if milestone.deal_version <= previous_version:
            violations.append(DealReplayViolation("VERSION_REGRESSION", "Transaction milestone deal_version must strictly increase.", milestone.sequence, milestone.deal_version))
        if previous_status is not None and fs != previous_status:
            violations.append(DealReplayViolation("STATUS_CHAIN_BREAK", f"Replay expected from_status={previous_status}, got {fs}.", milestone.sequence, milestone.deal_version))
        previous_status, previous_version, expected_sequence = ts, milestone.deal_version, expected_sequence + 1
    return DealReplayResult(not violations, deal_id, tenant_id, previous_status, len(items), tuple(violations))
__all__ = ["DealReplayError", "DealReplayResult", "DealReplayViolation", "verify_transaction_replay"]
