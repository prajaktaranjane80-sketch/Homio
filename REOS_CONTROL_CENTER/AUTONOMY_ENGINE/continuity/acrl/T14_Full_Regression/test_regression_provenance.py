from .regression_provenance import RegressionProvenance

def test_provenance_defaults_valid():
    RegressionProvenance().validate()

def test_provenance_is_bounded_to_t01_t13():
    p=RegressionProvenance(upstream_layers=tuple(range(1,14))); p.validate()
    bad=RegressionProvenance(upstream_layers=tuple(range(1,15)))
    try: bad.validate()
    except ValueError: return
    assert False
