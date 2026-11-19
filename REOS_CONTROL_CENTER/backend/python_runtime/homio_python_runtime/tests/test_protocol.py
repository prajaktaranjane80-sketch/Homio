import hashlib
import hmac
import json
import uuid
from types import SimpleNamespace

import pytest

from homio_python_runtime import protocol

SECRET = b"b3-test-key-that-is-32-bytes-long"
NOW = 1_800_000_000_000
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


class Owners:
    def __init__(self):
        self.contexts = []
        self.identities = []

    def verify_access_token(self, token):
        assert token == "raw-secret-token"
        return SimpleNamespace(
            issuer="https://issuer.example.test/",
            subject="subject-1",
            audiences=("homio-api",),
            client_id="homio-web",
            token_id="jti-1",
            email="must-not-leak@example.test",
        )

    def resolve_external(self, provider, subject):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            identity_id=uuid.UUID(CONTEXT["actor"]["identityId"]),
            reference_id=uuid.UUID("77777777-7777-4777-8777-777777777777"),
            provider=provider,
            subject=subject,
            reason="resolved",
        )

    def resolve_context(self, tenant_id):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            tenant_id=tenant_id,
            tenant_revision=4,
            reason="resolved",
            context=SimpleNamespace(
                tenant_status=SimpleNamespace(value="ACTIVE"),
                tenant_kind=SimpleNamespace(value="BROKERAGE"),
                operating_mode=SimpleNamespace(value="BROKER_SAAS"),
            ),
        )

    def resolve_membership(self, tenant_id, organization_id, identity_id):
        return SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            membership_id=uuid.UUID(CONTEXT["tenant"]["membershipId"]),
            tenant_id=tenant_id,
            organization_id=organization_id,
            identity_id=identity_id,
            membership_revision=7,
            reason="resolved",
            membership=object(),
        )


def runtime_for(owners):
    return protocol.PythonDomainRuntime(
        oidc_verifier=owners,
        identity_resolver=owners,
        tenant_resolver=owners,
        membership_resolver=owners,
        trusted_issuer="https://issuer.example.test/",
        trusted_audience="homio-api",
    )


def signed_request(operation, payload, context=CONTEXT, **overrides):
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
        "context": context,
        "payload": payload,
        "idempotency": None,
    }
    message.update(overrides)
    canonical = protocol.canonical_json(message).encode("utf-8")
    message["signature"] = hmac.new(
        SECRET,
        canonical,
        hashlib.sha256,
    ).hexdigest()
    return message


def test_verified_oidc_access_token_is_projected_without_email_or_token():
    owners = Owners()
    request = signed_request(
        "oidc.verify_access_token",
        {"accessToken": "raw-secret-token"},
        context={"correlationId": "66666666-6666-4666-8666-666666666666"},
    )
    response = protocol.process_request(
        json.dumps(request).encode(),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    )
    parsed = json.loads(response)

    assert parsed["status"] == "success"
    assert parsed["result"] == {
        "issuer": "https://issuer.example.test/",
        "subject": "subject-1",
        "audiences": ["homio-api"],
        "clientId": "homio-web",
        "tokenId": "jti-1",
    }
    assert "email" not in parsed["result"]
    assert "raw-secret-token" not in response.decode()


def test_trusted_context_is_preserved_when_calling_existing_core_identity_owner():
    owners = Owners()
    request = signed_request(
        "core001.identity.resolve",
        {
            "provider": "https://issuer.example.test/",
            "subject": "subject-1",
        },
    )
    parsed = json.loads(protocol.process_request(
        json.dumps(request).encode(),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    ))

    assert parsed["context"] == CONTEXT
    assert parsed["result"]["identityId"] == CONTEXT["actor"]["identityId"]
    assert "subject" not in parsed["result"]
    assert "provider" not in parsed["result"]


def test_tenant_resolution_rejects_cross_tenant_payload_before_domain_call():
    owners = Owners()
    request = signed_request(
        "core001.tenant.resolve_context",
        {"tenantId": "99999999-9999-4999-8999-999999999999"},
    )
    parsed = json.loads(protocol.process_request(
        json.dumps(request).encode(),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    ))

    assert parsed["status"] == "failure"
    assert parsed["error"]["code"] == "TENANT_SCOPE_MISMATCH"


