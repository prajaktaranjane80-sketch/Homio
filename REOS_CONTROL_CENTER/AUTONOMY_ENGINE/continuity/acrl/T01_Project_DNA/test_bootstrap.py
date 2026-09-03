"""Tests for T01 new-agent bootstrap."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .bootstrap import (
    bootstrap_is_safe_for_resume,
    build_project_bootstrap,
)
from .freshness import FreshnessPolicy


def _write_state(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)

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
            "type": "Global AI Real Estate OS",
            "north_star": "Test.",
            "operating_principle": "Test.",
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_bootstrap_contains_identity_and_authority(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

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
        freshness_policy=FreshnessPolicy(max_age_seconds=3600),
    )

    payload = bootstrap.to_dict()

    assert payload["identity"]["project_name"] == "HOMIO"
    assert payload["freshness"]["status"] == "CURRENT"
    assert payload["authority"]["execution_authorized"] is False
    assert payload["authority"]["write_authorized"] is False
    assert payload["authority"]["chat_memory_authoritative"] is False


def test_current_bootstrap_is_safe_for_resume(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

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
        freshness_policy=FreshnessPolicy(max_age_seconds=3600),
    )

    assert bootstrap_is_safe_for_resume(bootstrap) is True