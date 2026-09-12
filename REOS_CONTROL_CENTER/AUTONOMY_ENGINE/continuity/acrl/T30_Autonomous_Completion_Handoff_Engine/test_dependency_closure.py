from .dependency_closure import validate_dependency_closure

def test_dependency_closure_detects_missing_parent():
    ok, gaps = validate_dependency_closure({'B': ['A']}, {'B'})
    assert ok is False
    assert gaps == ['A']
