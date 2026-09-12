import json
from pathlib import Path


def test_t27_contract():
    path = Path(__file__).with_name(
        "t27.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T27"
    assert (
        data["name"]
        == "Dependency-Aware Work Scheduler"
    )
    assert len(
        data["deep_audit"]
    ) == 26
