
from __future__ import annotations

"""
ACRL T16 — Repository Intelligence & File Discovery

Purpose
-------
Provides deterministic, read-only repository intelligence for the ACRL
autonomous developer.

Design rules
------------
1. This module MUST NOT modify repository files.
2. This module MUST NOT become a business source of truth.
3. Repository truth is observed, classified, fingerprinted and reported.
4. Unsafe filesystem traversal fails closed.
5. Results are deterministic for the same repository state.
6. Generated/cache/vendor directories are excluded from the authoritative
   source map unless explicitly requested.
7. T17 consumes this layer's snapshot to perform change-impact analysis.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping
import ast
import hashlib
import json
import os


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RepositoryIntelligenceError(Exception):
    """Base error for T16."""


class RepositorySourceError(RepositoryIntelligenceError):
    """Repository source cannot be accessed safely."""


class RepositoryIntegrityError(RepositoryIntelligenceError):
    """Repository observation failed integrity validation."""


class RepositoryFingerprintError(RepositoryIntegrityError):
    """Raised when repository fingerprint integrity is invalid."""


class RepositoryPathSecurityError(RepositoryIntelligenceError):
    """A requested path escapes the repository boundary."""


class RepositoryDiscoveryError(RepositoryIntelligenceError):
    """Repository discovery failed."""


class RepositoryClassificationError(RepositoryIntelligenceError):
    """Repository source classification failed."""

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SourceKind(str, Enum):
    PYTHON = "PYTHON"
    TEST = "TEST"
    CONFIGURATION = "CONFIGURATION"
    DOCUMENTATION = "DOCUMENTATION"
    DATA = "DATA"
    GENERATED = "GENERATED"
    VENDOR = "VENDOR"
    CACHE = "CACHE"
    BINARY = "BINARY"
    UNKNOWN = "UNKNOWN"


class FileAuthority(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    DERIVED = "DERIVED"
    GENERATED = "GENERATED"
    EXCLUDED = "EXCLUDED"
    UNKNOWN = "UNKNOWN"


class FileRisk(str, Enum):
    NORMAL = "NORMAL"
    PROTECTED = "PROTECTED"
    SENSITIVE = "SENSITIVE"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Immutable records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RepositoryFile:
    relative_path: str
    absolute_path: str
    size_bytes: int
    sha256: str
    source_kind: SourceKind
    authority: FileAuthority
    risk: FileRisk
    is_symlink: bool


@dataclass(frozen=True)
class ModuleImport:
    module: str
    relative_path: str


@dataclass(frozen=True)
class ModuleRecord:
    relative_path: str
    module_name: str
    imports: tuple[str, ...]
    parse_valid: bool


@dataclass(frozen=True)
class RepositorySnapshot:
    schema_version: str
    repository_root: str
    files: tuple[RepositoryFile, ...]
    modules: tuple[ModuleRecord, ...]
    protected_paths: tuple[str, ...]
    excluded_paths: tuple[str, ...]
    fingerprint: str

    @property
    def authoritative_files(self) -> tuple[RepositoryFile, ...]:
        return tuple(
            item
            for item in self.files
            if item.authority == FileAuthority.AUTHORITATIVE
        )

    @property
    def test_files(self) -> tuple[RepositoryFile, ...]:
        return tuple(
            item
            for item in self.files
            if item.source_kind == SourceKind.TEST
        )

    @property
    def python_files(self) -> tuple[RepositoryFile, ...]:
        return tuple(
            item
            for item in self.files
            if item.source_kind in {
                SourceKind.PYTHON,
                SourceKind.TEST,
            }
        )


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".coverage",
        ".idea",
        ".vscode",
    }
)


DEFAULT_GENERATED_NAMES = frozenset(
    {
        "*.pyc",
        "*.pyo",
        "*.egg-info",
    }
)


DEFAULT_PROTECTED_NAMES = frozenset(
    {
        ".git",
        ".gitignore",
        ".gitmodules",
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "secrets.json",
        "credentials.json",
        "state.json",
    }
)


DEFAULT_SENSITIVE_SUFFIXES = frozenset(
    {
        ".pem",
        ".key",
        ".crt",
        ".p12",
        ".pfx",
        ".secret",
    }
)


# ---------------------------------------------------------------------------
# Path security
# ---------------------------------------------------------------------------


class RepositoryPathGuard:
    """
    Enforces the repository root boundary.

    This guard is deliberately independent of any write operation.
    T16 is observation-only.
    """

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()

    def resolve(self, candidate: Path | str) -> Path:
        candidate_path = Path(candidate)

        if not candidate_path.is_absolute():
            candidate_path = self.repository_root / candidate_path

        resolved = candidate_path.resolve()

        try:
            resolved.relative_to(self.repository_root)
        except ValueError as exc:
            raise RepositoryPathSecurityError(
                f"Path escapes repository root: {candidate}"
            ) from exc

        return resolved


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


class SourceClassifier:
    """Deterministically classifies repository files."""

    CONFIG_SUFFIXES = frozenset(
        {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".xml",
        }
    )

    DOCUMENTATION_SUFFIXES = frozenset(
        {
            ".md",
            ".rst",
            ".txt",
            ".adoc",
        }
    )

    DATA_SUFFIXES = frozenset(
        {
            ".csv",
            ".tsv",
            ".sql",
            ".db",
            ".sqlite",
        }
    )

    BINARY_SUFFIXES = frozenset(
        {
            ".exe",
            ".dll",
            ".so",
            ".bin",
            ".zip",
            ".7z",
            ".rar",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".mp4",
            ".mov",
        }
    )

    def __init__(
        self,
        excluded_directories: Iterable[str] = DEFAULT_EXCLUDED_DIRECTORIES,
        generated_names: Iterable[str] = DEFAULT_GENERATED_NAMES,
        protected_names: Iterable[str] = DEFAULT_PROTECTED_NAMES,
        sensitive_suffixes: Iterable[str] = DEFAULT_SENSITIVE_SUFFIXES,
    ) -> None:
        self.excluded_directories = frozenset(excluded_directories)
        self.generated_names = frozenset(generated_names)
        self.protected_names = frozenset(protected_names)
        self.sensitive_suffixes = frozenset(sensitive_suffixes)

    def classify(
        self,
        relative_path: str,
        is_symlink: bool = False,
    ) -> tuple[SourceKind, FileAuthority, FileRisk]:
        path = Path(relative_path)
        name = path.name
        suffix = path.suffix.lower()

        parts = set(path.parts)

        if parts & self.excluded_directories:
            return (
                SourceKind.CACHE,
                FileAuthority.EXCLUDED,
                FileRisk.NORMAL,
            )

        if is_symlink:
            return (
                SourceKind.UNKNOWN,
                FileAuthority.UNKNOWN,
                FileRisk.UNKNOWN,
            )

        if name in self.protected_names:
            return (
                SourceKind.CONFIGURATION,
                FileAuthority.AUTHORITATIVE,
                FileRisk.PROTECTED,
            )

        if suffix in self.sensitive_suffixes:
            return (
                SourceKind.UNKNOWN,
                FileAuthority.EXCLUDED,
                FileRisk.SENSITIVE,
            )

        if suffix in {".py", ".pyw"}:
            if name.startswith("test_") or name.endswith("_test.py"):
                return (
                    SourceKind.TEST,
                    FileAuthority.DERIVED,
                    FileRisk.NORMAL,
                )

            return (
                SourceKind.PYTHON,
                FileAuthority.AUTHORITATIVE,
                FileRisk.NORMAL,
            )

        if suffix in self.CONFIG_SUFFIXES:
            return (
                SourceKind.CONFIGURATION,
                FileAuthority.AUTHORITATIVE,
                FileRisk.NORMAL,
            )

        if suffix in self.DOCUMENTATION_SUFFIXES:
            return (
                SourceKind.DOCUMENTATION,
                FileAuthority.DERIVED,
                FileRisk.NORMAL,
            )

        if suffix in self.DATA_SUFFIXES:
            return (
                SourceKind.DATA,
                FileAuthority.DERIVED,
                FileRisk.NORMAL,
            )

        if suffix in self.BINARY_SUFFIXES:
            return (
                SourceKind.BINARY,
                FileAuthority.EXCLUDED,
                FileRisk.NORMAL,
            )

        if suffix == ".pyc":
            return (
                SourceKind.GENERATED,
                FileAuthority.GENERATED,
                FileRisk.NORMAL,
            )

        return (
            SourceKind.UNKNOWN,
            FileAuthority.UNKNOWN,
            FileRisk.UNKNOWN,
        )


# ---------------------------------------------------------------------------
# Module topology
# ---------------------------------------------------------------------------


class PackageTopologyResolver:
    """Builds deterministic Python module topology without importing code."""

    def __init__(self, repository_root: Path) -> None:
        self.repository_root = repository_root

    def module_name(self, relative_path: str) -> str:
        path = Path(relative_path)

        if path.suffix != ".py":
            return ""

        parts = list(path.with_suffix("").parts)

        if parts and parts[-1] == "__init__":
            parts = parts[:-1]

        return ".".join(parts)

    def parse_imports(self, absolute_path: Path) -> tuple[str, ...]:
        try:
            source = absolute_path.read_text(
                encoding="utf-8",
                errors="strict",
            )
            tree = ast.parse(source, filename=str(absolute_path))
        except (OSError, UnicodeError, SyntaxError):
            return ()

        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)

        return tuple(sorted(imports))

    def resolve(self, files: Iterable[RepositoryFile]) -> tuple[ModuleRecord, ...]:
        records: list[ModuleRecord] = []

        for item in files:
            if item.source_kind not in {
                SourceKind.PYTHON,
                SourceKind.TEST,
            }:
                continue

            absolute = Path(item.absolute_path)
            imports = self.parse_imports(absolute)

            records.append(
                ModuleRecord(
                    relative_path=item.relative_path,
                    module_name=self.module_name(item.relative_path),
                    imports=imports,
                    parse_valid=self._parse_valid(absolute),
                )
            )

        records.sort(key=lambda record: record.relative_path)

        return tuple(records)

    def _parse_valid(self, path: Path) -> bool:
        try:
            source = path.read_text(
                encoding="utf-8",
                errors="strict",
            )
            ast.parse(source, filename=str(path))
            return True
        except (OSError, UnicodeError, SyntaxError):
            return False


# ---------------------------------------------------------------------------
# Repository scanner
# ---------------------------------------------------------------------------


class RepositoryScanner:
    """Read-only deterministic filesystem scanner."""

    def __init__(
        self,
        repository_root: Path | str,
        classifier: SourceClassifier | None = None,
    ) -> None:
        self.guard = RepositoryPathGuard(Path(repository_root))
        self.repository_root = self.guard.repository_root
        self.classifier = classifier or SourceClassifier()

        if not self.repository_root.exists():
            raise RepositorySourceError(
                f"Repository does not exist: {self.repository_root}"
            )

        if not self.repository_root.is_dir():
            raise RepositorySourceError(
                f"Repository root is not a directory: {self.repository_root}"
            )

    def scan(self) -> tuple[RepositoryFile, ...]:
        discovered: list[RepositoryFile] = []

        for root, directories, filenames in os.walk(
            self.repository_root,
            topdown=True,
            followlinks=False,
        ):
            root_path = Path(root)

            directories[:] = sorted(
                directory
                for directory in directories
                if directory not in self.classifier.excluded_directories
            )

            for filename in sorted(filenames):
                candidate = root_path / filename

                try:
                    relative = candidate.relative_to(
                        self.repository_root
                    ).as_posix()

                    resolved = self.guard.resolve(candidate)

                    is_symlink = candidate.is_symlink()

                    if is_symlink:
                        source_kind, authority, risk = (
                            SourceKind.UNKNOWN,
                            FileAuthority.UNKNOWN,
                            FileRisk.UNKNOWN,
                        )
                        digest = self._symlink_digest(candidate)
                        size = 0
                    else:
                        source_kind, authority, risk = (
                            self.classifier.classify(
                                relative,
                                is_symlink=False,
                            )
                        )

                        if authority == FileAuthority.EXCLUDED:
                            continue

                        size = candidate.stat().st_size
                        digest = self._file_sha256(candidate)

                    discovered.append(
                        RepositoryFile(
                            relative_path=relative,
                            absolute_path=str(resolved),
                            size_bytes=size,
                            sha256=digest,
                            source_kind=source_kind,
                            authority=authority,
                            risk=risk,
                            is_symlink=is_symlink,
                        )
                    )

                except RepositoryPathSecurityError:
                    raise

                except OSError as exc:
                    raise RepositoryDiscoveryError(
                        f"Unable to inspect repository file: {candidate}"
                    ) from exc

        discovered.sort(key=lambda item: item.relative_path)

        return tuple(discovered)

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()

        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise RepositoryDiscoveryError(
                f"Unable to fingerprint file: {path}"
            ) from exc

        return digest.hexdigest()

    @staticmethod
    def _symlink_digest(path: Path) -> str:
        target = os.readlink(path)
        return hashlib.sha256(
            f"SYMLINK:{target}".encode("utf-8")
        ).hexdigest()


# ---------------------------------------------------------------------------
# Repository intelligence engine
# ---------------------------------------------------------------------------


class RepositoryIntelligenceEngine:
    """
    Main T16 orchestration engine.

    T16 observes the repository and produces a deterministic snapshot.
    It intentionally has no mutation API.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(
        self,
        repository_root: Path | str,
        *,
        protected_paths: Iterable[str] = (),
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.scanner = RepositoryScanner(self.repository_root)
        self.topology = PackageTopologyResolver(self.repository_root)
        self.protected_paths = tuple(
            sorted(
                Path(path).as_posix()
                for path in protected_paths
            )
        )

    def discover(self) -> RepositorySnapshot:
        files = self.scanner.scan()

        modules = self.topology.resolve(files)

        excluded_paths = tuple(
            sorted(
                item.relative_path
                for item in files
                if item.authority == FileAuthority.EXCLUDED
            )
        )

        fingerprint = self._fingerprint(
            files=files,
            modules=modules,
            protected_paths=self.protected_paths,
        )

        snapshot = RepositorySnapshot(
            schema_version=self.SCHEMA_VERSION,
            repository_root=str(self.repository_root),
            files=files,
            modules=modules,
            protected_paths=self.protected_paths,
            excluded_paths=excluded_paths,
            fingerprint=fingerprint,
        )

        self._validate_snapshot(snapshot)

        return snapshot

    def find(
        self,
        pattern: str,
        *,
        source_kind: SourceKind | None = None,
        authority: FileAuthority | None = None,
    ) -> tuple[RepositoryFile, ...]:
        snapshot = self.discover()

        normalized_pattern = pattern.replace("\\", "/").lower()

        results = []

        for item in snapshot.files:
            if normalized_pattern not in item.relative_path.lower():
                continue

            if source_kind is not None and item.source_kind != source_kind:
                continue

            if authority is not None and item.authority != authority:
                continue

            results.append(item)

        return tuple(results)

    def get_module(
        self,
        module_name: str,
    ) -> ModuleRecord | None:
        snapshot = self.discover()

        for module in snapshot.modules:
            if module.module_name == module_name:
                return module

        return None

    @staticmethod
    def _fingerprint(
        *,
        files: Iterable[RepositoryFile],
        modules: Iterable[ModuleRecord],
        protected_paths: Iterable[str],
    ) -> str:
        payload = {
            "files": [
                {
                    "relative_path": item.relative_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                    "source_kind": item.source_kind.value,
                    "authority": item.authority.value,
                    "risk": item.risk.value,
                    "is_symlink": item.is_symlink,
                }
                for item in files
            ],
            "modules": [
                {
                    "relative_path": item.relative_path,
                    "module_name": item.module_name,
                    "imports": list(item.imports),
                    "parse_valid": item.parse_valid,
                }
                for item in modules
            ],
            "protected_paths": sorted(protected_paths),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_snapshot(
        snapshot: RepositorySnapshot,
    ) -> None:
        if not snapshot.repository_root:
            raise RepositoryIntegrityError(
                "Repository snapshot has no repository root."
            )

        if not snapshot.fingerprint:
            raise RepositoryIntegrityError(
                "Repository snapshot has no fingerprint."
            )

        paths = [
            item.relative_path
            for item in snapshot.files
        ]

        if paths != sorted(paths):
            raise RepositoryIntegrityError(
                "Repository file ordering is not deterministic."
            )

        module_paths = [
            item.relative_path
            for item in snapshot.modules
        ]

        if module_paths != sorted(module_paths):
            raise RepositoryIntegrityError(
                "Repository module ordering is not deterministic."
            )


# ---------------------------------------------------------------------------
# Public functional API
# ---------------------------------------------------------------------------


def discover_repository(
    repository_root: Path | str,
    *,
    protected_paths: Iterable[str] = (),
) -> RepositorySnapshot:
    """
    Discover and fingerprint a repository.

    This is the primary functional entry point for T16.
    """
    engine = RepositoryIntelligenceEngine(
        repository_root,
        protected_paths=protected_paths,
    )

    return engine.discover()


def find_repository_files(
    repository_root: Path | str,
    pattern: str,
    *,
    source_kind: SourceKind | None = None,
    authority: FileAuthority | None = None,
) -> tuple[RepositoryFile, ...]:
    """Search the deterministic repository snapshot."""
    engine = RepositoryIntelligenceEngine(repository_root)

    return engine.find(
        pattern,
        source_kind=source_kind,
        authority=authority,
    )


def repository_fingerprint(
    repository_root: Path | str,
) -> str:
    """Return the deterministic repository fingerprint."""
    return discover_repository(repository_root).fingerprint


__all__ = [
    "DEFAULT_EXCLUDED_DIRECTORIES",
    "DEFAULT_GENERATED_NAMES",
    "DEFAULT_PROTECTED_NAMES",
    "DEFAULT_SENSITIVE_SUFFIXES",
    "FileAuthority",
    "FileRisk",
    "ModuleImport",
    "ModuleRecord",
    "PackageTopologyResolver",
    "RepositoryClassificationError",
    "RepositoryDiscoveryError",
    "RepositoryFile",
    "RepositoryFingerprintError",
    "RepositoryIntegrityError",
    "RepositoryIntelligenceEngine",
    "RepositoryIntelligenceError",
    "RepositoryPathGuard",
    "RepositoryPathSecurityError",
    "RepositoryScanner",
    "RepositorySnapshot",
    "RepositorySourceError",
    "SourceClassifier",
    "SourceKind",
    "discover_repository",
    "find_repository_files",
    "repository_fingerprint",
]

