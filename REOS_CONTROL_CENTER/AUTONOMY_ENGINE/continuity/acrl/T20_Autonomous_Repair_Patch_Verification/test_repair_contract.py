from __future__ import annotations

import json
from pathlib import Path

from .patch_verification import tree_fingerprint


def _contract():
    path = Path(__file__).with_name("t20.contract.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_t20_contract_exists():
    payload = _contract()

    assert payload["layer"] == "T20"
    assert payload["schema_version"] == "1.0"
    assert len(payload["deep_audit"]) == 26
    assert "26_adversarial_red_team_coverage" in payload["deep_audit"]

    assert payload["t21_handoff"]["result_field"] == (
        "RepairResult.candidate_patch"
    )
    assert "does not authorize Git writes" in (
        payload["t21_handoff"]["authority_rule"]
    )


def test_non_python_external_verification_is_contractually_required():
    external = _contract()["external_verification"]

    assert external["required_for_non_python_changes"] is True
    assert "run_id" in external["evidence_fields"]
    assert "source_commit_sha" in external["evidence_fields"]
    assert "result_fingerprint" in external["evidence_fields"]
    assert "must not produce VERIFIED" in external["failure_policy"]


def test_t20_forbids_main_mutation():
    forbidden = set(_contract()["forbidden"])

    assert "state.json mutation" in forbidden
    assert "main repository mutation" in forbidden
    assert "self approval" in forbidden


def test_t20_tree_fingerprint_excludes_t21_lock_file(
    tmp_path: Path,
):
    source = tmp_path / "source.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    baseline = tree_fingerprint(tmp_path)

    lock_file = tmp_path / ".reos_t21_transaction.lock"
    lock_file.write_text("12345\n", encoding="utf-8")

    assert tree_fingerprint(tmp_path) == baseline
