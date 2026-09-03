"""T16 PART-01 — Deterministic repository fingerprint."""

from __future__ import annotations

from hashlib import sha256

from .topology import RepositoryTopology


class RepositoryFingerprintError(RuntimeError):
    """Raised when a repository fingerprint cannot be generated."""


def fingerprint_topology(topology: RepositoryTopology) -> str:
    """Generate a deterministic SHA-256 fingerprint from topology."""

    try:
        lines: list[str] = []

        for entry in topology.entries:
            lines.append(
                "|".join(
                    (
                        entry.relative_path,
                        entry.kind.value,
                        entry.classification.value,
                        str(entry.is_symlink),
                    )
                )
            )

        lines.append("EXCLUDED_DIRECTORIES")

        lines.extend(topology.excluded_directories)

        canonical = "\n".join(lines)

        return sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    except (AttributeError, TypeError, ValueError) as exc:
        raise RepositoryFingerprintError(
            "Unable to generate deterministic repository fingerprint."
        ) from exc


__all__ = [
    "RepositoryFingerprintError",
    "fingerprint_topology",
]