"""Generate a provenance-bound HOMIO / REOS technical reference atlas.

This module reuses ACRL T16 for repository classification and static source
parsing. Git's tracked tree is the complete inventory authority; T16's normal
scanner exclusions therefore cannot silently remove tracked files.

The generator reads repository metadata and source text for static parsing only.
It never imports or executes HOMIO business code, changes state.json, authorizes
work, or writes to the source branch. Publication is owned by the GitHub Actions
workflow, which writes the generated JSON to a separate reference branch.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

REPOSITORY_FULL_NAME = "prajaktaranjane80-sketch/Homio"
SOURCE_BRANCH = "reos-development"
REFERENCE_BRANCH = "reos-project-reference"
ATLAS_RELATIVE_PATH = "REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json"
ENTRYPOINT_RELATIVE_PATH = "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
STATE_RELATIVE_PATH = "REOS_CONTROL_CENTER/data/state.json"
GENERATOR_RELATIVE_PATH = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T16_Repository_Intelligence_File_Discovery/"
    "project_reference_atlas/project_reference_atlas.py"
)
SCHEMA_RELATIVE_PATH = "REOS_CONTROL_CENTER/contracts/project_reference_atlas.schema.json"
GENERATOR_VERSION = "1.0.0"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SENSITIVE_PARTS = {
    ".env", ".env.local", ".env.production", "secrets", "secret",
    "credentials", "credential", "private", "token-store", "id_rsa",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".secret"}
TEST_NAME_RE = re.compile(r"(^test_.*|.*_test|.*\.test|.*\.spec)$", re.I)
PATH_IN_CODE_RE = re.compile(r"`([^`\r\n]{2,240})`")


class AtlasGenerationError(RuntimeError):
    """Raised when a trustworthy atlas cannot be generated."""


@dataclass(frozen=True)
class GitEntry:
    path: str
    mode: str
    object_type: str
    object_sha: str
    size_bytes: int | None

    @property
    def is_symlink(self) -> bool:
        return self.mode == "120000"

    @property
    def is_submodule(self) -> bool:
        return self.mode == "160000" or self.object_type == "commit"


def _run_git(root: Path, *args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AtlasGenerationError(
            f"git {' '.join(args)} failed ({completed.returncode}): "
            f"{completed.stderr.strip()[:500]}"
        )
    return completed.stdout.strip()


def _run_git_bytes(root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", "replace")[:500]
        raise AtlasGenerationError(
            f"git {' '.join(args)} failed ({completed.returncode}): {message}"
        )
    return completed.stdout


def _live_remote_head(root: Path, branch: str) -> str:
    output = _run_git(root, "ls-remote", "origin", f"refs/heads/{branch}")
    if not output:
        raise AtlasGenerationError(
            f"Remote origin has no visible refs/heads/{branch} reference."
        )
    sha = output.split()[0]
    if not SHA_RE.fullmatch(sha):
        raise AtlasGenerationError("Remote branch returned an invalid commit SHA.")
    return sha


def _normalized_origin(origin: str) -> str:
    value = origin.strip()
    if value.startswith("git@github.com:"):
        value = "https://github.com/" + value.split(":", 1)[1]
    elif value.startswith("ssh://git@github.com/"):
        value = "https://github.com/" + value.removeprefix("ssh://git@github.com/")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != "github.com":
        raise AtlasGenerationError("Git origin is not the canonical GitHub host.")
    path = parsed.path.removesuffix(".git").strip("/").lower()
    return "https://github.com/" + path


def _identity(root: Path, expected_branch: str, require_live_tip: bool) -> dict[str, str]:
    top_level = Path(_run_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top_level != root.resolve():
        raise AtlasGenerationError("Atlas root does not match the Git repository root.")
    branch = _run_git(root, "branch", "--show-current")
    if branch != expected_branch:
        raise AtlasGenerationError(
            f"Expected source branch {expected_branch!r}; found {branch!r}."
        )
    origin = _run_git(root, "remote", "get-url", "origin")
    if _normalized_origin(origin) != "https://github.com/" + REPOSITORY_FULL_NAME.lower():
        raise AtlasGenerationError("Git origin does not match the canonical HOMIO repository.")
    if _run_git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AtlasGenerationError("Working tree is dirty; refusing to mix uncommitted files into the T16 snapshot.")
    head = _run_git(root, "rev-parse", "HEAD")
    tree = _run_git(root, "rev-parse", "HEAD^{tree}")
    committed_at = _run_git(root, "show", "-s", "--format=%cI", "HEAD")
    if not SHA_RE.fullmatch(head) or not SHA_RE.fullmatch(tree):
        raise AtlasGenerationError("Git returned an invalid HEAD or tree SHA.")
    identity = {
        "repository": REPOSITORY_FULL_NAME,
        "source_branch": branch,
        "source_commit_sha": head,
        "source_tree_sha": tree,
        "source_commit_time": committed_at,
    }
    if require_live_tip:
        remote_head = _live_remote_head(root, expected_branch)
        if remote_head != head:
            raise AtlasGenerationError(
                "Checked-out source SHA is not the current live origin branch tip. "
                f"checkout={head}; remote={remote_head}. Refusing stale publication."
            )
    return identity


def _safe_repo_path(raw: str) -> str:
    normalized = raw.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
        or candidate.is_absolute()
    ):
        raise AtlasGenerationError(f"Unsafe Git tree path: {raw!r}")
    return normalized


def _git_entries(root: Path) -> list[GitEntry]:
    """Read every tracked leaf from Git's tree, including T16-excluded paths."""
    raw = _run_git_bytes(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    records = [item for item in raw.split(b"\0") if item]
    parsed: list[tuple[str, str, str, str]] = []
    for record in records:
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split(" ", 2)
            path = _safe_repo_path(path_bytes.decode("utf-8", "surrogateescape"))
        except (ValueError, UnicodeError) as exc:
            raise AtlasGenerationError("Could not parse a Git tree entry safely.") from exc
        if object_type not in {"blob", "commit"}:
            raise AtlasGenerationError(
                f"Unsupported Git tree object type {object_type!r} at {path!r}."
            )
        if not SHA_RE.fullmatch(object_sha):
            raise AtlasGenerationError(f"Invalid Git object SHA for {path!r}.")
        parsed.append((path, mode, object_type, object_sha))

    sizes: dict[str, int] = {}
    blob_shas = [sha for _, _, kind, sha in parsed if kind == "blob"]
    if blob_shas:
        batch_input = "".join(f"{sha}\n" for sha in blob_shas)
        batch_output = _run_git(root, "cat-file", "--batch-check", input_text=batch_input)
        for line in batch_output.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[1] == "blob":
                try:
                    sizes[parts[0]] = int(parts[2])
                except ValueError as exc:
                    raise AtlasGenerationError("Git returned a non-numeric blob size.") from exc
        if len(sizes) != len(set(blob_shas)):
            raise AtlasGenerationError("Git did not return a size for every tracked blob.")

    entries = [
        GitEntry(path, mode, kind, sha, sizes.get(sha) if kind == "blob" else None)
        for path, mode, kind, sha in parsed
    ]
    entries.sort(key=lambda item: item.path.casefold())
    if len({entry.path for entry in entries}) != len(entries):
        raise AtlasGenerationError("Git tree contains duplicate tracked paths.")
    return entries


def _is_sensitive_path(path: str) -> bool:
    parts = {part.casefold() for part in PurePosixPath(path).parts}
    suffix = PurePosixPath(path).suffix.casefold()
    name = PurePosixPath(path).name.casefold()
    return bool(parts.intersection(SENSITIVE_PARTS)) or name in SENSITIVE_PARTS or suffix in SENSITIVE_SUFFIXES


def _path_category(entry: GitEntry) -> str:
    path = entry.path
    lower = path.casefold()
    name = PurePosixPath(path).name.casefold()
    suffix = PurePosixPath(path).suffix.casefold()
    parts = {part.casefold() for part in PurePosixPath(path).parts}
    if entry.is_submodule:
        return "SUBMODULE"
    if entry.is_symlink:
        return "SYMLINK"
    if _is_sensitive_path(path):
        return "SENSITIVE_OR_SECRET_MATERIAL"
    if "node_modules" in parts or "vendor" in parts or "third_party" in parts:
        return "VENDOR"
    if any(part in {"dist", "build", "coverage", "generated", "__pycache__"} for part in parts):
        return "GENERATED_OR_BUILD_OUTPUT"
    if TEST_NAME_RE.match(name.rsplit(".", 1)[0]) or "tests" in parts or "test" in parts:
        return "TEST"
    if suffix in {".md", ".rst", ".txt", ".adoc"}:
        return "DOCUMENTATION"
    if suffix in {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".html", ".css", ".scss", ".sass", ".less"}:
        return "SOURCE"
    if suffix in {".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".xml"} or name in {
        "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
        "requirements.txt", "pyproject.toml", "setup.cfg", "tox.ini", "dockerfile",
        "makefile", "justfile",
    }:
        return "CONFIGURATION"
    if suffix in {".sql", ".json", ".jsonl", ".csv", ".tsv", ".parquet", ".db", ".sqlite"}:
        return "DATA_OR_SCHEMA"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".woff", ".woff2", ".ttf", ".otf"}:
        return "BINARY_ASSET"
    return "UNKNOWN"


