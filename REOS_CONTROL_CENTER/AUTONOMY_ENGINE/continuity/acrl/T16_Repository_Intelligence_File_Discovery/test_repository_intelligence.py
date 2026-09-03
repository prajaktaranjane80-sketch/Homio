from __future__ import annotations

from pathlib import Path

import pytest

import AUTONOMY_ENGINE.continuity.acrl.repository_intelligence

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
    (root / "__pycache__").mkdir()

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

    (root / "core" / "domain.pyo").write_bytes(
        b"generated"
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

    (root / "__pycache__" / "generated.pyc").write_bytes(
        b"generated"
    )

    return root


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def test_path_normalization_is_deterministic() -> None:
    assert AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.normalize_repository_path(
        r".\Core\DOMAIN.py"
    ) == "core/domain.py"


# ---------------------------------------------------------------------------
# Basic discovery
# ---------------------------------------------------------------------------


def test_repository_is_discovered(repository: Path) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert snapshot.repository_root == str(repository.resolve())
    assert snapshot.files
    assert snapshot.fingerprint


def test_discovery_is_deterministic(repository: Path) -> None:
    first = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)
    second = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert first.fingerprint == second.fingerprint
    assert first.files == second.files
    assert first.modules == second.modules
    assert first.excluded_paths == second.excluded_paths


def test_file_paths_are_sorted(repository: Path) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    paths = [
        item.relative_path
        for item in snapshot.files
    ]

    assert paths == sorted(
        paths,
        key=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.normalize_repository_path,
    )


def test_snapshot_has_unique_paths(repository: Path) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    normalized = [
        AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.normalize_repository_path(item.relative_path)
        for item in snapshot.files
    ]

    assert len(normalized) == len(set(normalized))


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


