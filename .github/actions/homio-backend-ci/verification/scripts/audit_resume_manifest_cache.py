#!/usr/bin/env python3
"""Refresh T14's derived resume cache after the existing backend CI suite passes.

This adapter calls the existing T14 builder/validator and T16 repository scanner.
It writes only beneath RUNNER_TEMP; it never edits tracked files or state.json.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

EXPECTED_REPOSITORY = "prajaktaranjane80-sketch/Homio"
EXPECTED_BRANCH = "reos-development"
STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
TEMPLATE_PATH = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T14_Repository_Intelligence_Context/audit_resume_manifest.json"
)
_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
CONTROL_CENTER_ROOT = REPOSITORY_ROOT / "REOS_CONTROL_CENTER"
if str(CONTROL_CENTER_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_CENTER_ROOT))

SCOPE_PREFIXES = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T23_Reference_Evidence_Resolution_Engine/",
)

SCOPE_FILES = (
    "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py",
    "REOS_CONTROL_CENTER/reos_control_center.py",
    STATE_PATH,
    "REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md",
    ".github/actions/homio-backend-ci/verification/action.yml",
    ".github/actions/homio-backend-ci/verification/scripts/acrl_runtime_resume.sh",
    ".github/actions/homio-backend-ci/verification/scripts/acrl_full_suite.sh",
    ".github/actions/homio-backend-ci/verification/scripts/audit_resume_manifest_cache.py",
    "REOS_CONTROL_CENTER/tets/test_audit_resume_manifest_cache.py",
)


class CacheInitializationError(RuntimeError):
    """The canonical repository cannot safely produce a resume cache."""


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CacheInitializationError(
            f"Git read failed ({' '.join(args)}): {message or result.returncode}"
        )
    return result.stdout


def _git_text(root: Path, *args: str) -> str:
    try:
        return _git(root, *args).decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise CacheInitializationError("Git returned non-UTF-8 text") from exc


def _safe_repo_path(path: str) -> bool:
    return bool(path) and not path.startswith("/") and "\\" not in path and all(
        part not in {"", ".", ".."} for part in path.split("/")
    )


def parse_git_tree(raw: bytes) -> dict[str, str]:
    """Parse `git ls-tree -r -z` into safe tracked blob IDs."""
    blobs: dict[str, str] = {}

    for record in raw.split(b"\0"):
        if not record:
            continue

        try:
            metadata, raw_path = record.split(b"\t", 1)
            _mode, kind, sha = metadata.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise CacheInitializationError("Malformed Git tree entry") from exc

        if kind != "blob":
            continue

        if not _safe_repo_path(path) or not _SHA.fullmatch(sha):
            raise CacheInitializationError(
                f"Unsafe path or invalid blob identity: {path!r}"
            )

        if path in blobs:
            raise CacheInitializationError(f"Duplicate Git tree path: {path}")

        blobs[path] = sha

    return blobs


def parse_name_status(raw: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse NUL-delimited `git diff --name-status -z` output fail-closed."""
    tokens = [token for token in raw.split(b"\0") if token]
    changed: set[str] = set()
    deleted: set[str] = set()
    index = 0

    def path_token() -> str:
        nonlocal index

        if index >= len(tokens):
            raise CacheInitializationError("Incomplete Git diff record")

        try:
            path = tokens[index].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CacheInitializationError("Non-UTF-8 Git diff path") from exc

        index += 1

        if not _safe_repo_path(path):
            raise CacheInitializationError(f"Unsafe changed path: {path!r}")

        return path

    while index < len(tokens):
        try:
            status = tokens[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise CacheInitializationError("Invalid Git diff status") from exc

        index += 1
        marker = status[:1]

        if marker in {"R", "C"}:
            old_path, new_path = path_token(), path_token()
            changed.add(new_path)
            if marker == "R":
                deleted.add(old_path)
        elif marker == "D":
            deleted.add(path_token())
        elif marker in {"A", "M", "T"}:
            changed.add(path_token())
        else:
            raise CacheInitializationError(
                f"Unsupported Git diff status: {status}"
            )

    return tuple(sorted(changed)), tuple(sorted(deleted))


def validate_cache_destination(
    workspace: Path,
    runner_temp: Path,
    destination: Path,
) -> Path:
    """Allow exactly one external cache path; never write into the worktree."""
    workspace = workspace.resolve()
    runner_temp = runner_temp.resolve()
    destination = destination.resolve()
    expected = (
        runner_temp / "homio-acrl" / "audit_resume_manifest.json"
    ).resolve()

    if destination != expected or destination.is_relative_to(workspace):
        raise CacheInitializationError(
            "Cache path must be RUNNER_TEMP/homio-acrl/"
            "audit_resume_manifest.json, outside the worktree"
        )

    if not destination.is_relative_to(runner_temp):
        raise CacheInitializationError("Cache path escapes RUNNER_TEMP")

    return destination


def _canonical_state_hash(state: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(state))
    integrity = clone.setdefault("integrity", {})

    if not isinstance(integrity, dict):
        raise CacheInitializationError("Canonical state integrity is malformed")

    integrity["sha256"] = None
    payload = json.dumps(
        clone,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _current_position(state: Mapping[str, Any]) -> dict[str, str]:
    execution = state.get("execution")

    if not isinstance(execution, Mapping):
        raise CacheInitializationError(
            "Canonical state has no execution object"
        )

    gate = execution.get("current_gate")
    subtask = execution.get("current_subtask")
    label = execution.get("current_task")
    status = execution.get("status")

    values = (gate, subtask, label, status)
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise CacheInitializationError(
            "Canonical execution position is incomplete"
        )

    return {
        "current_gate": gate,
        "current_task": subtask,
        "current_subtask": subtask,
        "current_subtask_status": status,
        "current_task_label": label,
    }


def _read_canonical_identity(
    workspace: Path,
    blobs: Mapping[str, str],
) -> tuple[str, dict[str, str]]:
    path = workspace / STATE_PATH

    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CacheInitializationError(
            f"Canonical state cannot be read: {exc}"
        ) from exc

    if not isinstance(state, dict):
        raise CacheInitializationError(
            "Canonical state root must be an object"
        )

    integrity = state.get("integrity")
    if (
        not isinstance(integrity, dict)
        or integrity.get("sha256") != _canonical_state_hash(state)
    ):
        raise CacheInitializationError(
            "Canonical state integrity check failed"
        )

    state_sha = blobs.get(STATE_PATH)
    live_state_sha = _git_text(
        workspace,
        "rev-parse",
        f"HEAD:{STATE_PATH}",
    )

    if not isinstance(state_sha, str) or live_state_sha != state_sha:
        raise CacheInitializationError(
            "Canonical state blob identity is inconsistent with HEAD"
        )

    return state_sha, _current_position(state)


def _manifest_delta(
    workspace: Path,
    manifest: Mapping[str, Any] | None,
    head: str,
) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
    base = (
        manifest.get("audit_base_commit_sha")
        if isinstance(manifest, Mapping)
        else None
    )

    if not isinstance(base, str) or not _SHA.fullmatch(base):
        return None, (), ()

    if base == head:
        return base, (), ()

    ancestor = subprocess.run(
        [
            "git",
            "-C",
            str(workspace),
            "merge-base",
            "--is-ancestor",
            base,
            head,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if ancestor.returncode != 0:
        return None, (), ()

    raw_diff = _git(
        workspace,
        "diff",
        "--name-status",
        "-z",
        "--find-renames=50%",
        base,
        head,
        "--",
    )
    changed, deleted = parse_name_status(raw_diff)
    return base, changed, deleted


def _load_previous(
    cache_path: Path,
    template_path: Path,
) -> tuple[dict[str, Any] | None, str]:
    from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
        ManifestValidationError,
        load_manifest_file,
    )

    source = cache_path if cache_path.is_file() else template_path

    try:
        return load_manifest_file(source), str(source)
    except (OSError, ManifestValidationError, json.JSONDecodeError) as exc:
        return None, f"INVALID:{source}:{exc}"


def _scope_paths(blobs: Mapping[str, str]) -> tuple[str, ...]:
    paths = {
        path
        for path in blobs
        if any(path.startswith(prefix) for prefix in SCOPE_PREFIXES)
    }
    paths.update(SCOPE_FILES)

    missing = sorted(path for path in paths if path not in blobs)
    if missing:
        raise CacheInitializationError(
            "Required baseline paths are absent: " + ", ".join(missing)
        )

    return tuple(sorted(paths))


def _assert_inventory_covers_scope(
    scope_paths: tuple[str, ...],
    inventory_paths: set[str],
) -> None:
    """Do not label Git-tree-only paths as content actually inspected by T16."""
    missing = sorted(set(scope_paths) - inventory_paths)
    if missing:
        raise CacheInitializationError(
            "T16 did not inventory required baseline paths: "
            + ", ".join(missing)
        )


def _write_and_read_back(
    path: Path,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
        load_manifest_file,
        validate_manifest_shape,
    )

    validate_manifest_shape(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=".audit-resume-",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temp_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary, path)
        read_back = load_manifest_file(path)

        if read_back != dict(manifest):
            raise CacheInitializationError(
                "Sealed manifest read-back did not match"
            )

        return read_back
    finally:
        temporary.unlink(missing_ok=True)


def initialize_cache_from_environment() -> dict[str, Any]:
    """Called only after a successful canonical backend CI run."""
    env = os.environ

    if env.get("GITHUB_ACTIONS", "").lower() != "true":
        raise CacheInitializationError(
            "Only GitHub Actions may initialize this cache"
        )

    repo = env.get("GITHUB_REPOSITORY", "")
    ref = env.get("GITHUB_REF", "")
    event = env.get("GITHUB_EVENT_NAME", "")

    if repo != EXPECTED_REPOSITORY or ref != f"refs/heads/{EXPECTED_BRANCH}":
        raise CacheInitializationError(
            "Unexpected repository or branch; fail closed"
        )

    if event not in {"push", "workflow_dispatch"}:
        raise CacheInitializationError(f"Unsupported event: {event!r}")

    run_id = env.get("GITHUB_RUN_ID", "")
    expected_head = env.get("GITHUB_SHA", "")

    if not run_id.isdigit() or not _SHA.fullmatch(expected_head):
        raise CacheInitializationError(
            "Missing/invalid Actions run ID or triggering SHA"
        )

    try:
        workspace = Path(env["GITHUB_WORKSPACE"]).resolve()
        runner_temp = Path(env["RUNNER_TEMP"]).resolve()
        cache_path = validate_cache_destination(
            workspace,
            runner_temp,
            Path(env["HOMIO_ACRL_RESUME_CACHE_PATH"]),
        )
    except (KeyError, OSError) as exc:
        raise CacheInitializationError(
            f"Required runner path unavailable: {exc}"
        ) from exc

    repository_root = Path(
        _git_text(workspace, "rev-parse", "--show-toplevel")
    ).resolve()

    if repository_root != workspace:
        raise CacheInitializationError(
            "GITHUB_WORKSPACE is not the repository root"
        )

    head = _git_text(workspace, "rev-parse", "HEAD")
    if head != expected_head:
        raise CacheInitializationError(
            "Checked-out HEAD does not match GITHUB_SHA"
        )

    if _git(
        workspace,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ):
        raise CacheInitializationError(
            "Worktree is dirty; refusing to refresh the cache"
        )

    blobs = parse_git_tree(
        _git(
            workspace,
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            "HEAD",
        )
    )
    state_sha, position = _read_canonical_identity(workspace, blobs)
    template_path = workspace / TEMPLATE_PATH
    previous, previous_source = _load_previous(cache_path, template_path)

    delta_base, changed_paths, deleted_paths = _manifest_delta(
        workspace,
        previous,
        head,
    )

    live = {
        "repository": repo,
        "branch": EXPECTED_BRANCH,
        "head_commit_sha": head,
        "state_json_blob_sha": state_sha,
        "working_tree_clean": True,
        "changed_paths": list(changed_paths),
        "deleted_paths": list(deleted_paths),
        "delta_base_commit_sha": (
            delta_base if previous is not None else head
        ),
        "path_blob_shas": blobs,
        "current_position": position,
    }

    from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
        ResumeDecision,
        assess_resume_manifest,
        build_manifest,
        load_manifest_file,
    )

    if previous is None:
        decision, reason = "INVALID_MANIFEST", previous_source
    else:
        assessed = assess_resume_manifest(previous, live)
        decision, reason = assessed.decision.value, assessed.reason

    print(f"PREVIOUS_RESUME_DECISION={decision}")
    print(f"PREVIOUS_RESUME_REASON={reason}")
    print(f"RESUME_CACHE_SOURCE={previous_source}")

    if decision == ResumeDecision.FAST_RESUME.value and previous is not None:
        cached = load_manifest_file(cache_path)
        print("RESUME_CACHE_REFRESH=SKIPPED_VALID_CACHE")
        print(f"RESUME_CACHE_HEAD={head}")
        print(f"RESUME_CACHE_AUDITED_PATHS={len(cached['audited_path_blob_shas'])}")
        print(f"RESUME_CACHE_FINGERPRINT={cached['manifest_fingerprint']}")
        return cached

    # This step runs only after all preceding backend verification has passed.
    from AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
        discover_repository,
    )

    inventory = discover_repository(workspace)
    if not inventory.fingerprint:
        raise CacheInitializationError(
            "T16 returned no repository inventory fingerprint"
        )

    scope_paths = _scope_paths(blobs)
    inventory_paths = {item.relative_path for item in inventory.files}
    _assert_inventory_covers_scope(scope_paths, inventory_paths)

    scope_prefix_paths = [
        path for path in scope_paths if path.startswith(SCOPE_PREFIXES)
    ]

    timestamp = datetime.now(timezone.utc)
    server_url = env.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    evidence_id = f"BACKEND-CI-{run_id}"
    evidence = {
        "evidence_id": evidence_id,
        "kind": "ci",
        "url": f"{server_url}/{repo}/actions/runs/{run_id}",
        "source_commit_sha": head,
        "result": "PASS",
        "retrieved_at": timestamp.isoformat(),
        "finding_ids": ["ACRL-RESUME-REGRESSION"],
    }

    manifest = build_manifest(
        repository=repo,
        branch=EXPECTED_BRANCH,
        audit_base_commit_sha=head,
        state_json_blob_sha=state_sha,
        position_snapshot={
            **position,
            "t16_repository_fingerprint": inventory.fingerprint,
            "source_inventory_file_count": len(inventory.files),
            "resume_cache_scope": "T07/T14/T16/T23 plus canonical context paths",
            "cache_location": (
                "external GitHub Actions cache/artifact; not canonical state"
            ),
        },
        audited_path_blob_shas={
            path: blobs[path] for path in scope_paths
        },
        finding_status={
            "ACRL-RESUME-REGRESSION": {
                "status": "PASS",
                "paths": sorted(scope_prefix_paths),
                "evidence_ids": [evidence_id],
            },
            "CANONICAL-CONTEXT-IDENTITY": {
                "status": "OBSERVED",
                "paths": list(SCOPE_FILES),
                "evidence_ids": [],
            },
        },
        test_ci_evidence=[evidence],
        research_evidence=[],
        blockers=[],
        generated_at=timestamp,
    )

    read_back = _write_and_read_back(cache_path, manifest)

    fresh_live = {
        "repository": repo,
        "branch": EXPECTED_BRANCH,
        "head_commit_sha": head,
        "state_json_blob_sha": state_sha,
        "working_tree_clean": True,
        "changed_paths": [],
        "deleted_paths": [],
        "delta_base_commit_sha": head,
        "path_blob_shas": blobs,
        "current_position": position,
    }

    verified = assess_resume_manifest(read_back, fresh_live)

    if (
        verified.decision is not ResumeDecision.FAST_RESUME
        or verified.full_audit_required
    ):
        raise CacheInitializationError(
            "New cache failed independent same-HEAD read-back: "
            f"{verified.decision.value}: {verified.reason}"
        )

    final_head = _git_text(workspace, "rev-parse", "HEAD")
    final_status = _git(
        workspace,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )

    if final_head != head or final_status:
        raise CacheInitializationError(
            "Repository changed during cache sealing"
        )

    print("RESUME_CACHE_REFRESH=SEALED_AND_READ_BACK")
    print(f"RESUME_CACHE_HEAD={head}")
    print(f"RESUME_CACHE_STATE_BLOB_SHA={state_sha}")
    print(
        f"RESUME_CACHE_AUDITED_PATHS="
        f"{len(read_back['audited_path_blob_shas'])}"
    )
    print(f"RESUME_CACHE_T16_INVENTORY_FILES={len(inventory.files)}")
    print(f"RESUME_CACHE_FINGERPRINT={read_back['manifest_fingerprint']}")

    return read_back


def main() -> int:
    if sys.argv[1:] != ["--refresh-after-ci"]:
        print(
            "Usage: audit_resume_manifest_cache.py --refresh-after-ci",
            file=sys.stderr,
        )
        return 2

    try:
        initialize_cache_from_environment()
    except CacheInitializationError as exc:
        print(
            f"RESUME_CACHE_INITIALIZATION=FAIL_CLOSED: {exc}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
