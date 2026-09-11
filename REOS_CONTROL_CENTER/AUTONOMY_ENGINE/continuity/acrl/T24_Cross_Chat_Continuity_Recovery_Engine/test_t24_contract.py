import json
from pathlib import Path


def test_t24_contract_is_complete():
    path = Path(__file__).with_name(
        "t24.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T24"

    assert (
        data["name"]
        == "Cross-Chat Continuity Recovery Engine"
    )

    assert (
        len(
            data["deep_audit"]
        )
        == 26
    )

    assert (
        "use chat history as authority"
        in data["forbidden"]
    )

    assert (
        "use GPT memory as authority"
        in data["forbidden"]
    )

    assert (
        "invent missing state"
        in data["forbidden"]
    )
