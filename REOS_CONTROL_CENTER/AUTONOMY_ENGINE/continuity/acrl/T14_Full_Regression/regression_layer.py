"""ACRL T14 — Complete Test & Regression Layer.

Final ACRL verification layer.

Design:
    - Additive only.
    - Does not modify previous ACRL modules.
    - Does not modify ACRL __init__.py.
    - Does not execute project operations.
    - Does not mutate controller state.
    - Does not replace pytest.
    - Produces a deterministic regression plan.
    - Detects missing/duplicate/broken ACRL layers.
    - Fails closed when the ACRL layer graph is inconsistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import importlib
import json
from typing import Any, Iterable, Mapping


class RegressionLayerError(RuntimeError):
    """Base T14 error."""


class RegressionLayerValidationError(
    RegressionLayerError
):
    """Invalid regression input."""


class RegressionLayerIntegrityError(
    RegressionLayerError
):
    """Regression graph integrity failure."""


class RegressionLayerConflictError(
    RegressionLayerError
):
    """Regression layer conflict."""


class RegressionDecision(str, Enum):
    """Canonical T14 decisions."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class RegressionReason(str, Enum):
    """Canonical T14 reasons."""

    VALID = "VALID"
    MISSING_LAYER = "MISSING_LAYER"
    MISSING_TEST = "MISSING_TEST"
    IMPORT_FAILURE = "IMPORT_FAILURE"
    DUPLICATE_LAYER = "DUPLICATE_LAYER"
    INVALID_LAYER_NUMBER = "INVALID_LAYER_NUMBER"
    GRAPH_CONFLICT = "GRAPH_CONFLICT"
    MANIFEST_CONFLICT = "MANIFEST_CONFLICT"


@dataclass(frozen=True)
class RegressionLayerSpec:
    """Immutable specification of one ACRL layer."""

    layer_number: int
    name: str
    module_name: str
    test_module_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_number": self.layer_number,
            "name": self.name,
            "module_name": self.module_name,
            "test_module_name": self.test_module_name,
        }


@dataclass(frozen=True)
class RegressionLayerResult:
    """Result of validating one ACRL layer."""

    spec: RegressionLayerSpec
    module_available: bool
    test_module_available: bool
    import_valid: bool
    error: str | None = None

    @property
    def passed(self) -> bool:
        return (
            self.module_available
            and self.test_module_available
            and self.import_valid
            and self.error is None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "module_available": self.module_available,
            "test_module_available": (
                self.test_module_available
            ),
            "import_valid": self.import_valid,
            "passed": self.passed,
            "error": self.error,
        }


@dataclass(frozen=True)
class RegressionReport:
    """Immutable T14 regression readiness report."""

    schema_version: str
    decision: RegressionDecision
    reason: RegressionReason
    total_layers: int
    passed_layers: int
    failed_layers: int
    results: tuple[RegressionLayerResult, ...]
    fingerprint: str
    fail_closed: bool

    @property
    def ready(self) -> bool:
        return (
            self.decision == RegressionDecision.READY
            and self.failed_layers == 0
            and not self.fail_closed
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "total_layers": self.total_layers,
            "passed_layers": self.passed_layers,
            "failed_layers": self.failed_layers,
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "fingerprint": self.fingerprint,
            "fail_closed": self.fail_closed,
            "ready": self.ready,
        }


