"""ACRL T03 — atomic state observation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from .state_observation import (
    StateObservationSourceError,
    observe_authoritative_state,
)


def test_observes_existing_file(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        '{"gate":"CORE-005"}',
        encoding="utf-8",
    )

    observed = observe_authoritative_state(state)

    assert observed.path == str(state.resolve())
    assert observed.size > 0
    assert observed.modified_ns > 0
    assert len(observed.sha256) == 64
    assert observed.raw_bytes == b'{"gate":"CORE-005"}'


def test_missing_file_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(StateObservationSourceError):
        observe_authoritative_state(
            tmp_path / "state.json"
        )


def test_directory_is_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "state.json"
    directory.mkdir()

    with pytest.raises(StateObservationSourceError):
        observe_authoritative_state(directory)


def test_same_content_produces_same_hash(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state.json"
    state.write_text(
        "{}",
        encoding="utf-8",
    )

    first = observe_authoritative_state(state)
    second = observe_authoritative_state(state)

    assert first.sha256 == second.sha256