def _path_domains(path: str) -> list[str]:
    lower = path.casefold()
    name = PurePosixPath(path).name.casefold()
    domains: list[str] = []
    if ".github/workflows/" in lower or ".github/actions/" in lower:
        domains.append("CI_CD_AND_AUTOMATION")
    if any(token in lower for token in ("openapi", "swagger", "api/", "route", "contract")):
        domains.append("API_OR_CONTRACT")
    if any(token in lower for token in ("migration", "schema", "database", "postgres", "redis", "/sql/", "/db/")) or name.endswith(".sql"):
        domains.append("DATABASE_AND_PERSISTENCE")
    if any(token in lower for token in ("event", "outbox", "queue", "workflow", "consumer", "publisher")):
        domains.append("EVENTS_AND_WORKFLOWS")
    if any(token in lower for token in ("search", "index", "embedding", "retrieval")):
        domains.append("SEARCH_AND_RETRIEVAL")
    if any(token in lower for token in ("auth", "security", "tenant", "permission", "policy")):
        domains.append("SECURITY_AND_TENANCY")
    if any(token in lower for token in ("package.json", "package-lock", "requirements", "pyproject", "poetry.lock", "uv.lock", "pnpm-lock", "yarn.lock")):
        domains.append("DEPENDENCY_MANAGEMENT")
    if not domains:
        domains.append("GENERAL_REPOSITORY")
    return domains


