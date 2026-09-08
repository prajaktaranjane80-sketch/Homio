"""
ACRL T15 — Operator Identity.

Deterministic identity and request fingerprinting for T15.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .operator_autonomy import OperatorRequest


@dataclass(frozen=True)
class OperatorIdentity:
    """Immutable identity record for a T15 request."""

    identity_version: str
    schema_version: str
    authority: str
    request_fingerprint: str
    identity_fingerprint: str
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_version": self.identity_version,
            "schema_version": self.schema_version,
            "authority": self.authority,
            "request_fingerprint": self.request_fingerprint,
            "identity_fingerprint": self.identity_fingerprint,
            "algorithm": self.algorithm,
        }


class OperatorIdentityEngine:
    """Deterministic T15 identity engine."""

    IDENTITY_VERSION = "T15-IDENTITY-1.0"
    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @staticmethod
    def canonicalize(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def fingerprint_request(
        cls,
        request: OperatorRequest,
    ) -> str:
        if not isinstance(request, OperatorRequest):
            raise TypeError(
                "request must be an OperatorRequest."
            )

        return hashlib.sha256(
            cls.canonicalize(
                request.to_dict()
            ).encode("utf-8")
        ).hexdigest()

    @classmethod
    def build(
        cls,
        request: OperatorRequest,
    ) -> OperatorIdentity:
        request_fingerprint = cls.fingerprint_request(request)

        payload = {
            "identity_version": cls.IDENTITY_VERSION,
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "request_fingerprint": request_fingerprint,
            "algorithm": cls.ALGORITHM,
        }

        identity_fingerprint = hashlib.sha256(
            cls.canonicalize(payload).encode("utf-8")
        ).hexdigest()

        return OperatorIdentity(
            identity_version=cls.IDENTITY_VERSION,
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            request_fingerprint=request_fingerprint,
            identity_fingerprint=identity_fingerprint,
            algorithm=cls.ALGORITHM,
        )

    @classmethod
    def validate(
        cls,
        identity: OperatorIdentity,
    ) -> bool:
        if not isinstance(identity, OperatorIdentity):
            raise TypeError(
                "identity must be an OperatorIdentity."
            )

        if identity.identity_version != cls.IDENTITY_VERSION:
            raise ValueError(
                "Unsupported T15 identity version."
            )

        if identity.schema_version != cls.SCHEMA_VERSION:
            raise ValueError(
                "Unsupported T15 schema version."
            )

        if identity.authority != cls.AUTHORITY:
            raise ValueError(
                "Invalid T15 identity authority."
            )

        if identity.algorithm != cls.ALGORITHM:
            raise ValueError(
                "Unsupported T15 identity algorithm."
            )

        if (
            not isinstance(
                identity.request_fingerprint,
                str,
            )
            or len(identity.request_fingerprint) != 64
        ):
            raise ValueError(
                "Invalid T15 request fingerprint."
            )

        expected = hashlib.sha256(
            cls.canonicalize(
                {
                    "identity_version": identity.identity_version,
                    "schema_version": identity.schema_version,
                    "authority": identity.authority,
                    "request_fingerprint": (
                        identity.request_fingerprint
                    ),
                    "algorithm": identity.algorithm,
                }
            ).encode("utf-8")
        ).hexdigest()

        if expected != identity.identity_fingerprint:
            raise ValueError(
                "T15 identity fingerprint mismatch."
            )

        return True


__all__ = [
    "OperatorIdentity",
    "OperatorIdentityEngine",
]
