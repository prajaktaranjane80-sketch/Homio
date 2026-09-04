from collections.abc import Mapping
from typing import Any

from .resume_policy import ResumePolicy, ResumePolicyEngine
from .resume_provenance import ResumeProvenance, ResumeProvenanceEngine


class ResumeValidationError(ValueError):
    pass


class ResumeValidationEngine:
    MAX_METADATA_FIELDS = 64
    MAX_METADATA_KEY_LENGTH = 128
    MAX_METADATA_VALUE_LENGTH = 4096

    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def validate_policy(cls, policy: ResumePolicy) -> bool:
        return ResumePolicyEngine.validate(policy)

    @classmethod
    def validate_provenance(cls, provenance: ResumeProvenance) -> bool:
        return ResumeProvenanceEngine.validate(provenance)

    @classmethod
    def validate_metadata(cls, metadata: Mapping[str, Any] | None) -> bool:
        if metadata is None:
            return True

        if not isinstance(metadata, Mapping):
            return False

        if len(metadata) > cls.MAX_METADATA_FIELDS:
            return False

        for key, value in metadata.items():
            if not isinstance(key, str):
                return False

            if len(key) > cls.MAX_METADATA_KEY_LENGTH:
                return False

            if isinstance(value, str):
                if len(value) > cls.MAX_METADATA_VALUE_LENGTH:
                    return False
            elif isinstance(value, (int, float, bool)) or value is None:
                continue
            elif isinstance(value, (list, tuple)):
                if len(value) > cls.MAX_METADATA_FIELDS:
                    return False
            elif isinstance(value, Mapping):
                if len(value) > cls.MAX_METADATA_FIELDS:
                    return False
            else:
                return False

        return True

    @classmethod
    def validate_authority(cls, authority: str) -> bool:
        return authority == cls.AUTHORITY

    @classmethod
    def validate_fingerprint(cls, fingerprint: str) -> bool:
        if not isinstance(fingerprint, str):
            return False

        if len(fingerprint) != 64:
            return False

        return all(
            character in "0123456789abcdef"
            for character in fingerprint.lower()
        )

    @classmethod
    def validate_request_structure(cls, request: Any) -> bool:
        if request is None:
            return False

        required = (
            "checkpoint_available",
            "checkpoint_valid",
            "state_available",
            "state_valid",
            "gate_available",
            "gate_valid",
            "authority_valid",
            "integrity_valid",
            "architecture_stable",
            "recovery_safe",
        )

        for field in required:
            if not hasattr(request, field):
                return False

        metadata = getattr(request, "metadata", None)

        return cls.validate_metadata(metadata)

    @classmethod
    def validate_report_structure(cls, report: Any) -> bool:
        if report is None:
            return False

        required = (
            "schema_version",
            "authority",
            "decision",
            "reason",
            "request_fingerprint",
            "validated",
            "fail_closed",
            "explanation",
        )

        for field in required:
            if not hasattr(report, field):
                return False

        if not cls.validate_authority(report.authority):
            return False

        if not cls.validate_fingerprint(report.request_fingerprint):
            return False

        return True

    @classmethod
    def validate_request(
        cls,
        request: Any,
        policy: ResumePolicy,
        provenance: ResumeProvenance | None = None,
    ) -> bool:
        if not cls.validate_request_structure(request):
            return False

        if not cls.validate_policy(policy):
            return False

        if provenance is not None and not cls.validate_provenance(provenance):
            return False

        return True

    @classmethod
    def validate_report(cls, report: Any) -> bool:
        if not cls.validate_report_structure(report):
            return False

        if not report.validated:
            return False

        if report.decision == "FAIL_CLOSED" and not report.fail_closed:
            return False

        return True