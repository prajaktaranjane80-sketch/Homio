"""ACRL T10 — Drift Detection.

Additive-only drift detection layer.

T10 detects differences between an approved authoritative baseline
and current execution state.

Design rules:
    - Never modify T01-T09.
    - Never modify __init__.py.
    - Never repair state.
    - Never silently accept drift.
    - Detection is deterministic.
    - Unknown/missing authoritative data fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class DriftDetectionError(RuntimeError):
    """Base T10 error."""


class DriftValidationError(
    DriftDetectionError
):
    """Raised when drift input is invalid."""


class DriftAuthorityError(
    DriftDetectionError
):
    """Raised when authoritative information is unavailable."""


class DriftIntegrityError(
    DriftDetectionError
):
    """Raised when baseline integrity cannot be trusted."""


class DriftSeverity(str, Enum):
    """Severity classification for detected drift."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DriftType(str, Enum):
    """Supported authoritative drift categories."""

    NONE = "NONE"
    PROJECT = "PROJECT"
    ARCHITECTURE = "ARCHITECTURE"
    EXECUTION = "EXECUTION"
    GATE_CONTINUITY = "GATE_CONTINUITY"
    DEPENDENCY_AUTHORITY = "DEPENDENCY_AUTHORITY"
    CHECKPOINT = "CHECKPOINT"
    CROSS_LAYER = "CROSS_LAYER"


@dataclass(frozen=True)
class DriftFinding:
    """One deterministic drift finding."""

    drift_type: DriftType
    severity: DriftSeverity
    component: str
    expected_fingerprint: str
    actual_fingerprint: str
    changed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "component": self.component,
            "expected_fingerprint": (
                self.expected_fingerprint
            ),
            "actual_fingerprint": (
                self.actual_fingerprint
            ),
            "changed": self.changed,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DriftReport:
    """Complete immutable drift report."""

    schema_version: str
    authority: str
    baseline_fingerprint: str
    current_fingerprint: str
    drift_detected: bool
    severity: DriftSeverity
    findings: tuple[DriftFinding, ...]
    fail_closed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "baseline_fingerprint": (
                self.baseline_fingerprint
            ),
            "current_fingerprint": (
                self.current_fingerprint
            ),
            "drift_detected": self.drift_detected,
            "severity": self.severity.value,
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
            "fail_closed": self.fail_closed,
        }


@dataclass(frozen=True)
class DriftBaseline:
    """Immutable approved baseline."""

    schema_version: str
    authority: str
    components: Mapping[str, Any]
    component_fingerprints: Mapping[str, str]
    overall_fingerprint: str
    integrity_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "components": dict(self.components),
            "component_fingerprints": dict(
                self.component_fingerprints
            ),
            "overall_fingerprint": (
                self.overall_fingerprint
            ),
            "integrity_fingerprint": (
                self.integrity_fingerprint
            ),
        }


