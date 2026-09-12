from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .truth_fingerprint import digest
from .truth_models import ArtifactTruth, CanonicalManifest, Conflict


def build_manifest(
    *,
    project: str,
    branch: str,
    authority_id: str,
    canonical_state_path: str,
    state_digest: str,
    state_revision: str,
    execution: dict[str, Any],
    derived_artifacts: list[ArtifactTruth],
    conflicts: tuple[Conflict, ...],
) -> CanonicalManifest:
    payload = {
        "schema_version": "1.0",
        "project": project,
        "branch": branch,
        "authority_id": authority_id,
        "canonical_state_path": canonical_state_path,
        "state_digest": state_digest,
        "state_revision": state_revision,
        "execution": execution,
        "derived_artifacts": [asdict(x) for x in derived_artifacts],
        "conflicts": [asdict(x) for x in conflicts],
    }
    return CanonicalManifest(
        schema_version="1.0",
        project=project,
        branch=branch,
        authority_id=authority_id,
        canonical_state_path=canonical_state_path,
        state_digest=state_digest,
        state_revision=state_revision,
        current_gate=str(execution.get("current_gate") or ""),
        current_task=str(execution.get("current_task") or ""),
        current_subtask=execution.get("current_subtask"),
        execution_status=str(execution.get("status") or ""),
        derived_artifacts=tuple(derived_artifacts),
        conflicts=tuple(conflicts),
        manifest_digest=digest(payload),
    )
