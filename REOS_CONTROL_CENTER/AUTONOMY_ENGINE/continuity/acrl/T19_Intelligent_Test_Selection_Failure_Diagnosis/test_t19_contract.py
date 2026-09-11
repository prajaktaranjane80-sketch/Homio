from __future__ import annotations

import json
from pathlib import Path


def test_t19_contract_exists():
    path = Path(__file__).with_name(
        "t19.contract.json"
    )

    assert path.exists()


def test_t19_contract_is_valid_json():
    path = Path(__file__).with_name(
        "t19.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["layer"] == "T19"
    assert payload["schema_version"] == "1.0"


def test_t19_is_read_only():
    path = Path(__file__).with_name(
        "t19.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    capabilities = payload["capabilities"]

    assert capabilities["execution"] is False
    assert capabilities["repository_mutation"] is False
    assert capabilities["state_mutation"] is False
    assert capabilities["code_repair"] is False


def test_t19_has_complete_audit():
    path = Path(__file__).with_name(
        "t19.contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    audit = payload["deep_audit"]

    assert len(audit) == 26
    assert all(
        str(index).zfill(2) in key
        or key in {
            "10_security_boundary",
            "11_determinism",
            "12_concurrency",
            "13_recovery",
            "14_gpt_limitation_coverage",
            "15_new_agent_usability",
            "16_cross_chat_continuity",
            "17_read_capability",
            "18_write_capability",
            "19_testability",
            "20_observability",
            "21_integration_contract",
            "22_missing_layers",
            "23_authority_permission_boundary",
            "24_idempotency_replay_safety",
            "25_versioning_migration_compatibility",
            "26_adversarial_red_team_coverage",
        }
        for index, key in enumerate(
            audit.keys(),
            start=1,
        )
    )
