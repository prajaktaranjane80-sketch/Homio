from pathlib import Path
from tempfile import TemporaryDirectory
import json
from .truth_sync_controller import CanonicalTruthSyncController
from .reconciliation_policy import ReconciliationPolicy
from .truth_models import CanonicalManifest, Conflict, ConflictSeverity


def test_critical_conflict_cannot_be_synchronized():
    manifest = CanonicalManifest("1", "HOMIO / REOS", "reos-development", "x", "data/state.json", "d", "c", "CORE-005", "task", None, "OK", tuple(), (Conflict("x", ConflictSeverity.CRITICAL, "gate", "a", "b", "x", "conflict"),), "m")
    plan = ReconciliationPolicy().plan(manifest)
    assert plan.blocked is True
