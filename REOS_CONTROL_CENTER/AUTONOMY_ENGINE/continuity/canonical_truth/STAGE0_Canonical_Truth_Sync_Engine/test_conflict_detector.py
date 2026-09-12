from .conflict_detector import ConflictDetector
from .truth_models import ArtifactTruth, TruthRole, ConflictSeverity


def test_critical_gate_conflict():
    authority = ArtifactTruth("a", "state.json", TruthRole.AUTHORITATIVE, True, "x", "x", {"current_gate": "CORE-005"})
    derived = [ArtifactTruth("d", "REOS_NEXT_CHAT.txt", TruthRole.DERIVED, True, "y", "y", {"current_gate": "CORE-004"})]
    conflicts = ConflictDetector().compare(authority, derived)
    assert conflicts
    assert conflicts[0].severity == ConflictSeverity.CRITICAL
