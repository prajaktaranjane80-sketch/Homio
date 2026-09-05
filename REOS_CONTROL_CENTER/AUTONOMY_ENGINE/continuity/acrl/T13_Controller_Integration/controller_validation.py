"""ACRL T13 — Controller Integration Validation.

Structural and defensive validation for T13 integration evidence.

Design rules:
- Validation must not replace T13 integration semantics.
- Semantic conflict conditions are handled by controller_integration.py.
- Invalid metadata remains a validation failure.
- Controller/ACRL authority and integrity states are preserved
for the integration engine to classify where appropriate.
- Validation is read-only and non-mutating.
"""


from collections.abc import Mapping
from typing import Any

from .controller_integration import (
ACRLContinuityView,
ControllerIntegrationReport,
ControllerIntegrationRequest,
ControllerStateView,
)

class ControllerValidationError(ValueError):
    """Raised when T13 integration evidence is structurally invalid."""

class ControllerValidationEngine:
    """Defensive structural validator for T13 integration evidence."""

MAX_METADATA_FIELDS = 64
MAX_KEY_LENGTH = 128
MAX_STRING_LENGTH = 4096

REQUIRED_CONTROLLER_FIELDS = {
    "current_gate",
    "current_subtask",
    "current_task",
    "status",
    "state_hash",
    "architecture_locked",
    "authoritative",
    "checkpoint_id",
}

REQUIRED_ACRL_FIELDS = {
    "current_gate",
    "current_subtask",
    "current_task",
    "checkpoint_id",
    "architecture_locked",
    "authority_valid",
    "integrity_valid",
    "resume_safe",
    "fingerprint",
}

@classmethod
def validate_metadata(
    cls,
    metadata: Mapping[str, Any] | None,
) -> bool:
    """Validate bounded flat metadata without changing semantics."""

    if metadata is None:
        return True

    if not isinstance(metadata, Mapping):
        raise ControllerValidationError(
            "metadata must be a mapping."
        )

    if len(metadata) > cls.MAX_METADATA_FIELDS:
        raise ControllerValidationError(
            "metadata exceeds maximum field count."
        )

    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ControllerValidationError(
                "metadata keys must be strings."
            )

        if len(key) > cls.MAX_KEY_LENGTH:
            raise ControllerValidationError(
                "metadata key exceeds maximum length."
            )

        if (
            isinstance(value, str)
            and len(value) > cls.MAX_STRING_LENGTH
        ):
            raise ControllerValidationError(
                "metadata string value exceeds maximum length."
            )

        if isinstance(
            value,
            (Mapping, list, tuple, set),
        ):
            raise ControllerValidationError(
                "nested metadata structures are not permitted."
            )

    return True

@classmethod
def validate_controller(
    cls,
    controller: ControllerStateView,
) -> bool:
    """Validate controller evidence structurally.

    Empty current_gate/current_task values are structurally valid
    strings and are intentionally preserved for
    controller_integration.py to classify into deterministic
    fail-closed integration decisions.

    Authority is different: a controller explicitly marked as
    non-authoritative is invalid evidence and must be rejected.
    """

    if not isinstance(
        controller,
        ControllerStateView,
    ):
        raise ControllerValidationError(
            "Invalid ControllerStateView."
        )

    for field_name in cls.REQUIRED_CONTROLLER_FIELDS:
        if not hasattr(controller, field_name):
            raise ControllerValidationError(
                f"Missing controller field: {field_name}"
            )

    cls.validate_metadata(controller.metadata)

    if not isinstance(
        controller.current_gate,
        str,
    ):
        raise ControllerValidationError(
            "Controller gate must be a string."
        )

    if (
        controller.current_subtask is not None
        and not isinstance(
            controller.current_subtask,
            str,
        )
    ):
        raise ControllerValidationError(
            "Controller subtask must be a string or None."
        )

    if not isinstance(
        controller.current_task,
        str,
    ):
        raise ControllerValidationError(
            "Controller task must be a string."
        )

    if not isinstance(
        controller.status,
        str,
    ):
        raise ControllerValidationError(
            "Controller status must be a string."
        )

    if (
        controller.state_hash is not None
        and not isinstance(
            controller.state_hash,
            str,
        )
    ):
        raise ControllerValidationError(
            "Controller state_hash must be a string or None."
        )

    if not isinstance(
        controller.architecture_locked,
        bool,
    ):
        raise ControllerValidationError(
            "Controller architecture_locked must be boolean."
        )

    if not isinstance(
        controller.authoritative,
        bool,
    ):
        raise ControllerValidationError(
            "Controller authoritative must be boolean."
        )

    if not controller.authoritative:
        raise ControllerValidationError(
            "Controller authority is invalid."
        )

    if (
        controller.checkpoint_id is not None
        and not isinstance(
            controller.checkpoint_id,
            str,
        )
    ):
        raise ControllerValidationError(
            "Controller checkpoint_id must be a string or None."
        )

    return True

