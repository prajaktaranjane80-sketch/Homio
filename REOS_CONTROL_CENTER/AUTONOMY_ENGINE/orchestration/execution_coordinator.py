"""
Deterministic execution coordinator for AUTONOMY_ENGINE.

This module is an additive orchestration boundary.

Authority model
---------------
- REOS_CONTROL_CENTER remains the authoritative controller.
- This coordinator never becomes a controller.
- This coordinator never mutates controller state directly.
- This coordinator never discovers or invents an executor.
- All mutation execution remains dependency-injected.
- Existing AUTONOMY_ENGINE modules remain unchanged.

Execution model
---------------
ActionProposal
    -> validation
    -> capability-reuse / duplicate protection
    -> approval/policy/risk/guard inputs
    -> enforcement preflight
    -> controlled mutation boundary
    -> authoritative executor
    -> postflight verification
    -> deterministic result

Safety principles
-----------------
- Fail closed.
- Default deny.
- No implicit authorization.
- No implicit capability grant.
- No implicit retry.
- No executor discovery.
- No controller command invention.
- No state.json mutation.
- No mutation before every required gate is positive.
- Failed execution is terminal for the coordinator instance.
- Evidence is preserved.
- Capability/module creation is checked against a fresh repository-derived
  capability catalog before mutation.
- Capability/module creation is checked again immediately before mutation
  to prevent TOCTOU duplicate creation.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from continuity.acrl.T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    FileAuthority,
    RepositoryIntelligenceEngine,
)

from execution.enforcement import EnforcementDecision
from execution.mutation_adapter import (
    ControlledMutationAdapter,
    MutationBlockReason,
    MutationRequest,
    MutationResult,
)

from orchestration.capability_reuse_guard import (
    CapabilityRecord,
    CapabilityRequest,
    CapabilityReuseGuard,
    ReuseDecision,
)

from protocols.action_protocol import (
    ActionProposal,
    ProtocolDecision,
    validate_proposal,
)


class CoordinationStatus(str, Enum):
    """Deterministic lifecycle status of one execution coordination attempt."""

    BLOCKED = "BLOCKED"
    READY = "READY"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class CoordinationBlockReason(str, Enum):
    """Machine-readable coordinator refusal reasons."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    ALREADY_COORDINATED = "ALREADY_COORDINATED"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    MUTATION_BLOCKED = "MUTATION_BLOCKED"
    POSTFLIGHT_BLOCKED = "POSTFLIGHT_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    CAPABILITY_REUSE_BLOCKED = "CAPABILITY_REUSE_BLOCKED"
    CAPABILITY_REUSE_UNAVAILABLE = "CAPABILITY_REUSE_UNAVAILABLE"


@dataclass(frozen=True)
class ExecutionContext:
    """
    Explicit execution authorization context.

    Every safety decision must be supplied by an upstream authority.
    The coordinator never infers missing permissions.
    """

    authorized: bool = False
    capability_available: bool = False
    policy_allowed: bool = False
    risk_allowed: bool = False
    guard_allowed: bool = False
    idempotency_clear: bool = False
    tripwires_clear: bool = False
    architecture_locked: bool = True

    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CoordinationResult:
    """Immutable final result of one coordinated execution attempt."""

    status: CoordinationStatus
    action_id: str
    allowed: bool
    reason: str
    protocol: ProtocolDecision
    enforcement: EnforcementDecision | None = None
    mutation: MutationResult | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "protocol": {
                "valid": self.protocol.valid,
                "errors": list(self.protocol.errors),
            },
            "enforcement": (
                self.enforcement.to_dict()
                if self.enforcement is not None
                else None
            ),
            "mutation": (
                self.mutation.to_dict()
                if self.mutation is not None
                else None
            ),
            "evidence": dict(self.evidence),
        }


