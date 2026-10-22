"""T16 static import discovery for JavaScript, TypeScript and CSS.

This module reads source as text. It never imports or executes project code.
Only repository-internal relative and configured tsconfig alias imports are
resolved; package imports and remote URLs remain external evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


class WebSourceParseError(RuntimeError):
    """Raised when web-source discovery cannot be trusted."""


WEB_SOURCE_SUFFIXES = frozenset(
    {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".css",
        ".scss",
        ".sass",
        ".less",
    }
)

CSS_SOURCE_SUFFIXES = frozenset(
    {".css", ".scss", ".sass", ".less"}
)

_SOURCE_LIMIT_BYTES = 2 * 1024 * 1024

_FROM_IMPORT = re.compile(
    r"""(?m)^[ \t]*(?:import|export)\b
        (?:(?!^[ \t]*(?:import|export)\b)[\s\S]){0,4096}?
        \bfrom\s*["']([^"']+)["']""",
    re.VERBOSE,
)
_SIDE_EFFECT_IMPORT = re.compile(
    r"""\bimport\s*["']([^"']+)["']"""
)
_DYNAMIC_IMPORT = re.compile(
    r"""\bimport\s*\(\s*["']([^"']+)["']\s*\)"""
)
_COMMONJS_REQUIRE = re.compile(
    r"""\brequire\s*\(\s*["']([^"']+)["']\s*\)"""
)
_CSS_IMPORT = re.compile(
    r"""(?im)^\s*@import\s+(?:url\(\s*)?["']?([^"'()\s;]+)["']?\s*\)?"""
)


@dataclass(frozen=True, slots=True)
class WebImportEvidence:
    """One statically observed web-source import."""

    source_path: str
    imported_name: str
    import_kind: str
    line_number: int
    resolved_path: str | None


def _safe_source_file(
    root: Path,
    relative_path: str,
) -> tuple[Path, str]:
    base = root.resolve()

    raw = relative_path.replace("\\", "/").strip()
    candidate_path = Path(raw)

    if (
        not raw
        or candidate_path.is_absolute()
        or any(part in {"", ".", ".."} for part in raw.split("/"))
    ):
        raise WebSourceParseError(
            "Web source path must be a safe repository-relative path."
        )

    unresolved = base / candidate_path

    if unresolved.is_symlink():
        raise WebSourceParseError(
            "Symbolic-link source files are not parsed."
        )

    try:
        source = unresolved.resolve(strict=True)
        source.relative_to(base)
    except (OSError, ValueError) as exc:
        raise WebSourceParseError(
            "Web source is missing or escapes the repository."
        ) from exc

    if not source.is_file():
        raise WebSourceParseError(
            "Web source path is not a regular file."
        )

    if source.suffix.lower() not in WEB_SOURCE_SUFFIXES:
        raise WebSourceParseError(
            "Unsupported web source extension."
        )

    try:
        size = source.stat().st_size
    except OSError as exc:
        raise WebSourceParseError(
            "Unable to inspect web source size."
        ) from exc

    if size > _SOURCE_LIMIT_BYTES:
        raise WebSourceParseError(
            "Web source exceeds the static parser size limit."
        )

    return source, source.relative_to(base).as_posix()


def _tsconfig_candidates(root: Path) -> tuple[Path, ...]:
    """Known HOMIO frontend locations, without scanning dependencies."""
    return (
        root / "tsconfig.json",
        root / "Frontend" / "tsconfig.json",
        root / "frontend" / "tsconfig.json",
        root / "REOS_CONTROL_CENTER" / "Frontend" / "tsconfig.json",
        root / "REOS_CONTROL_CENTER" / "frontend" / "tsconfig.json",
    )


def _load_tsconfig_paths(root: Path) -> tuple[Path, dict[str, list[str]]]:
    for config_path in _tsconfig_candidates(root):
        if not config_path.is_file() or config_path.is_symlink():
            continue

        try:
            payload = json.loads(
                config_path.read_text(encoding="utf-8-sig")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise WebSourceParseError(
                "Unable to read frontend tsconfig safely."
            ) from exc

        compiler = payload.get("compilerOptions", {})
        if not isinstance(compiler, dict):
            raise WebSourceParseError(
                "tsconfig compilerOptions must be an object."
            )

        raw_paths = compiler.get("paths", {})
        if not isinstance(raw_paths, dict):
            raise WebSourceParseError(
                "tsconfig paths must be an object."
            )

        paths: dict[str, list[str]] = {}
        for key, targets in raw_paths.items():
            if not isinstance(key, str) or not key:
                continue

            if isinstance(targets, str):
                targets = [targets]

            if not isinstance(targets, list) or not all(
                isinstance(value, str) and value
                for value in targets
            ):
                raise WebSourceParseError(
                    "Each tsconfig path mapping must contain string targets."
                )

            paths[key] = list(targets)

        base_url = compiler.get("baseUrl")
        config_base = config_path.parent

        if isinstance(base_url, str) and base_url:
            config_base = (config_base / base_url).resolve()

        return config_base, paths

    return root, {}


def _candidate_files(candidate: Path) -> tuple[Path, ...]:
    """Return deterministic extension and index candidates."""
    values: list[Path] = [candidate]

    if candidate.suffix:
        return tuple(values)

    for suffix in (
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".json",
    ):
        values.append(candidate.with_suffix(suffix))

    for suffix in (
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".css",
    ):
        values.append(candidate / f"index{suffix}")

    return tuple(values)


def resolve_web_import(
    root: Path,
    source_path: str,
    specifier: str,
) -> str | None:
    """Resolve an import to a file inside the repository, if known."""
    base = root.resolve()
    name = specifier.strip()

    if (
        not name
        or name.startswith(("/", "#", "//"))
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", name)
    ):
        return None

    candidates: list[Path] = []
    source = (base / source_path).resolve()

    if name.startswith("."):
        candidates.append(source.parent / name)
    else:
        config_base, mappings = _load_tsconfig_paths(base)

        for pattern, targets in mappings.items():
            if "*" in pattern:
                prefix, suffix = pattern.split("*", 1)
                if not name.startswith(prefix) or not name.endswith(suffix):
                    continue

                end = len(name) - len(suffix) if suffix else len(name)
                middle = name[len(prefix):end]

                for target in targets:
                    if target.count("*") > 1:
                        continue
                    rendered = target.replace("*", middle, 1)
                    candidates.append(config_base / rendered)
            elif name == pattern:
                candidates.extend(config_base / target for target in targets)

        # Bare package names such as "react" intentionally remain external.

    for candidate in candidates:
        for file_candidate in _candidate_files(candidate):
            try:
                resolved = file_candidate.resolve(strict=True)
                resolved.relative_to(base)
            except (OSError, ValueError):
                continue

            if not resolved.is_file() or resolved.is_symlink():
                continue

            return resolved.relative_to(base).as_posix()

    return None


def _match_imports(
    text: str,
    source_path: str,
    root: Path,
    *,
    css_only: bool,
) -> tuple[WebImportEvidence, ...]:
    patterns = (
        ((_CSS_IMPORT, "CSS_IMPORT"),)
        if css_only
        else (
            (_FROM_IMPORT, "STATIC_IMPORT"),
            (_SIDE_EFFECT_IMPORT, "SIDE_EFFECT_IMPORT"),
            (_DYNAMIC_IMPORT, "DYNAMIC_IMPORT"),
            (_COMMONJS_REQUIRE, "COMMONJS_REQUIRE"),
        )
    )

    evidence: dict[tuple[int, str, str], WebImportEvidence] = {}

    for pattern, kind in patterns:
        for match in pattern.finditer(text):
            specifier = match.group(1).strip()
            line_number = text.count("\n", 0, match.start()) + 1

            if not specifier:
                continue

            key = (line_number, specifier, kind)
            evidence[key] = WebImportEvidence(
                source_path=source_path,
                imported_name=specifier,
                import_kind=kind,
                line_number=line_number,
                resolved_path=resolve_web_import(
                    root,
                    source_path,
                    specifier,
                ),
            )

    return tuple(
        sorted(
            evidence.values(),
            key=lambda item: (
                item.line_number,
                item.imported_name,
                item.import_kind,
            ),
        )
    )


def parse_web_imports(
    root: Path | str,
    relative_path: str,
) -> tuple[WebImportEvidence, ...]:
    """Extract deterministic local import evidence from a web source file."""
    base = Path(root).resolve()
    source, normalized_path = _safe_source_file(
        base,
        relative_path,
    )

    try:
        text = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise WebSourceParseError(
            "Unable to decode web source as UTF-8."
        ) from exc

    return _match_imports(
        text,
        normalized_path,
        base,
        css_only=source.suffix.lower() in CSS_SOURCE_SUFFIXES,
    )


__all__ = [
    "CSS_SOURCE_SUFFIXES",
    "WEB_SOURCE_SUFFIXES",
    "WebImportEvidence",
    "WebSourceParseError",
    "parse_web_imports",
    "resolve_web_import",
]
