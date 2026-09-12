from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .truth_fingerprint import digest
from .truth_models import ReconciliationPlan, SyncReceipt, SyncStatus


def build_receipt(plan: ReconciliationPlan, status: SyncStatus, synchronized: Iterable[str], blocked: Iterable[str]) -> SyncReceipt:
    synchronized_tuple = tuple(synchronized)
    blocked_tuple = tuple(blocked)
    payload = {
        "manifest_digest": plan.base_state_digest,
        "plan_id": plan.plan_id,
        "status": status.value,
        "synchronized_targets": synchronized_tuple,
        "blocked_targets": blocked_tuple,
    }
    return SyncReceipt(
        receipt_id=f"receipt-{digest(payload)[:20]}",
        manifest_digest=plan.base_state_digest,
        plan_id=plan.plan_id,
        status=status,
        synchronized_targets=synchronized_tuple,
        blocked_targets=blocked_tuple,
        receipt_digest=digest(payload),
    )
