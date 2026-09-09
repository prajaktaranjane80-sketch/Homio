from pathlib import Path
from .change_impact_analysis import ImpactPolicy, T17Provenance

def test_policy_is_read_only():
    p = ImpactPolicy(); p.validate(); assert p.allow_execution is False and p.allow_state_mutation is False

def test_provenance_is_control_center_bound():
    p = T17Provenance(); p.validate(); assert p.authority == "REOS_CONTROL_CENTER" and p.read_only is True
