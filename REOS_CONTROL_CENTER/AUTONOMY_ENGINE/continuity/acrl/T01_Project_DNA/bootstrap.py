"""ACRL T01 — New-agent bootstrap projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fingerprint import extract_project_fingerprints
from .freshness import (
    FreshnessPolicy,
    FreshnessResult,
    StateFreshness,
    classify_state_freshness,
)
from .identity import ProjectIdentity, build_project_identity
from .project_dna import ProjectDNAReader


BOOTSTRAP_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ProjectBootstrap:
    """Compact machine payload for a fresh AI/operator session."""

    identity: ProjectIdentity
    freshness: FreshnessResult
    dna_payload: dict[str, Any]
    fingerprints: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": BOOTSTRAP_SCHEMA_VERSION,
            "identity": self.identity.to_dict(),
            "freshness": self.freshness.to_dict(),
            "project_dna": self.dna_payload,
            "fingerprints": self.fingerprints,
            "authority": {
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
                "chat_memory_authoritative": False,
            },
        }


def build_project_bootstrap(
    control_center_root: Path | str | None = None,
    *,
    observed_at=None,
    freshness_policy: FreshnessPolicy | None = None,
) -> ProjectBootstrap:
    """Build a complete read-only T01 bootstrap payload."""

    reader = ProjectDNAReader(control_center_root)
    dna = reader.read()

    identity = build_project_identity(dna)
    fingerprints = extract_project_fingerprints(dna)

    state = reader._read_state(reader.state_path)

    freshness = classify_state_freshness(
        state,
        observed_at=observed_at,
        policy=freshness_policy,
    )

    return ProjectBootstrap(
        identity=identity,
        freshness=freshness,
        dna_payload=dna.to_dict(),
        fingerprints=fingerprints.to_dict(),
    )


def bootstrap_is_safe_for_resume(
    bootstrap: ProjectBootstrap,
) -> bool:
    """Return whether the T01 payload is safe to hand to a resume flow."""

    return bootstrap.freshness.status == StateFreshness.CURRENT


__all__ = [
    "BOOTSTRAP_SCHEMA_VERSION",
    "ProjectBootstrap",
    "bootstrap_is_safe_for_resume",
    "build_project_bootstrap",
]