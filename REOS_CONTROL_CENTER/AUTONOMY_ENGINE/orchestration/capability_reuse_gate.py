from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

from capability_reuse_guard import (
    CapabilityRecord,
    CapabilityRequest,
    CapabilityReuseGuard,
    ReuseDecision,
    ReuseDecisionResult,
)


CatalogProvider = Callable[[], Iterable[CapabilityRecord]]


@dataclass(frozen=True, slots=True)
class CapabilityReuseOutcome:
    required: bool
    allowed: bool
    decision: ReuseDecision | None
    result: ReuseDecisionResult | None = None
    blockers: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "allowed": self.allowed,
            "decision": (
                self.decision.value
                if self.decision is not None
                else None
            ),
            "result": (
                self.result.to_dict()
                if self.result is not None
                else None
            ),
            "blockers": list(self.blockers),
            "evidence": dict(self.evidence),
        }


class CapabilityReuseGate:
    """
    Execution-boundary adapter for the existing deterministic
    CapabilityReuseGuard.

    This module does not own project state, architecture authority,
    Git, or mutation execution.
    """

    CREATE_OPERATIONS = frozenset(
        {
            "CREATE",
            "CAPABILITY_CREATE",
            "MODULE_CREATE",
        }
    )

    EXTEND_OPERATIONS = frozenset(
        {
            "EXTEND",
            "CAPABILITY_EXTEND",
            "MODULE_EXTEND",
        }
    )

    def __init__(
        self,
        catalog_provider: CatalogProvider,
        *,
        guard: CapabilityReuseGuard | None = None,
    ) -> None:
        if not callable(catalog_provider):
            raise TypeError("catalog_provider must be callable")

        self._catalog_provider = catalog_provider
        self._guard = guard or CapabilityReuseGuard()

    @classmethod
    def from_registry(
        cls,
        registry: Any,
    ) -> "CapabilityReuseGate":
        """
        Adapt the existing CapabilityRegistry.

        CapabilityRegistry remains the existing registry.
        This gate only derives CapabilityRecord objects from it.
        """

        def provider() -> tuple[CapabilityRecord, ...]:
            return tuple(
                CapabilityRecord.from_capability(item)
                for item in registry.all()
            )

        return cls(provider)

    @classmethod
    def required_for(cls, proposal: Any) -> bool:
        parameters = getattr(
            proposal,
            "parameters",
            {},
        )

        if not isinstance(parameters, Mapping):
            return False

        if parameters.get("creates_capability") is True:
            return True

        operation = str(
            parameters.get(
                "capability_operation",
                "",
            )
        ).strip().upper()

        return operation in (
            cls.CREATE_OPERATIONS
            | cls.EXTEND_OPERATIONS
        )

    def request_from_proposal(
        self,
        proposal: Any,
    ) -> CapabilityRequest:
        parameters = getattr(
            proposal,
            "parameters",
            {},
        )

        payload = (
            parameters.get("capability_reuse")
            if isinstance(parameters, Mapping)
            else None
        )

        if not isinstance(payload, Mapping):
            raise ValueError(
                "capability_reuse metadata is required"
            )

        def text(
            name: str,
            *,
            required: bool = True,
        ) -> str:
            value = payload.get(name, "")

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                if required:
                    raise ValueError(
                        f"capability_reuse.{name} is required"
                    )

                return ""

            return value.strip()

        def many(
            name: str,
        ) -> tuple[str, ...]:
            value = payload.get(name, ())

            if isinstance(value, str):
                return (value,)

            if not isinstance(
                value,
                (list, tuple),
            ):
                raise ValueError(
                    f"capability_reuse.{name} "
                    "must be a list or tuple"
                )

            return tuple(
                str(item)
                for item in value
                if str(item).strip()
            )

        return CapabilityRequest(
            capability_id=text(
                "capability_id"
            ),
            name=text("name"),
            description=text(
                "description",
                required=False,
            ),
            responsibility=text(
                "responsibility"
            ),
            architecture_ids=many(
                "architecture_ids"
            ),
            source_of_truth=text(
                "source_of_truth",
                required=False,
            ),
            inputs=many("inputs"),
            outputs=many("outputs"),
            owner=text(
                "owner",
                required=False,
            ),
            allow_create_new=(
                payload.get(
                    "allow_create_new",
                    True,
                )
                is True
            ),
        )

    def evaluate_proposal(
        self,
        proposal: Any,
    ) -> CapabilityReuseOutcome:
        """
        Evaluate one action before mutation.

        For CREATE operations:
            only CREATE_NEW may cross the mutation boundary.

        REUSE / EXTEND / BLOCK therefore stop creation.
        """

        if not self.required_for(proposal):
            return CapabilityReuseOutcome(
                required=False,
                allowed=True,
                decision=None,
                evidence={
                    "reuse_gate": "NOT_REQUIRED",
                },
            )

        try:
            request = self.request_from_proposal(
                proposal
            )

            catalog = tuple(
                self._catalog_provider()
            )

            expected_fingerprint = None

            parameters = getattr(
                proposal,
                "parameters",
                {},
            )

            payload = parameters.get(
                "capability_reuse"
            )

            if isinstance(
                payload,
                Mapping,
            ):
                supplied = payload.get(
                    "catalog_fingerprint"
                )

                if (
                    isinstance(supplied, str)
                    and supplied.strip()
                ):
                    expected_fingerprint = supplied

            result = self._guard.evaluate(
                request,
                catalog,
                expected_catalog_fingerprint=(
                    expected_fingerprint
                ),
            )

            operation = str(
                parameters.get(
                    "capability_operation",
                    "CREATE",
                )
            ).strip().upper()

            if operation in self.CREATE_OPERATIONS:
                allowed = (
                    result.decision
                    == ReuseDecision.CREATE_NEW
                )

                blockers = (
                    ()
                    if allowed
                    else (
                        "reuse_required_before_new_capability_creation",
                    )
                )

            elif operation in self.EXTEND_OPERATIONS:
                allowed = result.decision in {
                    ReuseDecision.REUSE,
                    ReuseDecision.EXTEND,
                }

                blockers = (
                    ()
                    if allowed
                    else (
                        "extend_target_not_found_or_catalog_changed",
                    )
                )

            else:
                allowed = (
                    result.decision
                    != ReuseDecision.BLOCK
                )

                blockers = result.blockers

            return CapabilityReuseOutcome(
                required=True,
                allowed=allowed,
                decision=result.decision,
                result=result,
                blockers=blockers,
                evidence={
                    "reuse_gate": "EVALUATED",
                    "catalog_fingerprint": (
                        result.catalog_fingerprint
                    ),
                    "request_fingerprint": (
                        result.request_fingerprint
                    ),
                },
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            return CapabilityReuseOutcome(
                required=True,
                allowed=False,
                decision=ReuseDecision.BLOCK,
                blockers=(
                    "invalid_capability_reuse_request",
                ),
                evidence={
                    "reuse_gate": "BLOCKED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

    def revalidate(
        self,
        outcome: CapabilityReuseOutcome,
        *,
        current_catalog: (
            Iterable[CapabilityRecord] | None
        ) = None,
    ) -> CapabilityReuseOutcome:
        """
        Revalidate the original decision against the
        latest catalog.

        This provides the TOCTOU protection needed before
        the write/commit boundary.
        """

        if (
            not outcome.required
            or outcome.result is None
        ):
            return outcome

        catalog = (
            tuple(current_catalog)
            if current_catalog is not None
            else tuple(
                self._catalog_provider()
            )
        )

        result = self._guard.revalidate(
            outcome.result,
            catalog,
        )

        allowed = (
            result.decision
            == ReuseDecision.CREATE_NEW
        )

        return CapabilityReuseOutcome(
            required=True,
            allowed=allowed,
            decision=result.decision,
            result=result,
            blockers=(
                ()
                if allowed
                else (
                    "capability_catalog_changed",
                )
            ),
            evidence={
                "reuse_gate": "REVALIDATED",
                "catalog_fingerprint": (
                    result.catalog_fingerprint
                ),
            },
        )


__all__ = [
    "CapabilityReuseGate",
    "CapabilityReuseOutcome",
]
