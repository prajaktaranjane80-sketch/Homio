
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.ai_platform.agent_runtime import (
    AgentRequest,
    AgentRuntime,
    AgentRuntimeError,
    AgentSettings,
)
from AUTONOMY_ENGINE.ai_platform.contracts import AIResponse, RequestContext
from AUTONOMY_ENGINE.ai_platform.errors import (
    GatewayDisabledError,
    ProviderResponseInvalidError,
    RequestContextMissingError,
)
from AUTONOMY_ENGINE.ai_platform.tool_bridge import (
    ToolBridge,
    ToolBridgeConfigurationError,
    ToolExecutionBlockedError,
    ToolDefinition,
    ToolProposal,
)

CONTEXT = RequestContext(
    principal_id="user-1",
    tenant_id="tenant-1",
    authentication_context_ref="auth-context-1",
    correlation_id="trace-1",
)


def final(answer: str = "The request is complete.") -> str:
    return json.dumps({"kind": "final", "answer": answer})


def tool_call(
    *,
    call_id: str = "call-1",
    tool: str = "search_properties",
    arguments: dict | None = None,
    reason: str = "Search for property records",
) -> str:
    return json.dumps(
        {
            "kind": "tool_call",
            "call_id": call_id,
            "tool": tool,
            "arguments": (
                arguments
                if arguments is not None
                else {"query": "pune apartment"}
            ),
            "reason": reason,
        }
    )


class FakeModelGateway:
    def __init__(
        self,
        outputs: list[str],
        *,
        bad_identity: bool = False,
    ) -> None:
        self.outputs = list(outputs)
        self.requests = []
        self.bad_identity = bad_identity

    def complete(self, request):
        self.requests.append(request)
        if not self.outputs:
            raise AssertionError("Unexpected extra model call")

        output = self.outputs.pop(0)
        return AIResponse(
            request_id=(
                "wrong-request"
                if self.bad_identity
                else request.request_id
            ),
            correlation_id=request.context.correlation_id,
            text=output,
            provider_id="fake-provider",
            model_id=request.model_id or "fake-model",
        )


class FakeToolGateway:
    def __init__(self) -> None:
        self.calls = []
        self.adapters = {
            "property_search": self._search_properties,
        }

    @staticmethod
    def _search_properties(arguments):
        return {
            "items": [
                {
                    "record_id": "inventory-1",
                    "name": "Apartment",
                }
            ],
            "api_key": "do-not-disclose-this-value",
        }

    def authorize(
        self,
        request,
        *,
        preflight_ok: bool,
        evidence_ok: bool,
    ):
        return SimpleNamespace(
            allowed=preflight_ok and evidence_ok
        )

    def execute(
        self,
        request,
        *,
        preflight_ok: bool,
        evidence_ok: bool,
    ):
        self.calls.append(
            (request.action, dict(request.arguments))
        )
        return self.adapters[request.action](request.arguments)


def make_tool_bridge(
    *,
    gateway: FakeToolGateway | None = None,
    preflight=lambda proposal, context: True,
    evidence_check=lambda proposal, context: True,
    action_name: str = "property_search",
    max_calls_per_run: int = 1,
) -> tuple[ToolBridge, FakeToolGateway]:
    target = gateway or FakeToolGateway()

    definition = ToolDefinition(
        name="search_properties",
        action_name=action_name,
        description="Search authorized property records by a bounded query.",
        required_arguments=("query",),
        allowed_arguments=("query",),
        max_calls_per_run=max_calls_per_run,
        timeout_seconds=2.0,
    )

    bridge = ToolBridge(
        gateway=target,
        tools=(definition,),
        enabled=True,
        preflight=preflight,
        evidence_check=evidence_check,
        timeout_runner=lambda operation, timeout_seconds: operation(),
    )
    return bridge, target


def make_request(**overrides) -> AgentRequest:
    values = {
        "request_id": "agent-request-1",
        "task": "Find an apartment in Pune.",
        "context": CONTEXT,
    }
    values.update(overrides)
    return AgentRequest(**values)


def test_agent_runtime_is_disabled_by_default() -> None:
    gateway = FakeModelGateway([final()])
    runtime = AgentRuntime(gateway=gateway)

    with pytest.raises(GatewayDisabledError):
        runtime.run(make_request())

    assert gateway.requests == []


