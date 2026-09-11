from dataclasses import dataclass
from enum import Enum

import pytest

from .checkpoint_authorization import (
    validate_authorization,
)


class Decision(Enum):
    AUTHORIZE = "AUTHORIZE"


@dataclass
class Authorization:
    decision: Decision
    execution_authorized: bool
    state_mutated: bool
    authorization_fingerprint: str


def test_valid_authorization():
    authorization = Authorization(
        decision=Decision.AUTHORIZE,
        execution_authorized=True,
        state_mutated=False,
        authorization_fingerprint="a" * 64,
    )

    validate_authorization(
        authorization,
        expected_fingerprint="a" * 64,
        expected_nonce="nonce",
    )


def test_wrong_fingerprint_is_blocked():
    authorization = Authorization(
        decision=Decision.AUTHORIZE,
        execution_authorized=True,
        state_mutated=False,
        authorization_fingerprint="a" * 64,
    )

    with pytest.raises(ValueError):
        validate_authorization(
            authorization,
            expected_fingerprint="b" * 64,
            expected_nonce="nonce",
        )
