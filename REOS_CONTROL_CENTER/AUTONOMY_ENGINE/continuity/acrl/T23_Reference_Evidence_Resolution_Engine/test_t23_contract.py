import json
from pathlib import Path


def test_t23_contract():
    path = Path(__file__).with_name(
        "t23.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T23"
    assert (
        data["name"]
        == "Reference / Evidence Resolution Engine"
    )

    assert (
        len(
            data["deep_audit"]
        )
        == 26
    )

    forbidden = data["forbidden"]

    assert (
        "execute shell commands"
        in forbidden
    )

    assert (
        "authorize itself"
        in forbidden
    )

    assert (
        "invent missing evidence"
        in forbidden
    )
