from .regression_layer import RegressionLayerEngine, RegressionDecision
from pathlib import Path

def test_full_tree_ready(tmp_path):
    for spec in RegressionLayerEngine.LAYER_SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    r=RegressionLayerEngine.validate_all_layers(tmp_path)
    assert r.decision is RegressionDecision.READY and r.ready

def test_syntax_failure_is_fail_closed(tmp_path):
    for spec in RegressionLayerEngine.LAYER_SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    (tmp_path/'T12_Resume_Safety_Validation'/'test_bad.py').write_text('def broken(:\n')
    r=RegressionLayerEngine.validate_all_layers(tmp_path)
    assert r.fail_closed and r.decision is RegressionDecision.FAIL_CLOSED
