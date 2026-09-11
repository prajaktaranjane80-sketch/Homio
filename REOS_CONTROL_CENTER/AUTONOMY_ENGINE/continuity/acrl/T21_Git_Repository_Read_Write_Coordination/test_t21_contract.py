from __future__ import annotations

import json
from pathlib import Path


def test_t21_contract():
    path = Path(__file__).with_name(
        "t21.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["layer"] == "T21"
    assert payload["schema_version"] == "1.0"
    assert len(
        payload["deep_audit"]
    ) == 26


def test_force_push_is_forbidden():
    path = Path(__file__).with_name(
        "t21.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "force push"
        in payload["forbidden"]
    )