def test_membership_resolution_rejects_actor_substitution():
    owners = Owners()
    request = signed_request(
        "core001.membership.resolve",
        {
            "tenantId": CONTEXT["tenant"]["tenantId"],
            "organizationId": CONTEXT["tenant"]["organizationId"],
            "identityId": "99999999-9999-4999-8999-999999999999",
        },
    )
    parsed = json.loads(protocol.process_request(
        json.dumps(request).encode(),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    ))

    assert parsed["status"] == "failure"
    assert parsed["error"]["code"] == "ACTOR_SCOPE_MISMATCH"


@pytest.mark.parametrize("overrides", [
    {"serviceId": "untrusted-service"},
    {"audience": "public-api"},
    {"version": 99},
])
def test_wrong_service_audience_or_contract_version_is_rejected(overrides):
    message = signed_request(
        "core001.identity.resolve",
        {"provider": "issuer", "subject": "subject"},
        **overrides,
    )
    with pytest.raises(protocol.ProtocolError):
        protocol.verify_request(
            message,
            SECRET,
            now_ms=NOW,
            replay_guard=protocol.ReplayGuard(),
        )


def test_request_with_modified_payload_fails_hmac_verification():
    message = signed_request(
        "core001.identity.resolve",
        {"provider": "issuer", "subject": "subject"},
    )
    message["payload"]["subject"] = "attacker-subject"

    with pytest.raises(protocol.ProtocolError, match="AUTHENTICATION_FAILED"):
        protocol.verify_request(
            message,
            SECRET,
            now_ms=NOW,
            replay_guard=protocol.ReplayGuard(),
        )


def test_nonce_replay_is_rejected_even_when_request_has_a_valid_signature():
    guard = protocol.ReplayGuard()
    message = signed_request(
        "core001.identity.resolve",
        {"provider": "issuer", "subject": "subject"},
    )
    protocol.verify_request(
        message,
        SECRET,
        now_ms=NOW,
        replay_guard=guard,
    )

    with pytest.raises(protocol.ProtocolError, match="REPLAY_DETECTED"):
        protocol.verify_request(
            message,
            SECRET,
            now_ms=NOW,
            replay_guard=guard,
        )


def test_unsupported_authorization_operation_is_never_fabricated_from_t03():
    owners = Owners()
    message = signed_request(
        "core001.authorization.authorize",
        {"operation": "inventory.read"},
    )
    parsed = json.loads(protocol.process_request(
        json.dumps(message).encode(),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    ))

    assert parsed["status"] == "failure"
    assert parsed["error"]["code"] == "OPERATION_NOT_ALLOWED"


def test_worker_reads_one_signed_frame_and_emits_one_signed_response():
    from io import BytesIO
    from homio_python_runtime.worker import run_worker

    owners = Owners()
    runtime = runtime_for(owners)
    request = signed_request(
        "core001.identity.resolve",
        {
            "provider": "https://issuer.example.test/",
            "subject": "subject-1",
        },
    )
    request["issuedAtMs"] = int(__import__("time").time() * 1000)
    unsigned = {
        key: value
        for key, value in request.items()
        if key != "signature"
    }
    request["signature"] = hmac.new(
        SECRET,
        protocol.canonical_json(unsigned).encode(),
        hashlib.sha256,
    ).hexdigest()

    input_stream = BytesIO(json.dumps(request).encode() + b"\n")
    output_stream = BytesIO()
    error_stream = BytesIO()

    exit_code = run_worker(
        runtime,
        secret=SECRET,
        input_stream=input_stream,
        output_stream=output_stream,
        error_stream=error_stream,
    )

    response = json.loads(output_stream.getvalue().splitlines()[0])
    assert exit_code == 0
    assert response["status"] == "success"
    assert response["requestId"] == request["requestId"]
    assert response["context"] == CONTEXT
    assert error_stream.getvalue() == b""
