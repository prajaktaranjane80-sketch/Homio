from __future__ import annotations

from dataclasses import dataclass

from .truth_models import CanonicalManifest, ReconciliationPlan, SyncReceipt


@dataclass(frozen=True)
class TruthHealthReport:
    healthy: bool
    authority_ok: bool
    state_ok: bool
    derived_ok: bool
    conflict_count: int
    message: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def build_report(manifest: CanonicalManifest, plan: ReconciliationPlan, receipt: SyncReceipt | None) -> TruthHealthReport:
    conflict_count = len(manifest.conflicts)
    authority_ok = manifest.canonical_state_path.endswith("data/state.json")
    state_ok = bool(manifest.state_digest and manifest.current_gate and manifest.current_task)
    derived_ok = receipt is not None and not plan.blocked
    healthy = authority_ok and state_ok and derived_ok and conflict_count == 0
    return TruthHealthReport(
        healthy=healthy,
        authority_ok=authority_ok,
        state_ok=state_ok,
        derived_ok=derived_ok,
        conflict_count=conflict_count,
        message="Truth plane healthy." if healthy else "Truth plane requires reconciliation or investigation.",
    )
