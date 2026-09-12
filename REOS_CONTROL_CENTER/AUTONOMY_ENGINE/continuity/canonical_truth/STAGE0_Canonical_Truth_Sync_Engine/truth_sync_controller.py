from __future__ import annotations

from pathlib import Path

from .authority_registry import AuthorityRegistry
from .canonical_manifest import build_manifest
from .conflict_detector import ConflictDetector
from .derived_artifact_reader import DerivedArtifactReader
from .derived_sync_engine import DerivedSyncEngine
from .git_truth_reader import GitTruthReader
from .health_report import build_report
from .reconciliation_policy import ReconciliationPolicy
from .sync_guard import SyncGuard
from .truth_fingerprint import digest
from .truth_models import ArtifactTruth, ConflictSeverity, SyncStatus
from .state_reader import CanonicalStateReader


class TruthSyncError(RuntimeError):
    pass


class CanonicalTruthSyncController:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.registry = AuthorityRegistry()
        self.registry.validate()
        self.state_reader = CanonicalStateReader(self.root)
        self.git_reader = GitTruthReader(self.root)
        self.artifact_reader = DerivedArtifactReader(self.root)
        self.detector = ConflictDetector()
        self.policy = ReconciliationPolicy()
        self.guard = SyncGuard()
        self.derived_sync = DerivedSyncEngine(self.root)

    def inspect(self) -> dict:
        state = self.state_reader.read()
        execution = self.state_reader.execution_projection(state)
        state_digest = self.state_reader.digest(state)
        git = self.git_reader.read()

        authority = ArtifactTruth(
            artifact_id="canonical-state",
            path=self.state_reader.path.as_posix(),
            role=self.artifact_reader.classifier.classify(self.state_reader.path, self.root),
            present=True,
            digest=state_digest,
            semantic_digest=state_digest,
            claims={
                "current_gate": execution["current_gate"],
                "current_task": execution["current_task"],
                "current_subtask": execution["current_subtask"],
                "status": execution["status"],
            },
        )

        paths = [
            ("next-chat", self.root / "REOS_NEXT_CHAT.txt"),
            ("continuity-state", self.root / "PROJECT_CONTINUITY" / "continuity_state.json"),
            ("truth-manifest", self.root / "artifacts" / "truth_sync" / "truth_manifest.json"),
        ]
        derived = [self.artifact_reader.inspect(path, artifact_id) for artifact_id, path in paths]
        conflicts = self.detector.compare(authority, derived)
        manifest = build_manifest(
            project=self.registry.project,
            branch=git.branch,
            authority_id="REOS_CONTROL_CENTER/data/state.json",
            canonical_state_path=self.state_reader.path.as_posix(),
            state_digest=state_digest,
            state_revision=git.commit,
            execution=execution,
            derived_artifacts=derived,
            conflicts=conflicts,
        )
        plan = self.policy.plan(manifest)
        return {
            "manifest": manifest,
            "plan": plan,
            "git": git,
            "authority": authority,
        }

    def synchronize(self):
        bundle = self.inspect()
        manifest = bundle["manifest"]
        plan = bundle["plan"]
        self.guard.validate(manifest, plan)
        receipt = self.derived_sync.synchronize(manifest, plan)
        report = build_report(manifest, plan, receipt)
        return manifest, plan, receipt, report
