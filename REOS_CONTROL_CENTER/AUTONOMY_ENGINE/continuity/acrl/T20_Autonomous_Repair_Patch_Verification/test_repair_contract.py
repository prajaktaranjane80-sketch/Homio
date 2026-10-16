from __future__ import annotations

import json
from pathlib import Path

from .patch_verification import tree_fingerprint


def test_t20_contract_exists():
    path = Path(__file__).with_name(
        "t20.contract.json"
    )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert payload["layer"] == "T20"
    assert payload["schema_version"] == "1.0"
    assert len(payload["deep_audit"]) == 26
    assert (
        "26_adversarial_red_team_coverage"
        in payload["deep_audit"]
    )
    assert (
        payload["t21_handoff"]["result_field"]
        == "RepairResult.candidate_patch"
    )
    assert (
        "does not authorize Git writes"
        in payload["t21_handoff"]["authority_rule"]
    )


def test_t20_forbids_main_mutation():
    path = Path(__file__).with_name(
        "t20.contract.json"
    )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    forbidden = set(payload["forbidden"])

    assert "state.json mutation" in forbidden
    assert "main repository mutation" in forbidden
    assert "self approval" in forbidden


def test_t20_tree_fingerprint_excludes_t21_lock_file(
    tmp_path: Path,
):
    source = tmp_path / "source.py"
    source.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    baseline = tree_fingerprint(tmp_path)

    lock_file = tmp_path / ".reos_t21_transaction.lock"
    lock_file.write_text(
        "12345\n",
        encoding="utf-8",
    )

    assert tree_fingerprint(tmp_path) == baseline