def _infer_owner(path: str, registry: Mapping[str, Any]) -> dict[str, str | None]:
    """Resolve only path-backed owners; unknown paths remain explicitly unknown."""
    candidates: list[tuple[int, str, str]] = []
    for key, value in registry.items():
        if not isinstance(value, Mapping):
            continue
        owner_path = value.get("path")
        if isinstance(owner_path, str) and (
            path == owner_path or path.startswith(owner_path.rstrip("/") + "/")
        ):
            candidates.append((len(owner_path), str(key), owner_path))
    if candidates:
        _, key, owner_path = max(candidates)
        return {
            "owner_key": key,
            "owner_path": owner_path,
            "confidence": "HIGH_EXPLICIT_ENTRYPOINT_REGISTRY",
        }

    parts = PurePosixPath(path).parts
    for part in parts:
        if re.match(r"^T\d{2}_", part):
            return {
                "owner_key": part.split("_", 1)[0].lower(),
                "owner_path": "/".join(parts[: parts.index(part) + 1]),
                "confidence": "HIGH_EXPLICIT_ACRL_FOLDER_BOUNDARY",
            }
    if path.startswith(".github/workflows/") or path.startswith(".github/actions/"):
        return {
            "owner_key": "github_actions_pipeline",
            "owner_path": ".github",
            "confidence": "HIGH_EXPLICIT_PLATFORM_BOUNDARY",
        }
    if path.startswith("REOS_CONTROL_CENTER/backend/"):
        return {
            "owner_key": "backend_workstream",
            "owner_path": "REOS_CONTROL_CENTER/backend",
            "confidence": "HIGH_EXPLICIT_WORKSTREAM_PATH",
        }
    return {
        "owner_key": None,
        "owner_path": None,
        "confidence": "UNRESOLVED_NO_EXPLICIT_OWNER_EVIDENCE",
    }


def _load_entrypoint_literals(root: Path) -> dict[str, Any]:
    path = root / ENTRYPOINT_RELATIVE_PATH
    if not path.is_file():
        return {"document_registry": {}, "workstream_routing": {}, "acrl_owner_routing": {}}
    try:
        source = path.read_text(encoding="utf-8-sig")
        module = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise AtlasGenerationError(
            "The existing AI_AGENT_ENTRYPOINT.py could not be parsed safely."
        ) from exc
    wanted = {"DOCUMENT_REGISTRY", "WORKSTREAM_ROUTING", "ACRL_OWNER_ROUTING"}
    found: dict[str, Any] = {}
    for node in module.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            value = node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            value = node.value
        else:
            continue
        if name in wanted:
            try:
                found[name] = ast.literal_eval(value)
            except (ValueError, TypeError):
                # Dynamic expressions are not executed or guessed.
                found[name] = {}
    return {
        "document_registry": found.get("DOCUMENT_REGISTRY", {}),
        "workstream_routing": found.get("WORKSTREAM_ROUTING", {}),
        "acrl_owner_routing": found.get("ACRL_OWNER_ROUTING", {}),
    }


