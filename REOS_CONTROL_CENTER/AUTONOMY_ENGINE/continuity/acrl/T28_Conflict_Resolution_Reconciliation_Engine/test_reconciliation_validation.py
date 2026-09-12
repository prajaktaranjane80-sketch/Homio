import pytest

from reconciliation_models import ReconciliationRequest
from reconciliation_validation import validate_request


def test_request_requires_identity():
    request = ReconciliationRequest(
        reconciliation_id="",
        scheduler_fingerprint="S",
        continuity_fingerprint="C",
        evidence_fingerprint="E",
        policy=__import__(
            "reconciliation_models"
        ).ReconciliationPolicy(),
    )

    with pytest.raises(ValueError):
        validate_request(request)