class ExecutionCoordinator:
    """
    Deterministic coordinator between safety boundaries.

    The coordinator is orchestration only. It does not own controller
    authority and cannot create a mutation executor by itself.

    Capability/module creation receives an additional machine-enforced
    duplicate/reuse check before mutation.
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
        mutation_adapter: ControlledMutationAdapter | None = None,
        *,
        capability_reuse_guard: CapabilityReuseGuard | None = None,
        capability_catalog_provider: (
            Callable[[], Iterable[CapabilityRecord]] | None
        ) = None,
        repository_root: Path | str | None = None,
    ) -> None:
        self._mutation_adapter = (
            mutation_adapter
            if mutation_adapter is not None
            else ControlledMutationAdapter()
        )

        self._coordinated_action_ids: set[str] = set()

        self._capability_reuse_guard = (
            capability_reuse_guard
            if capability_reuse_guard is not None
            else CapabilityReuseGuard()
        )

        self._repository_root = (
            Path(repository_root).resolve()
            if repository_root is not None
            else Path(__file__).resolve().parents[2]
        )

        self._capability_catalog_provider = (
            capability_catalog_provider
            if capability_catalog_provider is not None
            else self._build_repository_capability_catalog
        )

    def preflight(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
    ) -> tuple[ProtocolDecision, EnforcementDecision | None]:
        """
        Perform protocol and enforcement validation without mutation.

        Capability/module creation is also duplicate-checked here.
        """

        protocol = validate_proposal(proposal)

        if not protocol.valid:
            return protocol, None

        reuse_allowed, reuse_evidence, reuse_reason = (
            self._capability_reuse_preflight(
                proposal
            )
        )

        if not reuse_allowed:
            return (
                protocol,
                EnforcementDecision(
                    allowed=False,
                    stage="PREFLIGHT",
                    reason=reuse_reason,
                    checks=("capability_reuse",),
                    failures=("capability_reuse:failed",),
                    metadata=reuse_evidence,
                ),
            )

        enforcement = self._build_enforcement_decision(context)

        return protocol, enforcement

    def execute(
        self,
        proposal: ActionProposal,
        context: ExecutionContext,
        *,
        executor: Any = None,
        postflight: Mapping[str, bool] | None = None,
    ) -> CoordinationResult:
        """
        Coordinate exactly one execution attempt.

        No executor is discovered or invented here.

        Capability/module creation is checked:
        1. before mutation,
        2. again immediately before mutation.

        The second check is a TOCTOU protection against another agent/chat
        creating the same capability between initial evaluation and mutation.
        """

        action_id = self._safe_action_id(proposal)

        if action_id in self._coordinated_action_ids:
            protocol = validate_proposal(proposal)

            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action has already been coordinated by this instance.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                    "coordination_replay_blocked": True,
                },
            )

        protocol = validate_proposal(proposal)

        if not protocol.valid:
            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Action proposal failed protocol validation.",
                protocol=protocol,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                },
            )

        enforcement = self._build_enforcement_decision(context)

        if not enforcement.allowed:
            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason="Execution was blocked by enforcement preflight.",
                protocol=protocol,
                enforcement=enforcement,
                evidence={
                    **dict(context.evidence),
                    "coordination_attempted": True,
                    "execution_attempted": False,
                },
            )

        reuse_allowed, reuse_evidence, reuse_reason = (
            self._capability_reuse_preflight(
                proposal
            )
        )

        if not reuse_allowed:
            self._coordinated_action_ids.add(
                action_id
            )

            return CoordinationResult(
                status=CoordinationStatus.BLOCKED,
                action_id=action_id,
                allowed=False,
                reason=reuse_reason,
                protocol=protocol,
                enforcement=enforcement,
                evidence={
                    **dict(context.evidence),
                    "capability_reuse": reuse_evidence,
                    "coordination_attempted": True,
                    "execution_attempted": False,
                    "capability_reuse_blocked": True,
                },
            )

        request = MutationRequest(
            proposal=proposal,
            authorized=context.authorized,
            capability_available=context.capability_available,
            policy_allowed=context.policy_allowed,
            risk_allowed=context.risk_allowed,
            guard_allowed=context.guard_allowed,
            idempotency_clear=context.idempotency_clear,
            tripwires_clear=context.tripwires_clear,
            architecture_locked=context.architecture_locked,
            executor=executor,
            evidence={
                **dict(context.evidence),
                "capability_reuse": reuse_evidence,
            },
        )

        self._coordinated_action_ids.add(
            action_id
        )

        mutation = self._mutation_adapter.execute(
            request
        )

        if not mutation.executed:
            status = (
                CoordinationStatus.FAILED
                if mutation.decision.status.value == "FAILED"
                else CoordinationStatus.BLOCKED
            )

            return CoordinationResult(
                status=status,
                action_id=action_id,
                allowed=False,
                reason=(
                    mutation.error
                    if mutation.error
                    else (
                        "Controlled mutation boundary "
                        "did not complete execution."
                    )
                ),
                protocol=protocol,
                enforcement=enforcement,
                mutation=mutation,
                evidence={
                    **dict(context.evidence),
                    **dict(reuse_evidence),
                    **dict(mutation.evidence),
                    "capability_reuse": reuse_evidence,
                    "coordination_attempted": True,
                    "execution_attempted": (
                        mutation.evidence.get(
                            "mutation_attempted"
                        )
                        is True
                    ),
                },
            )

        postflight_data = dict(
            postflight or {}
        )

        postflight_decision = (
            self._postflight_decision(
                mutation=mutation,
                postflight=postflight_data,
            )
        )

        if not postflight_decision.allowed:
            return CoordinationResult(
                status=CoordinationStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason=(
                    "Mutation executed but "
                    "postflight verification failed."
                ),
                protocol=protocol,
                enforcement=postflight_decision,
                mutation=mutation,
                evidence={
                    **dict(context.evidence),
                    **dict(mutation.evidence),
                    "capability_reuse": reuse_evidence,
                    "coordination_attempted": True,
                    "execution_attempted": True,
                    "execution_succeeded": True,
                    "postflight_passed": False,
                },
            )

        return CoordinationResult(
            status=CoordinationStatus.EXECUTED,
            action_id=action_id,
            allowed=True,
            reason=(
                "Execution completed and postflight "
                "verification passed."
            ),
            protocol=protocol,
            enforcement=postflight_decision,
            mutation=mutation,
            evidence={
                **dict(context.evidence),
                **dict(mutation.evidence),
                "capability_reuse": reuse_evidence,
                "coordination_attempted": True,
                "execution_attempted": True,
                "execution_succeeded": True,
                "postflight_passed": True,
            },
        )

    @classmethod
    def _reuse_required(
        cls,
        proposal: ActionProposal,
    ) -> bool:
        """Return whether capability/module duplicate protection is required."""

        parameters = getattr(
            proposal,
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            Mapping,
        ):
            return False

        if parameters.get(
            "creates_capability"
        ) is True:
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

    def _capability_reuse_preflight(
        self,
        proposal: ActionProposal,
    ) -> tuple[
        bool,
        dict[str, Any],
        str,
    ]:
        """
        Evaluate capability/module reuse protection.

        Returns:
            allowed,
            machine-readable evidence,
            deterministic reason.
        """

        if not self._reuse_required(
            proposal
        ):
            return (
                True,
                {
                    "required": False,
                    "status": "NOT_REQUIRED",
                },
                "Capability reuse protection not required.",
            )

        try:
            request = (
                self._capability_request_from_proposal(
                    proposal
                )
            )

            first_catalog = tuple(
                self._capability_catalog_provider()
            )

            first_result = (
                self._capability_reuse_guard.evaluate(
                    request,
                    first_catalog,
                )
            )

            operation = str(
                proposal.parameters.get(
                    "capability_operation",
                    "CREATE",
                )
            ).strip().upper()

            first_allowed = (
                self._reuse_decision_allowed(
                    operation,
                    first_result.decision,
                )
            )

            evidence: dict[str, Any] = {
                "required": True,
                "operation": operation,
                "first_check": (
                    first_result.to_dict()
                ),
                "catalog_fingerprint": (
                    first_result.catalog_fingerprint
                ),
                "request_fingerprint": (
                    first_result.request_fingerprint
                ),
            }

            if not first_allowed:
                return (
                    False,
                    evidence,
                    (
                        "Capability reuse protection "
                        "blocked the proposed creation."
                    ),
                )

            # Fresh repository/catalog evaluation immediately before mutation.
            # This is the actual TOCTOU protection.
            second_catalog = tuple(
                self._capability_catalog_provider()
            )

            second_result = (
                self._capability_reuse_guard.evaluate(
                    request,
                    second_catalog,
                )
            )

            second_allowed = (
                self._reuse_decision_allowed(
                    operation,
                    second_result.decision,
                )
            )

            evidence["second_check"] = (
                second_result.to_dict()
            )
            evidence["second_catalog_fingerprint"] = (
                second_result.catalog_fingerprint
            )

            if not second_allowed:
                return (
                    False,
                    evidence,
                    (
                        "Capability reuse protection "
                        "blocked the mutation after "
                        "fresh catalog revalidation."
                    ),
                )

            return (
                True,
                evidence,
                (
                    "Capability reuse protection "
                    "passed."
                ),
            )

        except (
            TypeError,
            ValueError,
            RuntimeError,
            OSError,
            SyntaxError,
        ) as exc:
            return (
                False,
                {
                    "required": True,
                    "status": "BLOCKED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                (
                    "Capability reuse protection "
                    "failed closed because its catalog "
                    "or request could not be validated."
                ),
            )

    @classmethod
    def _reuse_decision_allowed(
        cls,
        operation: str,
        decision: ReuseDecision,
    ) -> bool:
        """Map reuse decisions to the requested capability operation."""

        if operation in cls.CREATE_OPERATIONS:
            return (
                decision
                is ReuseDecision.CREATE_NEW
            )

        if operation in cls.EXTEND_OPERATIONS:
            return decision in {
                ReuseDecision.REUSE,
                ReuseDecision.EXTEND,
            }

        return decision is not ReuseDecision.BLOCK

    @staticmethod
    def _capability_request_from_proposal(
        proposal: ActionProposal,
    ) -> CapabilityRequest:
        """Convert proposal metadata into a deterministic guard request."""

        parameters = getattr(
            proposal,
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            Mapping,
        ):
            raise ValueError(
                "ActionProposal parameters must be a mapping."
            )

        payload = parameters.get(
            "capability_reuse"
        )

        if not isinstance(
            payload,
            Mapping,
        ):
            raise ValueError(
                "capability_reuse metadata is required."
            )

        def text(
            name: str,
            *,
            required: bool = True,
        ) -> str:
            value = payload.get(
                name,
                "",
            )

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                if required:
                    raise ValueError(
                        f"capability_reuse.{name} "
                        "is required."
                    )

                return ""

            return value.strip()

        def many(
            name: str,
        ) -> tuple[str, ...]:
            value = payload.get(
                name,
                (),
            )

            if isinstance(
                value,
                str,
            ):
                return (
                    value.strip(),
                ) if value.strip() else ()

            if not isinstance(
                value,
                (list, tuple),
            ):
                raise ValueError(
                    f"capability_reuse.{name} "
                    "must be a list or tuple."
                )

            return tuple(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

        return CapabilityRequest(
            capability_id=text(
                "capability_id"
            ),
            name=text(
                "name"
            ),
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
            inputs=many(
                "inputs"
            ),
            outputs=many(
                "outputs"
            ),
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

    def _build_repository_capability_catalog(
        self,
    ) -> tuple[CapabilityRecord, ...]:
        """
        Build a deterministic derived capability catalog from T16 repository
        intelligence.

        This is derived intelligence only.

        It does NOT replace:
        - state.json authority
        - architecture authority
        - capability registry authority
        - Git authority

        The catalog describes existing authoritative Python modules so semantic
        responsibility overlap can be checked before a new capability/module
        crosses the mutation boundary.
        """

        engine = RepositoryIntelligenceEngine(
            self._repository_root
        )

        snapshot = engine.discover()

        records: list[CapabilityRecord] = []

        for repository_file in snapshot.python_files:
            if (
                repository_file.authority
                is not FileAuthority.AUTHORITATIVE
            ):
                continue

            relative_path = (
                repository_file.relative_path
            )

            path = Path(
                repository_file.absolute_path
            )

            try:
                source = path.read_text(
                    encoding="utf-8"
                )

                # Preserve compatibility with UTF-8-BOM source files.
                source = source.lstrip(
                    "\ufeff"
                )

                tree = ast.parse(
                    source,
                    filename=str(path),
                )

            except (
                OSError,
                SyntaxError,
                UnicodeError,
            ) as exc:
                raise RuntimeError(
                    "Capability catalog could not "
                    "parse authoritative repository "
                    f"module: {relative_path}"
                ) from exc

            docstring = (
                ast.get_docstring(tree)
                or ""
            ).strip()

            paragraphs = [
                part.strip()
                for part in re.split(
                    r"\n\s*\n",
                    docstring,
                )
                if part.strip()
            ]

            responsibility = (
                paragraphs[0][:2048]
                if paragraphs
                else (
                    "Python module "
                    + Path(
                        relative_path
                    ).stem.replace(
                        "_",
                        " ",
                    )
                )
            )

            module_name = (
                Path(
                    relative_path
                ).stem.replace(
                    "_",
                    " ",
                ).strip().title()
            )

            imported_modules: set[str] = set()
            output_symbols: set[str] = set()

            for node in ast.walk(
                tree
            ):
                if isinstance(
                    node,
                    ast.Import,
                ):
                    for alias in node.names:
                        imported_modules.add(
                            alias.name
                        )

                elif isinstance(
                    node,
                    ast.ImportFrom,
                ):
                    if node.module:
                        imported_modules.add(
                            node.module
                        )

                elif isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    if not node.name.startswith(
                        "_"
                    ):
                        output_symbols.add(
                            node.name
                        )

            architecture_ids = tuple(
                sorted(
                    set(
                        re.findall(
                            r"\bT\d{2}\b",
                            relative_path.upper(),
                        )
                    )
                )
            )

            records.append(
                CapabilityRecord(
                    capability_id=(
                        "MODULE::"
                        + relative_path.replace(
                            "\\",
                            "/",
                        )
                    ),
                    name=module_name,
                    description=docstring,
                    responsibility=responsibility,
                    architecture_ids=architecture_ids,
                    source_of_truth=relative_path,
                    inputs=tuple(
                        sorted(
                            imported_modules
                        )
                    ),
                    outputs=tuple(
                        sorted(
                            output_symbols
                        )
                    ),
                    owner="REOS_CONTROL_CENTER",
                )
            )

        return tuple(
            sorted(
                records,
                key=lambda item:
                item.capability_id,
            )
        )

    @staticmethod
    def _safe_action_id(
        proposal: ActionProposal,
    ) -> str:
        """Extract an action id without allowing malformed input to escape."""

        try:
            action_id = proposal.action_id
        except Exception:
            return "<invalid-action-id>"

        return (
            action_id
            if isinstance(
                action_id,
                str,
            )
            and action_id
            else "<invalid-action-id>"
        )

    @staticmethod
    def _build_enforcement_decision(
        context: ExecutionContext,
    ) -> EnforcementDecision:
        """
        Build the coordinator's deterministic enforcement decision.

        Enforcement remains default-deny. Every required condition must be
        explicitly true.
        """

        failures: list[str] = []

        checks = (
            ("authorization", context.authorized),
            ("capability", context.capability_available),
            ("policy", context.policy_allowed),
            ("risk", context.risk_allowed),
            ("guard", context.guard_allowed),
            ("idempotency", context.idempotency_clear),
            ("tripwires", context.tripwires_clear),
            (
                "architecture_lock",
                context.architecture_locked,
            ),
        )

        for name, allowed in checks:
            if allowed is not True:
                failures.append(
                    f"{name}:failed"
                )

        return EnforcementDecision(
            allowed=not failures,
            stage="PREFLIGHT",
            reason=(
                "All coordinator enforcement checks passed."
                if not failures
                else (
                    "Coordinator enforcement "
                    "rejected the operation."
                )
            ),
            checks=tuple(
                name
                for name, _ in checks
            ),
            failures=tuple(
                failures
            ),
        )

    @staticmethod
    def _postflight_decision(
        *,
        mutation: MutationResult,
        postflight: Mapping[str, bool],
    ) -> EnforcementDecision:
        """Create deterministic postflight verification."""

        failures: list[str] = []

        if mutation.executed is not True:
            failures.append(
                "execution_failed"
            )

        if (
            postflight.get(
                "evidence_complete"
            )
            is not True
        ):
            failures.append(
                "evidence_incomplete"
            )

        if (
            postflight.get(
                "provenance_valid"
            )
            is not True
        ):
            failures.append(
                "provenance_invalid"
            )

        if (
            postflight.get(
                "state_consistent"
            )
            is not True
        ):
            failures.append(
                "state_inconsistent"
            )

        return EnforcementDecision(
            allowed=not failures,
            stage="POSTFLIGHT",
            reason=(
                "Postflight verification passed."
                if not failures
                else (
                    "Postflight verification "
                    "rejected completion."
                )
            ),
            checks=(
                "execution_result",
                "evidence",
                "provenance",
                "state_consistency",
            ),
            failures=tuple(
                failures
            ),
            metadata={
                "mutation_status": (
                    mutation.decision.status.value
                ),
                "mutation_executed": (
                    mutation.executed
                ),
            },
        )

    def coordinated(
        self,
        action_id: str,
    ) -> bool:
        """Return whether this coordinator already coordinated an action."""

        return (
            action_id
            in self._coordinated_action_ids
        )

    def reset(self) -> None:
        """
        Clear only local coordination memory.

        This does not clear controller state or persistent idempotency state.
        """

        self._coordinated_action_ids.clear()

    @staticmethod
    def mutation_block_reason() -> tuple[
        MutationBlockReason,
        ...,
    ]:
        """
        Expose known mutation refusal classes without owning their policy.

        This is intentionally informational and performs no mutation.
        """

        return tuple(
            MutationBlockReason
        )


__all__ = [
    "CoordinationBlockReason",
    "CoordinationResult",
    "CoordinationStatus",
    "ExecutionContext",
    "ExecutionCoordinator",
]
