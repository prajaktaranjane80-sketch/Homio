from __future__ import annotations

import json
from pathlib import Path


def test_t20_contract_exists():
    path = Path(__file__).with_name(
        "t20.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["layer"] == "T20"
    assert payload["schema_version"] == "1.0"
    assert len(payload["deep_audit"]) == 26
    assert (
        "26_adversarial_red_team_coverage"
        in payload["deep_audit"]
    )


def test_t20_forbids_main_mutation():
    path = Path(__file__).with_name(
        "t20.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    forbidden = set(
        payload["forbidden"]
    )

    assert "state.json mutation" in forbidden
    assert "main repository mutation" in forbidden
    assert "self approval" in forbidden
