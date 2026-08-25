
from core.semantic_consistency import SemanticConsistencyEngine, SemanticField

def resolver(path, value):
    mapping = {
        "execution_plan.status": SemanticField(
            path, value, "execution", "progress", "gate-sequence", "control-center"
        ),
        "architecture.status": SemanticField(
            path, value, "architecture", "governance", "approval", "architecture-registry"
        ),
    }
    return mapping.get(path)

def test_different_lifecycle_dimensions_are_not_contradictions():
    engine = SemanticConsistencyEngine(resolver)
    result = engine.compare(
        "execution_plan.status", "COMPLETE",
        "architecture.status", "PENDING",
    )
    assert result.status == "NOT_COMPARABLE"
