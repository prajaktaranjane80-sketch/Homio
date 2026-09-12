from .semantic_normalizer import canonical_json


def test_volatile_fields_do_not_drift_truth():
    a = {"execution": {"current_gate": "CORE-005"}, "updated_at": "1"}
    b = {"updated_at": "999", "execution": {"current_gate": "CORE-005"}}
    assert canonical_json(a) == canonical_json(b)
