from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from .oidc_config import OIDCConfigurationError, OIDCSettings
from .oidc_verifier import AuthenticationError, OIDCVerifier

ISSUER = "https://identity.example.test/"
AUDIENCE = "homio-api"
SETTINGS = OIDCSettings(ISSUER, AUDIENCE, "https://identity.example.test/jwks")


class FakeJwksClient:
    def __init__(self, key, fail=False):
        self.key, self.fail, self.calls = key, fail, 0

    def get_signing_key_from_jwt(self, token):
        self.calls += 1
        if self.fail:
            raise RuntimeError("sensitive provider detail")
        return SimpleNamespace(key=self.key)


@pytest.fixture(scope="module")
def rsa_pair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private, private.public_key()


@pytest.fixture
def verifier(rsa_pair):
    client = FakeJwksClient(rsa_pair[1])
    return OIDCVerifier(SETTINGS, client), client, rsa_pair[0]


def mint(key, algorithm="RS256", **changes):
    now = int(time.time())
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": "provider-subject",
        "iat": now, "exp": now + 300,
        "email": "user@example.test", "email_verified": True,
    }
    for name, value in changes.items():
        if value is None:
            claims.pop(name, None)
        else:
            claims[name] = value
    return jwt.encode(claims, key, algorithm=algorithm, headers={"kid": "test-key"})


def test_valid_rs256(verifier):
    instance, _, key = verifier
    principal = instance.verify_access_token(mint(key))
    assert principal.subject == "provider-subject"
    assert principal.audiences == (AUDIENCE,)
    assert principal.email_verified is True


def test_valid_es256():
    key = ec.generate_private_key(ec.SECP256R1())
    principal = OIDCVerifier(SETTINGS, FakeJwksClient(key.public_key())).verify_access_token(
        mint(key, algorithm="ES256")
    )
    assert principal.subject == "provider-subject"


@pytest.mark.parametrize("changes", [
    {"iss": "https://attacker.example.test/"},
    {"aud": "other-api"},
    {"exp": int(time.time()) - 60, "iat": int(time.time()) - 120},
    {"nbf": int(time.time()) + 120},
    {"sub": None},
])
def test_invalid_claims_rejected(verifier, changes):
    instance, _, key = verifier
    with pytest.raises(AuthenticationError):
        instance.verify_access_token(mint(key, **changes))


def test_bad_signature_rejected(verifier):
    instance, _, _ = verifier
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthenticationError):
        instance.verify_access_token(mint(other))


def test_hs256_rejected_before_key_lookup(verifier):
    instance, client, _ = verifier
    token = mint("long-test-secret-that-is-not-used-as-a-real-key", algorithm="HS256")
    with pytest.raises(AuthenticationError, match="unsupported_token_algorithm"):
        instance.verify_access_token(token)
    assert client.calls == 0


def test_malformed_or_oversized_rejected(verifier):
    instance, client, _ = verifier
    for token in ("", "not-a-jwt", " " + "a.b.c", "x" * 16_385):
        with pytest.raises(AuthenticationError):
            instance.verify_access_token(token)
    assert client.calls == 0


def test_jwks_failure_fails_closed(rsa_pair):
    instance = OIDCVerifier(SETTINGS, FakeJwksClient(rsa_pair[1], fail=True))
    with pytest.raises(AuthenticationError, match="verification_key_unavailable") as exc:
        instance.verify_access_token(mint(rsa_pair[0]))
    assert "sensitive provider detail" not in str(exc.value)


def test_configuration_fails_closed():
    with pytest.raises(OIDCConfigurationError):
        OIDCSettings.from_env({})
    with pytest.raises(OIDCConfigurationError):
        OIDCSettings("http://identity.test/", AUDIENCE, "https://identity.test/jwks")


def test_multiple_audiences_preserved(verifier):
    instance, _, key = verifier
    principal = instance.verify_access_token(mint(key, aud=[AUDIENCE, "other-resource"]))
    assert principal.audiences == (AUDIENCE, "other-resource")