from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit


class OIDCConfigurationError(ValueError):
    """Required OIDC trust configuration is missing or unsafe."""


def _https_url(name: str, value: str) -> str:
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme.lower() == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
        _ = parsed.port
    except ValueError as exc:
        raise OIDCConfigurationError(f"{name} must be a valid HTTPS URL") from exc
    if not valid:
        raise OIDCConfigurationError(
            f"{name} must be HTTPS without credentials, query or fragment"
        )
    return value


@dataclass(frozen=True, slots=True)
class OIDCSettings:
    issuer: str
    audience: str
    jwks_url: str
    leeway_seconds: int = 30

    def __post_init__(self) -> None:
        if not isinstance(self.issuer, str) or not self.issuer or self.issuer != self.issuer.strip():
            raise OIDCConfigurationError("HOMIO_OIDC_ISSUER is required")
        _https_url("HOMIO_OIDC_ISSUER", self.issuer)

        if not isinstance(self.jwks_url, str) or not self.jwks_url or self.jwks_url != self.jwks_url.strip():
            raise OIDCConfigurationError("HOMIO_OIDC_JWKS_URL is required")
        _https_url("HOMIO_OIDC_JWKS_URL", self.jwks_url)

        if (
            not isinstance(self.audience, str)
            or not self.audience
            or self.audience != self.audience.strip()
            or len(self.audience) > 512
            or any(ord(char) < 0x21 for char in self.audience)
        ):
            raise OIDCConfigurationError("HOMIO_OIDC_AUDIENCE is invalid")

        if type(self.leeway_seconds) is not int or not 0 <= self.leeway_seconds <= 120:
            raise OIDCConfigurationError("leeway_seconds must be between 0 and 120")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "OIDCSettings":
        source = os.environ if environ is None else environ
        names = ("HOMIO_OIDC_ISSUER", "HOMIO_OIDC_AUDIENCE", "HOMIO_OIDC_JWKS_URL")
        values = {name: source.get(name, "").strip() for name in names}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise OIDCConfigurationError("Missing configuration: " + ", ".join(missing))
        return cls(
            issuer=values["HOMIO_OIDC_ISSUER"],
            audience=values["HOMIO_OIDC_AUDIENCE"],
            jwks_url=values["HOMIO_OIDC_JWKS_URL"],
        )