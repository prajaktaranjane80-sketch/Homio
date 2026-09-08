"""ACRL T14 core regression tests."""
from __future__ import annotations

from pathlib import Path
import pytest

from .regression_layer import (
    RegressionDecision,
    RegressionLayerEngine,
    RegressionLayerIntegrityError,
    RegressionLayerSpec,
    RegressionLayerValidationError,
    RegressionReason,
    acrl_regression_ready,
    validate_acrl_regression,
)


def make_tree(root: Path, *, bad_test: bool = False) -> None:
    for spec in RegressionLayerEngine.LAYER_SPECS:
        directory = root / spec.directory
        directory.mkdir(parents=True)
        (directory / spec.core_file).write_text("x = 1\n", encoding="utf-8")
        (directory / "test_core.py").write_text(
            "def test_core():\n    assert True\n", encoding="utf-8"
        )
    if bad_test:
        (root / "T12_Resume_Safety_Validation" / "test_bad.py").write_text(
            "def broken(:\n", encoding="utf-8"
        )


def test_manifest_is_canonical_and_contiguous() -> None:
    numbers = [x.layer_number for x in RegressionLayerEngine.LAYER_SPECS]
    assert numbers == list(range(1, 15))
    assert RegressionLayerEngine.LAYER_SPECS[11].directory == "T12_Resume_Safety_Validation"
    assert RegressionLayerEngine.LAYER_SPECS[12].directory == "T13_Controller_Integration"
    assert RegressionLayerEngine.LAYER_SPECS[13].directory == "T14_Full_Regression"


def test_manifest_validation() -> None:
    RegressionLayerEngine.validate_manifest()


def test_full_tree_is_ready(tmp_path: Path) -> None:
    make_tree(tmp_path)
    report = RegressionLayerEngine.validate_all_layers(tmp_path)
    assert report.decision is RegressionDecision.READY
    assert report.reason is RegressionReason.VALID
    assert report.ready
    assert report.total_layers == 14
    assert report.passed_layers == 14
    assert report.failed_layers == 0
    assert report.fail_closed is False
    assert report.metrics["total_layers"] == 14
    assert report.metrics["syntax_failures"] == 0


def test_syntax_failure_is_fail_closed(tmp_path: Path) -> None:
    make_tree(tmp_path, bad_test=True)
    report = RegressionLayerEngine.validate_all_layers(tmp_path)
    assert report.decision is RegressionDecision.FAIL_CLOSED
    assert report.reason is RegressionReason.SYNTAX_FAILURE
    assert report.fail_closed
    assert not report.ready


def test_missing_layer_is_fail_closed(tmp_path: Path) -> None:
    make_tree(tmp_path)
    target = tmp_path / "T07_New_Chat_Bootstrap"
    for child in target.iterdir():
        child.unlink()
    target.rmdir()
    report = RegressionLayerEngine.validate_all_layers(tmp_path)
    assert report.fail_closed
    assert not report.ready


def test_missing_tests_is_fail_closed(tmp_path: Path) -> None:
    make_tree(tmp_path)
    for spec in RegressionLayerEngine.LAYER_SPECS:
        (tmp_path / spec.directory / "test_core.py").unlink()
    report = RegressionLayerEngine.validate_all_layers(tmp_path)
    assert report.fail_closed


def test_repeated_validation_has_stable_identity(tmp_path: Path) -> None:
    make_tree(tmp_path)
    first = validate_acrl_regression() if False else RegressionLayerEngine.validate_all_layers(tmp_path)
    second = RegressionLayerEngine.validate_all_layers(tmp_path)
    assert first.fingerprint == second.fingerprint


def test_pytest_targets_are_layer_directories() -> None:
    targets = RegressionLayerEngine.build_pytest_targets()
    assert len(targets) == 14
    assert targets[0] == "T01_Project_DNA"
    assert targets[-1] == "T14_Full_Regression"


def test_invalid_spec_is_rejected() -> None:
    with pytest.raises(RegressionLayerValidationError):
        RegressionLayerEngine.validate_layer(object())


def test_failed_report_is_not_ready() -> None:
    spec = RegressionLayerSpec(
        1, "X", "bad.module", "bad.tests", "T01_Project_DNA", "missing.py"
    )
    result = RegressionLayerEngine.validate_layer(spec, acrl_root=Path("/tmp/definitely-missing"))
    report = RegressionLayerEngine.build_report((result,))
    assert report.decision is RegressionDecision.FAIL_CLOSED
    assert acrl_regression_ready(report) is False
    with pytest.raises(RegressionLayerIntegrityError):
        RegressionLayerEngine.assert_ready(report)


def test_report_serializes() -> None:
    report = RegressionLayerEngine.build_report(())
    data = report.to_dict()
    assert "metrics" in data
    assert "policy_schema" in data
    assert "provenance_fingerprint" in data
    assert "compatibility" in data
