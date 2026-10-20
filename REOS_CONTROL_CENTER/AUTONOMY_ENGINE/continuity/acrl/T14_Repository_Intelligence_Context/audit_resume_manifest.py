"""T14 fast-resume manifest validation.

The manifest is a derived cache only. It never supplies execution authority,
selects a task, authorizes writes, or makes old evidence current.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "1.0"
AUTHORITY = "REOS_CONTROL_CENTER"
MANIFEST_STATUS = "DERIVED_NON_AUTHORITATIVE_CACHE_ONLY"

DEFAULT_MANIFEST_RELATIVE_PATH = Path(
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T14_Repository_Intelligence_Context/audit_resume_manifest.json"
)
_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class ResumeDecision(str, Enum):
    FAST_RESUME = "FAST_RESUME"
    TARGETED_REAUDIT = "TARGETED_REAUDIT"
    FULL_AUDIT_REQUIRED = "FULL_AUDIT_REQUIRED"
    INVALID_MANIFEST = "INVALID_MANIFEST"


class ManifestValidationError(ValueError):
    """Manifest is malformed or has an invalid integrity fingerprint."""


@dataclass(frozen=True, slots=True)
class ResumeAssessment:
    decision: ResumeDecision
    reason: str
    repository: str | None
    branch: str | None
    current_head_sha: str | None
    current_state_blob_sha: str | None
    invalidated_paths: tuple[str, ...] = ()
    affected_findings: tuple[str, ...] = ()
    stale_evidence_ids: tuple[str, ...] = ()
    full_audit_required: bool = False
    resume_packet: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "repository": self.repository,
            "branch": self.branch,
            "current_head_sha": self.current_head_sha,
            "current_state_blob_sha": self.current_state_blob_sha,
            "invalidated_paths": list(self.invalidated_paths),
            "affected_findings": list(self.affected_findings),
            "stale_evidence_ids": list(self.stale_evidence_ids),
            "full_audit_required": self.full_audit_required,
            "resume_packet": dict(self.resume_packet or {}),
        }


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def manifest_fingerprint(manifest: Mapping[str, Any]) -> str:
    """Accidental-drift fingerprint, not an authenticity signature."""
    payload = dict(manifest)
    payload.pop("manifest_fingerprint", None)
    return hashlib.sha256(
        _canonical_json(payload).encode("utf-8")
    ).hexdigest()


def seal_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a manifest and attach its deterministic content fingerprint."""
    sealed = dict(manifest)
    sealed.pop("manifest_fingerprint", None)
    sealed["manifest_fingerprint"] = manifest_fingerprint(sealed)
    return sealed


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA.fullmatch(value))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestValidationError(f"{name} must be an object")
    return value


def _validate_repo_relative_path(path: Any) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ManifestValidationError(
            "Repository path must be a non-empty string"
        )

    normalized = path.replace("\\", "/")
    parts = normalized.split("/")

    if (
        normalized.startswith("/")
        or ".." in parts
        or "." in parts
        or "" in parts
    ):
        raise ManifestValidationError(
            f"Unsafe repository-relative path: {path}"
        )

    if any(ord(char) < 32 for char in normalized):
        raise ManifestValidationError(
            "Control characters are forbidden in paths"
        )

    return normalized