def test_missing_trusted_context_stops_before_model_call() -> None:
    gateway = FakeModelGateway([final()])
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    with pytest.raises(RequestContextMissingError):
        runtime.run(make_request(context=None))

    assert gateway.requests == []


def test_final_model_answer_returns_a_typed_response() -> None:
    gateway = FakeModelGateway(
        [final("Two suitable records were found.")]
    )
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    response = runtime.run(make_request())

    assert response.answer == "Two suitable records were found."
    assert response.request_id == "agent-request-1"
    assert response.provider_id == "fake-provider"
    assert response.model_id == "fake-model"
    assert response.iterations == 1
    assert response.tool_calls == ()
    assert gateway.requests[0].operation == "agent.plan"


def test_read_only_tool_call_then_final_answer() -> None:
    model = FakeModelGateway(
        [
            tool_call(),
            final("One authorized property record was found."),
        ]
    )
    bridge, gateway = make_tool_bridge()
    runtime = AgentRuntime(
        gateway=model,
        tool_bridge=bridge,
        settings=AgentSettings(enabled=True),
    )

    response = runtime.run(make_request())

    assert response.answer == "One authorized property record was found."
    assert response.iterations == 2
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].tool_name == "search_properties"
    assert gateway.calls == [
        ("property_search", {"query": "pune apartment"})
    ]
    assert "UNTRUSTED_TOOL_TRACE_JSON" in model.requests[1].input_text
    assert "do-not-disclose-this-value" not in model.requests[1].input_text
    assert "[REDACTED]" in model.requests[1].input_text


def test_runtime_rejects_duplicate_request_id() -> None:
    gateway = FakeModelGateway([final(), final()])
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    runtime.run(make_request())

    with pytest.raises(
        AgentRuntimeError,
        match="duplicate agent request",
    ):
        runtime.run(make_request())

    assert len(gateway.requests) == 1


def test_bad_model_response_identity_is_rejected() -> None:
    gateway = FakeModelGateway([final()], bad_identity=True)
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    with pytest.raises(ProviderResponseInvalidError):
        runtime.run(make_request())


def test_invalid_model_json_is_rejected() -> None:
    gateway = FakeModelGateway(["This is not JSON"])
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    with pytest.raises(ProviderResponseInvalidError):
        runtime.run(make_request())


def test_final_response_with_extra_keys_is_rejected() -> None:
    output = json.dumps(
        {
            "kind": "final",
            "answer": "Done",
            "tool": "run_shell",
        }
    )
    gateway = FakeModelGateway([output])
    runtime = AgentRuntime(
        gateway=gateway,
        settings=AgentSettings(enabled=True),
    )

    with pytest.raises(ProviderResponseInvalidError):
        runtime.run(make_request())


def test_repeated_tool_fingerprint_is_rejected_before_second_execution() -> None:
    model = FakeModelGateway(
        [tool_call(), tool_call(), final()]
    )
    bridge, gateway = make_tool_bridge(max_calls_per_run=4)
    runtime = AgentRuntime(
        gateway=model,
        tool_bridge=bridge,
        settings=AgentSettings(
            enabled=True,
            max_iterations=4,
        ),
    )

    with pytest.raises(ProviderResponseInvalidError):
        runtime.run(make_request())

    assert len(gateway.calls) == 1


def test_duplicate_call_id_is_blocked_even_when_arguments_change() -> None:
    bridge, gateway = make_tool_bridge(max_calls_per_run=4)

    first = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )
    second = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "mumbai"},
    )

    bridge.execute(first, CONTEXT, run_id="run-1")

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(second, CONTEXT, run_id="run-1")

    assert len(gateway.calls) == 1


def test_repeated_tool_arguments_are_blocked_by_bridge() -> None:
    bridge, gateway = make_tool_bridge(max_calls_per_run=4)

    first = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )
    second = ToolProposal(
        call_id="call-2",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )

    bridge.execute(first, CONTEXT, run_id="run-1")

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(second, CONTEXT, run_id="run-1")

    assert len(gateway.calls) == 1


def test_unknown_tool_name_is_blocked() -> None:
    bridge, gateway = make_tool_bridge()
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="run_shell",
        arguments={},
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")

    assert gateway.calls == []


