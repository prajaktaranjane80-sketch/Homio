"""L4 Part 01 acceptance tests — Canonical Project Identity Foundation.

This test verifies that the existing T01 Project DNA capability provides the
minimum authoritative identity required to start a fresh HOMIO / REOS session.

No new continuity logic is implemented here.
The test only verifies the existing T01 capability against the L4 Part 01
milestone contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .bootstrap import build_project_bootstrap
from .freshness import FreshnessPolicy


def _write_authoritative_state(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "version": "3.4",
            "schema_version": 3,
            "updated_at": "2026-08-30T11:59:00+00:00",
            "control_center_version": "7.0",
        },
        "constitution": {
            "canonical_source": "data/state.json",
            "architecture_before_code": True,
            "single_source_of_truth": True,
            "micro_modular": True,
            "no_duplicate_logic": True,
            "no_silent_architecture_changes": True,
            "chat_history_is_not_project_memory": True,
        },
        "project": {
            "name": "HOMIO",
            "type": "Global AI Real Estate OS + International Brokerage + SaaS",
            "north_star": (
                "Generate genuine property demand, acquire verified inventory, "
                "protect lead/deal ownership, protect commission, automate "
                "operations, and scale internationally."
            ),
            "operating_principle": (
                "AI automates; governance controls; evidence protects; "
                "humans approve irreversible/high-risk actions."
            ),
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_l4_part01_canonical_project_identity_contract(
    tmp_path: Path,
) -> None:
    """Verify the complete Part 01 identity contract in one machine test."""

    _write_authoritative_state(tmp_path)

    bootstrap = build_project_bootstrap(
        tmp_path,
        observed_at=datetime(
            2026,
            8,
            30,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        ),
        freshness_policy=FreshnessPolicy(
            max_age_seconds=3600,
        ),
    )

    payload = bootstrap.to_dict()

    identity = payload["identity"]
    project_dna = payload["project_dna"]
    dna_authority = project_dna["authority"]
    dna_fingerprint = project_dna["fingerprint"]
    bootstrap_authority = payload["authority"]

    # 1. HOMIO / REOS identity.
    assert identity["product"] == "HOMIO / REOS"

    # 2. Project = HOMIO.
    assert identity["project_name"] == "HOMIO"

    # 3. Canonical state = data/state.json.
    assert (
        dna_authority["canonical_source"]
        == "data/state.json"
    )

    # 4. Chat memory is non-authoritative.
    assert (
        dna_authority["chat_history_is_not_project_memory"]
        is True
    )
    assert (
        bootstrap_authority["chat_memory_authoritative"]
        is False
    )

    # 5. Architecture-before-code is enforced.
    assert (
        dna_authority["architecture_before_code"]
        is True
    )

    # 6. Duplicate logic is forbidden.
    assert (
        dna_authority["no_duplicate_logic"]
        is True
    )

    # 7. State fingerprint is available.
    assert (
        isinstance(
            dna_fingerprint["source_state_sha256"],
            str,
        )
    )
    assert len(
        dna_fingerprint["source_state_sha256"]
    ) == 64

    assert (
        isinstance(
            dna_fingerprint["semantic_state_sha256"],
            str,
        )
    )
    assert len(
        dna_fingerprint["semantic_state_sha256"]
    ) == 64

    # 8. Execution / write / approval authority is NOT GRANTED.
    assert (
        bootstrap_authority["execution_authorized"]
        is False
    )
    assert (
        bootstrap_authority["write_authorized"]
        is False
    )
    assert (
        bootstrap_authority["approval_authorized"]
        is False
    )
