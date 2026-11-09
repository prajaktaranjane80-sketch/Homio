from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from .oidc_config import OIDCSettings


MAX_ACCESS_TOKEN_CHARS = 16_384
MAX_SUBJECT_CHARS = 255
MAX_CLIENT_ID_CHARS = 512
MAX_TOKEN_ID_CHARS = 255

ALLOWED_SIGNING_ALGORITHMS = ("RS256", "ES256")
ALLOWED_ACCESS_TOKEN_TYPES = frozenset(
    {
        "at+jwt",
        "application/at+jwt",
    }
)


class AuthenticationError(RuntimeError):
    """Safe, non-sensitive authentication failure code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    """Verified identity and access-token revocation identifiers.

    token_id is the verified RFC 9068 jti claim.
    client_id is the verified OAuth client identifier.

    The raw bearer token is deliberately not retained in this object.
    """

    issuer: str
    subject: str
    audiences: tuple[str, ...]
    client_id: str
    token_id: str
    email: str | None = None
    email_verified: bool = False


class SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class OIDCVerifier:
    """Fail-closed RFC 9068 JWT access-token verifier.

    This verifier deliberately rejects ordinary OpenID Connect ID tokens.
    It accepts only signed JWT access tokens using the RFC 9068 token type,
    trusted issuer, configured API audience and required access-token claims.
    """

    def __init__(
        self,
        settings: OIDCSettings,
        jwks_client: SigningKeyClient | None = None,
    ) -> None:
        self._settings = settings
        self._jwks_client = jwks_client or PyJWKClient(
            settings.jwks_url,
            cache_keys=True,
            lifespan=300,
            timeout=5,
        )

    @staticmethod
    def _validate_access_token_header(header: object) -> str:
        if not isinstance(header, dict):
            raise AuthenticationError("malformed_access_token")

        algorithm = header.get("alg")

        if algorithm not in ALLOWED_SIGNING_ALGORITHMS:
            raise AuthenticationError("unsupported_token_algorithm")

        token_type = header.get("typ")

        if (
            not isinstance(token_type, str)
            or token_type.lower() not in ALLOWED_ACCESS_TOKEN_TYPES
        ):
            raise AuthenticationError("invalid_access_token_type")

        if "crit" in header:
            raise AuthenticationError("unsupported_critical_token_header")

        kid = header.get("kid")

        if (
            not isinstance(kid, str)
            or not kid
            or len(kid) > MAX_TOKEN_ID_CHARS
            or kid.strip() != kid
        ):
            raise AuthenticationError("invalid_signing_key_id")

        return algorithm

    @staticmethod
    def _validate_required_access_token_claims(
        claims: object,
    ) -> tuple[str, str, str, tuple[str, ...]]:
        if not isinstance(claims, dict):
            raise AuthenticationError("invalid_access_token")

        subject = claims.get("sub")
        client_id = claims.get("client_id")
        token_id = claims.get("jti")
        raw_audience = claims.get("aud")

        if (
            not isinstance(subject, str)
            or not subject.strip()
            or len(subject) > MAX_SUBJECT_CHARS
        ):
            raise AuthenticationError("invalid_access_token")

        if (
            not isinstance(client_id, str)
            or not client_id
            or client_id.strip() != client_id
            or len(client_id) > MAX_CLIENT_ID_CHARS
        ):
            raise AuthenticationError("invalid_access_token")

        if (
            not isinstance(token_id, str)
            or not token_id
            or token_id.strip() != token_id
            or len(token_id) > MAX_TOKEN_ID_CHARS
        ):
            raise AuthenticationError("invalid_access_token")

        if isinstance(raw_audience, str) and raw_audience:
            audiences = (raw_audience,)
        elif (
            isinstance(raw_audience, list)
            and raw_audience
            and all(
                isinstance(item, str)
                and item
                and item.strip() == item
                for item in raw_audience
            )
        ):
            audiences = tuple(raw_audience)
        else:
            raise AuthenticationError("invalid_access_token")

        return subject, client_id, token_id, audiences

    def verify_access_token(
        self,
        token: str,
    ) -> AuthenticatedPrincipal:
        if (
            not isinstance(token, str)
            or not token
            or token != token.strip()
            or len(token) > MAX_ACCESS_TOKEN_CHARS
            or token.count(".") != 2
        ):
            raise AuthenticationError("malformed_access_token")

        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:
            raise AuthenticationError(
                "malformed_access_token"
            ) from exc

        self._validate_access_token_header(header)

        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(
                token
            ).key
        except Exception as exc:
            raise AuthenticationError(
                "verification_key_unavailable"
            ) from exc

        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=list(ALLOWED_SIGNING_ALGORITHMS),
                issuer=self._settings.issuer,
                audience=self._settings.audience,
                leeway=self._settings.leeway_seconds,
                options={
                    "require": [
                        "exp",
                        "iat",
                        "iss",
                        "aud",
                        "sub",
                        "client_id",
                        "jti",
                    ],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            )
        except PyJWTError as exc:
            raise AuthenticationError(
                "invalid_access_token"
            ) from exc

        subject, client_id, token_id, audiences = (
            self._validate_required_access_token_claims(claims)
        )

        if self._settings.audience not in audiences:
            raise AuthenticationError("invalid_access_token")

        raw_email = claims.get("email")
        email: str | None = None

        if (
            isinstance(raw_email, str)
            and 0 < len(raw_email) <= 254
            and raw_email.strip() == raw_email
            and not any(ord(char) < 32 for char in raw_email)
        ):
            email = raw_email

        return AuthenticatedPrincipal(
            issuer=self._settings.issuer,
            subject=subject,
            audiences=audiences,
            client_id=client_id,
            token_id=token_id,
            email=email,
            email_verified=claims.get("email_verified") is True,
        )