def validate_manifest_shape(manifest: Mapping[str, Any]) -> None:
    """Fail closed on missing fields, unsafe paths, hashes or fingerprint."""
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ManifestValidationError(
            "Unsupported manifest schema version"
        )

    if manifest.get("status") != "SEALED":
        raise ManifestValidationError(
            "Manifest is uninitialized or not sealed"
        )

    if manifest.get("manifest_status") != MANIFEST_STATUS:
        raise ManifestValidationError(
            "Manifest status is not cache-only"
        )

    if manifest.get("authority") != AUTHORITY:
        raise ManifestValidationError(
            "Manifest authority label mismatch"
        )

    for key in (
        "repository",
        "branch",
        "audit_base_commit_sha",
        "state_json_blob_sha",
        "generated_at",
    ):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ManifestValidationError(f"{key} is required")

    if not _valid_sha(manifest.get("audit_base_commit_sha")):
        raise ManifestValidationError("Invalid audit_base_commit_sha")

    if not _valid_sha(manifest.get("state_json_blob_sha")):
        raise ManifestValidationError("Invalid state_json_blob_sha")

    if _parse_time(manifest.get("generated_at")) is None:
        raise ManifestValidationError(
            "generated_at must be an ISO-8601 timestamp with timezone"
        )

    for key in (
        "position_snapshot",
        "audited_path_blob_shas",
        "finding_status",
    ):
        _require_mapping(manifest.get(key), key)

    if not isinstance(manifest.get("test_ci_evidence"), list):
        raise ManifestValidationError(
            "test_ci_evidence must be an array"
        )

    if not isinstance(manifest.get("research_evidence"), list):
        raise ManifestValidationError(
            "research_evidence must be an array"
        )

    if not isinstance(manifest.get("blockers"), list) or not all(
        isinstance(item, str) for item in manifest["blockers"]
    ):
        raise ManifestValidationError(
            "blockers must be an array of strings"
        )

    for path, sha in manifest["audited_path_blob_shas"].items():
        _validate_repo_relative_path(path)
        if not _valid_sha(sha):
            raise ManifestValidationError(
                f"Invalid blob SHA for audited path: {path}"
            )

    for finding_id, finding in manifest["finding_status"].items():
        if (
            not isinstance(finding_id, str)
            or not finding_id.strip()
            or not isinstance(finding, Mapping)
        ):
            raise ManifestValidationError(
                "Finding status entries must map IDs to objects"
            )

        if not isinstance(finding.get("status"), str) or not finding["status"].strip():
            raise ManifestValidationError(
                f"Finding status is missing: {finding_id}"
            )

        for field in ("paths", "evidence_ids"):
            value = finding.get(field)
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                raise ManifestValidationError(
                    f"{field} must be a string array for finding {finding_id}"
                )

        for path in finding["paths"]:
            _validate_repo_relative_path(path)

    evidence_groups = (
        ("test_ci_evidence", {"test", "ci"}),
        ("research_evidence", {"research"}),
    )

    for key, allowed_kinds in evidence_groups:
        for record in manifest[key]:
            if not isinstance(record, Mapping):
                raise ManifestValidationError(
                    f"{key} contains a non-object record"
                )

            if (
                not isinstance(record.get("evidence_id"), str)
                or not record["evidence_id"].strip()
            ):
                raise ManifestValidationError(
                    f"{key} evidence_id is required"
                )

            if record.get("kind") not in allowed_kinds:
                raise ManifestValidationError(
                    f"{key} evidence kind is invalid"
                )

            url = record.get("url")
            if not isinstance(url, str) or not url.startswith("https://"):
                raise ManifestValidationError(
                    f"{key} evidence URL must use HTTPS"
                )

            if _parse_time(record.get("retrieved_at")) is None:
                raise ManifestValidationError(
                    f"{key} retrieved_at must be timezone-aware ISO-8601"
                )

            if (
                record.get("kind") in {"test", "ci"}
                and not _valid_sha(record.get("source_commit_sha"))
            ):
                raise ManifestValidationError(
                    f"{key} test/CI evidence requires source_commit_sha"
                )

    if manifest.get("manifest_fingerprint") != manifest_fingerprint(manifest):
        raise ManifestValidationError(
            "Manifest content fingerprint mismatch"
        )


