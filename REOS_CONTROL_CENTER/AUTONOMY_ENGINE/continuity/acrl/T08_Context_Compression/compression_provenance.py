"""ACRL T08 — Compression Provenance.

Provides immutable provenance metadata for compressed context.

Boundary:
    Provenance records origin and transformation identity.
    It does not create authority and does not mutate source state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class CompressionProvenanceError(ValueError):
    """Base provenance error."""


class CompressionProvenanceIntegrityError(
    CompressionProvenanceError
):
    """Raised when provenance integrity verification fails."""


@dataclass(frozen=True)
class CompressionProvenance:
    """Immutable provenance record for one T08 compression result."""

    source_bootstrap_id: str
    source_bootstrap_fingerprint: str
    compression_version: str
    schema_version: str
    policy_version: str
    output_fingerprint: str

    def __post_init__(self) -> None:
        values = (
            ("source_bootstrap_id", self.source_bootstrap_id),
            (
                "source_bootstrap_fingerprint",
                self.source_bootstrap_fingerprint,
            ),
            ("compression_version", self.compression_version),
            ("schema_version", self.schema_version),
            ("policy_version", self.policy_version),
            ("output_fingerprint", self.output_fingerprint),
        )

        for name, value in values:
            if not isinstance(value, str) or not value.strip():
                raise CompressionProvenanceError(
                    f"{name} cannot be empty."
                )

    def to_dict(self) -> dict[str, str]:
        """Return machine-readable provenance metadata."""

        return {
            "source_bootstrap_id": self.source_bootstrap_id,
            "source_bootstrap_fingerprint": (
                self.source_bootstrap_fingerprint
            ),
            "compression_version": self.compression_version,
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "output_fingerprint": self.output_fingerprint,
        }

    def fingerprint(self) -> str:
        """Return deterministic provenance fingerprint."""

        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def verify_output(
        self,
        output_fingerprint: str,
    ) -> bool:
        """Verify provenance points to the supplied output."""

        if not isinstance(
            output_fingerprint,
            str,
        ):
            return False

        return (
            output_fingerprint
            == self.output_fingerprint
        )

    def verify_source(
        self,
        source_bootstrap_id: str,
        source_bootstrap_fingerprint: str,
    ) -> bool:
        """Verify provenance points to the expected source."""

        return (
            source_bootstrap_id
            == self.source_bootstrap_id
            and source_bootstrap_fingerprint
            == self.source_bootstrap_fingerprint
        )

    def validate(
        self,
        *,
        expected_source_id: str | None = None,
        expected_source_fingerprint: str | None = None,
        expected_output_fingerprint: str | None = None,
        expected_policy_version: str | None = None,
        expected_schema_version: str | None = None,
        expected_compression_version: str | None = None,
    ) -> None:
        """Fail closed when provenance does not match expectations."""

        if (
            expected_source_id is not None
            and self.source_bootstrap_id
            != expected_source_id
        ):
            raise CompressionProvenanceIntegrityError(
                "Source bootstrap identity mismatch."
            )

        if (
            expected_source_fingerprint is not None
            and self.source_bootstrap_fingerprint
            != expected_source_fingerprint
        ):
            raise CompressionProvenanceIntegrityError(
                "Source bootstrap fingerprint mismatch."
            )

        if (
            expected_output_fingerprint is not None
            and self.output_fingerprint
            != expected_output_fingerprint
        ):
            raise CompressionProvenanceIntegrityError(
                "Output fingerprint mismatch."
            )

        if (
            expected_policy_version is not None
            and self.policy_version
            != expected_policy_version
        ):
            raise CompressionProvenanceIntegrityError(
                "Compression policy version mismatch."
            )

        if (
            expected_schema_version is not None
            and self.schema_version
            != expected_schema_version
        ):
            raise CompressionProvenanceIntegrityError(
                "Compression schema version mismatch."
            )

        if (
            expected_compression_version is not None
            and self.compression_version
            != expected_compression_version
        ):
            raise CompressionProvenanceIntegrityError(
                "Compression version mismatch."
            )


def build_compression_provenance(
    *,
    source_bootstrap_id: str,
    source_bootstrap_fingerprint: str,
    compression_version: str,
    schema_version: str,
    policy_version: str,
    output_fingerprint: str,
) -> CompressionProvenance:
    """Build an immutable T08 provenance record."""

    return CompressionProvenance(
        source_bootstrap_id=source_bootstrap_id,
        source_bootstrap_fingerprint=(
            source_bootstrap_fingerprint
        ),
        compression_version=compression_version,
        schema_version=schema_version,
        policy_version=policy_version,
        output_fingerprint=output_fingerprint,
    )


def provenance_from_mapping(
    value: Mapping[str, Any],
) -> CompressionProvenance:
    """Reconstruct provenance from machine-readable metadata."""

    if not isinstance(value, Mapping):
        raise CompressionProvenanceError(
            "Provenance must be a mapping."
        )

    required = (
        "source_bootstrap_id",
        "source_bootstrap_fingerprint",
        "compression_version",
        "schema_version",
        "policy_version",
        "output_fingerprint",
    )

    missing = [
        key
        for key in required
        if key not in value
    ]

    if missing:
        raise CompressionProvenanceError(
            "Provenance fields are missing: "
            f"{sorted(missing)}"
        )

    return CompressionProvenance(
        source_bootstrap_id=str(
            value["source_bootstrap_id"]
        ),
        source_bootstrap_fingerprint=str(
            value["source_bootstrap_fingerprint"]
        ),
        compression_version=str(
            value["compression_version"]
        ),
        schema_version=str(
            value["schema_version"]
        ),
        policy_version=str(
            value["policy_version"]
        ),
        output_fingerprint=str(
            value["output_fingerprint"]
        ),
    )


__all__ = [
    "CompressionProvenance",
    "CompressionProvenanceError",
    "CompressionProvenanceIntegrityError",
    "build_compression_provenance",
    "provenance_from_mapping",
]