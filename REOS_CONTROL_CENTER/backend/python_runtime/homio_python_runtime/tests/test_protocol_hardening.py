
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from types import SimpleNamespace

import pytest

from homio_python_runtime import protocol

SECRET = b"b3-test-key-that-is-32-bytes-long"
NOW = 1_800_000_000_000
ISSUER = "https://issuer.example.test/"
CORRELATION = {
    "correlationId": "66666666-6666-4666-8666-666666666666"
}
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
    **CORRELATION,
}


class Owners:
    def __init__(self):
        self.identity_calls = 0
        self.tenant_calls = 0
        self.membership_calls = 0
        self.identity_result = SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            identity_id=uuid.UUID(CONTEXT["actor"]["identityId"]),
            reference_id=uuid.UUID("77777777-7777-4777-8777-777777777777"),
            provider=ISSUER,
            subject="provider-subject",
            reason="private internal resolution details",
        )
        self.tenant_result = SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            tenant_id=uuid.UUID(CONTEXT["tenant"]["tenantId"]),
            tenant_revision=4,
            reason="private internal tenant details",
            context=SimpleNamespace(
                tenant_status=SimpleNamespace(value="ACTIVE"),
                tenant_kind=SimpleNamespace(value="BROKERAGE"),
                operating_mode=SimpleNamespace(value="BROKER_SAAS"),
            ),
        )
        self.membership_result = SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            membership_id=uuid.UUID(CONTEXT["tenant"]["membershipId"]),
            tenant_id=uuid.UUID(CONTEXT["tenant"]["tenantId"]),
            organization_id=uuid.UUID(CONTEXT["tenant"]["organizationId"]),
            identity_id=uuid.UUID(CONTEXT["actor"]["identityId"]),
            membership_revision=7,
            reason="private internal membership details",
            membership=object(),
        )

    def verify_access_token(self, token):
        if token != "raw-secret-token":
            raise ValueError("invalid token")
        return SimpleNamespace(
            issuer=ISSUER,
            subject="provider-subject",
            audiences=("homio-api",),
            client_id="homio-web",
            token_id="jti-1",
            email="must-not-leak@example.test",
        )

    def resolve_external(self, provider, subject):
        self.identity_calls += 1
        return self.identity_result

    def resolve_context(self, tenant_id):
        self.tenant_calls += 1
        return self.tenant_result

    def resolve_membership(self, *, tenant_id, organization_id, identity_id):
        self.membership_calls += 1
        return self.membership_result


def runtime_for(owners):
    return protocol.PythonDomainRuntime(
        oidc_verifier=owners,
        identity_resolver=owners,
        tenant_resolver=owners,
        membership_resolver=owners,
        trusted_issuer=ISSUER,
        trusted_audience="homio-api",
    )


