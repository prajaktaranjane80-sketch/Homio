import json
from pathlib import Path


def test_t25_contract():
    path = Path(__file__).with_name(
        "t25.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T25"

    assert (
        data["name"]
        == "Context / Token / Work-Budget Manager"
    )

    assert (
        len(
            data["deep_audit"]
        )
        == 26
    )

    assert (
        "execute work"
        in data["forbidden"]
    )

    assert (
        "increase limits implicitly"
        in data["forbidden"]
    )
