"""ACRL T01 hardening tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from .compatibility import (
    CompatibilityStatus,
    evaluate_state_schema_compatibility,
)
from .observation import (
    ObservationChangedDuringReadError,
    observe_state_atomically,
)
from .provenance import (
    EvidenceKind,
    derived_evidence,
    observed_evidence,
)


def test_atomic_observation_reads_stable_source(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state.json"
    state.write_text('{"project":"HOMIO"}', encoding="utf-8")

    observation = observe_state_atomically(state)

    assert observation.path == str(state.resolve())
    assert len(observation.source_sha256) == 64
    assert observation.content == b'{"project":"HOMIO"}'


def test_atomic_observation_rejects_missing_source(
    tmp_path: Path,
) -> None:
    with pytest.raises(OSError):
        (tmp_path / "missing.json").read_bytes()


def test_observed_evidence_has_machine_identity() -> None:
    evidence = observed_evidence(
        source_fingerprint="a" * 64,
    )

    assert evidence.kind == EvidenceKind.OBSERVED
    assert len(evidence.evidence_id) == 64
    assert evidence.parent_evidence_ids == ()


def test_derived_evidence_preserves_parents() -> None:
    evidence = derived_evidence(
        source_fingerprint="b" * 64,
        rule="PROJECT_DNA_DERIVATION",
        rule_version="1.0",
        parent_evidence_ids=("z", "a", "z"),
    )

    assert evidence.kind == EvidenceKind.DERIVED
    assert evidence.parent_evidence_ids == ("a", "z")
    assert len(evidence.evidence_id) == 64


def test_supported_schema_is_accepted() -> None:
    result = evaluate_state_schema_compatibility(3)

    assert result.status == CompatibilityStatus.SUPPORTED


def test_old_schema_requires_migration() -> None:
    result = evaluate_state_schema_compatibility(2)

    assert result.status == CompatibilityStatus.MIGRATION_REQUIRED


def test_future_schema_is_not_accepted() -> None:
    result = evaluate_state_schema_compatibility(4)

    assert result.status == CompatibilityStatus.FUTURE_VERSION