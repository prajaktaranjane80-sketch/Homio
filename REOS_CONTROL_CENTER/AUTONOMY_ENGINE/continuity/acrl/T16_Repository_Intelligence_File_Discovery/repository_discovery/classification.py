"""T16 PART-01 — Repository entry classification.

Classifies filesystem entries without importing or executing project code.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class EntryKind(str, Enum):
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    SYMLINK = "SYMLINK"
    OTHER = "OTHER"


class SourceClassification(str, Enum):
    SOURCE = "SOURCE"
    TEST = "TEST"
    CONFIG = "CONFIG"
    DOCUMENTATION = "DOCUMENTATION"
    DATA = "DATA"
    GENERATED = "GENERATED"
    CACHE = "CACHE"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


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
        ".idea",
        ".vscode",
    }
)

DEFAULT_GENERATED_SUFFIXES = frozenset(
    {
        ".pyc",
        ".pyo",
    }
)

DEFAULT_GENERATED_NAMES = frozenset(
    {
        ".egg-info",
    }
)

DEFAULT_PROTECTED_NAMES = frozenset(
    {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "state.json",
    }
)

DEFAULT_PROTECTED_DIRECTORIES = frozenset(
    {
        "data",
        "architecture",
    }
)


def classify_entry(path: Path) -> tuple[EntryKind, SourceClassification]:
    """Classify one filesystem entry deterministically."""

    if path.is_symlink():
        return EntryKind.SYMLINK, SourceClassification.UNKNOWN

    if path.is_dir():
        return EntryKind.DIRECTORY, SourceClassification.UNKNOWN

    if not path.is_file():
        return EntryKind.OTHER, SourceClassification.UNKNOWN

    name = path.name
    suffix = path.suffix.lower()

    if name in DEFAULT_PROTECTED_NAMES:
        return EntryKind.FILE, SourceClassification.PROTECTED

    if suffix in DEFAULT_GENERATED_SUFFIXES:
        return EntryKind.FILE, SourceClassification.GENERATED

    if name.endswith(".egg-info"):
        return EntryKind.FILE, SourceClassification.GENERATED

    if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
        return EntryKind.FILE, SourceClassification.CACHE

    if path.stem.startswith("test_") or name.endswith("_test.py"):
        return EntryKind.FILE, SourceClassification.TEST

    if suffix in {".py", ".pyi"}:
        return EntryKind.FILE, SourceClassification.SOURCE

    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini"}:
        return EntryKind.FILE, SourceClassification.CONFIG

    if suffix in {".md", ".rst", ".txt"}:
        return EntryKind.FILE, SourceClassification.DOCUMENTATION

    if suffix in {".csv", ".tsv", ".db", ".sqlite"}:
        return EntryKind.FILE, SourceClassification.DATA

    return EntryKind.FILE, SourceClassification.UNKNOWN


__all__ = [
    "EntryKind",
    "SourceClassification",
    "DEFAULT_EXCLUDED_DIRECTORIES",
    "DEFAULT_GENERATED_SUFFIXES",
    "DEFAULT_GENERATED_NAMES",
    "DEFAULT_PROTECTED_NAMES",
    "DEFAULT_PROTECTED_DIRECTORIES",
    "classify_entry",
]