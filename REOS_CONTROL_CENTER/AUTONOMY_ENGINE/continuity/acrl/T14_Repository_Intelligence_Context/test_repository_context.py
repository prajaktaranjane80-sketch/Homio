from __future__ import annotations

from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.repository_context import (
    AUTHORITY,
    RepositoryContextAuthorityError,
    RepositoryContextDecision,
    RepositoryContextEngine,
    RepositoryContextReason,
    RepositoryContextRequest,
    resolve_repository_context,
)


@pytest.fixture()
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()

    (root / "AUTONOMY_ENGINE").mkdir()
    (root / "core").mkdir()
    (root / "tests").mkdir()

    (root / "core" / "inventory.py").write_text(
        "class Inventory:\n    pass\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_inventory.py").write_text(
        "from core.inventory import Inventory\n\n"
        "def test_inventory():\n"
        "    assert Inventory()\n",
        encoding="utf-8",
    )

    (root / "README.md").write_text(
        "# Inventory\n",
        encoding="utf-8",
    )

    return root


def make_request(
    repository: Path,
    **kwargs,
) -> RepositoryContextRequest:
    values = {
        "repository_root": repository,
        "current_gate": "CORE-004",
        "current_task": "Implement inventory domain",
        "current_subtask": "CORE-004-T02",
    }
    values.update(kwargs)
    return RepositoryContextRequest(**values)


def test_resolves_repository_context(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            candidate_paths=("core/inventory.py",),
        )
    )

    assert (
        report.decision
        == RepositoryContextDecision.RESOLVED
    )

    assert (
        report.reason
        == RepositoryContextReason.VALID
    )

    assert report.repository_fingerprint

    assert any(
        item.relative_path
        == "core/inventory.py"
        for item in report.relevant_files
    )


def test_discovers_tests_for_relevant_files(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            search_terms=("inventory",),
        )
    )

    assert any(
        item.relative_path
        == "tests/test_inventory.py"
        for item in report.test_files
    )


def test_discovers_python_files(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            search_terms=("inventory",),
        )
    )

    assert any(
        item.relative_path
        == "core/inventory.py"
        for item in report.python_files
    )


def test_task_terms_are_derived_deterministically() -> None:
    first = RepositoryContextEngine.derive_search_terms(
        "CORE-004",
        "Implement inventory domain",
        "CORE-004-T02",
    )

    second = RepositoryContextEngine.derive_search_terms(
        "CORE-004",
        "Implement inventory domain",
        "CORE-004-T02",
    )

    assert first == second
    assert "inventory" in first


def test_no_relevant_files_blocks(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            current_gate=None,
            current_task=None,
            current_subtask=None,
            candidate_paths=("missing/file.py",),
            search_terms=("does-not-exist",),
        )
    )

    assert (
        report.decision
        == RepositoryContextDecision.BLOCKED
    )

    assert (
        report.reason
        == RepositoryContextReason.NO_RELEVANT_FILES
    )


def test_wrong_authority_is_rejected(
    repository: Path,
) -> None:
    with pytest.raises(
        RepositoryContextAuthorityError
    ):
        resolve_repository_context(
            make_request(
                repository,
                expected_authority="OTHER_SYSTEM",
            )
        )


def test_execution_is_never_authorized(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            candidate_paths=("core/inventory.py",),
        )
    )

    assert report.execution_authorized is False
    assert report.observational_only is True


def test_report_authority_is_control_center(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            candidate_paths=("core/inventory.py",),
        )
    )

    assert report.authority == AUTHORITY
    assert report.authority == "REOS_CONTROL_CENTER"


def test_resolution_is_deterministic(
    repository: Path,
) -> None:
    request = make_request(
        repository,
        search_terms=("inventory",),
    )

    first = resolve_repository_context(request)
    second = resolve_repository_context(request)

    assert first.to_dict() == second.to_dict()


def test_context_preserves_reconstructed_position(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            candidate_paths=("core/inventory.py",),
        )
    )

    assert report.current_gate == "CORE-004"
    assert (
        report.current_task
        == "Implement inventory domain"
    )
    assert (
        report.current_subtask
        == "CORE-004-T02"
    )


def test_candidate_path_has_priority(
    repository: Path,
) -> None:
    report = resolve_repository_context(
        make_request(
            repository,
            candidate_paths=("core/inventory.py",),
            search_terms=("readme",),
        )
    )

    paths = {
        item.relative_path
        for item in report.relevant_files
    }

    assert "core/inventory.py" in paths
