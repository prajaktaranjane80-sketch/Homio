from __future__ import annotations

"""
ACRL T16 — Repository Intelligence & File Discovery.

Read-only repository observation layer for deterministic file discovery,
classification, Python topology, search, and repository fingerprinting.
"""

import ast
import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class RepositoryIntelligenceError(Exception):
    """Base error for T16."""


class RepositorySourceError(RepositoryIntelligenceError):
    """Repository source cannot be accessed safely."""


class RepositoryIntegrityError(RepositoryIntelligenceError):
    """Repository observation failed integrity validation."""


class RepositoryFingerprintError(RepositoryIntegrityError):
    """Repository fingerprint integrity is invalid."""


class RepositoryPathSecurityError(RepositoryIntelligenceError):
    """A requested path escapes the repository boundary."""


class RepositoryDiscoveryError(RepositoryIntelligenceError):
    """Repository discovery failed."""


class RepositoryClassificationError(RepositoryIntelligenceError):
    """Repository source classification failed."""


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


class SearchMatchMode(str, Enum):
    CONTAINS = "CONTAINS"
    EXACT = "EXACT"
    GLOB = "GLOB"


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
class RepositoryScanResult:
    files: tuple[RepositoryFile, ...]
    excluded_paths: tuple[str, ...]


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
            if item.source_kind
            in {
                SourceKind.PYTHON,
                SourceKind.TEST,
            }
        )


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


def normalize_repository_path(
    value: str | Path,
) -> str:
    """
    Normalize repository-relative paths and search patterns.

    Filesystem access is not performed.
    """

    normalized = str(value).replace("\\", "/").strip()

    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    if normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized.lower()


class RepositoryPathGuard:
    """Enforces repository-root path boundaries."""

    def __init__(
        self,
        repository_root: Path,
    ) -> None:
        self.repository_root = repository_root.resolve()

    def resolve(
        self,
        candidate: Path | str,
    ) -> Path:
        candidate_path = Path(candidate)

        if not candidate_path.is_absolute():
            candidate_path = (
                self.repository_root
                / candidate_path
            )

        resolved = candidate_path.resolve()

        try:
            resolved.relative_to(
                self.repository_root
            )
        except ValueError as exc:
            raise RepositoryPathSecurityError(
                "Path escapes repository root: "
                f"{candidate}"
            ) from exc

        return resolved


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
        excluded_directories: Iterable[str] = (
            DEFAULT_EXCLUDED_DIRECTORIES
        ),
        generated_names: Iterable[str] = (
            DEFAULT_GENERATED_NAMES
        ),
        protected_names: Iterable[str] = (
            DEFAULT_PROTECTED_NAMES
        ),
        sensitive_suffixes: Iterable[str] = (
            DEFAULT_SENSITIVE_SUFFIXES
        ),
    ) -> None:
        self.excluded_directories = frozenset(
            str(item).lower()
            for item in excluded_directories
        )

        self.generated_names = frozenset(
            str(item).lower()
            for item in generated_names
        )

        self.protected_names = frozenset(
            str(item).lower()
            for item in protected_names
        )

        self.sensitive_suffixes = frozenset(
            str(item).lower()
            for item in sensitive_suffixes
        )

    def classify(
        self,
        relative_path: str,
        is_symlink: bool = False,
    ) -> tuple[
        SourceKind,
        FileAuthority,
        FileRisk,
    ]:
        path = Path(relative_path)

        name = path.name
        normalized_name = name.lower()
        suffix = path.suffix.lower()

        parts = {
            part.lower()
            for part in path.parts
        }

        if is_symlink:
            return (
                SourceKind.UNKNOWN,
                FileAuthority.UNKNOWN,
                FileRisk.UNKNOWN,
            )

        if any(
            fnmatch.fnmatch(
                normalized_name,
                pattern,
            )
            for pattern in self.generated_names
        ):
            return (
                SourceKind.GENERATED,
                FileAuthority.GENERATED,
                FileRisk.NORMAL,
            )

        if parts & self.excluded_directories:
            return (
                SourceKind.CACHE,
                FileAuthority.EXCLUDED,
                FileRisk.NORMAL,
            )

        if normalized_name in self.protected_names:
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

        if suffix in {
            ".py",
            ".pyw",
        }:
            if (
                normalized_name.startswith("test_")
                or normalized_name.endswith("_test.py")
            ):
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

        return (
            SourceKind.UNKNOWN,
            FileAuthority.UNKNOWN,
            FileRisk.UNKNOWN,
        )


