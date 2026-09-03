"""ACRL T01 — Project identity metadata."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .project_dna import ProjectDNA


IDENTITY_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ProjectIdentity:
    """Stable machine identity derived from Project DNA."""

    product: str
    project_name: str
    project_type: str
    controller_version: str
    state_schema_version: int
    dna_schema_version: str
    canonical_source: str
    identity_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": IDENTITY_SCHEMA_VERSION,
            "product": self.product,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "controller_version": self.controller_version,
            "state_schema_version": self.state_schema_version,
            "dna_schema_version": self.dna_schema_version,
            "canonical_source": self.canonical_source,
            "identity_sha256": self.identity_sha256,
        }


def build_project_identity(dna: ProjectDNA) -> ProjectIdentity:
    """Build deterministic project identity from an existing DNA projection."""

    canonical = {
        "product": dna.product,
        "project_name": dna.project_name,
        "project_type": dna.project_type,
        "controller_version": dna.controller_version,
        "state_schema_version": dna.state_schema_version,
        "dna_schema_version": dna.dna_schema_version,
        "canonical_source": dna.canonical_source,
    }

    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    identity_sha256 = hashlib.sha256(encoded).hexdigest()

    return ProjectIdentity(
        product=dna.product,
        project_name=dna.project_name,
        project_type=dna.project_type,
        controller_version=dna.controller_version,
        state_schema_version=dna.state_schema_version,
        dna_schema_version=dna.dna_schema_version,
        canonical_source=dna.canonical_source,
        identity_sha256=identity_sha256,
    )


__all__ = [
    "IDENTITY_SCHEMA_VERSION",
    "ProjectIdentity",
    "build_project_identity",
]