from __future__ import annotations

import os
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.repository_intelligence import (
    FileAuthority,
    FileRisk,
    RepositoryFile,
    RepositoryIntelligenceEngine,
    RepositoryPathGuard,
    RepositoryPathSecurityError,
    RepositoryScanner,
    RepositorySourceError,
    SourceClassifier,
    SourceKind,
    discover_repository,
    find_repository_files,
    repository_fingerprint,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"

    (root / "AUTONOMY_ENGINE" / "continuity" / "acrl").mkdir(
        parents=True
    )
    (root / "core").mkdir()
    (root / "tests").mkdir()
    (root / ".git").mkdir()

    (root / "main.py").write_text(
        "from core.domain import Domain\n\nvalue = Domain()\n",
        encoding="utf-8",
    )

    (root / "core" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )

    (root / "core" / "domain.py").write_text(
        "class Domain:\n    pass\n",
        encoding="utf-8",
    )

    (root / "tests" / "test_domain.py").write_text(
        "from core.domain import Domain\n\n"
        "def test_domain():\n"
        "    assert Domain()\n",
        encoding="utf-8",
    )

    (root / "README.md").write_text(
        "# Repository\n",
        encoding="utf-8",
    )

    (root / "settings.json").write_text(
        '{"enabled": true}\n',
        encoding="utf-8",
    )

    (root / ".env").write_text(
        "SECRET=value\n",
        encoding="utf-8",
    )

    (root / ".git" / "config").write_text(
        "[core]\n",
        encoding="utf-8",
    )

    return root


# ---------------------------------------------------------------------------
# Basic discovery
# ---------------------------------------------------------------------------


def test_repository_is_discovered(repository: Path) -> None:
    snapshot = discover_repository(repository)

    assert snapshot.repository_root == str(repository.resolve())
    assert snapshot.files
    assert snapshot.fingerprint


def test_discovery_is_deterministic(repository: Path) -> None:
    first = discover_repository(repository)
    second = discover_repository(repository)

    assert first.fingerprint == second.fingerprint
    assert first.files == second.files
    assert first.modules == second.modules


def test_file_paths_are_sorted(repository: Path) -> None:
    snapshot = discover_repository(repository)

    paths = [item.relative_path for item in snapshot.files]

    assert paths == sorted(paths)


def test_python_file_is_authoritative(repository: Path) -> None:
    snapshot = discover_repository(repository)

    main = next(
        item
        for item in snapshot.files
        if item.relative_path == "main.py"
    )

    assert main.source_kind == SourceKind.PYTHON
    assert main.authority == FileAuthority.AUTHORITATIVE
    assert main.risk == FileRisk.NORMAL


def test_test_file_is_detected(repository: Path) -> None:
    snapshot = discover_repository(repository)

    test_file = next(
        item
        for item in snapshot.files
        if item.relative_path == "tests/test_domain.py"
    )

    assert test_file.source_kind == SourceKind.TEST
    assert test_file.authority == FileAuthority.DERIVED


def test_documentation_is_detected(repository: Path) -> None:
    snapshot = discover_repository(repository)

    readme = next(
        item
        for item in snapshot.files
        if item.relative_path == "README.md"
    )

    assert readme.source_kind == SourceKind.DOCUMENTATION


def test_configuration_is_detected(repository: Path) -> None:
    snapshot = discover_repository(repository)

    config = next(
        item
        for item in snapshot.files
        if item.relative_path == "settings.json"
    )

    assert config.source_kind == SourceKind.CONFIGURATION
    assert config.authority == FileAuthority.AUTHORITATIVE


def test_protected_file_is_detected(repository: Path) -> None:
    snapshot = discover_repository(repository)

    env_file = next(
        item
        for item in snapshot.files
        if item.relative_path == ".env"
    )

    assert env_file.risk == FileRisk.PROTECTED


# ---------------------------------------------------------------------------
# Exclusion
# ---------------------------------------------------------------------------


def test_git_directory_is_not_discovered(repository: Path) -> None:
    snapshot = discover_repository(repository)

    assert not any(
        item.relative_path.startswith(".git/")
        for item in snapshot.files
    )


def test_pycache_is_excluded(repository: Path) -> None:
    pycache = repository / "core" / "__pycache__"
    pycache.mkdir()

    (pycache / "domain.cpython-312.pyc").write_bytes(
        b"generated"
    )

    snapshot = discover_repository(repository)

    assert not any(
        "__pycache__" in item.relative_path
        for item in snapshot.files
    )


# ---------------------------------------------------------------------------
# Python topology
# ---------------------------------------------------------------------------


def test_python_imports_are_resolved(repository: Path) -> None:
    snapshot = discover_repository(repository)

    main_module = next(
        module
        for module in snapshot.modules
        if module.relative_path == "main.py"
    )

    assert "core.domain" in main_module.imports
    assert main_module.parse_valid is True


def test_test_module_is_in_topology(repository: Path) -> None:
    snapshot = discover_repository(repository)

    test_module = next(
        module
        for module in snapshot.modules
        if module.relative_path == "tests/test_domain.py"
    )

    assert test_module.module_name == "tests.test_domain"
    assert "core.domain" in test_module.imports


def test_invalid_python_is_not_reported_as_valid(
    repository: Path,
) -> None:
    invalid = repository / "invalid.py"

    invalid.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    snapshot = discover_repository(repository)

    invalid_module = next(
        module
        for module in snapshot.modules
        if module.relative_path == "invalid.py"
    )

    assert invalid_module.parse_valid is False


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_changes_when_source_changes(
    repository: Path,
) -> None:
    first = repository_fingerprint(repository)

    source = repository / "core" / "domain.py"

    source.write_text(
        "class Domain:\n"
        "    value = 1\n",
        encoding="utf-8",
    )

    second = repository_fingerprint(repository)

    assert first != second


def test_fingerprint_is_stable_without_changes(
    repository: Path,
) -> None:
    assert repository_fingerprint(repository) == (
        repository_fingerprint(repository)
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_find_repository_files(repository: Path) -> None:
    results = find_repository_files(
        repository,
        "domain",
    )

    paths = {item.relative_path for item in results}

    assert "core/domain.py" in paths
    assert "tests/test_domain.py" in paths


def test_find_can_filter_by_source_kind(
    repository: Path,
) -> None:
    results = find_repository_files(
        repository,
        "domain",
        source_kind=SourceKind.TEST,
    )

    assert len(results) == 1
    assert results[0].relative_path == "tests/test_domain.py"


def test_find_can_filter_by_authority(
    repository: Path,
) -> None:
    results = find_repository_files(
        repository,
        "domain",
        authority=FileAuthority.AUTHORITATIVE,
    )

    assert all(
        item.authority == FileAuthority.AUTHORITATIVE
        for item in results
    )


# ---------------------------------------------------------------------------
# Path security
# ---------------------------------------------------------------------------


def test_path_escape_is_rejected(repository: Path) -> None:
    guard = RepositoryPathGuard(repository)

    with pytest.raises(RepositoryPathSecurityError):
        guard.resolve("../outside")


def test_absolute_external_path_is_rejected(
    repository: Path,
    tmp_path: Path,
) -> None:
    guard = RepositoryPathGuard(repository)

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(RepositoryPathSecurityError):
        guard.resolve(outside)


# ---------------------------------------------------------------------------
# Repository validation
# ---------------------------------------------------------------------------


def test_missing_repository_is_rejected(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    with pytest.raises(RepositorySourceError):
        RepositoryScanner(missing)


def test_file_as_repository_is_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "repository.txt"
    file_path.write_text("not a repository", encoding="utf-8")

    with pytest.raises(RepositorySourceError):
        RepositoryScanner(file_path)


# ---------------------------------------------------------------------------
# Classifier contract
# ---------------------------------------------------------------------------


def test_classifier_marks_env_as_protected() -> None:
    classifier = SourceClassifier()

    kind, authority, risk = classifier.classify(".env")

    assert kind == SourceKind.CONFIGURATION
    assert authority == FileAuthority.AUTHORITATIVE
    assert risk == FileRisk.PROTECTED


def test_classifier_marks_test_as_derived() -> None:
    classifier = SourceClassifier()

    kind, authority, risk = classifier.classify(
        "tests/test_example.py"
    )

    assert kind == SourceKind.TEST
    assert authority == FileAuthority.DERIVED
    assert risk == FileRisk.NORMAL


# ---------------------------------------------------------------------------
# Engine API
# ---------------------------------------------------------------------------


def test_engine_find(repository: Path) -> None:
    engine = RepositoryIntelligenceEngine(repository)

    results = engine.find("main.py")

    assert len(results) == 1
    assert results[0].relative_path == "main.py"


def test_engine_get_module(repository: Path) -> None:
    engine = RepositoryIntelligenceEngine(repository)

    module = engine.get_module("core.domain")

    assert module is not None
    assert module.relative_path == "core/domain.py"


def test_engine_missing_module_returns_none(
    repository: Path,
) -> None:
    engine = RepositoryIntelligenceEngine(repository)

    assert engine.get_module("does.not.exist") is None


def test_snapshot_authoritative_files(repository: Path) -> None:
    snapshot = discover_repository(repository)

    assert all(
        item.authority == FileAuthority.AUTHORITATIVE
        for item in snapshot.authoritative_files
    )


def test_snapshot_test_files(repository: Path) -> None:
    snapshot = discover_repository(repository)

    assert snapshot.test_files
    assert all(
        item.source_kind == SourceKind.TEST
        for item in snapshot.test_files
    )


# ---------------------------------------------------------------------------
# Symlink safety
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.name == "nt",
    reason="Symlink creation may require elevated privileges on Windows.",
)
def test_symlink_is_not_followed(
    repository: Path,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text(
        "SECRET = True\n",
        encoding="utf-8",
    )

    link = repository / "outside_link.py"
    link.symlink_to(outside)

    snapshot = discover_repository(repository)

    linked = next(
        item
        for item in snapshot.files
        if item.relative_path == "outside_link.py"
    )

    assert linked.is_symlink is True
    assert linked.authority == FileAuthority.UNKNOWN
    assert linked.risk == FileRisk.UNKNOWN


# ---------------------------------------------------------------------------
# Snapshot immutability
# ---------------------------------------------------------------------------


def test_snapshot_is_immutable(repository: Path) -> None:
    snapshot = discover_repository(repository)

    with pytest.raises(Exception):
        snapshot.fingerprint = "tampered"


# ---------------------------------------------------------------------------
# Public API contract
# ---------------------------------------------------------------------------


def test_repository_file_is_structured_record(
    repository: Path,
) -> None:
    snapshot = discover_repository(repository)

    item = next(
        item
        for item in snapshot.files
        if item.relative_path == "main.py"
    )

    assert isinstance(item, RepositoryFile)
    assert item.sha256
    assert item.size_bytes > 0


def test_fingerprint_is_sha256(repository: Path) -> None:
    fingerprint = repository_fingerprint(repository)

    assert len(fingerprint) == 64
    int(fingerprint, 16)


def test_protected_paths_can_be_supplied(
    repository: Path,
) -> None:
    engine = RepositoryIntelligenceEngine(
        repository,
        protected_paths=[
            "AUTONOMY_ENGINE/continuity/acrl",
            "data/state.json",
        ],
    )

    snapshot = engine.discover()

    assert snapshot.protected_paths == (
        "AUTONOMY_ENGINE/continuity/acrl",
        "data/state.json",
    )


# ---------------------------------------------------------------------------
# Final T16 contract
# ---------------------------------------------------------------------------


def test_t16_produces_complete_repository_intelligence(
    repository: Path,
) -> None:
    snapshot = discover_repository(repository)

    assert snapshot.schema_version == "1.0"
    assert snapshot.repository_root
    assert snapshot.files
    assert snapshot.modules
    assert snapshot.fingerprint
    assert snapshot.authoritative_files
    assert snapshot.test_files

    for item in snapshot.files:
        assert item.relative_path
        assert item.absolute_path
        assert item.sha256
        assert item.source_kind
        assert item.authority
        assert item.risk