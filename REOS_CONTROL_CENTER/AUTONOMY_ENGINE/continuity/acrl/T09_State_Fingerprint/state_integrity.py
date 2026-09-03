"""ACRL T09 — State Integrity / Fingerprint.

Additive-only integrity layer.

T09 provides:
    - deterministic canonicalization
    - component fingerprints
    - composite state fingerprint
    - integrity verification
    - tamper detection
    - integrity reporting
    - fail-closed validation

Architecture rules:
    - T01-T08 are read-only dependencies.
    - __init__.py is not modified.
    - No project architecture is changed.
    - No authoritative state is invented.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class StateIntegrityError(RuntimeError):
    """Base T09 integrity error."""


class StateIntegrityValidationError(
    StateIntegrityError
):
    """Raised when integrity input is invalid."""


class StateIntegrityAuthorityError(
    StateIntegrityError
):
    """Raised when authoritative state is incomplete."""


class StateIntegrityFingerprintError(
    StateIntegrityError
):
    """Raised when fingerprint verification fails."""


class StateIntegrityTamperError(
    StateIntegrityError
):
    """Raised when state tampering is detected."""


@dataclass(frozen=True)
class ComponentFingerprint:
    """Fingerprint for one authoritative state component."""

    name: str
    fingerprint: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "fingerprint": self.fingerprint,
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True)
class StateIntegrityReport:
    """Immutable integrity verification report."""

    schema_version: str
    authority: str
    overall_fingerprint: str
    component_fingerprints: tuple[
        ComponentFingerprint,
        ...
    ]
    verified: bool
    tampered_components: tuple[str, ...]
    missing_components: tuple[str, ...]
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "overall_fingerprint": (
                self.overall_fingerprint
            ),
            "component_fingerprints": [
                item.to_dict()
                for item in self.component_fingerprints
            ],
            "verified": self.verified,
            "tampered_components": list(
                self.tampered_components
            ),
            "missing_components": list(
                self.missing_components
            ),
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True)
class StateIntegritySnapshot:
    """Immutable authoritative integrity snapshot."""

    schema_version: str
    authority: str
    components: Mapping[str, Any]
    component_fingerprints: tuple[
        ComponentFingerprint,
        ...
    ]
    overall_fingerprint: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "components": {
                key: value
                for key, value in self.components.items()
            },
            "component_fingerprints": [
                item.to_dict()
                for item in self.component_fingerprints
            ],
            "overall_fingerprint": (
                self.overall_fingerprint
            ),
            "algorithm": self.algorithm,
        }


class StateIntegrityEngine:
    """Build and verify deterministic state fingerprints."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    REQUIRED_COMPONENTS = (
        "project_identity",
        "architecture",
        "execution",
        "gate_continuity",
        "dependency_authority",
        "checkpoint",
    )

    @classmethod
    def canonicalize(
        cls,
        value: Any,
    ) -> str:
        """Return deterministic JSON representation."""

        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise StateIntegrityValidationError(
                "State cannot be deterministically "
                "canonicalized."
            ) from exc

    @classmethod
    def fingerprint(
        cls,
        value: Any,
    ) -> str:
        """Return SHA-256 fingerprint."""

        canonical = cls.canonicalize(value)

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _require_component(
        cls,
        name: str,
        value: Any,
    ) -> dict[str, Any]:
        if not isinstance(
            value,
            Mapping,
        ):
            raise StateIntegrityAuthorityError(
                f"Authoritative component '{name}' "
                "is missing or invalid."
            )

        return dict(value)

    @classmethod
    def _component_fingerprint(
        cls,
        name: str,
        value: Mapping[str, Any],
    ) -> ComponentFingerprint:
        return ComponentFingerprint(
            name=name,
            fingerprint=cls.fingerprint(
                value
            ),
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def _overall_payload(
        cls,
        component_fingerprints: tuple[
            ComponentFingerprint,
            ...,
        ],
    ) -> dict[str, Any]:
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "algorithm": cls.ALGORITHM,
            "components": [
                item.to_dict()
                for item in component_fingerprints
            ],
        }

    @classmethod
    def build(
        cls,
        components: Mapping[str, Any],
    ) -> StateIntegritySnapshot:
        """Build an integrity snapshot from authoritative components."""

        if not isinstance(
            components,
            Mapping,
        ):
            raise StateIntegrityValidationError(
                "Integrity input must be a mapping."
            )

        normalized: dict[str, dict[str, Any]] = {}

        for name in cls.REQUIRED_COMPONENTS:
            if name not in components:
                raise StateIntegrityAuthorityError(
                    f"Required authoritative component "
                    f"'{name}' is missing."
                )

            normalized[name] = cls._require_component(
                name,
                components[name],
            )

        component_fingerprints = tuple(
            cls._component_fingerprint(
                name,
                normalized[name],
            )
            for name in cls.REQUIRED_COMPONENTS
        )

        overall_payload = cls._overall_payload(
            component_fingerprints
        )

        overall_fingerprint = cls.fingerprint(
            overall_payload
        )

        return StateIntegritySnapshot(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            components=normalized,
            component_fingerprints=(
                component_fingerprints
            ),
            overall_fingerprint=(
                overall_fingerprint
            ),
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def verify(
        cls,
        snapshot: StateIntegritySnapshot,
        current_components: Mapping[str, Any],
    ) -> StateIntegrityReport:
        """Compare current state against an integrity snapshot."""

        if not isinstance(
            snapshot,
            StateIntegritySnapshot,
        ):
            raise StateIntegrityValidationError(
                "Invalid integrity snapshot."
            )

        if not isinstance(
            current_components,
            Mapping,
        ):
            raise StateIntegrityValidationError(
                "Current state must be a mapping."
            )

        if snapshot.authority != cls.AUTHORITY:
            raise StateIntegrityAuthorityError(
                "Integrity snapshot authority mismatch."
            )

        expected = {
            item.name: item.fingerprint
            for item in snapshot.component_fingerprints
        }

        actual_components: dict[
            str,
            dict[str, Any],
        ] = {}

        missing: list[str] = []

        for name in cls.REQUIRED_COMPONENTS:
            if name not in current_components:
                missing.append(name)
                continue

            actual_components[name] = (
                cls._require_component(
                    name,
                    current_components[name],
                )
            )

        tampered: list[str] = []

        actual_fingerprints: list[
            ComponentFingerprint
        ] = []

        for name in cls.REQUIRED_COMPONENTS:
            if name not in actual_components:
                continue

            actual = cls._component_fingerprint(
                name,
                actual_components[name],
            )

            actual_fingerprints.append(actual)

            if expected.get(name) != actual.fingerprint:
                tampered.append(name)

        verified = (
            not missing
            and not tampered
        )

        return StateIntegrityReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            overall_fingerprint=(
                snapshot.overall_fingerprint
            ),
            component_fingerprints=tuple(
                actual_fingerprints
            ),
            verified=verified,
            tampered_components=tuple(
                tampered
            ),
            missing_components=tuple(
                missing
            ),
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def verify_or_raise(
        cls,
        snapshot: StateIntegritySnapshot,
        current_components: Mapping[str, Any],
    ) -> StateIntegrityReport:
        """Verify and fail closed on integrity violations."""

        report = cls.verify(
            snapshot,
            current_components,
        )

        if report.missing_components:
            raise StateIntegrityAuthorityError(
                "Required authoritative components "
                "are missing: "
                f"{list(report.missing_components)}"
            )

        if report.tampered_components:
            raise StateIntegrityTamperError(
                "State integrity violation detected in: "
                f"{list(report.tampered_components)}"
            )

        if not report.verified:
            raise StateIntegrityFingerprintError(
                "State fingerprint verification failed."
            )

        return report

    @classmethod
    def compare(
        cls,
        left: Mapping[str, Any],
        right: Mapping[str, Any],
    ) -> bool:
        """Deterministically compare two state mappings."""

        if not isinstance(left, Mapping):
            raise StateIntegrityValidationError(
                "Left state must be a mapping."
            )

        if not isinstance(right, Mapping):
            raise StateIntegrityValidationError(
                "Right state must be a mapping."
            )

        return cls.fingerprint(left) == cls.fingerprint(
            right
        )


def build_state_integrity(
    components: Mapping[str, Any],
) -> StateIntegritySnapshot:
    """Convenience API for building integrity state."""

    return StateIntegrityEngine.build(
        components
    )


def verify_state_integrity(
    snapshot: StateIntegritySnapshot,
    current_components: Mapping[str, Any],
) -> StateIntegrityReport:
    """Convenience API for integrity verification."""

    return StateIntegrityEngine.verify(
        snapshot,
        current_components,
    )


__all__ = [
    "ComponentFingerprint",
    "StateIntegrityAuthorityError",
    "StateIntegrityEngine",
    "StateIntegrityError",
    "StateIntegrityFingerprintError",
    "StateIntegrityReport",
    "StateIntegritySnapshot",
    "StateIntegrityTamperError",
    "StateIntegrityValidationError",
    "build_state_integrity",
    "verify_state_integrity",
]