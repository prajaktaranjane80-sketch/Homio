from __future__ import annotations

import hashlib
import hmac
import json
import uuid

from homio_python_runtime import protocol, worker


SECRET = b"0123456789abcdef0123456789abcdef"
NOW = 1_800_000_000_000
ISSUER = "https://issuer.example.test/"
CONTEXT = {
    "actor": {
        "identityId": "11111111-1111-4111-8111-111111111111",
        "accountId": "22222222-2222-4222-8222-222222222222",
    },
    "tenant": {
        "tenantId": "33333333-3333-4333-8333-333333333333",
        "tenantRevision": 4,
        "organizationId": "44444444-4444-4444-8444-444444444444",
        "membershipId": "55555555-5555-4555-8555-555555555555",
        "membershipRevision": 7,
    },
    "correlationId": "66666666-6666-4666-8666-666666666666",
}


class CountingOwners:
    def __init__(self) -> None:
        self.calls = 0

    def verify_access_token(self, _token: str):
        self.calls += 1
        raise AssertionError("unsupported mutation must not invoke an owner")

    def resolve_external(self, _provider: str, _subject: str):
        self.calls += 1
        raise AssertionError("unsupported mutation must not invoke an owner")

    def resolve_context(self, _tenant_id):
        self.calls += 1
        raise AssertionError("unsupported mutation must not invoke an owner")

    def resolve_membership(self, **_scope):
        self.calls += 1
        raise AssertionError("unsupported mutation must not invoke an owner")


def _signed_request(operation: str) -> dict:
    message = {
        "protocol": protocol.PROTOCOL_NAME,
        "version": protocol.PROTOCOL_VERSION,
        "messageType": "request",
        "serviceId": protocol.SERVICE_ID,
        "audience": protocol.AUDIENCE,
        "requestId": str(uuid.uuid4()),
        "nonce": str(uuid.uuid4()),
        "issuedAtMs": NOW,
        "operation": operation,
        "context": CONTEXT,
        "payload": {"tenantId": CONTEXT["tenant"]["tenantId"]},
        "idempotency": None,
    }
    canonical = protocol.canonical_json(message).encode("utf-8")
    message["signature"] = hmac.new(SECRET, canonical, hashlib.sha256).hexdigest()
    return message


def test_unknown_mutation_operation_is_rejected_before_any_domain_owner_call():
    owners = CountingOwners()
    runtime = protocol.PythonDomainRuntime(
        oidc_verifier=owners,
        identity_resolver=owners,
        tenant_resolver=owners,
        membership_resolver=owners,
        trusted_issuer=ISSUER,
        trusted_audience="homio-api",
    )

    response = json.loads(
        protocol.process_request(
            json.dumps(_signed_request("core001.membership.create")).encode("utf-8"),
            runtime,
            secret=SECRET,
            replay_guard=protocol.ReplayGuard(),
            now_ms=NOW,
        )
    )

    assert response["status"] == "failure"
    assert response["error"]["code"] == "OPERATION_NOT_ALLOWED"
    assert owners.calls == 0


def test_missing_production_owner_composition_fails_closed_without_leaking_details(monkeypatch, capsys):
    monkeypatch.setenv("HOMIO_PYTHON_BRIDGE_SECRET", SECRET.hex())
    monkeypatch.setenv("HOMIO_PYTHON_RUNTIME_MODE", "production")
    monkeypatch.setenv(
        "HOMIO_PYTHON_RUNTIME_OWNER_FACTORY",
        "AUTONOMY_ENGINE.core.identity_tenant.missing_runtime_composition:build_runtime",
    )

    assert worker.main() == 5
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "PYTHON_RUNTIME_OWNER_COMPOSITION_UNAVAILABLE\n"
    assert "missing_runtime_composition" not in captured.err
