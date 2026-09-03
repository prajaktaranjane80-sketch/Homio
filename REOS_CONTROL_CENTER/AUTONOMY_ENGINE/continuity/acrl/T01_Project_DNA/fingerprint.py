"""ACRL T01 — Project DNA fingerprint contract."""

from __future__ import annotations

from dataclasses import dataclass

from .project_dna import ProjectDNA


FINGERPRINT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ProjectFingerprints:
    """The two fingerprints already established by Project DNA."""

    source_state_sha256: str
    semantic_state_sha256: str
    schema_version: str = FINGERPRINT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "source_state_sha256": self.source_state_sha256,
            "semantic_state_sha256": self.semantic_state_sha256,
        }


def extract_project_fingerprints(
    dna: ProjectDNA,
) -> ProjectFingerprints:
    """Expose fingerprint evidence without duplicating hash logic."""

    return ProjectFingerprints(
        source_state_sha256=dna.source_state_sha256,
        semantic_state_sha256=dna.semantic_state_sha256,
    )


def fingerprints_match(
    expected: ProjectFingerprints,
    observed: ProjectFingerprints,
) -> bool:
    """Return whether both fingerprint layers match exactly."""

    return (
        expected.source_state_sha256
        == observed.source_state_sha256
        and expected.semantic_state_sha256
        == observed.semantic_state_sha256
    )


__all__ = [
    "FINGERPRINT_SCHEMA_VERSION",
    "ProjectFingerprints",
    "extract_project_fingerprints",
    "fingerprints_match",
]