class RegressionLayerEngine:
    """Deterministic ACRL T14 regression engine."""

    SCHEMA_VERSION = "1.0"

    PACKAGE = (
        "AUTONOMY_ENGINE.continuity.acrl"
    )

    LAYER_SPECS: tuple[RegressionLayerSpec, ...] = (
        RegressionLayerSpec(
            1,
            "Project DNA",
            f"{PACKAGE}.project_dna",
            f"{PACKAGE}.test_project_dna",
        ),
        RegressionLayerSpec(
            2,
            "Architecture Lock",
            f"{PACKAGE}.architecture_lock",
            f"{PACKAGE}.test_architecture_lock",
        ),
        RegressionLayerSpec(
            3,
            "State Reconstruction",
            f"{PACKAGE}.state_reconstruction",
            f"{PACKAGE}.test_state_reconstruction",
        ),
        RegressionLayerSpec(
            4,
            "Gate/Subtask Continuity",
            f"{PACKAGE}.gate_subtask_continuity",
            f"{PACKAGE}.test_gate_subtask_continuity",
        ),
        RegressionLayerSpec(
            5,
            "Dependency & Authority Map",
            f"{PACKAGE}.dependency_authority_map",
            f"{PACKAGE}.test_dependency_authority_map",
        ),
        RegressionLayerSpec(
            6,
            "Checkpoint Engine",
            f"{PACKAGE}.checkpoint_engine",
            f"{PACKAGE}.test_checkpoint_engine",
        ),
        RegressionLayerSpec(
            7,
            "New-Chat Bootstrap / Handoff",
            f"{PACKAGE}.new_chat_bootstrap",
            f"{PACKAGE}.test_new_chat_bootstrap",
        ),
        RegressionLayerSpec(
            8,
            "Context Compression",
            f"{PACKAGE}.context_compression",
            f"{PACKAGE}.test_context_compression",
        ),
        RegressionLayerSpec(
            9,
            "State Integrity / Fingerprint",
            f"{PACKAGE}.state_integrity",
            f"{PACKAGE}.test_state_integrity",
        ),
        RegressionLayerSpec(
            10,
            "Drift Detection",
            f"{PACKAGE}.drift_detection",
            f"{PACKAGE}.test_drift_detection",
        ),
        RegressionLayerSpec(
            11,
            "Recovery / Fail-Closed Guard",
            f"{PACKAGE}.recovery_guard",
            f"{PACKAGE}.test_recovery_guard",
        ),
        RegressionLayerSpec(
            12,
            "Resume-Safety Validation",
            f"{PACKAGE}.resume_safety_validation",
            f"{PACKAGE}.test_resume_safety_validation",
        ),
        RegressionLayerSpec(
            13,
            "Controller Integration",
            f"{PACKAGE}.controller_integration",
            f"{PACKAGE}.test_controller_integration",
        ),
        RegressionLayerSpec(
            14,
            "Complete Test & Regression Layer",
            f"{PACKAGE}.regression_layer",
            f"{PACKAGE}.test_regression_layer",
        ),
    )

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
            raise RegressionLayerValidationError(
                "Regression data cannot be canonicalized."
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
    def validate_manifest(
        cls,
    ) -> None:
        specs = cls.LAYER_SPECS

        if not specs:
            raise RegressionLayerIntegrityError(
                "ACRL regression manifest is empty."
            )

        numbers = [
            spec.layer_number
            for spec in specs
        ]

        expected = list(
            range(1, len(specs) + 1)
        )

        if numbers != expected:
            raise RegressionLayerIntegrityError(
                "ACRL layer numbering is not contiguous."
            )

        module_names = [
            spec.module_name
            for spec in specs
        ]

        if len(module_names) != len(
            set(module_names)
        ):
            raise RegressionLayerIntegrityError(
                "Duplicate ACRL module detected."
            )

        test_names = [
            spec.test_module_name
            for spec in specs
        ]

        if len(test_names) != len(
            set(test_names)
        ):
            raise RegressionLayerIntegrityError(
                "Duplicate ACRL test module detected."
            )

    @classmethod
    def validate_layer(
        cls,
        spec: RegressionLayerSpec,
    ) -> RegressionLayerResult:
        if not isinstance(
            spec,
            RegressionLayerSpec,
        ):
            raise RegressionLayerValidationError(
                "Invalid regression layer specification."
            )

        module_available = True
        test_module_available = True
        import_valid = True
        error: str | None = None

        try:
            importlib.import_module(
                spec.module_name
            )
        except Exception as exc:
            module_available = False
            import_valid = False
            error = (
                f"Layer import failed: "
                f"{type(exc).__name__}: {exc}"
            )

        try:
            importlib.import_module(
                spec.test_module_name
            )
        except Exception as exc:
            test_module_available = False
            import_valid = False

            if error is None:
                error = (
                    f"Test import failed: "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                error += (
                    f" | Test import failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        return RegressionLayerResult(
            spec=spec,
            module_available=module_available,
            test_module_available=test_module_available,
            import_valid=import_valid,
            error=error,
        )

    @classmethod
    def build_report(
        cls,
        results: Iterable[
            RegressionLayerResult
        ],
    ) -> RegressionReport:
        normalized = tuple(results)

        failed = tuple(
            result
            for result in normalized
            if not result.passed
        )

        data = {
            "schema_version": cls.SCHEMA_VERSION,
            "results": [
                result.to_dict()
                for result in normalized
            ],
        }

        fingerprint = cls.fingerprint(data)

        if failed:
            reason = RegressionReason.IMPORT_FAILURE

            return RegressionReport(
                schema_version=cls.SCHEMA_VERSION,
                decision=(
                    RegressionDecision.FAIL_CLOSED
                ),
                reason=reason,
                total_layers=len(normalized),
                passed_layers=(
                    len(normalized) - len(failed)
                ),
                failed_layers=len(failed),
                results=normalized,
                fingerprint=fingerprint,
                fail_closed=True,
            )

        return RegressionReport(
            schema_version=cls.SCHEMA_VERSION,
            decision=RegressionDecision.READY,
            reason=RegressionReason.VALID,
            total_layers=len(normalized),
            passed_layers=len(normalized),
            failed_layers=0,
            results=normalized,
            fingerprint=fingerprint,
            fail_closed=False,
        )

    @classmethod
    def validate_all_layers(
        cls,
    ) -> RegressionReport:
        cls.validate_manifest()

        results = tuple(
            cls.validate_layer(spec)
            for spec in cls.LAYER_SPECS
        )

        return cls.build_report(results)

    @classmethod
    def assert_ready(
        cls,
        report: RegressionReport,
    ) -> RegressionReport:
        if not isinstance(
            report,
            RegressionReport,
        ):
            raise RegressionLayerValidationError(
                "Invalid regression report."
            )

        if not report.ready:
            raise RegressionLayerIntegrityError(
                "ACRL regression layer is not ready."
            )

        return report

    @classmethod
    def build_pytest_targets(
        cls,
    ) -> tuple[str, ...]:
        """Return deterministic pytest targets.

        T14 describes the full suite; it does not recursively invoke
        pytest from inside pytest.
        """

        cls.validate_manifest()

        return tuple(
            spec.test_module_name.replace(
                ".", "/"
            )
            + ".py"
            for spec in cls.LAYER_SPECS
        )


def validate_acrl_regression() -> RegressionReport:
    """Public T14 validation API."""

    return RegressionLayerEngine.validate_all_layers()


def acrl_regression_ready(
    report: RegressionReport,
) -> bool:
    """Return True only when T14 is fully ready."""

    if not isinstance(
        report,
        RegressionReport,
    ):
        raise RegressionLayerValidationError(
            "Invalid regression report."
        )

    return report.ready


__all__ = [
    "RegressionDecision",
    "RegressionLayerConflictError",
    "RegressionLayerEngine",
    "RegressionLayerError",
    "RegressionLayerIntegrityError",
    "RegressionLayerResult",
    "RegressionLayerSpec",
    "RegressionLayerValidationError",
    "RegressionReason",
    "RegressionReport",
    "acrl_regression_ready",
    "validate_acrl_regression",
]