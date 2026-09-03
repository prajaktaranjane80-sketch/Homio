"""ACRL T01 — final integration tests."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from AUTONOMY_ENGINE.continuity.acrl.T01_Project_DNA.health import (
    T01HealthStatus,
    evaluate_t01_health,
)
from AUTONOMY_ENGINE.continuity.acrl.T01_Project_DNA.linking import (
    build_t01_linked_context,
)
from AUTONOMY_ENGINE.continuity.acrl.T01_Project_DNA.project_dna import (
    ProjectDNAReader,
)
from AUTONOMY_ENGINE.continuity.acrl.T01_Project_DNA.freshness import (
    FreshnessPolicy,
)


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
            "type": "Global AI Real Estate OS + SaaS",
            "north_star": "Build the operating system for global real estate.",
            "operating_principle": (
                "AI automates; governance controls; evidence protects."
            ),
        },
        "phases": {
            "current": "PRE-CODING ARCHITECTURE",
        },
    }

    (data / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_t01_links_all_capabilities(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = build_t01_linked_context(
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
            max_age_seconds=3600
        ),
    )

    assert context.dna.project_name == "HOMIO"
    assert context.identity.project_name == "HOMIO"
    assert len(context.fingerprints.semantic_state_sha256) == 64
    assert context.observation.source_sha256 == (
        context.dna.source_state_sha256
    )
    assert context.provenance.source_fingerprint == (
        context.observation.source_sha256
    )
    assert context.freshness.status.value == "CURRENT"
    assert context.compatibility.status.value == "SUPPORTED"


def test_t01_health_is_ready_for_current_state(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = build_t01_linked_context(
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
            max_age_seconds=3600
        ),
    )

    health = evaluate_t01_health(context)

    assert health.status == T01HealthStatus.READY
    assert health.resume_safe is True
    assert health.execution_authorized is False
    assert health.write_authorized is False


def test_t01_linked_context_is_deterministic(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    observed_at = datetime(
        2026,
        8,
        30,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    policy = FreshnessPolicy(
        max_age_seconds=3600
    )

    first = build_t01_linked_context(
        tmp_path,
        observed_at=observed_at,
        freshness_policy=policy,
    )

    second = build_t01_linked_context(
        tmp_path,
        observed_at=observed_at,
        freshness_policy=policy,
    )

    assert first.dna == second.dna
    assert first.identity == second.identity
    assert first.fingerprints == second.fingerprints
    assert first.observation.source_sha256 == (
        second.observation.source_sha256
    )
    assert first.freshness.status == second.freshness.status
    assert first.compatibility == second.compatibility


def test_t01_never_grants_execution_or_write_authority(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = build_t01_linked_context(
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
            max_age_seconds=3600
        ),
    )

    payload = context.to_dict()

    assert payload["authority"]["execution_authorized"] is False
    assert payload["authority"]["write_authorized"] is False
    assert payload["authority"]["approval_authorized"] is False
    assert payload["authority"]["recovery_authorized"] is False
    assert payload["authority"]["migration_authorized"] is False


def test_t01_health_blocks_old_state(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    context = build_t01_linked_context(
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
            max_age_seconds=30
        ),
    )

    health = evaluate_t01_health(context)

    assert health.status == T01HealthStatus.BLOCKED
    assert health.resume_safe is False
    assert health.execution_authorized is False
    assert health.write_authorized is False
    assert "stale" in " ".join(health.reasons).lower()


def test_t01_uses_existing_project_dna_reader(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    dna = ProjectDNAReader(tmp_path).read()

    assert dna.project_name == "HOMIO"
    assert dna.canonical_source == "data/state.json"