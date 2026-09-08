from .regression_layer import RegressionLayerEngine


def test_missing_layer_fails_closed(tmp_path):
    for spec in RegressionLayerEngine.LAYER_SPECS[1:]:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    r=RegressionLayerEngine.validate_all_layers(tmp_path)
    assert r.fail_closed
    assert not r.ready


def test_missing_test_fails_closed(tmp_path):
    for spec in RegressionLayerEngine.LAYER_SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n')
    r=RegressionLayerEngine.validate_all_layers(tmp_path)
    assert r.fail_closed
    assert not r.ready


def test_valid_test_source_is_not_imported(tmp_path):
    for spec in RegressionLayerEngine.LAYER_SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    # Valid syntax but import would raise. T14 must inspect, not import, tests.
    (tmp_path/'T12_Resume_Safety_Validation'/'test_explosive.py').write_text('raise RuntimeError("must not import")\n')
    r=RegressionLayerEngine.validate_all_layers(tmp_path)
    assert r.ready
