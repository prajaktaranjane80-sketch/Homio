"""ACRL T13 — Controller Integration Identity."""

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .controller_integration import ControllerIntegrationRequest


@dataclass(frozen=True)
class ControllerIdentity:
    identity_version: str
    schema_version: str
    authority: str
    request_fingerprint: str
    fingerprint: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_version": self.identity_version,
            "schema_version": self.schema_version,
            "authority": self.authority,
            "request_fingerprint": self.request_fingerprint,
            "fingerprint": self.fingerprint,
            "algorithm": self.algorithm,
        }


class ControllerIdentityEngine:
    IDENTITY_VERSION = "T13-IDENTITY-1.0"
    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @staticmethod
    def _canonical(payload: Any) -> str:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def fingerprint_request(
        cls,
        request: ControllerIntegrationRequest,
    ) -> str:
        if not isinstance(request, ControllerIntegrationRequest):
            raise TypeError(
                "request must be a ControllerIntegrationRequest."
            )

        canonical = cls._canonical(request.to_dict())
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def build(
        cls,
        request: ControllerIntegrationRequest,
    ) -> ControllerIdentity:
        request_fingerprint = cls.fingerprint_request(request)

        payload = {
            "identity_version": cls.IDENTITY_VERSION,
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "request_fingerprint": request_fingerprint,
            "algorithm": cls.ALGORITHM,
        }

        fingerprint = hashlib.sha256(
            cls._canonical(payload).encode("utf-8")
        ).hexdigest()

        return ControllerIdentity(
            identity_version=cls.IDENTITY_VERSION,
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            request_fingerprint=request_fingerprint,
            fingerprint=fingerprint,
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def validate(cls, identity: ControllerIdentity) -> bool:
        if not isinstance(identity, ControllerIdentity):
            raise TypeError("identity must be a ControllerIdentity.")

        if identity.identity_version != cls.IDENTITY_VERSION:
            raise ValueError("Unsupported T13 identity version.")

        if identity.schema_version != cls.SCHEMA_VERSION:
            raise ValueError("Unsupported T13 schema version.")

        if identity.authority != cls.AUTHORITY:
            raise ValueError("Invalid T13 identity authority.")

        if identity.algorithm != cls.ALGORITHM:
            raise ValueError("Unsupported fingerprint algorithm.")

        if (
            not isinstance(identity.request_fingerprint, str)
            or len(identity.request_fingerprint) != 64
        ):
            raise ValueError("Invalid request fingerprint.")

        payload = {
            "identity_version": identity.identity_version,
            "schema_version": identity.schema_version,
            "authority": identity.authority,
            "request_fingerprint": identity.request_fingerprint,
            "algorithm": identity.algorithm,
        }

        expected = hashlib.sha256(
            cls._canonical(payload).encode("utf-8")
        ).hexdigest()

        if expected != identity.fingerprint:
            raise ValueError("T13 identity fingerprint mismatch.")

        return True