def _load_t16(root: Path, required: bool) -> tuple[Any | None, dict[str, Any]]:
    """Load and run exactly one existing T16 discovery snapshot."""
    repo_root = str(root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    module_base = (
        "REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl."
        "T16_Repository_Intelligence_File_Discovery"
    )
    try:
        repository_module = importlib.import_module(
            module_base + ".repository_intelligence"
        )
        engine = repository_module.RepositoryIntelligenceEngine(root)
        snapshot = engine.discover()
    except Exception as exc:  # T16 boundary: classify the failure, do not swallow it silently.
        if required:
            raise AtlasGenerationError(
                "Existing T16 repository discovery failed; atlas generation is blocked. "
                f"Failure type: {type(exc).__name__}."
            ) from exc
        return None, {
            "status": "UNAVAILABLE",
            "failure_type": type(exc).__name__,
            "snapshot_count": 0,
        }

    metadata: dict[str, dict[str, Any]] = {}
    for item in snapshot.files:
        metadata[item.relative_path] = {
            "source_kind": getattr(item.source_kind, "value", str(item.source_kind)),
            "authority": getattr(item.authority, "value", str(item.authority)),
            "risk": getattr(item.risk, "value", str(item.risk)),
            "size_bytes": int(item.size_bytes),
            "t16_sha256": str(item.sha256),
            "is_symlink": bool(item.is_symlink),
        }
    module_records = [
        {
            "path": item.relative_path,
            "module_name": item.module_name,
            "imports": list(item.imports),
            "parse_valid": bool(item.parse_valid),
        }
        for item in snapshot.modules
    ]
    return {
        "metadata": metadata,
        "modules": module_records,
        "excluded_paths": list(snapshot.excluded_paths),
        "fingerprint": str(snapshot.fingerprint),
    }, {
        "status": "AVAILABLE",
        "schema_version": str(snapshot.schema_version),
        "snapshot_count": 1,
        "files_classified": len(metadata),
        "modules_observed": len(module_records),
        "t16_fingerprint": str(snapshot.fingerprint),
    }


def _static_imports_from_one_t16_snapshot(
    root: Path,
    t16_snapshot: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    """Use T16's parsers against the single snapshot; do not rescan the tree."""
    if not t16_snapshot:
        return [], [], {"python_files_attempted": 0, "web_files_attempted": 0}
    base = (
        "REOS_CONTROL_CENTER.AUTONOMY_ENGINE.continuity.acrl."
        "T16_Repository_Intelligence_File_Discovery.source_intelligence"
    )
    try:
        python_parser = importlib.import_module(base + ".source_parser")
        web_parser = importlib.import_module(base + ".web_source_parser")
    except Exception as exc:
        return [], [f"T16 parser module unavailable: {type(exc).__name__}"], {
            "python_files_attempted": 0,
            "web_files_attempted": 0,
        }

    source_meta = t16_snapshot.get("metadata", {})
    edges: list[dict[str, Any]] = []
    failures: list[str] = []
    attempted = {"python_files_attempted": 0, "web_files_attempted": 0}
    for path, item in sorted(source_meta.items(), key=lambda pair: pair[0].casefold()):
        if item.get("is_symlink") or _is_sensitive_path(path):
            continue
        suffix = PurePosixPath(path).suffix.casefold()
        if suffix in {".py", ".pyi"}:
            attempted["python_files_attempted"] += 1
            try:
                imports = python_parser.parse_imports(root, path)
                for evidence in imports:
                    edges.append({
                        "source_path": evidence.source_path,
                        "imported_name": evidence.imported_name,
                        "import_kind": evidence.import_kind,
                        "line_number": int(evidence.line_number),
                        "resolved_path": None,
                        "resolution": "SYMBOLIC_IMPORT_ONLY",
                        "confidence": "STATIC_PARSE_CONFIRMED",
                    })
            except Exception as exc:
                failures.append(f"{path}:{type(exc).__name__}")
        elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".scss", ".sass", ".less"}:
            attempted["web_files_attempted"] += 1
            try:
                imports = web_parser.parse_web_imports(root, path)
                for evidence in imports:
                    edges.append({
                        "source_path": evidence.source_path,
                        "imported_name": evidence.imported_name,
                        "import_kind": evidence.import_kind,
                        "line_number": int(evidence.line_number),
                        "resolved_path": evidence.resolved_path,
                        "resolution": "RESOLVED_LOCAL" if evidence.resolved_path else "UNRESOLVED_OR_EXTERNAL",
                        "confidence": "STATIC_PARSE_CONFIRMED",
                    })
            except Exception as exc:
                failures.append(f"{path}:{type(exc).__name__}")
    edges.sort(key=lambda item: (
        item["source_path"].casefold(),
        item["line_number"],
        item["import_kind"],
        item["imported_name"],
    ))
    return edges, sorted(failures, key=str.casefold), attempted


def _documentation_references(
    root: Path,
    entries: Iterable[GitEntry],
    known_paths: set[str],
    max_bytes: int = 1_000_000,
) -> tuple[list[dict[str, str]], list[str]]:
    refs: list[dict[str, str]] = []
    skipped: list[str] = []
    for entry in entries:
        if _path_category(entry) != "DOCUMENTATION" or entry.is_symlink or entry.is_submodule:
            continue
        if _is_sensitive_path(entry.path) or (entry.size_bytes or 0) > max_bytes:
            skipped.append(entry.path)
            continue
        try:
            content = (root / entry.path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            skipped.append(entry.path)
            continue
        targets: set[str] = set()
        for candidate in PATH_IN_CODE_RE.findall(content):
            normalized = candidate.strip().replace("\\", "/")
            if normalized in known_paths and normalized != entry.path:
                targets.add(normalized)
        refs.extend(
            {"source_path": entry.path, "target_path": target, "evidence": "EXACT_BACKTICK_PATH"}
            for target in sorted(targets, key=str.casefold)
        )
    refs.sort(key=lambda item: (item["source_path"].casefold(), item["target_path"].casefold()))
    return refs, sorted(skipped, key=str.casefold)


def _workflow_jobs(root: Path, entries: Iterable[GitEntry]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in entries:
        if not (entry.path.startswith(".github/workflows/") or "/.github/workflows/" in entry.path):
            continue
        record: dict[str, Any] = {
            "path": entry.path,
            "object_sha": entry.object_sha,
            "job_names": [],
            "job_parser": "INDENTATION_BASED_STATIC_HINT_ONLY",
        }
        if not entry.is_symlink and not entry.is_submodule and not _is_sensitive_path(entry.path):
            try:
                content = (root / entry.path).read_text(encoding="utf-8-sig")
                in_jobs = False
                for line in content.splitlines():
                    if re.match(r"^jobs:\s*(?:#.*)?$", line):
                        in_jobs = True
                        continue
                    if in_jobs and line and not line[0].isspace() and not line.startswith("#"):
                        break
                    if in_jobs:
                        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(?:#.*)?$", line)
                        if match:
                            record["job_names"].append(match.group(1))
            except (OSError, UnicodeError):
                record["job_parser"] = "UNREADABLE"
        result.append(record)
    return sorted(result, key=lambda item: item["path"].casefold())


def _entrypoint_owner_records(literals: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    registry = literals.get("document_registry", {})
    if isinstance(registry, Mapping):
        for key, value in sorted(registry.items(), key=lambda pair: str(pair[0]).casefold()):
            if not isinstance(value, Mapping):
                continue
            records.append({
                "owner_key": str(key),
                "path": value.get("path"),
                "role": value.get("role"),
                "authority": value.get("authority"),
                "evidence": "AI_AGENT_ENTRYPOINT_DOCUMENT_REGISTRY",
            })
    return records


def _index_records(entries: list[GitEntry], t16_snapshot: Mapping[str, Any] | None,
                   entrypoint_literals: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = entrypoint_literals.get("document_registry", {})
    t16_meta = t16_snapshot.get("metadata", {}) if t16_snapshot else {}
    inventory: list[dict[str, Any]] = []
    for entry in entries:
        info = t16_meta.get(entry.path, {})
        category = _path_category(entry)
        if info:
            source_kind = info.get("source_kind", "UNKNOWN")
            authority = info.get("authority", "UNKNOWN")
            risk = info.get("risk", "UNKNOWN")
            classification_evidence = "T16_EXISTING_CLASSIFIER"
        else:
            source_kind = category
            authority = "UNKNOWN"
            risk = "SENSITIVE" if _is_sensitive_path(entry.path) else "UNKNOWN"
            classification_evidence = "GIT_TREE_PATH_ONLY"
        inventory.append({
            "path": entry.path,
            "mode": entry.mode,
            "object_type": entry.object_type,
            "object_sha": entry.object_sha,
            "byte_size": entry.size_bytes,
            "is_symlink": entry.is_symlink,
            "is_submodule": entry.is_submodule,
            "category": category,
            "source_kind": source_kind,
            "authority_classification": authority,
            "risk_classification": risk,
            "classification_evidence": classification_evidence,
            "owner": _infer_owner(entry.path, registry),
            "domains": _path_domains(entry.path),
        })
    indexes: dict[str, list[dict[str, Any]]] = {
        "api_and_contracts": [],
        "database_and_persistence": [],
        "events_and_workflows": [],
        "tests": [],
        "dependency_manifests": [],
        "documentation": [],
        "ci_workflows": [],
        "sensitive_or_secret_paths": [],
        "submodules": [],
        "symlinks": [],
        "unclassified": [],
    }
    for item in inventory:
        path = item["path"]
        domains = set(item["domains"])
        category = item["category"]
        target_indices = []
        if "API_OR_CONTRACT" in domains:
            target_indices.append("api_and_contracts")
        if "DATABASE_AND_PERSISTENCE" in domains:
            target_indices.append("database_and_persistence")
        if "EVENTS_AND_WORKFLOWS" in domains:
            target_indices.append("events_and_workflows")
        if category == "TEST":
            target_indices.append("tests")
        if "DEPENDENCY_MANAGEMENT" in domains:
            target_indices.append("dependency_manifests")
        if category == "DOCUMENTATION":
            target_indices.append("documentation")
        if "CI_CD_AND_AUTOMATION" in domains:
            target_indices.append("ci_workflows")
        if category == "SENSITIVE_OR_SECRET_MATERIAL":
            target_indices.append("sensitive_or_secret_paths")
        if item["is_submodule"]:
            target_indices.append("submodules")
        if item["is_symlink"]:
            target_indices.append("symlinks")
        if category == "UNKNOWN" or item["source_kind"] == "UNKNOWN":
            target_indices.append("unclassified")
        for key in target_indices:
            indexes[key].append({"path": path, "object_sha": item["object_sha"]})
    return inventory, indexes


def _canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("integrity", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_schema_contract(schema: Mapping[str, Any]) -> None:
    """Validate the checked-in JSON Schema contract without extra dependencies."""
    required = {
        "atlas_schema_version", "status", "repository", "source_baseline",
        "authority_model", "coverage", "inventory", "architecture",
        "relationships", "provenance", "known_limitations", "integrity",
    }
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise AtlasGenerationError("Atlas schema must use JSON Schema draft 2020-12.")
    schema_required = set(schema.get("required", []))
    if schema_required != required:
        raise AtlasGenerationError("Atlas schema top-level required fields do not match the generator contract.")
    properties = schema.get("properties")
    if not isinstance(properties, Mapping) or not required.issubset(properties):
        raise AtlasGenerationError("Atlas schema is missing one or more required top-level property definitions.")
    status_enum = set(properties.get("status", {}).get("enum", []))
    if status_enum != {"CURRENT", "INVENTORY_CURRENT_SEMANTICS_PARTIAL"}:
        raise AtlasGenerationError("Atlas schema status enum does not match generated status states.")
    if properties.get("atlas_schema_version", {}).get("const") != "1.0.0":
        raise AtlasGenerationError("Atlas schema version does not match the generator version contract.")


def _atlas_status(
    *,
    t16_available: bool,
    parser_failures: Iterable[str],
    invalid_t16_modules: Iterable[str],
) -> str:
    """Never label semantic enrichment current when any parser failed."""
    if t16_available and not tuple(parser_failures) and not tuple(invalid_t16_modules):
        return "CURRENT"
    return "INVENTORY_CURRENT_SEMANTICS_PARTIAL"


def validate_atlas(atlas: Mapping[str, Any]) -> None:
    required = {
        "atlas_schema_version", "status", "repository", "source_baseline",
        "authority_model", "coverage", "inventory", "architecture",
        "relationships", "provenance", "known_limitations", "integrity",
    }
    missing = required.difference(atlas)
    if missing:
        raise AtlasGenerationError(f"Atlas missing required sections: {sorted(missing)}")
    if atlas.get("atlas_schema_version") != "1.0.0":
        raise AtlasGenerationError("Atlas schema version is unsupported.")
    if atlas.get("status") not in {"CURRENT", "INVENTORY_CURRENT_SEMANTICS_PARTIAL"}:
        raise AtlasGenerationError("Atlas status is missing or unsupported.")
    if atlas.get("repository") != REPOSITORY_FULL_NAME:
        raise AtlasGenerationError("Atlas repository identity does not match HOMIO.")

    baseline = atlas.get("source_baseline")
    if not isinstance(baseline, Mapping):
        raise AtlasGenerationError("Atlas source baseline is not an object.")
    exact_baseline = {
        "repository": REPOSITORY_FULL_NAME,
        "source_branch": SOURCE_BRANCH,
        "state_json_path": STATE_RELATIVE_PATH,
        "entrypoint_path": ENTRYPOINT_RELATIVE_PATH,
        "reference_branch": REFERENCE_BRANCH,
        "reference_path": ATLAS_RELATIVE_PATH,
    }
    for key, value in exact_baseline.items():
        if baseline.get(key) != value:
            raise AtlasGenerationError(f"Atlas source baseline has an invalid {key}.")
    for key in ("source_commit_sha", "source_tree_sha", "state_json_blob_sha", "entrypoint_blob_sha"):
        if not SHA_RE.fullmatch(str(baseline.get(key, ""))):
            raise AtlasGenerationError(f"Atlas source baseline has an invalid {key}.")

    inventory = atlas.get("inventory")
    if not isinstance(inventory, Mapping) or inventory.get("source") != "git ls-tree -r -z --full-tree HEAD":
        raise AtlasGenerationError("Atlas inventory source is not the complete Git tracked tree.")
    entries = inventory.get("entries")
    if not isinstance(entries, list) or not entries:
        raise AtlasGenerationError("Atlas tracked inventory is empty or malformed.")
    paths = [item.get("path") if isinstance(item, Mapping) else None for item in entries]
    if any(not isinstance(path, str) for path in paths):
        raise AtlasGenerationError("Atlas inventory contains an invalid path record.")
    if len(paths) != len(set(paths)):
        raise AtlasGenerationError("Atlas inventory contains duplicate paths.")
    for item in entries:
        path = _safe_repo_path(str(item["path"]))
        if path != item["path"] or not SHA_RE.fullmatch(str(item.get("object_sha", ""))):
            raise AtlasGenerationError("Atlas inventory contains an invalid tracked object.")
        if item.get("object_type") not in {"blob", "commit"}:
            raise AtlasGenerationError(f"Atlas inventory has an invalid object type at {path!r}.")

    coverage = atlas.get("coverage")
    if not isinstance(coverage, Mapping):
        raise AtlasGenerationError("Atlas coverage section is not an object.")
    tracked_count = coverage.get("tracked_entry_count")
    inventory_count = coverage.get("inventory_entry_count")
    if (
        coverage.get("inventory_complete") is not True
        or not isinstance(tracked_count, int)
        or isinstance(tracked_count, bool)
        or not isinstance(inventory_count, int)
        or isinstance(inventory_count, bool)
        or tracked_count != len(entries)
        or inventory_count != len(entries)
    ):
        raise AtlasGenerationError("Atlas inventory completeness claim does not match exact tracked entry count.")
    if coverage.get("runtime_relationships_proven") is not False:
        raise AtlasGenerationError("Atlas must not claim runtime relationships are proven.")
    if coverage.get("all_repository_code_semantics_proven") is not False:
        raise AtlasGenerationError("Atlas must not claim complete repository semantic coverage.")

    integrity = atlas.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "sha256":
        raise AtlasGenerationError("Atlas integrity algorithm is invalid.")
    expected = _canonical_fingerprint(atlas)
    if integrity.get("sha256") != expected:
        raise AtlasGenerationError("Atlas integrity fingerprint does not match its content.")


def build_atlas(root: Path, *, require_t16: bool = True,
                require_live_tip: bool = False) -> dict[str, Any]:
    root = root.resolve()
    start_identity = _identity(root, SOURCE_BRANCH, require_live_tip)
    entries = _git_entries(root)
    if not entries:
        raise AtlasGenerationError("Git source tree is empty; refusing to publish an empty atlas.")
    known_paths = {item.path for item in entries}
    literals = _load_entrypoint_literals(root)
    t16_snapshot, t16_status = _load_t16(root, required=require_t16)
    imports, import_failures, attempted = _static_imports_from_one_t16_snapshot(root, t16_snapshot)
    documentation_refs, skipped_docs = _documentation_references(root, entries, known_paths)
    inventory, indexes = _index_records(entries, t16_snapshot, literals)
    workflow_records = _workflow_jobs(root, entries)

    reverse_imports: dict[str, list[str]] = {}
    for edge in imports:
        target = edge.get("resolved_path")
        if target:
            reverse_imports.setdefault(target, []).append(edge["source_path"])
    test_to_source: list[dict[str, str]] = []
    for edge in imports:
        if _path_category(next((item for item in entries if item.path == edge["source_path"]), GitEntry(edge["source_path"], "100644", "blob", "0" * 40, None))) == "TEST" and edge.get("resolved_path"):
            test_to_source.append({"test_path": edge["source_path"], "source_path": edge["resolved_path"], "evidence": "T16_STATIC_LOCAL_IMPORT"})

    state_entry = next((item for item in inventory if item["path"] == STATE_RELATIVE_PATH), None)
    entrypoint_entry = next((item for item in inventory if item["path"] == ENTRYPOINT_RELATIVE_PATH), None)
    schema_entry = next((item for item in inventory if item["path"] == SCHEMA_RELATIVE_PATH), None)
    if state_entry is None:
        raise AtlasGenerationError("Canonical state.json is missing from the tracked Git tree.")
    if entrypoint_entry is None:
        raise AtlasGenerationError("Canonical AI_AGENT_ENTRYPOINT.py is missing from the tracked Git tree.")
    if schema_entry is None:
        raise AtlasGenerationError("The Atlas JSON Schema is missing from the tracked Git tree.")
    try:
        schema_payload = json.loads((root / SCHEMA_RELATIVE_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AtlasGenerationError("The Atlas JSON Schema cannot be read as valid JSON.") from exc
    validate_schema_contract(schema_payload)

    tracked_count = len(entries)
    t16_classified = len(t16_snapshot.get("metadata", {})) if t16_snapshot else 0
    t16_modules = t16_snapshot.get("modules", []) if t16_snapshot else []
    parse_invalid = [item["path"] for item in t16_modules if not item["parse_valid"]]
    inventory_complete = len(inventory) == tracked_count and len({x["path"] for x in inventory}) == tracked_count
    if not inventory_complete:
        raise AtlasGenerationError("Git tracked inventory coverage failed exact-set integrity check.")

    atlas: dict[str, Any] = {
        "atlas_schema_version": "1.0.0",
        "status": _atlas_status(
            t16_available=t16_snapshot is not None,
            parser_failures=import_failures,
            invalid_t16_modules=parse_invalid,
        ),
        "repository": REPOSITORY_FULL_NAME,
        "source_baseline": {
            **start_identity,
            "state_json_path": STATE_RELATIVE_PATH,
            "state_json_blob_sha": state_entry["object_sha"],
            "entrypoint_path": ENTRYPOINT_RELATIVE_PATH,
            "entrypoint_blob_sha": entrypoint_entry["object_sha"],
            "reference_branch": REFERENCE_BRANCH,
            "reference_path": ATLAS_RELATIVE_PATH,
            "source_commit_time_is_not_generation_time": True,
        },
        "authority_model": {
            "execution_state": {"path": STATE_RELATIVE_PATH, "authority": "SOLE_CANONICAL_EXECUTION_STATE", "atlas_role": "PATH_AND_BLOB_IDENTITY_ONLY"},
            "code_and_history": {"branch": SOURCE_BRANCH, "authority": "CANONICAL_GIT_HISTORY"},
            "agent_policy": {"path": ENTRYPOINT_RELATIVE_PATH, "authority": "STABLE_AGENT_OPERATING_POLICY"},
            "technical_reference": {"branch": REFERENCE_BRANCH, "path": ATLAS_RELATIVE_PATH, "authority": "DERIVED_NON_AUTHORITATIVE_TECHNICAL_MAP"},
            "task_authorization": "EXISTING_CONTROL_CENTER_AND_ACRL_BOUNDARIES_ONLY",
            "acrl_boundary": "CONTINUITY_AND_RECOVERY_ONLY_NOT_PRODUCTION_SECURITY_RUNTIME",
            "chat_history": "NON_AUTHORITATIVE_CONTEXT_ONLY",
        },
        "coverage": {
            "tracked_entry_count": tracked_count,
            "inventory_entry_count": len(inventory),
            "inventory_complete": inventory_complete,
            "t16_classified_entry_count": t16_classified,
            "t16_coverage_is_not_used_as_git_inventory_coverage": True,
            "static_import_edges": len(imports),
            "documentation_reference_edges": len(documentation_refs),
            "workflow_files": len(workflow_records),
            "test_files": len(indexes["tests"]),
            "semantic_coverage": "PARTIAL_BY_DESIGN",
            "runtime_relationships_proven": False,
            "all_repository_code_semantics_proven": False,
        },
        "inventory": {
            "source": "git ls-tree -r -z --full-tree HEAD",
            "entries": inventory,
            "indexes": indexes,
        },
        "architecture": {
            "document_registry_owners": _entrypoint_owner_records(literals),
            "workstream_routing": literals.get("workstream_routing", {}),
            "acrl_owner_routing": literals.get("acrl_owner_routing", {}),
            "ci_workflows": workflow_records,
            "api_and_contracts": indexes["api_and_contracts"],
            "database_and_persistence": indexes["database_and_persistence"],
            "events_and_workflows": indexes["events_and_workflows"],
            "dependency_manifests": indexes["dependency_manifests"],
        },
        "relationships": {
            "static_imports": imports,
            "reverse_static_imports": [
                {"target_path": path, "imported_by": sorted(set(sources), key=str.casefold)}
                for path, sources in sorted(reverse_imports.items(), key=lambda pair: pair[0].casefold())
            ],
            "documentation_references": documentation_refs,
            "test_to_source_links": test_to_source,
            "test_link_confidence": "STATIC_LINKS_ONLY; ABSENCE_OF_A_LINK_IS_NOT_PROOF_OF_NO_COVERAGE",
        },
        "provenance": {
            "generator_version": GENERATOR_VERSION,
            "generator_path": GENERATOR_RELATIVE_PATH,
            "generator_blob_sha": next((item["object_sha"] for item in inventory if item["path"] == GENERATOR_RELATIVE_PATH), None),
            "schema_path": SCHEMA_RELATIVE_PATH,
            "schema_blob_sha": schema_entry["object_sha"],
            "t16": t16_status,
            "t16_excluded_paths": t16_snapshot.get("excluded_paths", []) if t16_snapshot else [],
            "parser_attempts": attempted,
            "source_parse_failures": import_failures,
            "t16_invalid_python_module_paths": sorted(parse_invalid, key=str.casefold),
            "documentation_files_skipped": skipped_docs,
            "no_repository_source_is_copied_into_atlas": True,
            "secrets_and_secret_values_are_not_copied": True,
        },
        "known_limitations": [
            "The inventory is complete for Git-tracked leaf entries at source_tree_sha; untracked runner files are intentionally excluded.",
            "T16 exclusions affect semantic enrichment only; they do not remove Git-tracked entries from inventory.",
            "Static import evidence is not a runtime call graph, dynamic plugin graph, or proof of reachable execution.",
            "Python imports are recorded symbolically; package-relative resolution is not asserted unless an exact local path was separately resolved.",
            "Workflow job names are indentation-based static hints; expressions, reusable-workflow expansion, matrices, and runtime job execution are not inferred.",
            "Database, API, event, and dependency indexes are path-based discovery indexes, not validated semantic contracts or proof of production wiring.",
            "Test-to-source links are only emitted when a local static import resolves; absence does not prove missing tests.",
            "Owner labels are emitted only from the existing EntryPoint registry, explicit ACRL folder boundaries, or explicit backend/.github paths; other ownership remains unresolved.",
            "state.json values and current task position are not duplicated; fetch live state.json separately for every task decision.",
            "External services, runtime environment variables, secrets, cloud resources, production topology, and dynamically loaded code are not inspected.",
        ],
    }
    atlas["integrity"] = {"algorithm": "sha256", "sha256": _canonical_fingerprint(atlas)}
    validate_atlas(atlas)

    end_identity = _identity(root, SOURCE_BRANCH, require_live_tip)
    if end_identity != start_identity:
        raise AtlasGenerationError("Source branch identity changed during atlas generation; refusing publication.")
    return atlas


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-branch", default=SOURCE_BRANCH)
    parser.add_argument("--require-live-tip", action="store_true")
    parser.add_argument("--allow-t16-unavailable", action="store_true")
    args = parser.parse_args(argv)
    if args.expected_branch != SOURCE_BRANCH:
        raise SystemExit(f"Refusing unexpected branch argument: {args.expected_branch}")
    atlas = build_atlas(
        args.repo_root,
        require_t16=not args.allow_t16_unavailable,
        require_live_tip=args.require_live_tip,
    )
    write_json_atomic(args.output, atlas)
    print(json.dumps({
        "status": atlas["status"],
        "source_commit_sha": atlas["source_baseline"]["source_commit_sha"],
        "source_tree_sha": atlas["source_baseline"]["source_tree_sha"],
        "tracked_entry_count": atlas["coverage"]["tracked_entry_count"],
        "inventory_complete": atlas["coverage"]["inventory_complete"],
        "static_import_edges": atlas["coverage"]["static_import_edges"],
        "integrity_sha256": atlas["integrity"]["sha256"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
