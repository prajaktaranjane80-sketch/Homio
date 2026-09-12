from __future__ import annotations

from .truth_models import ArtifactTruth, Conflict, ConflictSeverity


class ConflictDetector:
    def compare(self, authority: ArtifactTruth, derived: list[ArtifactTruth]) -> tuple[Conflict, ...]:
        conflicts: list[Conflict] = []
        authoritative = dict(authority.claims)
        for artifact in derived:
            if not artifact.present:
                continue
            observed = dict(artifact.claims)
            for field in ("current_gate", "current_task", "current_subtask", "status"):
                expected = authoritative.get(field)
                actual = observed.get(field)
                if actual in (None, ""):
                    continue
                if expected != actual:
                    conflicts.append(
                        Conflict(
                            conflict_id=f"STATE-{artifact.artifact_id}-{field}",
                            severity=ConflictSeverity.CRITICAL if field in {"current_gate", "current_subtask"} else ConflictSeverity.HIGH,
                            subject=field,
                            authoritative_value=expected,
                            observed_value=actual,
                            source_path=artifact.path,
                            reason="Derived artifact disagrees with canonical execution state.",
                        )
                    )
        return tuple(conflicts)
