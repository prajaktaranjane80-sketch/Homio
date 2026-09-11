import json
from pathlib import Path


def test_t22_contract_exists_and_is_complete():
    path = Path(__file__).with_name(
        "t22.contract.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["layer"] == "T22"
    assert data["schema_version"] == "1.0"

    audit = data["deep_audit"]

    assert len(audit) == 26

    for index in range(1, 27):
        key = f"{index:02d}_"

        assert any(
            item.startswith(key)
            for item in audit
        )

    assert (
        "execute commands"
        in data["forbidden"]
    )

    assert (
        "modify state.json"
        in data["forbidden"]
    )

    assert (
        "authorize itself"
        in data["forbidden"]
    )
