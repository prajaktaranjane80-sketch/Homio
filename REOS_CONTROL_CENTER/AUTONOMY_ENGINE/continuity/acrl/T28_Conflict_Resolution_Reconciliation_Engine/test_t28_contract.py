import json
from pathlib import Path


def test_contract():
    path = Path(__file__).with_name("t28.contract.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["layer"] == "T28"
    assert data["name"] == "Conflict Resolution & Reconciliation Engine"
    assert "T27" in data["upstream_layers"]
    assert "T29" in data["downstream_layers"]
