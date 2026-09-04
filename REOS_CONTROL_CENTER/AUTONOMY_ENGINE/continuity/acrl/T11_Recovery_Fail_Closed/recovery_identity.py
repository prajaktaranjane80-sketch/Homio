"""ACRL T11 — Recovery identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


class RecoveryIdentityError(RuntimeError):
    """Base recovery identity error."""


@dataclass(frozen=True)
class RecoveryIdentity:
    identity_version: str
    schema_version: str
    authority: str
    request_fingerprint: str
    decision: str
    identity_fingerprint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "identity_version": self.identity_version,
            "schema_version": self.schema_version,
            "authority": self.authority,
            "request_fingerprint": self.request_fingerprint,
            "decision": self.decision,
            "identity_fingerprint": self.identity_fingerprint,
        }


class RecoveryIdentityEngine:
    """Creates deterministic identity for recovery decisions."""

    IDENTITY_VERSION = "T11-IDENTITY-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @classmethod
    def _canonicalize(cls, value: Any) -> str:
        try:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as exc:
            raise RecoveryIdentityError(
                "Recovery identity input cannot be canonicalized."
            ) from exc

    @classmethod
    def _fingerprint(cls, value: Any) -> str:
        return hashlib.sha256(
            cls._canonicalize(value).encode("utf-8")
        ).hexdigest()

    @classmethod
    def build(
        cls,
        *,
        schema_version: str,
        authority: str,
        request_fingerprint: str,
        decision: str,
    ) -> RecoveryIdentity:
        if authority != cls.AUTHORITY:
            raise RecoveryIdentityError(
                "Invalid recovery identity authority."
            )

        if len(request_fingerprint) != 64:
            raise RecoveryIdentityError(
                "Invalid request fingerprint."
            )

        payload = {
            "identity_version": cls.IDENTITY_VERSION,
            "schema_version": schema_version,
            "authority": authority,
            "request_fingerprint": request_fingerprint,
            "decision": decision,
        }

        identity_fingerprint = cls._fingerprint(payload)

        return RecoveryIdentity(
            identity_version=cls.IDENTITY_VERSION,
            schema_version=schema_version,
            authority=authority,
            request_fingerprint=request_fingerprint,
            decision=decision,
            identity_fingerprint=identity_fingerprint,
        )

    @classmethod
    def validate(
        cls,
        identity: RecoveryIdentity,
    ) -> bool:
        if not isinstance(
            identity,
            RecoveryIdentity,
        ):
            raise RecoveryIdentityError(
                "Invalid recovery identity."
            )

        if identity.identity_version != cls.IDENTITY_VERSION:
            raise RecoveryIdentityError(
                "Unsupported recovery identity version."
            )

        if identity.authority != cls.AUTHORITY:
            raise RecoveryIdentityError(
                "Invalid recovery identity authority."
            )

        expected = cls.build(
            schema_version=identity.schema_version,
            authority=identity.authority,
            request_fingerprint=identity.request_fingerprint,
            decision=identity.decision,
        )

        if (
            expected.identity_fingerprint
            != identity.identity_fingerprint
        ):
            raise RecoveryIdentityError(
                "Recovery identity fingerprint mismatch."
            )

        return True


__all__ = [
    "RecoveryIdentity",
    "RecoveryIdentityEngine",
    "RecoveryIdentityError",
]