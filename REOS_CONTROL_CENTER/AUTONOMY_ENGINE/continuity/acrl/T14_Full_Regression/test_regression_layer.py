"""ACRL T14 — Complete Test & Regression Layer tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.regression_layer import (
    RegressionDecision,
    RegressionLayerEngine,
    RegressionLayerIntegrityError,
    RegressionLayerSpec,
    RegressionLayerValidationError,
    RegressionReason,
    acrl_regression_ready,
    validate_acrl_regression,
)


def test_manifest_contains_fourteen_layers() -> None:
    assert (
        len(RegressionLayerEngine.LAYER_SPECS)
        == 14
    )


def test_manifest_is_contiguous() -> None:
    numbers = [
        spec.layer_number
        for spec in RegressionLayerEngine.LAYER_SPECS
    ]

    assert numbers == list(range(1, 15))


def test_manifest_names_are_unique() -> None:
    names = [
        spec.module_name
        for spec in RegressionLayerEngine.LAYER_SPECS
    ]

    assert len(names) == len(set(names))


def test_manifest_test_names_are_unique() -> None:
    names = [
        spec.test_module_name
        for spec in RegressionLayerEngine.LAYER_SPECS
    ]

    assert len(names) == len(set(names))


def test_t01_is_present() -> None:
    assert (
        RegressionLayerEngine.LAYER_SPECS[0]
        .name
        == "Project DNA"
    )


def test_t13_is_present() -> None:
    spec = RegressionLayerEngine.LAYER_SPECS[12]

    assert (
        spec.name
        == "Controller Integration"
    )


def test_t14_is_present() -> None:
    spec = RegressionLayerEngine.LAYER_SPECS[13]

    assert (
        spec.name
        == "Complete Test & Regression Layer"
    )


def test_manifest_validation_passes() -> None:
    RegressionLayerEngine.validate_manifest()


def test_all_layers_can_be_imported() -> None:
    report = (
        RegressionLayerEngine
        .validate_all_layers()
    )

    assert report.failed_layers == 0


def test_all_layer_tests_can_be_imported() -> None:
    report = (
        RegressionLayerEngine
        .validate_all_layers()
    )

    assert all(
        result.test_module_available
        for result in report.results
    )


def test_all_layer_modules_are_importable() -> None:
    report = (
        RegressionLayerEngine
        .validate_all_layers()
    )

    assert all(
        result.module_available
        for result in report.results
    )


def test_report_is_ready() -> None:
    report = validate_acrl_regression()

    assert report.decision == (
        RegressionDecision.READY
    )


def test_report_reason_is_valid() -> None:
    report = validate_acrl_regression()

    assert report.reason == (
        RegressionReason.VALID
    )


def test_report_has_zero_failures() -> None:
    report = validate_acrl_regression()

    assert report.failed_layers == 0


def test_report_has_fourteen_layers() -> None:
    report = validate_acrl_regression()

    assert report.total_layers == 14


def test_report_all_layers_pass() -> None:
    report = validate_acrl_regression()

    assert report.passed_layers == 14


def test_report_is_not_fail_closed() -> None:
    report = validate_acrl_regression()

    assert report.fail_closed is False


def test_regression_ready_helper() -> None:
    report = validate_acrl_regression()

    assert acrl_regression_ready(
        report
    ) is True


def test_report_is_deterministic() -> None:
    first = validate_acrl_regression()
    second = validate_acrl_regression()

    assert (
        first.fingerprint
        == second.fingerprint
    )


def test_fingerprint_is_sha256() -> None:
    report = validate_acrl_regression()

    assert len(report.fingerprint) == 64


def test_report_serializes() -> None:
    report = validate_acrl_regression()

    data = report.to_dict()

    assert data["schema_version"] == "1.0"
    assert data["decision"] == "READY"
    assert data["reason"] == "VALID"
    assert data["ready"] is True


def test_layer_result_count_matches_manifest() -> None:
    report = validate_acrl_regression()

    assert (
        len(report.results)
        == len(
            RegressionLayerEngine.LAYER_SPECS
        )
    )


def test_each_result_passes() -> None:
    report = validate_acrl_regression()

    assert all(
        result.passed
        for result in report.results
    )


def test_layer_numbers_match_results() -> None:
    report = validate_acrl_regression()

    actual = [
        result.spec.layer_number
        for result in report.results
    ]

    expected = list(range(1, 15))

    assert actual == expected


def test_pytest_targets_are_deterministic() -> None:
    first = (
        RegressionLayerEngine
        .build_pytest_targets()
    )
    second = (
        RegressionLayerEngine
        .build_pytest_targets()
    )

    assert first == second


def test_pytest_target_count() -> None:
    targets = (
        RegressionLayerEngine
        .build_pytest_targets()
    )

    assert len(targets) == 14


def test_pytest_targets_are_test_files() -> None:
    targets = (
        RegressionLayerEngine
        .build_pytest_targets()
    )

    assert all(
        target.endswith(".py")
        for target in targets
    )


def test_invalid_spec_is_rejected() -> None:
    with pytest.raises(
        RegressionLayerValidationError
    ):
        RegressionLayerEngine.validate_layer(
            object()
        )


def test_invalid_report_is_rejected() -> None:
    with pytest.raises(
        RegressionLayerValidationError
    ):
        acrl_regression_ready(object())


def test_assert_ready_accepts_valid_report() -> None:
    report = validate_acrl_regression()

    result = (
        RegressionLayerEngine.assert_ready(
            report
        )
    )

    assert result is report


def test_failed_result_produces_fail_closed_report() -> None:
    spec = RegressionLayerSpec(
        layer_number=99,
        name="Synthetic Failure",
        module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "module_that_does_not_exist"
        ),
        test_module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "test_module_that_does_not_exist"
        ),
    )

    result = (
        RegressionLayerEngine.validate_layer(
            spec
        )
    )

    report = RegressionLayerEngine.build_report(
        (result,)
    )

    assert (
        report.decision
        == RegressionDecision.FAIL_CLOSED
    )

    assert report.fail_closed is True
    assert report.failed_layers == 1


def test_failed_report_is_not_ready() -> None:
    spec = RegressionLayerSpec(
        layer_number=99,
        name="Synthetic Failure",
        module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "module_that_does_not_exist"
        ),
        test_module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "test_module_that_does_not_exist"
        ),
    )

    result = (
        RegressionLayerEngine.validate_layer(
            spec
        )
    )

    report = RegressionLayerEngine.build_report(
        (result,)
    )

    assert acrl_regression_ready(
        report
    ) is False


def test_failed_report_assert_ready_rejects() -> None:
    spec = RegressionLayerSpec(
        layer_number=99,
        name="Synthetic Failure",
        module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "module_that_does_not_exist"
        ),
        test_module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "test_module_that_does_not_exist"
        ),
    )

    result = (
        RegressionLayerEngine.validate_layer(
            spec
        )
    )

    report = RegressionLayerEngine.build_report(
        (result,)
    )

    with pytest.raises(
        RegressionLayerIntegrityError
    ):
        RegressionLayerEngine.assert_ready(
            report
        )


def test_result_error_is_present_on_import_failure() -> None:
    spec = RegressionLayerSpec(
        layer_number=99,
        name="Synthetic Failure",
        module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "module_that_does_not_exist"
        ),
        test_module_name=(
            "AUTONOMY_ENGINE.continuity.acrl."
            "test_module_that_does_not_exist"
        ),
    )

    result = (
        RegressionLayerEngine.validate_layer(
            spec
        )
    )

    assert result.error is not None


def test_no_project_execution_is_authorized() -> None:
    report = validate_acrl_regression()

    # T14 is a verification/readiness layer only.
    # A regression report must never itself grant execution authority.
    assert not hasattr(
        report,
        "execution_authorized",
    )

    assert not hasattr(
        report,
        "execute",
    )

    assert not hasattr(
        report,
        "execute_project",
    )


def test_manifest_does_not_duplicate_controller_logic() -> None:
    spec = RegressionLayerEngine.LAYER_SPECS[12]

    assert (
        spec.module_name.endswith(
            "controller_integration"
        )
    )

    assert (
        spec.test_module_name.endswith(
            "test_controller_integration"
        )
    )


def test_t14_is_additive_module() -> None:
    spec = RegressionLayerEngine.LAYER_SPECS[13]

    assert (
        spec.module_name.endswith(
            "regression_layer"
        )
    )


def test_t14_has_its_own_test_module() -> None:
    spec = RegressionLayerEngine.LAYER_SPECS[13]

    assert (
        spec.test_module_name.endswith(
            "test_regression_layer"
        )
    )


def test_full_manifest_fingerprint_is_stable() -> None:
    manifest = [
        spec.to_dict()
        for spec in RegressionLayerEngine.LAYER_SPECS
    ]

    first = RegressionLayerEngine.fingerprint(
        manifest
    )

    second = RegressionLayerEngine.fingerprint(
        manifest
    )

    assert first == second


def test_regression_report_contains_all_layer_results() -> None:
    report = validate_acrl_regression()

    numbers = {
        result.spec.layer_number
        for result in report.results
    }

    assert numbers == set(range(1, 15))


def test_ready_report_requires_zero_failed_layers() -> None:
    report = validate_acrl_regression()

    assert report.ready is (
        report.failed_layers == 0
        and report.decision
        == RegressionDecision.READY
        and not report.fail_closed
    )