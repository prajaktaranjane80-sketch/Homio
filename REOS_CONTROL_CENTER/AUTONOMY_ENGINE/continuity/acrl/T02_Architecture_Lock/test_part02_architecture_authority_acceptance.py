"""L4 Part 02 acceptance tests — Architecture Authority Reconstruction."""

from __future__ import annotations

import json
from pathlib import Path

from .architecture_authority import (
    ArchitectureAuthorityReader,
)


def _write_state(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "schema_version": 3,
        },
        "constitution": {
            "canonical_source": "data/state.json",
            "architecture_before_code": True,
            "no_duplicate_logic": True,
            "no_silent_architecture_changes": True,
        },
        "architecture": {
            "approved": [
                {
                    "id": "ARCH-001",
                    "name": "Lead Generation Layer",
                    "status": "APPROVED",
                },
                {
                    "id": "ARCH-038",
                    "name": "Technology Stack Lock v1.0",
                    "status": "APPROVED",
                },
            ],
            "pending": [
                {
                    "id": "ARCH-039",
                    "name": "Master Blueprint v1.0",
                    "status": "PENDING",
                }
            ],
            "locked": False,
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


def test_l4_part02_reconstructs_architecture_authority(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    authority = ArchitectureAuthorityReader(
        tmp_path
    ).read()

    assert authority.canonical_source == (
        "data/state.json"
    )

    assert authority.status == (
        "APPROVED_NOT_FROZEN"
    )

    assert authority.locked is False

    assert authority.architecture_before_code is True

    assert authority.no_silent_architecture_changes is True

    assert authority.no_duplicate_logic is True

    assert (
        authority.approved[0][0]
        == "ARCH-001"
    )

    assert (
        authority.approved[-1][0]
        == "ARCH-038"
    )

    assert (
        authority.pending[0][0]
        == "ARCH-039"
    )

    assert len(
        authority.architecture_fingerprint
    ) == 64

    assert len(
        authority.source_state_sha256
    ) == 64


def test_l4_part02_does_not_grant_code_change_authority(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    authority = ArchitectureAuthorityReader(
        tmp_path
    ).read()

    assert authority.code_changes_allowed() is False

    payload = authority.to_dict()

    assert (
        payload["authority"]["execution_authorized"]
        is False
    )

    assert (
        payload["authority"]["write_authorized"]
        is False
    )

    assert (
        payload["authority"]["approval_authorized"]
        is False
    )


def test_l4_part02_does_not_claim_frozen_architecture(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    authority = ArchitectureAuthorityReader(
        tmp_path
    ).read()

    assert authority.is_frozen() is False

    assert authority.status != "FROZEN"
