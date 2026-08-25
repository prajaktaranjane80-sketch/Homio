from __future__ import annotations

from dataclasses import replace

import pytest

from execution.production_execution_contract import (
    ProductionAuthority,
    ProductionExecutionBlockReason,
    ProductionExecutionRequest,
    ProductionExecutionResult,
    ProductionExecutionStatus,
    ProductionExecutorIdentity,
    validate_production_request,
    validate_production_result,
)


def make_authority() -> ProductionAuthority:
    return ProductionAuthority(
        controller_name="REOS_CONTROL_CENTER",
        controller_root=r"D:\HOMIO\REOS_CONTROL_CENTER",
        authority_token="authoritative-controller-boundary",
        authority_version="v1",
    )


def make_executor() -> ProductionExecutorIdentity:
    return ProductionExecutorIdentity(
        executor_name="REOS_CONTROLLER_EXECUTOR",
        executor_version="R3",
        executor_type="controller",
        executor_fingerprint="test-executor-fingerprint",
    )


def make_request() -> ProductionExecutionRequest:
    return ProductionExecutionRequest(
        action_id="action-001",
        attempt_id="attempt-001",
        action="COMPLETE_SUBTASK",
        target="REOS_CONTROL_CENTER",
        authority=make_authority(),
        executor=make_executor(),
        parameters={"subtask": "ARCH001-T01"},
        evidence={"source": "test"},
    )


def make_result(
    *,
    executed: bool = False,
    allowed: bool = False,
    status: ProductionExecutionStatus = ProductionExecutionStatus.BLOCKED,
    block_reason: ProductionExecutionBlockReason | None = None,
) -> ProductionExecutionResult:
    return ProductionExecutionResult(
        action_id="action-001",
        attempt_id="attempt-001",
        status=status,
        executed=executed,
        allowed=allowed,
        reason="test result",
        block_reason=block_reason,
        executor_name="REOS_CONTROLLER_EXECUTOR",
        authority_version="v1",
        evidence={"test": True},
    )


def test_valid_production_request_passes() -> None:
    valid, errors = validate_production_request(make_request())

    assert valid is True
    assert errors == ()


def test_request_validation_is_side_effect_free() -> None:
    request = make_request()

    before = request.to_dict()
    valid, errors = validate_production_request(request)
    after = request.to_dict()

    assert valid is True
    assert errors == ()
    assert before == after


def test_non_request_object_is_rejected_fail_closed() -> None:
    valid, errors = validate_production_request(object())  # type: ignore[arg-type]

    assert valid is False
    assert errors == (
        ProductionExecutionBlockReason.INVALID_CONTRACT.value,
    )


def test_missing_action_id_is_rejected() -> None:
    request = replace(make_request(), action_id="")

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.ACTION_ID_MISSING.value in errors


def test_missing_attempt_id_is_rejected() -> None:
    request = replace(make_request(), attempt_id="")

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.ATTEMPT_ID_MISSING.value in errors


def test_missing_action_is_rejected() -> None:
    request = replace(make_request(), action="")

    valid, errors = validate_production_request(request)

    assert valid is False
    assert "action is required." in errors


def test_missing_target_is_rejected() -> None:
    request = replace(make_request(), target="")

    valid, errors = validate_production_request(request)

    assert valid is False
    assert "target is required." in errors


def test_missing_authority_is_rejected() -> None:
    request = replace(make_request(), authority=None)

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.AUTHORITY_MISSING.value in errors


