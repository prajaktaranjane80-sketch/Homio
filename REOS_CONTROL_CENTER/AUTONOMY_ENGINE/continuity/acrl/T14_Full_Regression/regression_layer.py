"""ACRL T14 — Complete Test & Regression Layer.

Read-only final regression capability for the canonical numbered ACRL tree.
It validates topology, source presence, source/test syntax, and produces a
stable fail-closed report. It does not execute tests or mutate project state.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .regression_compatibility import CompatibilityStatus, compare_schema
from .regression_identity import fingerprint, fingerprint_manifest
from .regression_metrics import summarize
from .regression_policy import RegressionPolicy
from .regression_provenance import RegressionProvenance
from .regression_registry import CanonicalLayerSpec, RegressionRegistry
from .regression_validation import validate_layer_spec_fields


class RegressionLayerError(RuntimeError):
    pass
class RegressionLayerValidationError(RegressionLayerError):
    pass
class RegressionLayerIntegrityError(RegressionLayerError):
    pass
class RegressionLayerConflictError(RegressionLayerError):
    pass

class RegressionDecision(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"

class RegressionReason(str, Enum):
    VALID = "VALID"
    MISSING_LAYER = "MISSING_LAYER"
    MISSING_TEST = "MISSING_TEST"
    IMPORT_FAILURE = "IMPORT_FAILURE"
    DUPLICATE_LAYER = "DUPLICATE_LAYER"
    INVALID_LAYER_NUMBER = "INVALID_LAYER_NUMBER"
    GRAPH_CONFLICT = "GRAPH_CONFLICT"
    MANIFEST_CONFLICT = "MANIFEST_CONFLICT"
    SYNTAX_FAILURE = "SYNTAX_FAILURE"
    POLICY_CONFLICT = "POLICY_CONFLICT"

@dataclass(frozen=True)
class RegressionLayerSpec:
    layer_number: int
    name: str
    module_name: str
    test_module_name: str
    directory: str | None = None
    core_file: str | None = None
    test_glob: str = "test_*.py"

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_number": self.layer_number, "name": self.name,
            "module_name": self.module_name, "test_module_name": self.test_module_name,
            "directory": self.directory, "core_file": self.core_file,
            "test_glob": self.test_glob,
        }

@dataclass(frozen=True)
class RegressionLayerResult:
    spec: RegressionLayerSpec
    module_available: bool
    test_module_available: bool
    import_valid: bool
    error: str | None = None
    source_path: str | None = None
    test_files: tuple[str, ...] = tuple()
    syntax_error: bool = False

    @property
    def passed(self) -> bool:
        return (self.module_available and self.test_module_available and
                self.import_valid and not self.syntax_error and self.error is None)

    def to_dict(self) -> dict[str, Any]:
        return {"spec": self.spec.to_dict(), "module_available": self.module_available,
                "test_module_available": self.test_module_available, "import_valid": self.import_valid,
                "passed": self.passed, "error": self.error, "source_path": self.source_path,
                "test_files": list(self.test_files), "syntax_error": self.syntax_error}

@dataclass(frozen=True)
class RegressionReport:
    schema_version: str
    decision: RegressionDecision
    reason: RegressionReason
    total_layers: int
    passed_layers: int
    failed_layers: int
    results: tuple[RegressionLayerResult, ...]
    fingerprint: str
    fail_closed: bool
    metrics: Mapping[str, int]
    policy_schema: str
    provenance_fingerprint: str
    compatibility: CompatibilityStatus

    @property
    def ready(self) -> bool:
        return (self.decision == RegressionDecision.READY and self.failed_layers == 0
                and not self.fail_closed and self.compatibility == CompatibilityStatus.SUPPORTED)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "decision": self.decision.value,
                "reason": self.reason.value, "total_layers": self.total_layers,
                "passed_layers": self.passed_layers, "failed_layers": self.failed_layers,
                "results": [x.to_dict() for x in self.results], "fingerprint": self.fingerprint,
                "fail_closed": self.fail_closed, "ready": self.ready,
                "metrics": dict(self.metrics), "policy_schema": self.policy_schema,
                "provenance_fingerprint": self.provenance_fingerprint,
                "compatibility": self.compatibility.value}


def _canonical_specs() -> tuple[RegressionLayerSpec, ...]:
    return tuple(
        RegressionLayerSpec(
            spec.layer_number,
            spec.name,
            spec.core_module_name,
            f"{spec.package_name}.tests",
            spec.directory,
            spec.core_file,
            spec.test_glob,
        ) for spec in RegressionRegistry.SPECS
    )


class RegressionLayerEngine:
    SCHEMA_VERSION = "1.0"
    PACKAGE = "AUTONOMY_ENGINE.continuity.acrl"
    LAYER_SPECS = _canonical_specs()

    @classmethod
    def canonicalize(cls, value: Any) -> str:
        from .regression_identity import canonicalize
        return canonicalize(value)

    @classmethod
    def fingerprint(cls, value: Any) -> str:
        return fingerprint(value)

    @classmethod
    def validate_manifest(cls) -> None:
        try:
            RegressionRegistry.validate()
            for spec in cls.LAYER_SPECS:
                validate_layer_spec_fields(spec.layer_number, spec.name,
                                           spec.directory or "", spec.core_file or "", spec.test_glob)
        except ValueError as exc:
            raise RegressionLayerIntegrityError(str(exc)) from exc

    @classmethod
    def _acrl_root(cls) -> Path:
        return Path(__file__).resolve().parent.parent

    @classmethod
    def _parse_file(cls, path: Path) -> str | None:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            return f"{type(exc).__name__}: {exc}"
        return None

    @classmethod
    def validate_layer(cls, spec: RegressionLayerSpec, acrl_root: Path | None = None) -> RegressionLayerResult:
        if not isinstance(spec, RegressionLayerSpec):
            raise RegressionLayerValidationError("Invalid regression layer specification.")
        if spec.directory and spec.core_file:
            base = (acrl_root or cls._acrl_root()) / spec.directory
            core = base / spec.core_file
            tests = tuple(sorted(base.glob(spec.test_glob))) if base.is_dir() else tuple()
            if not base.is_dir():
                return RegressionLayerResult(spec, False, False, False, "Layer directory missing.", str(core), tuple())
            if not core.is_file():
                return RegressionLayerResult(spec, False, bool(tests), False, "Layer core file missing.", str(core), tuple(map(str, tests)))
            if not tests:
                return RegressionLayerResult(spec, True, False, False, "No T14 regression test files discovered.", str(core), tuple())
            errors = []
            core_error = cls._parse_file(core)
            if core_error:
                errors.append(f"Core syntax: {core_error}")
            for test in tests:
                err = cls._parse_file(test)
                if err:
                    errors.append(f"Test syntax ({test.name}): {err}")
            return RegressionLayerResult(spec, True, True, not errors, " | ".join(errors) or None,
                                         str(core), tuple(map(str, tests)), bool(errors))
        raise RegressionLayerValidationError("Canonical layer metadata is required.")

    @classmethod
    def build_report(cls, results: Iterable[RegressionLayerResult]) -> RegressionReport:
        normalized = tuple(results)
        policy = RegressionPolicy()
        provenance = RegressionProvenance()
        try:
            policy.validate(); provenance.validate()
        except ValueError as exc:
            raise RegressionLayerIntegrityError(str(exc)) from exc
        failed = tuple(x for x in normalized if not x.passed)
        metrics_obj = summarize(normalized)
        data = {"schema_version": cls.SCHEMA_VERSION, "results": [x.to_dict() for x in normalized]}
        report_fp = fingerprint_manifest(data)
        provenance_fp = fingerprint(provenance.__dict__)
        compatibility = compare_schema(cls.SCHEMA_VERSION, policy.schema_version)
        reason = RegressionReason.SYNTAX_FAILURE if any(x.syntax_error for x in failed) else (RegressionReason.MISSING_LAYER if failed else RegressionReason.VALID)
        decision = RegressionDecision.FAIL_CLOSED if failed else RegressionDecision.READY
        return RegressionReport(cls.SCHEMA_VERSION, decision, reason, len(normalized), len(normalized)-len(failed),
                                len(failed), normalized, report_fp, bool(failed),
                                {"total_layers": metrics_obj.total_layers, "passed_layers": metrics_obj.passed_layers,
                                 "failed_layers": metrics_obj.failed_layers, "total_test_files": metrics_obj.total_test_files,
                                 "syntax_failures": metrics_obj.syntax_failures},
                                policy.schema_version, provenance_fp, compatibility)

    @classmethod
    def validate_all_layers(cls, acrl_root: Path | None = None) -> RegressionReport:
        cls.validate_manifest()
        results = tuple(cls.validate_layer(spec, acrl_root=acrl_root) for spec in cls.LAYER_SPECS)
        return cls.build_report(results)

    @classmethod
    def assert_ready(cls, report: RegressionReport) -> RegressionReport:
        if not isinstance(report, RegressionReport):
            raise RegressionLayerValidationError("Invalid regression report.")
        if not report.ready:
            raise RegressionLayerIntegrityError("ACRL regression layer is not ready.")
        return report

    @classmethod
    def build_pytest_targets(cls) -> tuple[str, ...]:
        cls.validate_manifest()
        return tuple(f"{spec.directory}" for spec in RegressionRegistry.SPECS)


def validate_acrl_regression() -> RegressionReport:
    return RegressionLayerEngine.validate_all_layers()


def acrl_regression_ready(report: RegressionReport) -> bool:
    if not isinstance(report, RegressionReport):
        raise RegressionLayerValidationError("Invalid regression report.")
    return report.ready


__all__ = [x for x in globals() if not x.startswith("_")]
