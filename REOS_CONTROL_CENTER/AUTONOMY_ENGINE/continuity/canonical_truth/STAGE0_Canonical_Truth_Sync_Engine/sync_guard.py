from __future__ import annotations

from .truth_models import CanonicalManifest, ReconciliationPlan


class SyncGuardError(RuntimeError):
    pass


class SyncGuard:
    def validate(self, manifest: CanonicalManifest, plan: ReconciliationPlan) -> None:
        if plan.base_state_digest != manifest.state_digest:
            raise SyncGuardError("Plan is based on a different canonical state.")
        if plan.blocked:
            raise SyncGuardError(plan.reason)
        if manifest.current_gate == "":
            raise SyncGuardError("Canonical gate is empty.")
        if manifest.current_task == "":
            raise SyncGuardError("Canonical task is empty.")
