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
CLIENT_ID = "homio-frontend"

SETTINGS = OIDCSettings(
    ISSUER,
    AUDIENCE,
    "https://identity.example.test/jwks",
)


class FakeJwksClient:
    def __init__(self, key, fail=False):
        self.key = key
        self.fail = fail
        self.calls = 0

    def get_signing_key_from_jwt(self, token):
        self.calls += 1

        if self.fail:
            raise RuntimeError("sensitive provider detail")

        return SimpleNamespace(key=self.key)


@pytest.fixture(scope="module")
def rsa_pair():
    private = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private, private.public_key()


@pytest.fixture
def verifier(rsa_pair):
    client = FakeJwksClient(rsa_pair[1])
    return OIDCVerifier(SETTINGS, client), client, rsa_pair[0]


def mint(
    key,
    algorithm="RS256",
    token_type="at+jwt",
    **changes,
):
    now = int(time.time())

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "provider-subject",
        "client_id": CLIENT_ID,
        "jti": "access-token-unique-id",
        "iat": now,
        "exp": now + 300,
        "email": "user@example.test",
        "email_verified": True,
    }

    for name, value in changes.items():
        if value is None:
            claims.pop(name, None)
        else:
            claims[name] = value

    headers = {
        "kid": "test-key",
    }

    if token_type is not None:
        headers["typ"] = token_type

    return jwt.encode(
        claims,
        key,
        algorithm=algorithm,
        headers=headers,
    )


def test_valid_rs256_access_token(verifier):
    instance, _, key = verifier

    principal = instance.verify_access_token(mint(key))

    assert principal.issuer == ISSUER
    assert principal.subject == "provider-subject"
    assert principal.audiences == (AUDIENCE,)
    assert principal.email_verified is True


def test_valid_es256_access_token():
    key = ec.generate_private_key(ec.SECP256R1())

    principal = OIDCVerifier(
        SETTINGS,
        FakeJwksClient(key.public_key()),
    ).verify_access_token(
        mint(key, algorithm="ES256")
    )

    assert principal.subject == "provider-subject"


@pytest.mark.parametrize(
    "token_type",
    [
        None,
        "JWT",
        "application/jwt",
        "id+jwt",
        "",
        " at+jwt",
        "at+jwt ",
    ],
)
def test_non_access_token_types_are_rejected_before_key_lookup(
    verifier,
    token_type,
):
    instance, client, key = verifier

    token = mint(
        key,
        token_type=token_type,
    )

    with pytest.raises(
        AuthenticationError,
        match="invalid_access_token_type",
    ):
        instance.verify_access_token(token)

    assert client.calls == 0


@pytest.mark.parametrize(
    "token_type",
    [
        "at+jwt",
        "at+JWT",
        "application/at+jwt",
        "APPLICATION/AT+JWT",
    ],
)
def test_rfc9068_access_token_media_types_are_accepted(
    verifier,
    token_type,
):
    instance, _, key = verifier

    principal = instance.verify_access_token(
        mint(
            key,
            token_type=token_type,
        )
    )

    assert principal.subject == "provider-subject"


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://attacker.example.test/"},
        {"aud": "other-api"},
        {
            "exp": int(time.time()) - 60,
            "iat": int(time.time()) - 120,
        },
        {"nbf": int(time.time()) + 120},
        {"sub": None},
        {"client_id": None},
        {"jti": None},
        {"client_id": ""},
        {"jti": ""},
        {"client_id": " invalid "},
        {"jti": " invalid "},
        {"client_id": 123},
        {"jti": 123},
        {"client_id": "x" * 513},
        {"jti": "x" * 256},
    ],
)
def test_invalid_or_missing_access_token_claims_are_rejected(
    verifier,
    changes,
):
    instance, _, key = verifier

    with pytest.raises(AuthenticationError):
        instance.verify_access_token(
            mint(key, **changes)
        )


