import pytest

from .continuity_models import (
    ContinuityRequest,
)
from .continuity_policy import (
    ContinuityPolicy,
)
from .continuity_validation import (
    validate_request,
)


def make_request():
    return ContinuityRequest(
        recovery_id="recovery-1",
        project_id="HOMIO",
        source_resolution_id="resolution-1",
        expected_project_fingerprint="a" * 64,
        expected_state_fingerprint="b" * 64,
        expected_branch="reos-development",
        expected_commit_sha="c" * 40,
        evidence_ids=("ev1",),
        recovery_nonce="nonce",
    )


def test_valid_request():
    validate_request(
        make_request(),
        ContinuityPolicy(),
    )


def test_invalid_commit():
    request = make_request()

    invalid = ContinuityRequest(
        recovery_id=request.recovery_id,
        project_id=request.project_id,
        source_resolution_id=request.source_resolution_id,
        expected_project_fingerprint=(
            request.expected_project_fingerprint
        ),
        expected_state_fingerprint=(
            request.expected_state_fingerprint
        ),
        expected_branch=request.expected_branch,
        expected_commit_sha="bad",
        evidence_ids=request.evidence_ids,
        recovery_nonce=request.recovery_nonce,
    )

    with pytest.raises(ValueError):
        validate_request(
            invalid,
            ContinuityPolicy(),
        )
