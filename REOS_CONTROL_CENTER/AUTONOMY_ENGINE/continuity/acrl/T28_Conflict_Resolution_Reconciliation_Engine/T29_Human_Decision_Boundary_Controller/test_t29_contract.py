import json
from pathlib import Path


def test_contract():
    path = Path(__file__).with_name("t29.contract.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["layer"] == "T29"
    assert data["name"] == "Human Decision Boundary Controller"
    assert "T28" in data["upstream_layers"]
    assert "T30" in data["downstream_layers"]
