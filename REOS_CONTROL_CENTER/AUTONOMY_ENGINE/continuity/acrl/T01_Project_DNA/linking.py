"""ACRL T01 — Final capability linking.

This module links the existing T01 micro-capabilities without replacing
or duplicating their core logic.

The linker is strictly read-only.

It does not:
- mutate authoritative state
- authorize execution
- authorize writing
- perform recovery
- perform migration
- change architecture
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

from .bootstrap import (
    ProjectBootstrap,
    build_project_bootstrap,
)
from .compatibility import (
    CompatibilityResult,
    evaluate_state_schema_compatibility,
)
from .fingerprint import (
    ProjectFingerprints,
    extract_project_fingerprints,
)
from .freshness import (
    FreshnessPolicy,
    FreshnessResult,
    classify_state_freshness,
)
from .identity import (
    ProjectIdentity,
    build_project_identity,
)
from .observation import (
    StateObservation,
    observe_state_atomically,
)
from .project_dna import (
    ProjectDNA,
    ProjectDNAReader,
)
from .provenance import (
    EvidenceRecord,
    observed_evidence,
)


LINKING_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class T01LinkedContext:
    """Complete read-only linked context produced by T01."""

    dna: ProjectDNA
    identity: ProjectIdentity
    fingerprints: ProjectFingerprints
    observation: StateObservation
    provenance: EvidenceRecord
    freshness: FreshnessResult
    compatibility: CompatibilityResult
    bootstrap: ProjectBootstrap

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical machine-readable T01 context."""

        return {
            "schema_version": LINKING_SCHEMA_VERSION,
            "dna": self.dna.to_dict(),
            "identity": self.identity.to_dict(),
            "fingerprints": self.fingerprints.to_dict(),
            "observation": self.observation.to_dict(),
            "provenance": self.provenance.to_dict(),
            "freshness": self.freshness.to_dict(),
            "compatibility": self.compatibility.to_dict(),
            "bootstrap": self.bootstrap.to_dict(),
            "authority": {
                "read_authorized": True,
                "write_authorized": False,
                "execution_authorized": False,
                "approval_authorized": False,
                "recovery_authorized": False,
                "migration_authorized": False,
            },
        }


def _decode_observed_state(
    observation: StateObservation,
) -> dict[str, Any]:
    """Decode one already-observed state snapshot."""

    try:
        value = json.loads(
            observation.content.decode("utf-8-sig")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "Observed authoritative state is not valid JSON."
        ) from exc

    if not isinstance(value, dict):
        raise ValueError(
            "Observed authoritative state must be a JSON object."
        )

    return value


def build_t01_linked_context(
    control_center_root: Path | str | None = None,
    *,
    observed_at=None,
    freshness_policy: FreshnessPolicy | None = None,
    supported_state_schema_minimum: int = 3,
    supported_state_schema_maximum: int = 3,
) -> T01LinkedContext:
    """Build the complete T01 linked read-only context."""

    reader = ProjectDNAReader(control_center_root)
    dna = reader.read()

    observation = observe_state_atomically(reader.state_path)
    state = _decode_observed_state(observation)

    if observation.source_sha256 != dna.source_state_sha256:
        raise ValueError(
            "T01 source fingerprint changed between DNA read "
            "and atomic observation."
        )

    identity = build_project_identity(dna)
    fingerprints = extract_project_fingerprints(dna)

    freshness = classify_state_freshness(
        state,
        observed_at=observed_at,
        policy=freshness_policy,
    )

    compatibility = evaluate_state_schema_compatibility(
        dna.state_schema_version,
        supported_minimum=supported_state_schema_minimum,
        supported_maximum=supported_state_schema_maximum,
    )

    provenance = observed_evidence(
        source_fingerprint=observation.source_sha256,
        producer="ACRL.T01.LINKING",
    )

    bootstrap = build_project_bootstrap(
        control_center_root,
        observed_at=observed_at,
        freshness_policy=freshness_policy,
    )

    return T01LinkedContext(
        dna=dna,
        identity=identity,
        fingerprints=fingerprints,
        observation=observation,
        provenance=provenance,
        freshness=freshness,
        compatibility=compatibility,
        bootstrap=bootstrap,
    )


__all__ = [
    "LINKING_SCHEMA_VERSION",
    "T01LinkedContext",
    "build_t01_linked_context",
]