def test_id_token_shaped_jwt_is_rejected(verifier):
    instance, client, key = verifier

    # ID tokens normally use typ=JWT (or omit typ). Even if someone
    # accidentally gives an ID token the API audience, it must not pass
    # the RFC 9068 access-token type check.
    token = mint(
        key,
        token_type="JWT",
        client_id=CLIENT_ID,
    )

    with pytest.raises(
        AuthenticationError,
        match="invalid_access_token_type",
    ):
        instance.verify_access_token(token)

    assert client.calls == 0


def test_bad_signature_is_rejected(verifier):
    instance, _, _ = verifier

    other = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with pytest.raises(AuthenticationError):
        instance.verify_access_token(
            mint(other)
        )


def test_hs256_is_rejected_before_key_lookup(verifier):
    instance, client, _ = verifier

    token = mint(
        "long-test-secret-that-is-not-used-as-a-real-key",
        algorithm="HS256",
    )

    with pytest.raises(
        AuthenticationError,
        match="unsupported_token_algorithm",
    ):
        instance.verify_access_token(token)

    assert client.calls == 0


def test_critical_jose_headers_are_rejected_before_key_lookup(verifier):
    instance, client, key = verifier

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "provider-subject",
        "client_id": CLIENT_ID,
        "jti": "access-token-unique-id",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
    }

    token = jwt.encode(
        claims,
        key,
        algorithm="RS256",
        headers={
            "kid": "test-key",
            "typ": "at+jwt",
            "crit": ["unknown-extension"],
            "unknown-extension": True,
        },
    )

    # PyJWT rejects an unsupported critical JOSE extension while parsing
    # the unverified header. OIDCVerifier deliberately normalizes that
    # parser failure to malformed_access_token. Both outcomes fail closed.
    with pytest.raises(
        AuthenticationError,
        match="malformed_access_token",
    ):
        instance.verify_access_token(token)

    # The invalid header must be rejected before any JWKS lookup.
    assert client.calls == 0


def test_malformed_or_oversized_tokens_are_rejected(verifier):
    instance, client, _ = verifier

    for token in (
        "",
        "not-a-jwt",
        " " + "a.b.c",
        "x" * 16_385,
    ):
        with pytest.raises(AuthenticationError):
            instance.verify_access_token(token)

    assert client.calls == 0


def test_jwks_failure_fails_closed(rsa_pair):
    instance = OIDCVerifier(
        SETTINGS,
        FakeJwksClient(
            rsa_pair[1],
            fail=True,
        ),
    )

    with pytest.raises(
        AuthenticationError,
        match="verification_key_unavailable",
    ) as exc:
        instance.verify_access_token(
            mint(rsa_pair[0])
        )

    assert "sensitive provider detail" not in str(exc.value)


def test_configuration_fails_closed():
    with pytest.raises(OIDCConfigurationError):
        OIDCSettings.from_env({})

    with pytest.raises(OIDCConfigurationError):
        OIDCSettings(
            "http://identity.test/",
            AUDIENCE,
            "https://identity.test/jwks",
        )


def test_multiple_audiences_are_preserved(verifier):
    instance, _, key = verifier

    principal = instance.verify_access_token(
        mint(
            key,
            aud=[
                AUDIENCE,
                "other-resource",
            ],
        )
    )

    assert principal.audiences == (
        AUDIENCE,
        "other-resource",
    )


def test_email_claim_is_bounded_and_never_used_as_identity_key(verifier):
    instance, _, key = verifier

    principal = instance.verify_access_token(
        mint(
            key,
            email="x" * 255,
        )
    )

    assert principal.subject == "provider-subject"
    assert principal.email is None


def test_access_token_subject_is_not_derived_from_email(verifier):
    instance, _, key = verifier

    principal = instance.verify_access_token(
        mint(
            key,
            sub="canonical-provider-subject",
            email="different@example.test",
        )
    )

    assert principal.subject == "canonical-provider-subject"