class DriftDetectionEngine:
    """Deterministic fail-closed drift detector."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    COMPONENTS = (
        "project_identity",
        "architecture",
        "execution",
        "gate_continuity",
        "dependency_authority",
        "checkpoint",
    )

    TYPE_MAP = {
        "project_identity": DriftType.PROJECT,
        "architecture": DriftType.ARCHITECTURE,
        "execution": DriftType.EXECUTION,
        "gate_continuity": DriftType.GATE_CONTINUITY,
        "dependency_authority": (
            DriftType.DEPENDENCY_AUTHORITY
        ),
        "checkpoint": DriftType.CHECKPOINT,
    }

    @classmethod
    def canonicalize(
        cls,
        value: Any,
    ) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise DriftValidationError(
                "Value cannot be deterministically "
                "canonicalized."
            ) from exc

    @classmethod
    def fingerprint(
        cls,
        value: Any,
    ) -> str:
        return hashlib.sha256(
            cls.canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _require_mapping(
        cls,
        name: str,
        value: Any,
    ) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise DriftAuthorityError(
                f"Authoritative component '{name}' "
                "is missing or invalid."
            )

        return dict(value)

    @classmethod
    def create_baseline(
        cls,
        components: Mapping[str, Any],
    ) -> DriftBaseline:
        """Create a deterministic approved baseline."""

        if not isinstance(
            components,
            Mapping,
        ):
            raise DriftValidationError(
                "Baseline components must be a mapping."
            )

        normalized: dict[str, dict[str, Any]] = {}

        for name in cls.COMPONENTS:
            if name not in components:
                raise DriftAuthorityError(
                    f"Required component '{name}' "
                    "is missing."
                )

            normalized[name] = cls._require_mapping(
                name,
                components[name],
            )

        component_fingerprints = {
            name: cls.fingerprint(
                normalized[name]
            )
            for name in cls.COMPONENTS
        }

        overall_payload = {
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "algorithm": cls.ALGORITHM,
            "components": component_fingerprints,
        }

        overall_fingerprint = cls.fingerprint(
            overall_payload
        )

        integrity_payload = {
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "components": normalized,
            "component_fingerprints": (
                component_fingerprints
            ),
            "overall_fingerprint": (
                overall_fingerprint
            ),
        }

        integrity_fingerprint = cls.fingerprint(
            integrity_payload
        )

        return DriftBaseline(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            components=normalized,
            component_fingerprints=(
                component_fingerprints
            ),
            overall_fingerprint=(
                overall_fingerprint
            ),
            integrity_fingerprint=(
                integrity_fingerprint
            ),
        )

    @classmethod
    def verify_baseline(
        cls,
        baseline: DriftBaseline,
    ) -> None:
        """Verify baseline has not been altered."""

        if not isinstance(
            baseline,
            DriftBaseline,
        ):
            raise DriftValidationError(
                "Invalid drift baseline."
            )

        if baseline.authority != cls.AUTHORITY:
            raise DriftAuthorityError(
                "Baseline authority mismatch."
            )

        recalculated_components = {
            name: cls.fingerprint(
                baseline.components[name]
            )
            for name in cls.COMPONENTS
            if name in baseline.components
        }

        if set(recalculated_components) != set(
            cls.COMPONENTS
        ):
            raise DriftAuthorityError(
                "Baseline is missing required components."
            )

        if dict(
            baseline.component_fingerprints
        ) != recalculated_components:
            raise DriftIntegrityError(
                "Baseline component fingerprints "
                "do not match authoritative state."
            )

        overall_payload = {
            "schema_version": baseline.schema_version,
            "authority": baseline.authority,
            "algorithm": cls.ALGORITHM,
            "components": recalculated_components,
        }

        expected_overall = cls.fingerprint(
            overall_payload
        )

        if expected_overall != (
            baseline.overall_fingerprint
        ):
            raise DriftIntegrityError(
                "Baseline overall fingerprint mismatch."
            )

        integrity_payload = {
            "schema_version": baseline.schema_version,
            "authority": baseline.authority,
            "components": dict(
                baseline.components
            ),
            "component_fingerprints": (
                recalculated_components
            ),
            "overall_fingerprint": (
                expected_overall
            ),
        }

        expected_integrity = cls.fingerprint(
            integrity_payload
        )

        if expected_integrity != (
            baseline.integrity_fingerprint
        ):
            raise DriftIntegrityError(
                "Baseline integrity fingerprint mismatch."
            )

    @classmethod
    def _classify_severity(
        cls,
        drift_type: DriftType,
    ) -> DriftSeverity:
        if drift_type == DriftType.ARCHITECTURE:
            return DriftSeverity.CRITICAL

        if drift_type in {
            DriftType.DEPENDENCY_AUTHORITY,
            DriftType.CROSS_LAYER,
        }:
            return DriftSeverity.HIGH

        if drift_type in {
            DriftType.EXECUTION,
            DriftType.GATE_CONTINUITY,
        }:
            return DriftSeverity.MEDIUM

        if drift_type in {
            DriftType.PROJECT,
            DriftType.CHECKPOINT,
        }:
            return DriftSeverity.LOW

        return DriftSeverity.NONE

    @classmethod
    def detect(
        cls,
        baseline: DriftBaseline,
        current_components: Mapping[str, Any],
    ) -> DriftReport:
        """Detect component-level drift."""

        cls.verify_baseline(baseline)

        if not isinstance(
            current_components,
            Mapping,
        ):
            raise DriftValidationError(
                "Current components must be a mapping."
            )

        missing = [
            name
            for name in cls.COMPONENTS
            if name not in current_components
        ]

        if missing:
            raise DriftAuthorityError(
                "Current authoritative state is missing: "
                f"{missing}"
            )

        findings: list[DriftFinding] = []

        actual_fingerprints: dict[str, str] = {}

        for name in cls.COMPONENTS:
            current = cls._require_mapping(
                name,
                current_components[name],
            )

            actual = cls.fingerprint(current)

            actual_fingerprints[name] = actual

            expected = (
                baseline.component_fingerprints[name]
            )

            changed = expected != actual

            if changed:
                drift_type = cls.TYPE_MAP[name]

                findings.append(
                    DriftFinding(
                        drift_type=drift_type,
                        severity=(
                            cls._classify_severity(
                                drift_type
                            )
                        ),
                        component=name,
                        expected_fingerprint=expected,
                        actual_fingerprint=actual,
                        changed=True,
                        reason=(
                            f"{name} differs from "
                            "the approved baseline."
                        ),
                    )
                )

        current_overall_payload = {
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "algorithm": cls.ALGORITHM,
            "components": actual_fingerprints,
        }

        current_overall = cls.fingerprint(
            current_overall_payload
        )

        if not findings:
            severity = DriftSeverity.NONE
            fail_closed = False
        else:
            severity_order = {
                DriftSeverity.NONE: 0,
                DriftSeverity.LOW: 1,
                DriftSeverity.MEDIUM: 2,
                DriftSeverity.HIGH: 3,
                DriftSeverity.CRITICAL: 4,
            }

            severity = max(
                (
                    finding.severity
                    for finding in findings
                ),
                key=lambda value: severity_order[value],
            )

            fail_closed = severity in {
                DriftSeverity.HIGH,
                DriftSeverity.CRITICAL,
            }

        return DriftReport(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            baseline_fingerprint=(
                baseline.overall_fingerprint
            ),
            current_fingerprint=current_overall,
            drift_detected=bool(findings),
            severity=severity,
            findings=tuple(findings),
            fail_closed=fail_closed,
        )

    @classmethod
    def detect_or_raise(
        cls,
        baseline: DriftBaseline,
        current_components: Mapping[str, Any],
    ) -> DriftReport:
        """Detect drift and fail closed for unsafe drift."""

        report = cls.detect(
            baseline,
            current_components,
        )

        if report.severity in {
            DriftSeverity.HIGH,
            DriftSeverity.CRITICAL,
        }:
            raise DriftDetectionError(
                "Unsafe architectural/authority drift detected."
            )

        return report


def create_drift_baseline(
    components: Mapping[str, Any],
) -> DriftBaseline:
    """Convenience baseline builder."""

    return DriftDetectionEngine.create_baseline(
        components
    )


def detect_drift(
    baseline: DriftBaseline,
    current_components: Mapping[str, Any],
) -> DriftReport:
    """Convenience drift detection API."""

    return DriftDetectionEngine.detect(
        baseline,
        current_components,
    )


__all__ = [
    "DriftBaseline",
    "DriftDetectionEngine",
    "DriftDetectionError",
    "DriftFinding",
    "DriftIntegrityError",
    "DriftReport",
    "DriftSeverity",
    "DriftType",
    "DriftAuthorityError",
    "DriftValidationError",
    "create_drift_baseline",
    "detect_drift",
]