def test_extra_tool_arguments_are_blocked() -> None:
    bridge, gateway = make_tool_bridge()
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={
            "query": "pune",
            "shell_command": "echo bad",
        },
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")

    assert gateway.calls == []


def test_missing_required_tool_arguments_are_blocked() -> None:
    bridge, gateway = make_tool_bridge()
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={},
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")

    assert gateway.calls == []


def test_failed_preflight_blocks_execution() -> None:
    bridge, gateway = make_tool_bridge(
        preflight=lambda proposal, context: False
    )
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")

    assert gateway.calls == []


def test_missing_evidence_blocks_execution() -> None:
    bridge, gateway = make_tool_bridge(
        evidence_check=lambda proposal, context: False
    )
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")

    assert gateway.calls == []


def test_sensitive_mutation_cannot_be_added_to_read_only_allowlist() -> None:
    with pytest.raises(ToolBridgeConfigurationError):
        make_tool_bridge(action_name="financial_mutation")


def test_shell_database_and_repository_actions_are_rejected() -> None:
    for name in (
        "run_shell",
        "database_lookup",
        "repository_read",
        "git_push",
    ):
        with pytest.raises(ToolBridgeConfigurationError):
            make_tool_bridge(action_name=name)


def test_bridge_is_disabled_by_default_and_advertises_no_tools() -> None:
    bridge = ToolBridge()

    assert bridge.enabled is False
    assert bridge.available_tools == ()
    assert bridge.describe_available_tools() == ()


def test_disabled_bridge_refuses_proposals() -> None:
    bridge = ToolBridge()
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )

    with pytest.raises(ToolExecutionBlockedError):
        bridge.execute(proposal, CONTEXT, run_id="run-1")


def test_enabled_bridge_requires_an_enforced_timeout_runner() -> None:
    gateway = FakeToolGateway()
    definition = ToolDefinition(
        name="search_properties",
        action_name="property_search",
        description="Search properties.",
        allowed_arguments=("query",),
        required_arguments=("query",),
    )

    with pytest.raises(ToolBridgeConfigurationError):
        ToolBridge(
            gateway=gateway,
            tools=(definition,),
            enabled=True,
            preflight=lambda proposal, context: True,
            evidence_check=lambda proposal, context: True,
        )


def test_tool_result_is_redacted_and_bounded() -> None:
    bridge, _ = make_tool_bridge()
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments={"query": "pune"},
    )

    result = bridge.execute(
        proposal,
        CONTEXT,
        run_id="run-1",
    )

    assert "do-not-disclose-this-value" not in result.output_json
    assert '"api_key":"[REDACTED]"' in result.output_json
    assert len(result.output_json) <= 3000


def test_tool_arguments_are_immutable_after_construction() -> None:
    original = {"query": "pune"}
    proposal = ToolProposal(
        call_id="call-1",
        tool_name="search_properties",
        arguments=original,
    )
    original["query"] = "overwritten"

    assert proposal.fingerprint() == (
        '{"arguments":{"query":"pune"},"tool":"search_properties"}'
    )


def test_agent_loop_limit_does_not_claim_success() -> None:
    model = FakeModelGateway(
        [
            tool_call(
                call_id="call-1",
                arguments={"query": "pune"},
            ),
            tool_call(
                call_id="call-2",
                arguments={"query": "mumbai"},
            ),
        ]
    )
    bridge, gateway = make_tool_bridge(max_calls_per_run=4)
    runtime = AgentRuntime(
        gateway=model,
        tool_bridge=bridge,
        settings=AgentSettings(
            enabled=True,
            max_iterations=2,
        ),
    )

    with pytest.raises(
        AgentRuntimeError,
        match="iteration limit",
    ):
        runtime.run(make_request())

    assert len(gateway.calls) == 2


def test_model_cannot_use_unlisted_tool_even_if_prompt_is_ignored() -> None:
    model = FakeModelGateway(
        [tool_call(tool="run_shell", arguments={})]
    )
    bridge, gateway = make_tool_bridge()
    runtime = AgentRuntime(
        gateway=model,
        tool_bridge=bridge,
        settings=AgentSettings(enabled=True),
    )

    with pytest.raises(ToolExecutionBlockedError):
        runtime.run(make_request())

    assert gateway.calls == []
