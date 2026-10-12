from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from .oidc_config import OIDCSettings

MAX_ACCESS_TOKEN_CHARS = 16_384
ALLOWED_SIGNING_ALGORITHMS = ("RS256", "ES256")


class AuthenticationError(RuntimeError):
    """Safe, non-sensitive authentication failure code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    issuer: str
    subject: str
    audiences: tuple[str, ...]
    email: str | None = None
    email_verified: bool = False


class SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class OIDCVerifier:
    """Fail-closed OIDC bearer-token verifier."""

    def __init__(self, settings: OIDCSettings, jwks_client: SigningKeyClient | None = None) -> None:
        self._settings = settings
        self._jwks_client = jwks_client or PyJWKClient(
            settings.jwks_url, cache_keys=True, lifespan=300, timeout=5
        )

    def verify_access_token(self, token: str) -> AuthenticatedPrincipal:
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
            raise AuthenticationError("malformed_access_token") from exc

        if header.get("alg") not in ALLOWED_SIGNING_ALGORITHMS:
            raise AuthenticationError("unsupported_token_algorithm")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid or len(kid) > 255:
            raise AuthenticationError("invalid_signing_key_id")

        try:
            key = self._jwks_client.get_signing_key_from_jwt(token).key
        except Exception as exc:
            raise AuthenticationError("verification_key_unavailable") from exc

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=list(ALLOWED_SIGNING_ALGORITHMS),
                issuer=self._settings.issuer,
                audience=self._settings.audience,
                leeway=self._settings.leeway_seconds,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except PyJWTError as exc:
            raise AuthenticationError("invalid_access_token") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError("invalid_access_token")

        raw_audience = claims.get("aud")
        if isinstance(raw_audience, str):
            audiences = (raw_audience,)
        elif isinstance(raw_audience, list) and all(
            isinstance(item, str) and item for item in raw_audience
        ):
            audiences = tuple(raw_audience)
        else:
            raise AuthenticationError("invalid_access_token")

        if self._settings.audience not in audiences:
            raise AuthenticationError("invalid_access_token")

        raw_email = claims.get("email")
        email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None
        return AuthenticatedPrincipal(
            issuer=self._settings.issuer,
            subject=subject,
            audiences=audiences,
            email=email,
            email_verified=claims.get("email_verified") is True,
        )