def build_manifest(
    *,
    repository: str,
    branch: str,
    audit_base_commit_sha: str,
    state_json_blob_sha: str,
    position_snapshot: Mapping[str, Any],
    audited_path_blob_shas: Mapping[str, str],
    finding_status: Mapping[str, Any],
    test_ci_evidence: Sequence[Mapping[str, Any]],
    research_evidence: Sequence[Mapping[str, Any]],
    blockers: Sequence[str] = (),
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build and validate a sealed cache from observed evidence; never writes it."""
    timestamp = generated_at or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "SEALED",
        "manifest_status": MANIFEST_STATUS,
        "authority": AUTHORITY,
        "repository": repository,
        "branch": branch,
        "audit_base_commit_sha": audit_base_commit_sha,
        "state_json_blob_sha": state_json_blob_sha,
        "position_snapshot": dict(position_snapshot),
        "audited_path_blob_shas": dict(audited_path_blob_shas),
        "finding_status": dict(finding_status),
        "test_ci_evidence": [dict(item) for item in test_ci_evidence],
        "research_evidence": [dict(item) for item in research_evidence],
        "blockers": list(blockers),
        "generated_at": timestamp.astimezone(timezone.utc).isoformat(),
    }

    sealed = seal_manifest(payload)
    validate_manifest_shape(sealed)
    return sealed


def _dependent_closure(
    seed_paths: Sequence[str],
    graph: Mapping[str, Sequence[str]],
) -> set[str]:
    """Graph convention: each key maps to paths that depend on that key."""
    closure: set[str] = set()
    queue = list(seed_paths)

    while queue:
        current = _validate_repo_relative_path(queue.pop(0))

        if current in closure:
            continue

        closure.add(current)
        dependents = graph.get(current, ())

        if not isinstance(dependents, Sequence) or isinstance(
            dependents, (str, bytes)
        ):
            raise ManifestValidationError(
                f"Dependency graph entry must be a path sequence: {current}"
            )

        for dependent in dependents:
            validated = _validate_repo_relative_path(dependent)
            if validated not in closure:
                queue.append(validated)

    return closure


def _expired_evidence(
    records: Sequence[Mapping[str, Any]],
    *,
    kind: str,
    now: datetime,
    head_sha: str,
    max_ci_age: timedelta,
    max_research_age: timedelta,
) -> set[str]:
    stale: set[str] = set()

    for record in records:
        if not isinstance(record, Mapping):
            stale.add("<malformed-evidence-record>")
            continue

        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            evidence_id = "<missing-evidence-id>"

        retrieved = _parse_time(record.get("retrieved_at"))
        max_age = max_research_age if kind == "research" else max_ci_age

        if (
            retrieved is None
            or retrieved > now
            or now - retrieved > max_age
        ):
            stale.add(evidence_id)
            continue

        if kind in {"test", "ci"}:
            source_sha = record.get("source_commit_sha")
            if not _valid_sha(source_sha) or source_sha != head_sha:
                stale.add(evidence_id)

    return stale


def assess_resume_manifest(
    manifest: Mapping[str, Any],
    live_snapshot: Mapping[str, Any],
    *,
    dependency_graph: Mapping[str, Sequence[str]] | None = None,
    now: datetime | None = None,
    max_ci_age: timedelta = timedelta(days=14),
    max_research_age: timedelta = timedelta(days=30),
) -> ResumeAssessment:
    """Validate cache against independently observed live HEAD and state SHA.

    Required live_snapshot keys:
      repository, branch, head_commit_sha, state_json_blob_sha,
      working_tree_clean, changed_paths, path_blob_shas,
      delta_base_commit_sha when HEAD differs, deleted_paths and
      current_position.

    The current position is always taken from this live input, never from the
    manifest's display-only position_snapshot.
    """
    repository = (
        live_snapshot.get("repository")
        if isinstance(live_snapshot, Mapping) else None
    )
    branch = (
        live_snapshot.get("branch")
        if isinstance(live_snapshot, Mapping) else None
    )
    head_sha = (
        live_snapshot.get("head_commit_sha")
        if isinstance(live_snapshot, Mapping) else None
    )
    state_sha = (
        live_snapshot.get("state_json_blob_sha")
        if isinstance(live_snapshot, Mapping) else None
    )

    when = now or datetime.now(timezone.utc)
    if when.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    when = when.astimezone(timezone.utc)

    def full(
        reason: str,
        stale_evidence: Sequence[str] = (),
    ) -> ResumeAssessment:
        current_position = (
            live_snapshot.get("current_position") or {}
            if isinstance(live_snapshot, Mapping) else {}
        )
        return ResumeAssessment(
            decision=ResumeDecision.FULL_AUDIT_REQUIRED,
            reason=reason,
            repository=repository if isinstance(repository, str) else None,
            branch=branch if isinstance(branch, str) else None,
            current_head_sha=head_sha if isinstance(head_sha, str) else None,
            current_state_blob_sha=state_sha if isinstance(state_sha, str) else None,
            stale_evidence_ids=tuple(sorted(set(stale_evidence))),
            full_audit_required=True,
            resume_packet={
                "active_task": dict(current_position)
                if isinstance(current_position, Mapping) else {},
                "manifest_reuse": False,
            },
        )

    try:
        validate_manifest_shape(manifest)
    except ManifestValidationError as exc:
        current_position = (
            live_snapshot.get("current_position") or {}
            if isinstance(live_snapshot, Mapping) else {}
        )
        return ResumeAssessment(
            decision=ResumeDecision.INVALID_MANIFEST,
            reason=str(exc),
            repository=repository if isinstance(repository, str) else None,
            branch=branch if isinstance(branch, str) else None,
            current_head_sha=head_sha if isinstance(head_sha, str) else None,
            current_state_blob_sha=state_sha if isinstance(state_sha, str) else None,
            full_audit_required=True,
            resume_packet={
                "active_task": dict(current_position)
                if isinstance(current_position, Mapping) else {},
                "manifest_reuse": False,
            },
        )

    if not isinstance(live_snapshot, Mapping):
        return full("Live snapshot is missing")

    if (
        not isinstance(repository, str) or not repository.strip()
        or not isinstance(branch, str) or not branch.strip()
    ):
        return full("Live repository identity/ref is missing")

    if live_snapshot.get("working_tree_clean") is not True:
        return full("Working tree is dirty or cleanliness is unverified")

    if not _valid_sha(head_sha) or not _valid_sha(state_sha):
        return full("Live HEAD or state.json blob SHA is missing/invalid")

    if repository != manifest["repository"]:
        return full("Repository identity mismatch")

    if branch != manifest["branch"]:
        return full("Branch/ref mismatch; silent fallback is forbidden")

    if state_sha != manifest["state_json_blob_sha"]:
        return full(
            "Canonical state.json changed; re-bootstrap from live authority"
        )

    generated_at = _parse_time(manifest.get("generated_at"))
    if generated_at is None or generated_at > when:
        return full("Manifest timestamp is invalid or in the future")

    graph = dependency_graph or {}
    changed_paths = live_snapshot.get("changed_paths")
    deleted_paths = live_snapshot.get("deleted_paths", ())
    delta_base_sha = live_snapshot.get("delta_base_commit_sha")
    current_path_shas = live_snapshot.get("path_blob_shas", {})

    if not isinstance(changed_paths, Sequence) or isinstance(
        changed_paths, (str, bytes)
    ):
        return full("Changed-path evidence is missing or malformed")

    if not isinstance(deleted_paths, Sequence) or isinstance(
        deleted_paths, (str, bytes)
    ):
        return full("Deleted-path evidence is malformed")

    if not isinstance(current_path_shas, Mapping):
        return full("Current path blob SHA map is malformed")

    try:
        changed = {
            _validate_repo_relative_path(path)
            for path in changed_paths
        }
        deleted = {
            _validate_repo_relative_path(path)
            for path in deleted_paths
        }
        audited = manifest["audited_path_blob_shas"]
        path_hash_mismatches: set[str] = set()

        if head_sha == manifest["audit_base_commit_sha"]:
            if changed or deleted:
                return full(
                    "HEAD matches audit base but changed-path report is non-empty"
                )
        else:
            if delta_base_sha != manifest["audit_base_commit_sha"]:
                return full(
                    "Changed-path delta is not proven against the manifest base commit"
                )

            if not changed and not deleted:
                return full(
                    "HEAD changed but no verified changed-path delta was supplied"
                )

            for path in changed:
                if path not in current_path_shas or not _valid_sha(
                    current_path_shas[path]
                ):
                    if path not in deleted:
                        return full(
                            f"Changed path lacks a verified current blob SHA: {path}"
                        )

            for path, old_sha in audited.items():
                if path in deleted:
                    path_hash_mismatches.add(path)
                elif (
                    path in current_path_shas
                    and current_path_shas[path] != old_sha
                ):
                    path_hash_mismatches.add(path)

    except ManifestValidationError as exc:
        return full(str(exc))

    all_changed = changed | deleted | path_hash_mismatches

    try:
        invalidated = (
            _dependent_closure(sorted(all_changed), graph)
            if all_changed else set()
        )
    except ManifestValidationError as exc:
        return full(str(exc))

    ci_stale = _expired_evidence(
        manifest["test_ci_evidence"],
        kind="ci",
        now=when,
        head_sha=head_sha,
        max_ci_age=max_ci_age,
        max_research_age=max_research_age,
    )
    research_stale = _expired_evidence(
        manifest["research_evidence"],
        kind="research",
        now=when,
        head_sha=head_sha,
        max_ci_age=max_ci_age,
        max_research_age=max_research_age,
    )
    stale_evidence = ci_stale | research_stale

    all_evidence_ids = {
        item.get("evidence_id")
        for item in (
            *manifest["test_ci_evidence"],
            *manifest["research_evidence"],
        )
        if isinstance(item, Mapping)
    }

    affected_findings: set[str] = set()

    for finding_id, finding in manifest["finding_status"].items():
        if not isinstance(finding_id, str) or not isinstance(finding, Mapping):
            return full("Finding status record is malformed", stale_evidence)

        finding_paths = finding.get("paths", ())
        if not isinstance(finding_paths, Sequence) or isinstance(
            finding_paths, (str, bytes)
        ):
            return full(
                f"Finding path list is malformed: {finding_id}",
                stale_evidence,
            )

        normalized_paths = {
            _validate_repo_relative_path(path)
            for path in finding_paths
        }

        evidence_ids = finding.get("evidence_ids", ())
        if not isinstance(evidence_ids, Sequence) or isinstance(
            evidence_ids, (str, bytes)
        ):
            return full(
                f"Finding evidence IDs are malformed: {finding_id}",
                stale_evidence,
            )

        status_label = str(finding.get("status", "")).upper()
        evidence_missing = (
            status_label in {"PASS", "VERIFIED", "COMPLETE", "DONE"}
            and (
                not evidence_ids
                or any(evidence_id not in all_evidence_ids for evidence_id in evidence_ids)
            )
        )

        if (
            normalized_paths & invalidated
            or set(evidence_ids) & stale_evidence
            or evidence_missing
        ):
            affected_findings.add(finding_id)

    current_position = live_snapshot.get("current_position", {})
    if not isinstance(current_position, Mapping):
        return full(
            "Current position must be an independently observed object",
            stale_evidence,
        )

    for field in (
        "current_gate", "current_task", "current_subtask",
        "current_subtask_status",
    ):
        value = current_position.get(field)
        if not isinstance(value, str) or not value.strip():
            return full(f"Live current position is missing {field}", stale_evidence)

    packet = {
        "authority": AUTHORITY,
        "repository": repository,
        "branch": branch,
        "head_commit_sha": head_sha,
        "state_json_blob_sha": state_sha,
        "active_task": dict(current_position),
        "last_exact_pass_evidence": [
            dict(item)
            for item in manifest["test_ci_evidence"]
            if (
                isinstance(item, Mapping)
                and item.get("result") == "PASS"
                and item.get("source_commit_sha") == head_sha
                and item.get("evidence_id") not in stale_evidence
            )
        ],
        "reviewed_paths": sorted(set(audited) - invalidated),
        "open_or_affected_findings": sorted(affected_findings),
        "blockers": list(manifest["blockers"]),
        "invalidated_paths": sorted(invalidated),
        "stale_evidence_ids": sorted(stale_evidence),
        "manifest_reuse": not bool(
            invalidated or affected_findings or stale_evidence
        ),
    }

    if invalidated or affected_findings or stale_evidence:
        decision = ResumeDecision.TARGETED_REAUDIT
        reason = (
            "Only changed paths, downstream dependents, affected findings, "
            "and stale evidence need refresh"
        )
    else:
        decision = ResumeDecision.FAST_RESUME
        reason = (
            "Manifest, live HEAD, state.json and recorded evidence are current"
        )

    return ResumeAssessment(
        decision=decision,
        reason=reason,
        repository=repository,
        branch=branch,
        current_head_sha=head_sha,
        current_state_blob_sha=state_sha,
        invalidated_paths=tuple(sorted(invalidated)),
        affected_findings=tuple(sorted(affected_findings)),
        stale_evidence_ids=tuple(sorted(stale_evidence)),
        full_audit_required=False,
        resume_packet=packet,
    )


def load_manifest_file(path: str | Path) -> dict[str, Any]:
    """Read a manifest; this function never writes or authorizes execution."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(
            "Manifest is unavailable or invalid JSON"
        ) from exc

    if not isinstance(payload, Mapping):
        raise ManifestValidationError("Manifest root must be an object")

    validate_manifest_shape(payload)
    return dict(payload)


__all__ = [
    "AUTHORITY",
    "DEFAULT_MANIFEST_RELATIVE_PATH",
    "MANIFEST_STATUS",
    "ManifestValidationError",
    "ResumeAssessment",
    "ResumeDecision",
    "SCHEMA_VERSION",
    "assess_resume_manifest",
    "build_manifest",
    "load_manifest_file",
    "manifest_fingerprint",
    "seal_manifest",
    "validate_manifest_shape",
]
