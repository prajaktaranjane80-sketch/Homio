
from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from .oidc_config import OIDCSettings
from .oidc_verifier import AuthenticationError, OIDCVerifier


ISSUER = "https://identity.example.test/"
AUDIENCE = "homio-api"

SETTINGS = OIDCSettings(
    ISSUER,
    AUDIENCE,
    "https://identity.example.test/jwks",
)


class FakeJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return SimpleNamespace(key=self.key)


@pytest.fixture
def rsa_pair():
    private = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private, private.public_key()


def mint(key, *, iat=None, exp=None):
    now = int(time.time())

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "provider-subject",
        "client_id": "homio-frontend",
        "jti": "access-token-unique-id",
        "iat": now if iat is None else iat,
        "exp": now + 300 if exp is None else exp,
    }

    token = jwt.encode(
        claims,
        key,
        algorithm="RS256",
        headers={
            "kid": "test-key",
            "typ": "at+jwt",
        },
    )

    return token, claims


def test_verified_access_token_exposes_exact_verified_iat_and_exp(
    rsa_pair,
):
    private, public = rsa_pair
    token, claims = mint(private)

    principal = OIDCVerifier(
        SETTINGS,
        FakeJwksClient(public),
    ).verify_access_token(token)

    assert principal.issued_at_epoch_seconds == claims["iat"]
    assert principal.expires_at_epoch_seconds == claims["exp"]


@pytest.mark.parametrize(
    ("claim_name", "claim_value"),
    [
        ("iat", time.time() - 5.5),
        ("exp", time.time() + 300.5),
    ],
)
def test_access_token_rejects_fractional_numeric_dates(
    rsa_pair,
    claim_name,
    claim_value,
):
    private, public = rsa_pair
    claims = {claim_name: claim_value}
    token, _ = mint(private, **claims)

    with pytest.raises(
        AuthenticationError,
        match="invalid_access_token",
    ):
        OIDCVerifier(
            SETTINGS,
            FakeJwksClient(public),
        ).verify_access_token(token)


def test_access_token_rejects_expiration_not_after_issue_time(
    rsa_pair,
):
    private, public = rsa_pair
    now = int(time.time())

    # Both claims are inside the verifier's configured clock leeway.
    # The invalid relationship must still be rejected.
    token, _ = mint(
        private,
        iat=now + 20,
        exp=now + 10,
    )

    with pytest.raises(
        AuthenticationError,
        match="invalid_access_token",
    ):
        OIDCVerifier(
            SETTINGS,
            FakeJwksClient(public),
        ).verify_access_token(token)
