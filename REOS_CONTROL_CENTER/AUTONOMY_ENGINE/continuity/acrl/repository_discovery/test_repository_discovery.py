"""T16 PART-01 — Repository Discovery & Identity tests.

These tests validate the isolated repository-discovery substrate.

The suite is filesystem-realistic:
- classification tests create actual filesystem entries;
- repository fixtures explicitly create their root;
- symlink capability failures are reported as test failures;
- no test silently skips a required capability.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.boundary import (
    RepositoryBoundary,
    RepositoryBoundaryError,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.classification import (
    EntryKind,
    SourceClassification,
    classify_entry,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.fingerprint import (
    fingerprint_topology,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.identity import (
    RepositoryIdentityError,
    identify_repository,
)
from AUTONOMY_ENGINE.continuity.acrl.repository_discovery.topology import (
    RepositoryTopologyScanner,
)


def build_repository(root: Path) -> Path:
    """Create a deterministic temporary repository fixture."""

    root.mkdir(
        parents=False,
        exist_ok=False,
    )

    directories = (
        root / "AUTONOMY_ENGINE",
        root / "core",
        root / "tests",
        root / ".git",
        root / "__pycache__",
    )

    for directory in directories:
        directory.mkdir(
            parents=False,
            exist_ok=False,
        )

    (root / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    (root / "core" / "domain.py").write_text(
        "class Domain: pass\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_domain.py").write_text(
        "def test_domain(): pass\n",
        encoding="utf-8",
    )

    (root / "README.md").write_text(
        "# Test Repository\n",
        encoding="utf-8",
    )

    (root / ".env").write_text(
        "SECRET=value\n",
        encoding="utf-8",
    )

    (root / "generated.pyc").write_bytes(
        b"generated",
    )

    return root


def test_repository_identity_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    first = identify_repository(repository)
    second = identify_repository(repository)

    assert first == second
    assert len(first.identity_hash) == 64
    assert first.name == "repo"


def test_repository_identity_requires_directory(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "file.txt"

    file_path.write_text(
        "x",
        encoding="utf-8",
    )

    with pytest.raises(RepositoryIdentityError):
        identify_repository(file_path)


def test_boundary_accepts_internal_path(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")
    boundary = RepositoryBoundary.create(repository)

    internal = repository / "main.py"

    assert boundary.contains(internal) is True
    assert boundary.require(internal).is_file()


def test_boundary_rejects_external_path(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")
    boundary = RepositoryBoundary.create(repository)

    outside = tmp_path / "outside.py"

    outside.write_text(
        "x",
        encoding="utf-8",
    )

    assert boundary.contains(outside) is False

    with pytest.raises(RepositoryBoundaryError):
        boundary.require(outside)


def test_source_classification(
    tmp_path: Path,
) -> None:
    source = tmp_path / "domain.py"

    source.write_text(
        "class Domain: pass\n",
        encoding="utf-8",
    )

    kind, classification = classify_entry(source)

    assert kind == EntryKind.FILE
    assert classification == SourceClassification.SOURCE


def test_test_classification(
    tmp_path: Path,
) -> None:
    test_file = tmp_path / "test_domain.py"

    test_file.write_text(
        "def test_domain(): pass\n",
        encoding="utf-8",
    )

    kind, classification = classify_entry(test_file)

    assert kind == EntryKind.FILE
    assert classification == SourceClassification.TEST


def test_generated_classification(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "module.pyc"

    generated.write_bytes(
        b"generated",
    )

    kind, classification = classify_entry(generated)

    assert kind == EntryKind.FILE
    assert classification == SourceClassification.GENERATED


def test_protected_classification(
    tmp_path: Path,
) -> None:
    protected = tmp_path / ".env"

    protected.write_text(
        "SECRET=value\n",
        encoding="utf-8",
    )

    kind, classification = classify_entry(protected)

    assert kind == EntryKind.FILE
    assert classification == SourceClassification.PROTECTED


def test_topology_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    scanner = RepositoryTopologyScanner(repository)

    first = scanner.scan()
    second = scanner.scan()

    assert first == second


def test_excluded_directories_are_reported(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    topology = RepositoryTopologyScanner(repository).scan()

    assert ".git" in topology.excluded_directories
    assert "__pycache__" in topology.excluded_directories


def test_excluded_directory_contents_are_not_scanned(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    hidden = repository / ".git" / "secret.py"

    hidden.write_text(
        "SECRET=True\n",
        encoding="utf-8",
    )

    topology = RepositoryTopologyScanner(repository).scan()

    paths = {
        entry.relative_path
        for entry in topology.entries
    }

    assert ".git/secret.py" not in paths


def test_topology_paths_are_sorted(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    topology = RepositoryTopologyScanner(repository).scan()

    paths = [
        entry.relative_path
        for entry in topology.entries
    ]

    assert paths == sorted(paths)


def test_fingerprint_is_deterministic(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    scanner = RepositoryTopologyScanner(repository)

    first = fingerprint_topology(scanner.scan())
    second = fingerprint_topology(scanner.scan())

    assert first == second
    assert len(first) == 64


def test_fingerprint_changes_when_structure_changes(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    scanner = RepositoryTopologyScanner(repository)

    first = fingerprint_topology(scanner.scan())

    (repository / "new_module.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    second = fingerprint_topology(scanner.scan())

    assert first != second


def test_symlink_is_classified_without_following(
    tmp_path: Path,
) -> None:
    repository = build_repository(tmp_path / "repo")

    outside = tmp_path / "outside.py"

    outside.write_text(
        "OUTSIDE=True\n",
        encoding="utf-8",
    )

    link = repository / "outside_link.py"

    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.fail(
            "PART-01 requires real symbolic-link capability for its "
            f"filesystem safety contract. Platform={os.name!r}; "
            f"symlink creation failed: {exc}"
        )

    assert link.is_symlink()

    kind, classification = classify_entry(link)

    assert kind == EntryKind.SYMLINK
    assert classification == SourceClassification.UNKNOWN

    topology = RepositoryTopologyScanner(repository).scan()

    linked = next(
        entry
        for entry in topology.entries
        if entry.relative_path == "outside_link.py"
    )

    assert linked.is_symlink is True
    assert linked.kind == EntryKind.SYMLINK
    assert linked.classification == SourceClassification.UNKNOWN
