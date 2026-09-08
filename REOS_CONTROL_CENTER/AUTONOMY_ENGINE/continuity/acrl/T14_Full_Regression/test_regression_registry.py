from pathlib import Path
from .regression_registry import RegressionRegistry

def test_registry_is_contiguous():
    RegressionRegistry.validate()
    assert tuple(x.layer_number for x in RegressionRegistry.SPECS)==tuple(range(1,15))

def test_registry_contains_t12():
    x=RegressionRegistry.SPECS[11]
    assert x.directory=='T12_Resume_Safety_Validation'
    assert x.core_file=='resume_safety_validation.py'

def test_discovery_finds_test_files(tmp_path):
    for spec in RegressionRegistry.SPECS:
        d=tmp_path/spec.directory; d.mkdir(); (d/spec.core_file).write_text('x=1\n'); (d/'test_one.py').write_text('def test_x():\n    assert True\n')
    found=RegressionRegistry.discover(tmp_path)
    assert all(found[s][2] for s in RegressionRegistry.SPECS)
