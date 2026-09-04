from dataclasses import dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class ResumeIdentity:
    schema_version: str
    authority: str
    request_fingerprint: str
    decision: str
    identity_version: str
    identity_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "request_fingerprint": self.request_fingerprint,
            "decision": self.decision,
            "identity_version": self.identity_version,
            "identity_fingerprint": self.identity_fingerprint,
        }


class ResumeIdentityEngine:
    IDENTITY_VERSION = "T12-IDENTITY-1.0"
    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"
    ALGORITHM = "sha256"

    @classmethod
    def _canonicalize(cls, value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def fingerprint(cls, value: Any) -> str:
        payload = cls._canonicalize(value).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def build(
        cls,
        request_fingerprint: str,
        decision: str,
    ) -> ResumeIdentity:
        if not isinstance(request_fingerprint, str):
            raise TypeError("Request fingerprint must be a string.")

        if len(request_fingerprint) != 64:
            raise ValueError("Request fingerprint must be a SHA-256 fingerprint.")

        if not isinstance(decision, str) or not decision:
            raise ValueError("Decision must be a non-empty string.")

        identity_payload = {
            "schema_version": cls.SCHEMA_VERSION,
            "authority": cls.AUTHORITY,
            "request_fingerprint": request_fingerprint,
            "decision": decision,
            "identity_version": cls.IDENTITY_VERSION,
        }

        identity_fingerprint = cls.fingerprint(identity_payload)

        return ResumeIdentity(
            schema_version=cls.SCHEMA_VERSION,
            authority=cls.AUTHORITY,
            request_fingerprint=request_fingerprint,
            decision=decision,
            identity_version=cls.IDENTITY_VERSION,
            identity_fingerprint=identity_fingerprint,
        )

    @classmethod
    def validate(cls, identity: ResumeIdentity) -> bool:
        if not isinstance(identity, ResumeIdentity):
            return False

        if identity.schema_version != cls.SCHEMA_VERSION:
            return False

        if identity.authority != cls.AUTHORITY:
            return False

        if identity.identity_version != cls.IDENTITY_VERSION:
            return False

        if len(identity.request_fingerprint) != 64:
            return False

        if len(identity.identity_fingerprint) != 64:
            return False

        expected = cls.build(
            identity.request_fingerprint,
            identity.decision,
        )

        return expected.identity_fingerprint == identity.identity_fingerprint