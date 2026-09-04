from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ResumePolicy:
    version: str
    authority: str
    require_authority: bool
    require_integrity: bool
    architecture_drift_fails_closed: bool
    ambiguous_state_fails_closed: bool
    unsafe_recovery_blocks_resume: bool
    stale_state_blocks_resume: bool
    allow_execution: bool
    allow_state_mutation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "authority": self.authority,
            "require_authority": self.require_authority,
            "require_integrity": self.require_integrity,
            "architecture_drift_fails_closed": self.architecture_drift_fails_closed,
            "ambiguous_state_fails_closed": self.ambiguous_state_fails_closed,
            "unsafe_recovery_blocks_resume": self.unsafe_recovery_blocks_resume,
            "stale_state_blocks_resume": self.stale_state_blocks_resume,
            "allow_execution": self.allow_execution,
            "allow_state_mutation": self.allow_state_mutation,
        }


class ResumePolicyEngine:
    POLICY_VERSION = "T12-POLICY-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def default(cls) -> ResumePolicy:
        return ResumePolicy(
            version=cls.POLICY_VERSION,
            authority=cls.AUTHORITY,
            require_authority=True,
            require_integrity=True,
            architecture_drift_fails_closed=True,
            ambiguous_state_fails_closed=True,
            unsafe_recovery_blocks_resume=True,
            stale_state_blocks_resume=True,
            allow_execution=False,
            allow_state_mutation=False,
        )

    @classmethod
    def validate(cls, policy: ResumePolicy) -> bool:
        if not isinstance(policy, ResumePolicy):
            return False

        if policy.version != cls.POLICY_VERSION:
            return False

        if policy.authority != cls.AUTHORITY:
            return False

        if not policy.require_authority:
            return False

        if not policy.require_integrity:
            return False

        if policy.architecture_drift_fails_closed is not True:
            return False

        if policy.ambiguous_state_fails_closed is not True:
            return False

        if policy.unsafe_recovery_blocks_resume is not True:
            return False

        if policy.stale_state_blocks_resume is not True:
            return False

        if policy.allow_execution:
            return False

        if policy.allow_state_mutation:
            return False

        return True

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ResumePolicy:
        if not isinstance(value, Mapping):
            raise TypeError("Resume policy must be a mapping.")

        policy = ResumePolicy(
            version=str(value.get("version", "")),
            authority=str(value.get("authority", "")),
            require_authority=bool(value.get("require_authority", False)),
            require_integrity=bool(value.get("require_integrity", False)),
            architecture_drift_fails_closed=bool(
                value.get("architecture_drift_fails_closed", False)
            ),
            ambiguous_state_fails_closed=bool(
                value.get("ambiguous_state_fails_closed", False)
            ),
            unsafe_recovery_blocks_resume=bool(
                value.get("unsafe_recovery_blocks_resume", False)
            ),
            stale_state_blocks_resume=bool(
                value.get("stale_state_blocks_resume", False)
            ),
            allow_execution=bool(value.get("allow_execution", True)),
            allow_state_mutation=bool(value.get("allow_state_mutation", True)),
        )

        if not cls.validate(policy):
            raise ValueError("Invalid or unsafe resume policy.")

        return policy