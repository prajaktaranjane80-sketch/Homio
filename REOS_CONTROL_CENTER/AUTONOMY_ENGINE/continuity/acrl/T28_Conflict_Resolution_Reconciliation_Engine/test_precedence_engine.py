from precedence_engine import precedence
from reconciliation_models import ConflictKind


def test_identity_has_highest_precedence():
    assert precedence(ConflictKind.IDENTITY_CONFLICT) > precedence(
        ConflictKind.STATE_MISMATCH
    )
