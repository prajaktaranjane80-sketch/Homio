from .regression_integration import validate_acrl_tree
from .regression_layer import RegressionDecision

def test_integration_uses_explicit_root(tmp_path):
    from .regression_registry import RegressionRegistry
    for spec in RegressionRegistry.SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    r=validate_acrl_tree(tmp_path)
    assert r.decision is RegressionDecision.READY
