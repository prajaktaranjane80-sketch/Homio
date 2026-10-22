from __future__ import annotations

import json
from pathlib import Path


def _contract():
    path = Path(__file__).with_name("t21.contract.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_t21_contract():
    payload = _contract()

    assert payload["layer"] == "T21"
    assert payload["schema_version"] == "1.0"
    assert len(payload["deep_audit"]) == 26


def test_force_push_is_forbidden():
    payload = _contract()
    assert "force push" in payload["forbidden"]


def test_repair_write_requires_t20_verified_patch():
    payload = _contract()
    handoff = payload["repair_handoff"]

    assert handoff["required_decision"] == "VERIFIED"
    assert handoff["patch_source"] == "RepairResult.candidate_patch"
    assert "must match" in handoff["fingerprint"]
    assert "T18 authorizes" in handoff["authority"]


def test_replay_claim_does_not_overstate_capability():
    payload = _contract()

    assert (
        "persistent replay prevention is not claimed"
        in payload["deep_audit"]["24_idempotency_replay_safety"]
    )


def test_api_error_recovery_policy_is_present():
    recovery = _contract()["api_error_recovery"]

    assert recovery["component"] == "github_api_error_recovery"
    assert "readback" in recovery["409"].lower()
    assert "silently switch branches" in recovery["404"]
    assert "bounded retries" in recovery["429"]
    assert "readback" in recovery["timeout_or_network_failure"]
