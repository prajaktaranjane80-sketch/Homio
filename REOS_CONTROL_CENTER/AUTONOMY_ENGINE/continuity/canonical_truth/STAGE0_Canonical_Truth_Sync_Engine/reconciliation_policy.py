from __future__ import annotations

from .truth_models import CanonicalManifest, ConflictSeverity, ReconciliationPlan


class ReconciliationPolicy:
    def plan(self, manifest: CanonicalManifest) -> ReconciliationPlan:
        critical = [c for c in manifest.conflicts if c.severity == ConflictSeverity.CRITICAL]
        high = [c for c in manifest.conflicts if c.severity == ConflictSeverity.HIGH]
        targets = tuple(a.path for a in manifest.derived_artifacts if a.role.value == "DERIVED")
        if critical:
            return ReconciliationPlan(
                plan_id=f"BLOCK-{manifest.manifest_digest[:16]}",
                base_state_digest=manifest.state_digest,
                actions=(),
                targets=targets,
                blocked=True,
                reason="Critical canonical-state conflict detected; derived synchronization is blocked until authoritative state is verified.",
            )
        if high:
            return ReconciliationPlan(
                plan_id=f"REVIEW-{manifest.manifest_digest[:16]}",
                base_state_digest=manifest.state_digest,
                actions=("REBUILD_DERIVED_ARTIFACTS",),
                targets=targets,
                blocked=False,
                reason="High-severity derived drift detected; rebuild derived artifacts from canonical state.",
            )
        return ReconciliationPlan(
            plan_id=f"SYNC-{manifest.manifest_digest[:16]}",
            base_state_digest=manifest.state_digest,
            actions=("ENSURE_DERIVED_ARTIFACTS",),
            targets=targets,
            blocked=False,
            reason="Canonical state is internally authoritative and derived artifacts may be synchronized.",
        )