def signed_request(operation, payload, context, *, now=NOW):
    message = {
        "protocol": protocol.PROTOCOL_NAME,
        "version": protocol.PROTOCOL_VERSION,
        "messageType": "request",
        "serviceId": protocol.SERVICE_ID,
        "audience": protocol.AUDIENCE,
        "requestId": str(uuid.uuid4()),
        "nonce": str(uuid.uuid4()),
        "issuedAtMs": now,
        "operation": operation,
        "context": context,
        "payload": payload,
        "idempotency": None,
    }
    message["signature"] = hmac.new(
        SECRET,
        protocol.canonical_json(message).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return message


def invoke(owners, operation, payload, context):
    return json.loads(protocol.process_request(
        json.dumps(signed_request(operation, payload, context)).encode("utf-8"),
        runtime_for(owners),
        secret=SECRET,
        replay_guard=protocol.ReplayGuard(),
        now_ms=NOW,
    ))


def test_identity_resolution_accepts_correlation_only_context_before_actor_exists():
    owners = Owners()
    response = invoke(
        owners,
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    assert response["status"] == "success"
    assert response["context"] == CORRELATION
    assert response["result"] == {
        "status": "RESOLVED",
        "identityId": CONTEXT["actor"]["identityId"],
        "referenceId": "77777777-7777-4777-8777-777777777777",
    }


def test_identity_resolution_refuses_unconfigured_issuer_before_owner_lookup():
    owners = Owners()
    response = invoke(
        owners,
        "core001.identity.resolve",
        {
            "provider": "https://attacker.example.test/",
            "subject": "provider-subject",
        },
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "ISSUER_NOT_ALLOWED"
    assert owners.identity_calls == 0


def test_identity_resolution_does_not_echo_external_subject_or_private_reason():
    owners = Owners()
    response = invoke(
        owners,
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    serialized = json.dumps(response)
    assert "provider-subject" not in serialized
    assert "private internal" not in serialized
    assert "provider" not in response["result"]
    assert "subject" not in response["result"]


def test_tenant_owner_result_must_remain_bound_to_requested_tenant():
    owners = Owners()
    owners.tenant_result = SimpleNamespace(
        status=SimpleNamespace(value="RESOLVED"),
        tenant_id=uuid.UUID("99999999-9999-4999-8999-999999999999"),
        tenant_revision=4,
        context=None,
        reason="wrong tenant",
    )
    response = invoke(
        owners,
        "core001.tenant.resolve_context",
        {"tenantId": CONTEXT["tenant"]["tenantId"]},
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "DOMAIN_RESULT_INVALID"


def test_resolved_tenant_must_have_a_valid_domain_context():
    owners = Owners()
    owners.tenant_result.context = None
    response = invoke(
        owners,
        "core001.tenant.resolve_context",
        {"tenantId": CONTEXT["tenant"]["tenantId"]},
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "DOMAIN_RESULT_INVALID"


def test_membership_owner_result_must_match_all_trusted_scope_fields():
    owners = Owners()
    owners.membership_result.identity_id = uuid.UUID(
        "99999999-9999-4999-8999-999999999999"
    )
    response = invoke(
        owners,
        "core001.membership.resolve",
        {
            "tenantId": CONTEXT["tenant"]["tenantId"],
            "organizationId": CONTEXT["tenant"]["organizationId"],
            "identityId": CONTEXT["actor"]["identityId"],
        },
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "DOMAIN_RESULT_INVALID"


def test_domain_result_status_is_allowlisted():
    owners = Owners()
    owners.identity_result.status = SimpleNamespace(value="ADMIN_GRANTED")
    response = invoke(
        owners,
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "DOMAIN_RESULT_INVALID"


def test_non_finite_and_duplicate_json_properties_are_rejected():
    with pytest.raises(protocol.ProtocolError, match="DUPLICATE_JSON_KEY"):
        protocol.parse_json(b'{"a":1,"a":2}', maximum=100)
    with pytest.raises(protocol.ProtocolError, match="FLOATING_POINT_NOT_ALLOWED"):
        protocol.parse_json(b'{"a":1.5}', maximum=100)


def test_replay_guard_fails_closed_when_full_instead_of_evicting_live_nonces():
    guard = protocol.ReplayGuard(maximum_entries=2)
    first = signed_request(
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    protocol.verify_request(first, SECRET, now_ms=NOW, replay_guard=guard)
    second = signed_request(
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    with pytest.raises(
        protocol.ProtocolError,
        match="REPLAY_GUARD_CAPACITY_EXCEEDED",
    ):
        protocol.verify_request(
            second,
            SECRET,
            now_ms=NOW + 1,
            replay_guard=guard,
        )


def test_json_surrogate_code_points_are_rejected_before_canonical_signing():
    with pytest.raises(protocol.ProtocolError, match="JSON_STRING_INVALID"):
        protocol.canonical_json({"value": "bad\ud800value"})


def test_versioned_contract_document_matches_python_protocol_constants():
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[3]
    contract_path = backend_root / "contracts" / "python-runtime" / "v1" / "contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["contract"]["protocol"] == protocol.PROTOCOL_NAME
    assert contract["contract"]["version"] == protocol.PROTOCOL_VERSION
    assert set(contract["operations"]) == set(protocol.ALLOWED_OPERATIONS)
    assert contract["authentication"]["service_id"] == protocol.SERVICE_ID
    assert contract["authentication"]["audience"] == protocol.AUDIENCE
    assert (
        contract["authentication"]["replay_guard_maximum_entries_per_worker"]
        == protocol.MAX_NONCE_ENTRIES
    )
    assert contract["mutation_policy"]["enabled"] is False
    assert contract["authentication"]["trust_policy"]["issuer"]
    assert contract["authentication"]["trust_policy"]["audience"]


def test_full_identity_context_cannot_be_rebound_to_another_canonical_identity():
    owners = Owners()
    owners.identity_result.identity_id = uuid.UUID(
        "99999999-9999-4999-8999-999999999999"
    )
    response = invoke(
        owners,
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "ACTOR_SCOPE_MISMATCH"


def test_mutations_remain_disabled_until_durable_b4_idempotency_is_bound():
    message = signed_request(
        "core001.membership.resolve",
        {
            "tenantId": CONTEXT["tenant"]["tenantId"],
            "organizationId": CONTEXT["tenant"]["organizationId"],
            "identityId": CONTEXT["actor"]["identityId"],
        },
        CONTEXT,
    )
    message["idempotency"] = {
        "key": "command-001",
        "fingerprint": "a" * 64,
    }
    unsigned = {
        key: value
        for key, value in message.items()
        if key != "signature"
    }
    message["signature"] = hmac.new(
        SECRET,
        protocol.canonical_json(unsigned).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    with pytest.raises(protocol.ProtocolError, match="MUTATION_NOT_ENABLED"):
        protocol.verify_request(
            message,
            SECRET,
            now_ms=NOW,
            replay_guard=protocol.ReplayGuard(),
        )


def test_request_and_nonce_must_have_distinct_replay_identities():
    message = signed_request(
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CORRELATION,
    )
    message["nonce"] = message["requestId"]
    unsigned = {
        key: value
        for key, value in message.items()
        if key != "signature"
    }
    message["signature"] = hmac.new(
        SECRET,
        protocol.canonical_json(unsigned).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    with pytest.raises(protocol.ProtocolError, match="REQUEST_ID_INVALID"):
        protocol.verify_request(
            message,
            SECRET,
            now_ms=NOW,
            replay_guard=protocol.ReplayGuard(),
        )


def test_oidc_result_issuer_must_match_the_configured_trust_issuer():
    owners = Owners()
    owners.verify_access_token = lambda _token: SimpleNamespace(
        issuer="https://attacker.example.test/",
        subject="provider-subject",
        audiences=("homio-api",),
        client_id="homio-web",
        token_id="jti-1",
        email="must-not-leak@example.test",
    )
    response = invoke(
        owners,
        "oidc.verify_access_token",
        {"accessToken": "raw-secret-token"},
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "OIDC_TRUST_CONFIGURATION_INVALID"


def test_oidc_result_must_include_the_configured_api_audience():
    owners = Owners()
    owners.verify_access_token = lambda _token: SimpleNamespace(
        issuer=ISSUER,
        subject="provider-subject",
        audiences=("another-api",),
        client_id="homio-web",
        token_id="jti-1",
        email="must-not-leak@example.test",
    )
    response = invoke(
        owners,
        "oidc.verify_access_token",
        {"accessToken": "raw-secret-token"},
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "OIDC_TRUST_CONFIGURATION_INVALID"


def test_unexpected_oidc_verifier_failure_is_classified_as_unavailable_without_details():
    owners = Owners()

    def fail(_token):
        raise RuntimeError("secret internal key-service detail")

    owners.verify_access_token = fail
    response = invoke(
        owners,
        "oidc.verify_access_token",
        {"accessToken": "raw-secret-token"},
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "OIDC_VERIFIER_UNAVAILABLE"
    assert "secret internal" not in json.dumps(response)


def test_known_oidc_invalid_token_failure_is_classified_as_invalid():
    owners = Owners()

    class InvalidToken(Exception):
        code = "invalid_access_token"

    def fail(_token):
        raise InvalidToken("private verification detail")

    owners.verify_access_token = fail
    response = invoke(
        owners,
        "oidc.verify_access_token",
        {"accessToken": "raw-secret-token"},
        CORRELATION,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "ACCESS_TOKEN_INVALID"
    assert "private verification detail" not in json.dumps(response)


def test_full_trusted_identity_resolution_rejects_a_missing_canonical_identity():
    owners = Owners()
    owners.identity_result = SimpleNamespace(
        status=SimpleNamespace(value="NOT_FOUND"),
        identity_id=None,
        reference_id=None,
        provider=ISSUER,
        subject="provider-subject",
        reason="identity is no longer available",
    )
    response = invoke(
        owners,
        "core001.identity.resolve",
        {"provider": ISSUER, "subject": "provider-subject"},
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "TRUSTED_CONTEXT_STALE"


def test_tenant_revision_must_match_the_server_verified_context():
    owners = Owners()
    owners.tenant_result.tenant_revision = 5
    response = invoke(
        owners,
        "core001.tenant.resolve_context",
        {"tenantId": CONTEXT["tenant"]["tenantId"]},
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "TRUSTED_CONTEXT_STALE"


def test_membership_revision_must_match_the_server_verified_context():
    owners = Owners()
    owners.membership_result.membership_revision = 8
    response = invoke(
        owners,
        "core001.membership.resolve",
        {
            "tenantId": CONTEXT["tenant"]["tenantId"],
            "organizationId": CONTEXT["tenant"]["organizationId"],
            "identityId": CONTEXT["actor"]["identityId"],
        },
        CONTEXT,
    )
    assert response["status"] == "failure"
    assert response["error"]["code"] == "TRUSTED_CONTEXT_STALE"


def test_oidc_issuer_configuration_rejects_userinfo_and_invalid_ports():
    assert protocol._is_https_issuer(ISSUER) is True
    assert protocol._is_https_issuer("https://@issuer.example.test/") is False
    assert protocol._is_https_issuer("https://issuer.example.test:invalid/") is False
    assert protocol._is_https_issuer("https://issuer.example.test/\n") is False


def test_production_owner_factory_namespace_excludes_acrl_runtime():
    from homio_python_runtime import worker

    assert worker._is_allowed_owner_module(
        "production",
        "AUTONOMY_ENGINE.core.identity_tenant.runtime_composition",
    ) is True
    assert worker._is_allowed_owner_module(
        "production",
        "AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard",
    ) is False
    assert worker._is_allowed_owner_module(
        "production",
        "homio_python_runtime.tests.fixtures.probe_owners",
    ) is False
    assert worker._is_allowed_owner_module(
        "test",
        "homio_python_runtime.tests.fixtures.probe_owners",
    ) is True


def test_versioned_contract_explicitly_excludes_acrl_from_production_owner_factory():
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[3]
    contract_path = backend_root / "contracts" / "python-runtime" / "v1" / "contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["owner_composition"]["forbidden_production_namespaces"] == [
        "AUTONOMY_ENGINE.continuity.acrl"
    ]