def test_invalid_authority_object_is_rejected() -> None:
    request = replace(
        make_request(),
        authority="fake-authority",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.AUTHORITY_INVALID.value in errors


@pytest.mark.parametrize(
    "field",
    [
        "controller_name",
        "controller_root",
        "authority_token",
        "authority_version",
    ],
)
def test_incomplete_authority_is_rejected(field: str) -> None:
    authority = make_authority()
    broken = replace(authority, **{field: ""})
    request = replace(make_request(), authority=broken)

    valid, errors = validate_production_request(request)

    assert valid is False
    assert any(field in error for error in errors)


def test_missing_executor_is_rejected() -> None:
    request = replace(make_request(), executor=None)

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.EXECUTOR_MISSING.value in errors


def test_invalid_executor_object_is_rejected() -> None:
    request = replace(
        make_request(),
        executor="fake-executor",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert ProductionExecutionBlockReason.EXECUTOR_INVALID.value in errors


@pytest.mark.parametrize(
    "field",
    [
        "executor_name",
        "executor_version",
        "executor_type",
        "executor_fingerprint",
    ],
)
def test_incomplete_executor_identity_is_rejected(field: str) -> None:
    executor = make_executor()
    broken = replace(executor, **{field: ""})
    request = replace(make_request(), executor=broken)

    valid, errors = validate_production_request(request)

    assert valid is False
    assert any(field in error for error in errors)


def test_non_mapping_parameters_are_rejected() -> None:
    request = replace(
        make_request(),
        parameters=["not", "a", "mapping"],  # type: ignore[arg-type]
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert "parameters must be a mapping." in errors


def test_non_mapping_evidence_is_rejected() -> None:
    request = replace(
        make_request(),
        evidence=["not", "a", "mapping"],  # type: ignore[arg-type]
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert "evidence must be a mapping." in errors


def test_request_status_must_be_contract_enum() -> None:
    request = replace(
        make_request(),
        status="EXECUTED",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert "status must be a ProductionExecutionStatus." in errors


def test_production_request_is_immutable() -> None:
    request = make_request()

    with pytest.raises(AttributeError):
        request.action_id = "tampered"  # type: ignore[misc]


def test_authority_is_immutable() -> None:
    authority = make_authority()

    with pytest.raises(AttributeError):
        authority.authority_token = "forged"  # type: ignore[misc]


def test_executor_identity_is_immutable() -> None:
    executor = make_executor()

    with pytest.raises(AttributeError):
        executor.executor_fingerprint = "forged"  # type: ignore[misc]


def test_valid_blocked_result_passes() -> None:
    result = make_result(
        executed=False,
        allowed=False,
        status=ProductionExecutionStatus.BLOCKED,
        block_reason=ProductionExecutionBlockReason.EXECUTOR_MISSING,
    )

    valid, errors = validate_production_result(result)

    assert valid is True
    assert errors == ()


def test_valid_executed_result_passes() -> None:
    result = make_result(
        executed=True,
        allowed=True,
        status=ProductionExecutionStatus.EXECUTED,
    )

    valid, errors = validate_production_result(result)

    assert valid is True
    assert errors == ()


def test_non_result_object_is_rejected_fail_closed() -> None:
    valid, errors = validate_production_result(object())  # type: ignore[arg-type]

    assert valid is False
    assert errors == (
        ProductionExecutionBlockReason.RESULT_INVALID.value,
    )


def test_executed_result_cannot_be_disallowed() -> None:
    result = make_result(
        executed=True,
        allowed=False,
        status=ProductionExecutionStatus.EXECUTED,
    )

    valid, errors = validate_production_result(result)

    assert valid is False
    assert "executed cannot be true when allowed is false." in errors


def test_result_action_id_is_required() -> None:
    result = replace(make_result(), action_id="")

    valid, errors = validate_production_result(result)

    assert valid is False
    assert ProductionExecutionBlockReason.ACTION_ID_MISSING.value in errors


def test_result_attempt_id_is_required() -> None:
    result = replace(make_result(), attempt_id="")

    valid, errors = validate_production_result(result)

    assert valid is False
    assert ProductionExecutionBlockReason.ATTEMPT_ID_MISSING.value in errors


def test_result_status_must_be_contract_enum() -> None:
    result = replace(
        make_result(),
        status="EXECUTED",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_result(result)

    assert valid is False
    assert "status must be a ProductionExecutionStatus." in errors


def test_result_executed_must_be_boolean() -> None:
    result = replace(
        make_result(),
        executed="yes",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_result(result)

    assert valid is False
    assert "executed must be boolean." in errors


def test_result_allowed_must_be_boolean() -> None:
    result = replace(
        make_result(),
        allowed="yes",  # type: ignore[arg-type]
    )

    valid, errors = validate_production_result(result)

    assert valid is False
    assert "allowed must be boolean." in errors


def test_result_evidence_must_be_mapping() -> None:
    result = replace(
        make_result(),
        evidence=["tampered"],  # type: ignore[arg-type]
    )

    valid, errors = validate_production_result(result)

    assert valid is False
    assert "evidence must be a mapping." in errors


def test_production_result_is_immutable() -> None:
    result = make_result()

    with pytest.raises(AttributeError):
        result.executed = True  # type: ignore[misc]


def test_request_to_dict_is_json_contract_shape() -> None:
    request = make_request()

    payload = request.to_dict()

    assert payload["action_id"] == "action-001"
    assert payload["attempt_id"] == "attempt-001"
    assert payload["authority"]["controller_name"] == "REOS_CONTROL_CENTER"
    assert payload["executor"]["executor_name"] == "REOS_CONTROLLER_EXECUTOR"
    assert payload["status"] == "PROPOSED"


def test_result_to_dict_is_json_contract_shape() -> None:
    result = make_result(
        executed=True,
        allowed=True,
        status=ProductionExecutionStatus.EXECUTED,
    )

    payload = result.to_dict()

    assert payload["action_id"] == "action-001"
    assert payload["attempt_id"] == "attempt-001"
    assert payload["status"] == "EXECUTED"
    assert payload["executed"] is True
    assert payload["allowed"] is True


def test_authority_token_is_recorded_but_does_not_grant_authority() -> None:
    authority = make_authority()

    assert authority.authority_token
    assert authority.validate()[0] is True


def test_executor_fingerprint_is_required_for_identity_provenance() -> None:
    executor = make_executor()

    assert executor.executor_fingerprint
    assert executor.validate()[0] is True


def test_contract_does_not_execute_anything_during_validation() -> None:
    request = make_request()
    executed = False

    valid, errors = validate_production_request(request)

    assert valid is True
    assert errors == ()
    assert executed is False


def test_invalid_request_accumulates_multiple_failures() -> None:
    request = ProductionExecutionRequest(
        action_id="",
        attempt_id="",
        action="",
        target="",
        authority=None,
        executor=None,
        parameters=[],
        evidence=[],
    )

    valid, errors = validate_production_request(request)

    assert valid is False
    assert len(errors) >= 7
    assert ProductionExecutionBlockReason.ACTION_ID_MISSING.value in errors
    assert ProductionExecutionBlockReason.ATTEMPT_ID_MISSING.value in errors
    assert ProductionExecutionBlockReason.AUTHORITY_MISSING.value in errors
    assert ProductionExecutionBlockReason.EXECUTOR_MISSING.value in errors


def test_contract_has_no_implicit_execution_permission() -> None:
    request = make_request()

    valid, errors = validate_production_request(request)

    assert valid is True
    assert errors == ()
    assert request.status is ProductionExecutionStatus.PROPOSED


def test_failed_result_can_be_valid_when_execution_was_not_successful() -> None:
    result = make_result(
        executed=False,
        allowed=False,
        status=ProductionExecutionStatus.FAILED,
    )

    valid, errors = validate_production_result(result)

    assert valid is True
    assert errors == ()


def test_block_reason_is_serialized_as_machine_value() -> None:
    result = make_result(
        executed=False,
        allowed=False,
        status=ProductionExecutionStatus.BLOCKED,
        block_reason=ProductionExecutionBlockReason.AUTHORITY_MISSING,
    )

    payload = result.to_dict()

    assert payload["block_reason"] == "AUTHORITY_MISSING"