@classmethod
def validate_acrl(
    cls,
    acrl: ACRLContinuityView,
) -> bool:
    """Validate ACRL continuity evidence structurally.

    integrity_valid and resume_safe are semantic state values.
    Their boolean values are preserved so controller_integration.py
    can classify them into deterministic FAIL_CLOSED or BLOCKED
    decisions.

    authority_valid is different: explicitly non-authoritative
    ACRL evidence is rejected as invalid integration evidence.
    """

    if not isinstance(
        acrl,
        ACRLContinuityView,
    ):
        raise ControllerValidationError(
            "Invalid ACRLContinuityView."
        )

    for field_name in cls.REQUIRED_ACRL_FIELDS:
        if not hasattr(acrl, field_name):
            raise ControllerValidationError(
                f"Missing ACRL field: {field_name}"
            )

    cls.validate_metadata(acrl.metadata)

    if not isinstance(
        acrl.current_gate,
        str,
    ):
        raise ControllerValidationError(
            "ACRL gate must be a string."
        )

    if (
        acrl.current_subtask is not None
        and not isinstance(
            acrl.current_subtask,
            str,
        )
    ):
        raise ControllerValidationError(
            "ACRL subtask must be a string or None."
        )

    if (
        acrl.current_task is not None
        and not isinstance(
            acrl.current_task,
            str,
        )
    ):
        raise ControllerValidationError(
            "ACRL task must be a string or None."
        )

    if (
        acrl.checkpoint_id is not None
        and not isinstance(
            acrl.checkpoint_id,
            str,
        )
    ):
        raise ControllerValidationError(
            "ACRL checkpoint_id must be a string or None."
        )

    if not isinstance(
        acrl.architecture_locked,
        bool,
    ):
        raise ControllerValidationError(
            "ACRL architecture_locked must be boolean."
        )

    if not isinstance(
        acrl.authority_valid,
        bool,
    ):
        raise ControllerValidationError(
            "ACRL authority_valid must be boolean."
        )

    if not acrl.authority_valid:
        raise ControllerValidationError(
            "ACRL authority is invalid."
        )

    if not isinstance(
        acrl.integrity_valid,
        bool,
    ):
        raise ControllerValidationError(
            "ACRL integrity_valid must be boolean."
        )

    if not isinstance(
        acrl.resume_safe,
        bool,
    ):
        raise ControllerValidationError(
            "ACRL resume_safe must be boolean."
        )

    if (
        acrl.fingerprint is not None
        and not isinstance(
            acrl.fingerprint,
            str,
        )
    ):
        raise ControllerValidationError(
            "ACRL fingerprint must be a string or None."
        )

    return True

@classmethod
def validate_request(
    cls,
    request: ControllerIntegrationRequest,
) -> bool:
    """Validate T13 request structure without consuming semantics."""

    if not isinstance(
        request,
        ControllerIntegrationRequest,
    ):
        raise ControllerValidationError(
            "Invalid ControllerIntegrationRequest."
        )

    cls.validate_controller(
        request.controller
    )

    cls.validate_acrl(
        request.acrl
    )

    if not isinstance(
        request.expected_authority,
        str,
    ):
        raise ControllerValidationError(
            "expected_authority must be a string."
        )

    return True

@classmethod
def validate_report(
    cls,
    report: ControllerIntegrationReport,
) -> bool:
    """Validate the immutable T13 integration report."""

    if not isinstance(
        report,
        ControllerIntegrationReport,
    ):
        raise ControllerValidationError(
            "Invalid ControllerIntegrationReport."
        )

    required = (
        "schema_version",
        "authority",
        "decision",
        "reason",
        "request_fingerprint",
        "validated",
        "fail_closed",
        "controller_gate",
        "acrl_gate",
        "controller_subtask",
        "acrl_subtask",
        "resume_authorized",
        "execution_authorized",
        "explanation",
    )

    for field_name in required:
        if not hasattr(report, field_name):
            raise ControllerValidationError(
                f"Missing report field: {field_name}"
            )

    if report.authority != "REOS_CONTROL_CENTER":
        raise ControllerValidationError(
            "Invalid report authority."
        )

    if (
        not isinstance(
            report.request_fingerprint,
            str,
        )
        or len(report.request_fingerprint) != 64
    ):
        raise ControllerValidationError(
            "Invalid report fingerprint."
        )

    if report.execution_authorized:
        raise ControllerValidationError(
            "T13 can never authorize execution."
        )

    return True

__all__ = [
    "ControllerValidationEngine",
    "ControllerValidationError",
]