class PackageTopologyResolver:
    """
    Builds deterministic Python module topology without
    importing application code.
    """

    def __init__(
        self,
        repository_root: Path,
    ) -> None:
        self.repository_root = repository_root

    def module_name(
        self,
        relative_path: str,
    ) -> str:
        path = Path(relative_path)

        if path.suffix != ".py":
            return ""

        parts = list(
            path.with_suffix("").parts
        )

        if (
            parts
            and parts[-1] == "__init__"
        ):
            parts = parts[:-1]

        return ".".join(parts)

    def parse_imports(
        self,
        absolute_path: Path,
    ) -> tuple[str, ...]:
        try:
            source = absolute_path.read_text(
                encoding="utf-8",
                errors="strict",
            )

            tree = ast.parse(
                source,
                filename=str(absolute_path),
            )
        except (
            OSError,
            UnicodeError,
            SyntaxError,
        ):
            return ()

        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                if node.module:
                    imports.add(node.module)

        return tuple(
            sorted(imports)
        )

    def resolve(
        self,
        files: Iterable[RepositoryFile],
    ) -> tuple[ModuleRecord, ...]:
        records: list[ModuleRecord] = []

        for item in files:
            if item.source_kind not in {
                SourceKind.PYTHON,
                SourceKind.TEST,
            }:
                continue

            if item.is_symlink:
                continue

            absolute = Path(
                item.absolute_path
            )

            records.append(
                ModuleRecord(
                    relative_path=item.relative_path,
                    module_name=self.module_name(
                        item.relative_path
                    ),
                    imports=self.parse_imports(
                        absolute
                    ),
                    parse_valid=self._parse_valid(
                        absolute
                    ),
                )
            )

        records.sort(
            key=lambda record:
            record.relative_path.lower()
        )

        return tuple(records)

    @staticmethod
    def _parse_valid(
        path: Path,
    ) -> bool:
        try:
            source = path.read_text(
                encoding="utf-8",
                errors="strict",
            )

            ast.parse(
                source,
                filename=str(path),
            )

            return True

        except (
            OSError,
            UnicodeError,
            SyntaxError,
        ):
            return False


