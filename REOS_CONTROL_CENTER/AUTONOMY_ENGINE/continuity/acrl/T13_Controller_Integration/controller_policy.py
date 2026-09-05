"""ACRL T13 — Controller Integration Policy."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerPolicy:
    version: str = "T13-POLICY-1.0"
    authority: str = "REOS_CONTROL_CENTER"

    reconciliation_allowed: bool = True
    resume_authorization_allowed: bool = True

    execution_authorization_allowed: bool = False
    state_mutation_allowed: bool = False
    controller_mutation_allowed: bool = False
    architecture_mutation_allowed: bool = False
    checkpoint_mutation_allowed: bool = False
    authority_promotion_allowed: bool = False
    recovery_execution_allowed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "authority": self.authority,
            "reconciliation_allowed": self.reconciliation_allowed,
            "resume_authorization_allowed": self.resume_authorization_allowed,
            "execution_authorization_allowed": self.execution_authorization_allowed,
            "state_mutation_allowed": self.state_mutation_allowed,
            "controller_mutation_allowed": self.controller_mutation_allowed,
            "architecture_mutation_allowed": self.architecture_mutation_allowed,
            "checkpoint_mutation_allowed": self.checkpoint_mutation_allowed,
            "authority_promotion_allowed": self.authority_promotion_allowed,
            "recovery_execution_allowed": self.recovery_execution_allowed,
        }


class ControllerPolicyEngine:
    POLICY_VERSION = "T13-POLICY-1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    @classmethod
    def default(cls) -> ControllerPolicy:
        return ControllerPolicy(
            version=cls.POLICY_VERSION,
            authority=cls.AUTHORITY,
            reconciliation_allowed=True,
            resume_authorization_allowed=True,
            execution_authorization_allowed=False,
            state_mutation_allowed=False,
            controller_mutation_allowed=False,
            architecture_mutation_allowed=False,
            checkpoint_mutation_allowed=False,
            authority_promotion_allowed=False,
            recovery_execution_allowed=False,
        )

    @classmethod
    def validate(cls, policy: ControllerPolicy) -> bool:
        if not isinstance(policy, ControllerPolicy):
            raise TypeError("policy must be a ControllerPolicy.")

        if policy.version != cls.POLICY_VERSION:
            raise ValueError("Unsupported controller policy version.")

        if policy.authority != cls.AUTHORITY:
            raise ValueError("Controller policy authority is invalid.")

        if not policy.reconciliation_allowed:
            raise ValueError("Controller reconciliation must remain enabled.")

        if not policy.resume_authorization_allowed:
            raise ValueError("Controller resume authorization must remain enabled.")

        forbidden = (
            policy.execution_authorization_allowed,
            policy.state_mutation_allowed,
            policy.controller_mutation_allowed,
            policy.architecture_mutation_allowed,
            policy.checkpoint_mutation_allowed,
            policy.authority_promotion_allowed,
            policy.recovery_execution_allowed,
        )

        if any(forbidden):
            raise ValueError(
                "T13 policy illegally enables a forbidden capability."
            )

        return True