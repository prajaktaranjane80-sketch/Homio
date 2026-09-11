import json
from pathlib import Path


def test_t26_contract():
    path = Path(__file__).with_name(
        "t26.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T26"

    assert (
        data["name"]
        == "Autonomous Execution Loop Controller"
    )

    assert (
        len(data["deep_audit"])
        == 26
    )

    assert (
        "execute shell commands"
        in data["forbidden"]
    )

    assert (
        "increase execution limits implicitly"
        in data["forbidden"]
    )