class RepositoryScanner:
    """Read-only deterministic repository scanner."""

    def __init__(
        self,
        repository_root: Path | str,
        classifier: SourceClassifier | None = None,
    ) -> None:
        self.guard = RepositoryPathGuard(
            Path(repository_root)
        )

        self.repository_root = (
            self.guard.repository_root
        )

        self.classifier = (
            classifier
            or SourceClassifier()
        )

        if not self.repository_root.exists():
            raise RepositorySourceError(
                "Repository does not exist: "
                f"{self.repository_root}"
            )

        if not self.repository_root.is_dir():
            raise RepositorySourceError(
                "Repository root is not a directory: "
                f"{self.repository_root}"
            )

    def scan(
        self,
    ) -> tuple[RepositoryFile, ...]:
        return self.scan_detailed().files

    def scan_detailed(
        self,
    ) -> RepositoryScanResult:
        discovered: list[RepositoryFile] = []
        excluded_paths: list[str] = []

        for root, directories, filenames in os.walk(
            self.repository_root,
            topdown=True,
            followlinks=False,
        ):
            root_path = Path(root)

            kept_directories: list[str] = []

            for directory in sorted(
                directories,
                key=str.lower,
            ):
                directory_lower = directory.lower()

                if (
                    directory_lower
                    in self.classifier.excluded_directories
                ):
                    directory_path = (
                        root_path / directory
                    )

                    try:
                        relative_directory = (
                            directory_path
                            .relative_to(
                                self.repository_root
                            )
                            .as_posix()
                        )
                    except ValueError as exc:
                        raise RepositoryPathSecurityError(
                            "Excluded directory escaped "
                            "repository root: "
                            f"{directory_path}"
                        ) from exc

                    excluded_paths.append(
                        relative_directory
                    )
                    continue

                kept_directories.append(
                    directory
                )

            directories[:] = kept_directories

            for filename in sorted(
                filenames,
                key=str.lower,
            ):
                candidate = (
                    root_path / filename
                )

                try:
                    relative = (
                        candidate
                        .relative_to(
                            self.repository_root
                        )
                        .as_posix()
                    )

                    is_symlink = (
                        candidate.is_symlink()
                    )

                    # IMPORTANT:
                    # A symlink must be observed as a repository
                    # entry without resolving its target.
                    #
                    # Resolving it here could legitimately point
                    # outside the repository and incorrectly trigger
                    # RepositoryPathSecurityError.
                    if is_symlink:
                        (
                            source_kind,
                            authority,
                            risk,
                        ) = (
                            SourceKind.UNKNOWN,
                            FileAuthority.UNKNOWN,
                            FileRisk.UNKNOWN,
                        )

                        digest = (
                            self._symlink_digest(
                                candidate
                            )
                        )

                        size = 0

                        repository_file = (
                            RepositoryFile(
                                relative_path=relative,
                                absolute_path=str(
                                    candidate.absolute()
                                ),
                                size_bytes=size,
                                sha256=digest,
                                source_kind=source_kind,
                                authority=authority,
                                risk=risk,
                                is_symlink=True,
                            )
                        )

                        discovered.append(
                            repository_file
                        )
                        continue

                    # Normal files are still strictly checked
                    # against the repository boundary.
                    resolved = self.guard.resolve(
                        candidate
                    )

                    (
                        source_kind,
                        authority,
                        risk,
                    ) = self.classifier.classify(
                        relative,
                        is_symlink=False,
                    )

                    size = candidate.stat().st_size

                    digest = (
                        self._file_sha256(
                            candidate
                        )
                    )

                    repository_file = (
                        RepositoryFile(
                            relative_path=relative,
                            absolute_path=str(
                                resolved
                            ),
                            size_bytes=size,
                            sha256=digest,
                            source_kind=source_kind,
                            authority=authority,
                            risk=risk,
                            is_symlink=False,
                        )
                    )

                    if (
                        authority
                        == FileAuthority.EXCLUDED
                    ):
                        excluded_paths.append(
                            relative
                        )
                        continue

                    discovered.append(
                        repository_file
                    )

                except RepositoryPathSecurityError:
                    raise

                except OSError as exc:
                    raise RepositoryDiscoveryError(
                        "Unable to inspect repository "
                        f"file: {candidate}"
                    ) from exc

        discovered.sort(
            key=lambda item:
            item.relative_path.lower()
        )

        excluded_paths = sorted(
            set(excluded_paths),
            key=str.lower,
        )

        return RepositoryScanResult(
            files=tuple(discovered),
            excluded_paths=tuple(
                excluded_paths
            ),
        )

    @staticmethod
    def _file_sha256(
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        try:
            with path.open("rb") as handle:
                for chunk in iter(
                    lambda:
                    handle.read(
                        1024 * 1024
                    ),
                    b"",
                ):
                    digest.update(chunk)

        except OSError as exc:
            raise RepositoryDiscoveryError(
                "Unable to fingerprint file: "
                f"{path}"
            ) from exc

        return digest.hexdigest()

    @staticmethod
    def _symlink_digest(
        path: Path,
    ) -> str:
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise RepositoryDiscoveryError(
                "Unable to inspect symlink: "
                f"{path}"
            ) from exc

        return hashlib.sha256(
            f"SYMLINK:{target}".encode(
                "utf-8"
            )
        ).hexdigest()


class RepositoryIntelligenceEngine:
    """Main T16 repository-intelligence engine."""

    SCHEMA_VERSION = "1.1"

    def __init__(
        self,
        repository_root: Path | str,
        *,
        protected_paths: Iterable[str] = (),
        classifier: SourceClassifier | None = None,
    ) -> None:
        self.repository_root = (
            Path(repository_root).resolve()
        )

        self.scanner = RepositoryScanner(
            self.repository_root,
            classifier=classifier,
        )

        self.topology = (
            PackageTopologyResolver(
                self.repository_root
            )
        )

        self.protected_paths = tuple(
            sorted(
                normalize_repository_path(
                    path
                )
                for path in protected_paths
            )
        )

    def discover(
        self,
    ) -> RepositorySnapshot:
        scan_result = (
            self.scanner.scan_detailed()
        )

        files = scan_result.files

        modules = self.topology.resolve(
            files
        )

        excluded_paths = tuple(
            sorted(
                set(
                    scan_result.excluded_paths
                ),
                key=str.lower,
            )
        )

        fingerprint = self._fingerprint(
            files=files,
            modules=modules,
            protected_paths=self.protected_paths,
            excluded_paths=excluded_paths,
        )

        snapshot = RepositorySnapshot(
            schema_version=self.SCHEMA_VERSION,
            repository_root=str(
                self.repository_root
            ),
            files=files,
            modules=modules,
            protected_paths=self.protected_paths,
            excluded_paths=excluded_paths,
            fingerprint=fingerprint,
        )

        self._validate_snapshot(
            snapshot
        )

        return snapshot

    def find(
        self,
        pattern: str,
        *,
        match_mode: SearchMatchMode = SearchMatchMode.EXACT,
        source_kind: SourceKind | None = None,
        authority: FileAuthority | None = None,
    ) -> tuple[RepositoryFile, ...]:
        snapshot = self.discover()

        if not isinstance(
            match_mode,
            SearchMatchMode,
        ):
            try:
                match_mode = SearchMatchMode(
                    match_mode
                )
            except ValueError as exc:
                raise RepositoryClassificationError(
                    "Unsupported search match mode: "
                    f"{match_mode}"
                ) from exc

        normalized_pattern = (
            normalize_repository_path(
                pattern
            )
        )

        has_path_separator = "/" in (
            normalized_pattern
        )

        results: list[RepositoryFile] = []

        for item in snapshot.files:
            if item.source_kind in {
                SourceKind.GENERATED,
                SourceKind.VENDOR,
                SourceKind.CACHE,
            }:
                continue

            normalized_path = (
                normalize_repository_path(
                    item.relative_path
                )
            )

            normalized_name = (
                Path(
                    normalized_path
                ).name.lower()
            )

            if (
                match_mode
                == SearchMatchMode.CONTAINS
            ):
                matched = (
                    normalized_pattern
                    in normalized_path
                )

            elif (
                match_mode
                == SearchMatchMode.EXACT
            ):
                if has_path_separator:
                    matched = (
                        normalized_pattern
                        == normalized_path
                    )
                else:
                    matched = (
                        normalized_pattern
                        == normalized_name
                    )

            elif (
                match_mode
                == SearchMatchMode.GLOB
            ):
                matched = fnmatch.fnmatch(
                    normalized_path,
                    normalized_pattern,
                )

            else:
                raise RepositoryClassificationError(
                    "Unsupported search match mode: "
                    f"{match_mode}"
                )

            if not matched:
                continue

            if (
                source_kind is not None
                and item.source_kind
                != source_kind
            ):
                continue

            if (
                authority is not None
                and item.authority
                != authority
            ):
                continue

            results.append(item)

        results.sort(
            key=lambda item:
            item.relative_path.lower()
        )

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
        excluded_paths: Iterable[str],
    ) -> str:
        payload = {
            "schema_version": "1.1",
            "files": [
                {
                    "relative_path": item.relative_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                    "source_kind": (
                        item.source_kind.value
                    ),
                    "authority": (
                        item.authority.value
                    ),
                    "risk": item.risk.value,
                    "is_symlink": item.is_symlink,
                }
                for item in files
            ],
            "modules": [
                {
                    "relative_path": item.relative_path,
                    "module_name": item.module_name,
                    "imports": list(
                        item.imports
                    ),
                    "parse_valid": (
                        item.parse_valid
                    ),
                }
                for item in modules
            ],
            "protected_paths": sorted(
                protected_paths,
                key=str.lower,
            ),
            "excluded_paths": sorted(
                excluded_paths,
                key=str.lower,
            ),
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

        if paths != sorted(
            paths,
            key=str.lower,
        ):
            raise RepositoryIntegrityError(
                "Repository file ordering "
                "is not deterministic."
            )

        module_paths = [
            item.relative_path
            for item in snapshot.modules
        ]

        if module_paths != sorted(
            module_paths,
            key=str.lower,
        ):
            raise RepositoryIntegrityError(
                "Repository module ordering "
                "is not deterministic."
            )

        excluded = list(
            snapshot.excluded_paths
        )

        if excluded != sorted(
            excluded,
            key=str.lower,
        ):
            raise RepositoryIntegrityError(
                "Repository excluded-path ordering "
                "is not deterministic."
            )


def discover_repository(
    repository_root: Path | str,
    *,
    protected_paths: Iterable[str] = (),
) -> RepositorySnapshot:
    """Discover and fingerprint a repository."""

    engine = RepositoryIntelligenceEngine(
        repository_root,
        protected_paths=protected_paths,
    )

    return engine.discover()


def find_repository_files(
    repository_root: Path | str,
    pattern: str,
    *,
    match_mode: SearchMatchMode = SearchMatchMode.EXACT,
    source_kind: SourceKind | None = None,
    authority: FileAuthority | None = None,
) -> tuple[RepositoryFile, ...]:
    """Search the deterministic repository snapshot."""

    engine = RepositoryIntelligenceEngine(
        repository_root
    )

    return engine.find(
        pattern,
        match_mode=match_mode,
        source_kind=source_kind,
        authority=authority,
    )


def repository_fingerprint(
    repository_root: Path | str,
) -> str:
    """Return the deterministic repository fingerprint."""

    return discover_repository(
        repository_root
    ).fingerprint


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
    "RepositoryScanResult",
    "RepositoryScanner",
    "RepositorySnapshot",
    "RepositorySourceError",
    "SearchMatchMode",
    "SourceClassifier",
    "SourceKind",
    "discover_repository",
    "find_repository_files",
    "normalize_repository_path",
    "repository_fingerprint",
]