def test_python_file_is_authoritative(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    main = next(
        item
        for item in snapshot.files
        if item.relative_path == "main.py"
    )

    assert main.source_kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.PYTHON
    assert main.authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE
    assert main.risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.NORMAL


def test_test_file_is_detected(repository: Path) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    test_file = next(
        item
        for item in snapshot.files
        if item.relative_path == "tests/test_domain.py"
    )

    assert test_file.source_kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.TEST
    assert test_file.authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.DERIVED


def test_documentation_is_detected(repository: Path) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    readme = next(
        item
        for item in snapshot.files
        if item.relative_path == "README.md"
    )

    assert readme.source_kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.DOCUMENTATION


def test_configuration_is_detected(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    config = next(
        item
        for item in snapshot.files
        if item.relative_path == "settings.json"
    )

    assert config.source_kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.CONFIGURATION
    assert config.authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE


def test_protected_file_is_detected(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    env_file = next(
        item
        for item in snapshot.files
        if item.relative_path == ".env"
    )

    assert env_file.risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.PROTECTED


# ---------------------------------------------------------------------------
# Exclusion / generated policy
# ---------------------------------------------------------------------------


def test_git_directory_is_not_discovered(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert not any(
        item.relative_path.startswith(".git/")
        for item in snapshot.files
    )


def test_pycache_is_excluded(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert not any(
        "__pycache__" in item.relative_path
        for item in snapshot.files
    )


def test_excluded_paths_are_reported(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert ".git" in snapshot.excluded_paths
    assert "__pycache__" in snapshot.excluded_paths


@pytest.mark.parametrize(
    "filename",
    [
        "generated.pyc",
        "generated.pyo",
        "generated.egg-info",
    ],
)
def test_generated_patterns_are_classified(
    repository: Path,
    filename: str,
) -> None:
    target = repository / filename

    if filename.endswith(".egg-info"):
        target.write_text(
            "generated",
            encoding="utf-8",
        )
    else:
        target.write_bytes(b"generated")

    scanner = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryScanner(repository)

    kind, authority, risk = scanner.classifier.classify(
        filename
    )

    assert kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.GENERATED
    assert authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.GENERATED
    assert risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.NORMAL


def test_sensitive_files_are_excluded(
    repository: Path,
) -> None:
    secret = repository / "private.key"
    secret.write_text(
        "PRIVATE",
        encoding="utf-8",
    )

    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert not any(
        item.relative_path == "private.key"
        for item in snapshot.files
    )

    assert "private.key" in snapshot.excluded_paths


# ---------------------------------------------------------------------------
# Python topology
# ---------------------------------------------------------------------------


def test_python_imports_are_resolved(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    main_module = next(
        module
        for module in snapshot.modules
        if module.relative_path == "main.py"
    )

    assert "core.domain" in main_module.imports
    assert main_module.parse_valid is True


def test_test_module_is_in_topology(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    test_module = next(
        module
        for module in snapshot.modules
        if module.relative_path
        == "tests/test_domain.py"
    )

    assert test_module.module_name == (
        "tests.test_domain"
    )
    assert "core.domain" in test_module.imports


def test_invalid_python_is_not_reported_as_valid(
    repository: Path,
) -> None:
    invalid = repository / "invalid.py"

    invalid.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

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
    first = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)

    source = repository / "core" / "domain.py"

    source.write_text(
        "class Domain:\n"
        "    value = 1\n",
        encoding="utf-8",
    )

    second = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)

    assert first != second


def test_fingerprint_is_stable_without_changes(
    repository: Path,
) -> None:
    assert AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository) == (
        AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)
    )


def test_fingerprint_changes_when_excluded_path_changes(
    repository: Path,
) -> None:
    first = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)

    extra = repository / "generated.pyc"
    extra.write_bytes(b"generated")

    second = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)

    assert first != second


# ---------------------------------------------------------------------------
# Exact / controlled search
# ---------------------------------------------------------------------------


def test_exact_search_returns_only_exact_path(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "main.py",
    )

    assert len(results) == 1
    assert results[0].relative_path == "main.py"


def test_exact_search_normalizes_windows_separators(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        r".\core\domain.py",
    )

    assert len(results) == 1
    assert results[0].relative_path == (
        "core/domain.py"
    )


def test_contains_search_is_explicit(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "domain",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.CONTAINS,
    )

    paths = {
        item.relative_path
        for item in results
    }

    assert "core/domain.py" in paths
    assert "tests/test_domain.py" in paths


def test_glob_search_is_explicit(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "core/*.py",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.GLOB,
    )

    paths = {
        item.relative_path
        for item in results
    }

    assert "core/domain.py" in paths
    assert "core/__init__.py" in paths


def test_contains_search_preserves_deterministic_order(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "domain",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.CONTAINS,
    )

    paths = [
        item.relative_path
        for item in results
    ]

    assert paths == sorted(
        paths,
        key=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.normalize_repository_path,
    )


def test_find_can_filter_by_source_kind(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "domain",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.CONTAINS,
        source_kind=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.TEST,
    )

    assert len(results) == 1
    assert results[0].relative_path == (
        "tests/test_domain.py"
    )


def test_find_can_filter_by_authority(
    repository: Path,
) -> None:
    results = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.find_repository_files(
        repository,
        "domain",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.CONTAINS,
        authority=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE,
    )

    assert all(
        item.authority
        == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE
        for item in results
    )


# ---------------------------------------------------------------------------
# Path security
# ---------------------------------------------------------------------------


def test_path_escape_is_rejected(
    repository: Path,
) -> None:
    guard = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryPathGuard(repository)

    with pytest.raises(AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryPathSecurityError):
        guard.resolve("../outside")


def test_absolute_external_path_is_rejected(
    repository: Path,
    tmp_path: Path,
) -> None:
    guard = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryPathGuard(repository)

    outside = tmp_path / "outside.txt"
    outside.write_text(
        "outside",
        encoding="utf-8",
    )

    with pytest.raises(AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryPathSecurityError):
        guard.resolve(outside)


# ---------------------------------------------------------------------------
# Repository validation
# ---------------------------------------------------------------------------


def test_missing_repository_is_rejected(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "does-not-exist"

    with pytest.raises(AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositorySourceError):
        AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryScanner(missing)


def test_file_as_repository_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "repository.txt"

    file_path.write_text(
        "not a repository",
        encoding="utf-8",
    )

    with pytest.raises(AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositorySourceError):
        AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryScanner(file_path)


# ---------------------------------------------------------------------------
# Classifier contract
# ---------------------------------------------------------------------------


def test_classifier_marks_env_as_protected() -> None:
    classifier = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceClassifier()

    kind, authority, risk = classifier.classify(
        ".env"
    )

    assert kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.CONFIGURATION
    assert authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE
    assert risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.PROTECTED


def test_classifier_marks_test_as_derived() -> None:
    classifier = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceClassifier()

    kind, authority, risk = classifier.classify(
        "tests/test_example.py"
    )

    assert kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.TEST
    assert authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.DERIVED
    assert risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.NORMAL


def test_classifier_marks_generated_pattern() -> None:
    classifier = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceClassifier()

    kind, authority, risk = classifier.classify(
        "build/output.pyc"
    )

    assert kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.GENERATED
    assert authority == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.GENERATED
    assert risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.NORMAL


# ---------------------------------------------------------------------------
# Engine API
# ---------------------------------------------------------------------------


def test_engine_find_exact(
    repository: Path,
) -> None:
    engine = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryIntelligenceEngine(repository)

    results = engine.find("main.py")

    assert len(results) == 1
    assert results[0].relative_path == "main.py"


def test_engine_find_contains(
    repository: Path,
) -> None:
    engine = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryIntelligenceEngine(repository)

    results = engine.find(
        "domain",
        match_mode=AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SearchMatchMode.CONTAINS,
    )

    assert {
        item.relative_path
        for item in results
    } == {
        "core/domain.py",
        "tests/test_domain.py",
    }


def test_engine_get_module(
    repository: Path,
) -> None:
    engine = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryIntelligenceEngine(repository)

    module = engine.get_module(
        "core.domain"
    )

    assert module is not None
    assert module.relative_path == (
        "core/domain.py"
    )


def test_engine_missing_module_returns_none(
    repository: Path,
) -> None:
    engine = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryIntelligenceEngine(repository)

    assert engine.get_module(
        "does.not.exist"
    ) is None


def test_snapshot_authoritative_files(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert all(
        item.authority
        == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.AUTHORITATIVE
        for item in snapshot.authoritative_files
    )


def test_snapshot_test_files(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert snapshot.test_files

    assert all(
        item.source_kind == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.SourceKind.TEST
        for item in snapshot.test_files
    )

# ---------------------------------------------------------------------------
# Symlink safety
# ---------------------------------------------------------------------------


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

    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    linked = next(
        item
        for item in snapshot.files
        if item.relative_path == "outside_link.py"
    )

    assert linked.is_symlink is True
    assert linked.authority == (
        AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileAuthority.UNKNOWN
    )
    assert linked.risk == AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.FileRisk.UNKNOWN

# ---------------------------------------------------------------------------
# Snapshot immutability
# ---------------------------------------------------------------------------


def test_snapshot_is_immutable(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    with pytest.raises(Exception):
        snapshot.fingerprint = "tampered"


# ---------------------------------------------------------------------------
# Public API contract
# ---------------------------------------------------------------------------


def test_repository_file_is_structured_record(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    item = next(
        item
        for item in snapshot.files
        if item.relative_path == "main.py"
    )

    assert isinstance(item, AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryFile)
    assert item.sha256
    assert item.size_bytes > 0


def test_fingerprint_is_sha256(
    repository: Path,
) -> None:
    fingerprint = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.repository_fingerprint(repository)

    assert len(fingerprint) == 64
    int(fingerprint, 16)


def test_protected_paths_can_be_supplied(
    repository: Path,
) -> None:
    engine = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.RepositoryIntelligenceEngine(
        repository,
        protected_paths=[
            "AUTONOMY_ENGINE/continuity/acrl",
            "data/state.json",
        ],
    )

    snapshot = engine.discover()

    assert snapshot.protected_paths == (
        "autonomy_engine/continuity/acrl",
        "data/state.json",
    )


# ---------------------------------------------------------------------------
# Final T16 contract
# ---------------------------------------------------------------------------


def test_t16_produces_complete_repository_intelligence(
    repository: Path,
) -> None:
    snapshot = AUTONOMY_ENGINE.continuity.acrl.repository_intelligence.discover_repository(repository)

    assert snapshot.schema_version == "1.1"
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

    assert snapshot.excluded_paths