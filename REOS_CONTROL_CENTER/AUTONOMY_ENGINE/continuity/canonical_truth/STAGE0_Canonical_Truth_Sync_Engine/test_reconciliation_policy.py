from .reconciliation_policy import ReconciliationPolicy
from .truth_models import CanonicalManifest, Conflict, ConflictSeverity, ArtifactTruth, TruthRole


def manifest(conflicts):
    return CanonicalManifest("1", "HOMIO / REOS", "reos-development", "x", "data/state.json", "d", "c", "g", "t", None, "OK", tuple(), tuple(conflicts), "m")


def test_critical_conflict_blocks():
    c = Conflict("x", ConflictSeverity.CRITICAL, "current_gate", "A", "B", "x", "bad")
    assert ReconciliationPolicy().plan(manifest([c])).blocked
