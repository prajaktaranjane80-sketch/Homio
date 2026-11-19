from __future__ import annotations

from collections import deque
import hashlib
import hmac
import json
import re
import time
from typing import Any, Mapping
from urllib.parse import urlsplit
from uuid import UUID

PROTOCOL_NAME = "homio.python-domain-runtime"
PROTOCOL_VERSION = 1
SERVICE_ID = "homio-backend"
AUDIENCE = "homio-python-domain-runtime"
RUNTIME_ID = "homio-python-runtime"
MAX_REQUEST_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 1_048_576
MAX_CLOCK_SKEW_MS = 30_000
MAX_NONCE_ENTRIES = 65_536
MAX_ACCESS_TOKEN_CHARS = 16_384
MAX_PROVIDER_CHARS = 255
MAX_SUBJECT_CHARS = 255

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

ALLOWED_OPERATIONS = frozenset({
    "oidc.verify_access_token",
    "core001.identity.resolve",
    "core001.tenant.resolve_context",
    "core001.membership.resolve",
})

_IDENTITY_STATUSES = frozenset({"RESOLVED", "NOT_FOUND", "REVOKED"})
_TENANT_STATUSES = frozenset({"RESOLVED", "NOT_FOUND", "INACTIVE", "ARCHIVED"})
_MEMBERSHIP_STATUSES = frozenset({"RESOLVED", "NOT_FOUND", "INACTIVE", "EXPIRED"})

_DOMAIN_ERROR_CODES = frozenset({
    "ISSUER_NOT_ALLOWED",
    "DOMAIN_DEPENDENCY_UNAVAILABLE",
    "DOMAIN_VALIDATION_FAILED",
    "DOMAIN_RESULT_INVALID",
    "DOMAIN_OWNER_UNAVAILABLE",
    "TENANT_SCOPE_MISMATCH",
    "ORGANIZATION_SCOPE_MISMATCH",
    "ACTOR_SCOPE_MISMATCH",
    "OPERATION_NOT_ALLOWED",
    "ACCESS_TOKEN_INVALID",
    "OIDC_VERIFIER_UNAVAILABLE",
    "OIDC_TRUST_CONFIGURATION_INVALID",
    "TRUSTED_CONTEXT_STALE",
})


class ProtocolError(ValueError):
    """Safe protocol rejection; never includes payloads, credentials or keys."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class DomainOperationError(RuntimeError):
    """Safe failure raised by an existing owner adapter."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("DUPLICATE_JSON_KEY")
        if key in {"__proto__", "prototype", "constructor"}:
            raise ProtocolError("FORBIDDEN_JSON_KEY")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ProtocolError("NON_FINITE_JSON_NUMBER")


def _validate_json_value(value: Any, *, depth: int = 0) -> None:
    if depth > 32:
        raise ProtocolError("JSON_DEPTH_EXCEEDED")

    if value is None or isinstance(value, bool):
        return

    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ProtocolError("JSON_STRING_INVALID")
        return

    if isinstance(value, int):
        if abs(value) > 9_007_199_254_740_991:
            raise ProtocolError("JSON_INTEGER_OUT_OF_RANGE")
        return

    if isinstance(value, list):
        if len(value) > 10_000:
            raise ProtocolError("JSON_ARRAY_TOO_LARGE")
        for item in value:
            _validate_json_value(item, depth=depth + 1)
        return

    if isinstance(value, dict):
        if len(value) > 10_000:
            raise ProtocolError("JSON_OBJECT_TOO_LARGE")
        for key, item in value.items():
            if not isinstance(key, str) or key in {
                "__proto__", "prototype", "constructor"
            }:
                raise ProtocolError("JSON_KEY_INVALID")
            _validate_json_value(key, depth=depth + 1)
            _validate_json_value(item, depth=depth + 1)
        return

    raise ProtocolError("JSON_VALUE_TYPE_UNSUPPORTED")


def parse_json(raw: bytes, *, maximum: int) -> Any:
    if not isinstance(raw, bytes) or not raw or len(raw) > maximum:
        raise ProtocolError("MESSAGE_SIZE_INVALID")

    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
            parse_float=lambda _value: (_ for _ in ()).throw(
                ProtocolError("FLOATING_POINT_NOT_ALLOWED")
            ),
        )
        _validate_json_value(parsed)
        return parsed
    except ProtocolError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise ProtocolError("JSON_INVALID") from None


def canonical_json(value: Any) -> str:
    _validate_json_value(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError, UnicodeEncodeError):
        raise ProtocolError("JSON_CANONICALIZATION_FAILED") from None


def _is_uuid(value: Any) -> bool:
    return isinstance(value, str) and bool(_UUID.fullmatch(value))


def _require_exact_keys(
    value: Any,
    keys: set[str],
    code: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ProtocolError(code)
    return value


def validate_correlation_context(value: Any) -> dict[str, Any]:
    context = _require_exact_keys(
        value,
        {"correlationId"},
        "CORRELATION_CONTEXT_INVALID",
    )
    if not _is_uuid(context["correlationId"]):
        raise ProtocolError("CORRELATION_ID_INVALID")
    return context


def validate_trusted_context(value: Any) -> dict[str, Any]:
    context = _require_exact_keys(
        value,
        {"actor", "tenant", "correlationId"},
        "TRUSTED_CONTEXT_INVALID",
    )
    actor = _require_exact_keys(
        context["actor"],
        {"identityId", "accountId"},
        "TRUSTED_ACTOR_INVALID",
    )
    tenant = _require_exact_keys(
        context["tenant"],
        {
            "tenantId",
            "tenantRevision",
            "organizationId",
            "membershipId",
            "membershipRevision",
        },
        "TRUSTED_TENANT_INVALID",
    )

    for field in ("identityId", "accountId"):
        if not _is_uuid(actor[field]):
            raise ProtocolError("TRUSTED_ACTOR_INVALID")

    for field in ("tenantId", "organizationId", "membershipId"):
        if not _is_uuid(tenant[field]):
            raise ProtocolError("TRUSTED_TENANT_INVALID")

    for field in ("tenantRevision", "membershipRevision"):
        revision = tenant[field]
        if type(revision) is not int or revision < 1:
            raise ProtocolError("TRUSTED_TENANT_INVALID")

    if not _is_uuid(context["correlationId"]):
        raise ProtocolError("CORRELATION_ID_INVALID")

    return context


def _is_https_issuer(value: Any) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_PROVIDER_CHARS
    ):
        return False

    if value != value.strip() or any(
        ord(character) < 0x21 or 0x7F <= ord(character) <= 0x9F
        for character in value
    ):
        return False

    try:
        parsed = urlsplit(value)
        _ = parsed.port
        return (
            parsed.scheme.lower() == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def _safe_domain_text(
    value: Any,
    *,
    maximum: int,
    code: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or value != value.strip()
        or any(
            ord(character) < 0x20 or 0x7F <= ord(character) <= 0x9F
            for character in value
        )
    ):
        raise ProtocolError(code)
    return value


class ReplayGuard:
    """Bounded, time-windowed replay protection for authenticated messages."""

    def __init__(self, maximum_entries: int = MAX_NONCE_ENTRIES) -> None:
        if type(maximum_entries) is not int or maximum_entries < 2:
            raise ValueError("maximum_entries must be at least two")

        self._maximum_entries = maximum_entries
        self._seen: dict[str, int] = {}
        self._ordered: deque[tuple[str, int]] = deque()

    def claim(self, request_id: str, nonce: str, *, now_ms: int) -> None:
        while self._ordered and self._ordered[0][1] < now_ms:
            key, expiry = self._ordered.popleft()
            if self._seen.get(key) == expiry:
                self._seen.pop(key, None)

        for value in (request_id, nonce):
            if value in self._seen:
                raise ProtocolError("REPLAY_DETECTED")

        if len(self._seen) + 2 > self._maximum_entries:
            raise ProtocolError("REPLAY_GUARD_CAPACITY_EXCEEDED")

        expiry = now_ms + MAX_CLOCK_SKEW_MS
        for value in (request_id, nonce):
            self._seen[value] = expiry
            self._ordered.append((value, expiry))


def _signature(secret: bytes, unsigned: Mapping[str, Any]) -> str:
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ProtocolError("SERVICE_SECRET_INVALID")

    return hmac.new(
        secret,
        canonical_json(dict(unsigned)).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def sign_message(secret: bytes, unsigned: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(unsigned)
    result["signature"] = _signature(secret, unsigned)
    return result


def verify_request(
    message: Any,
    secret: bytes,
    *,
    now_ms: int | None = None,
    replay_guard: ReplayGuard,
) -> dict[str, Any]:
    required = {
        "protocol",
        "version",
        "messageType",
        "serviceId",
        "audience",
        "requestId",
        "nonce",
        "issuedAtMs",
        "operation",
        "context",
        "payload",
        "idempotency",
        "signature",
    }

    request = _require_exact_keys(
        message,
        required,
        "REQUEST_ENVELOPE_INVALID",
    )

    if (
        request["protocol"] != PROTOCOL_NAME
        or type(request["version"]) is not int
        or request["version"] != PROTOCOL_VERSION
    ):
        raise ProtocolError("CONTRACT_VERSION_UNSUPPORTED")

    if request["messageType"] != "request":
        raise ProtocolError("MESSAGE_TYPE_INVALID")

    if (
        request["serviceId"] != SERVICE_ID
        or request["audience"] != AUDIENCE
    ):
        raise ProtocolError("SERVICE_IDENTITY_INVALID")

    if (
        not _is_uuid(request["requestId"])
        or not _is_uuid(request["nonce"])
        or request["requestId"] == request["nonce"]
    ):
        raise ProtocolError("REQUEST_ID_INVALID")

    issued_at = request["issuedAtMs"]
    if type(issued_at) is not int or issued_at < 0:
        raise ProtocolError("REQUEST_TIMESTAMP_INVALID")

    current = int(time.time() * 1000) if now_ms is None else now_ms
    if abs(current - issued_at) > MAX_CLOCK_SKEW_MS:
        raise ProtocolError("REQUEST_EXPIRED")

    signature = request["signature"]
    if not isinstance(signature, str) or not _HEX_SHA256.fullmatch(signature):
        raise ProtocolError("AUTHENTICATION_FAILED")

    unsigned = {
        key: value
        for key, value in request.items()
        if key != "signature"
    }
    expected = _signature(secret, unsigned)

    if not hmac.compare_digest(signature, expected):
        raise ProtocolError("AUTHENTICATION_FAILED")

    operation = request["operation"]
    if not isinstance(operation, str) or not operation or len(operation) > 96:
        raise ProtocolError("OPERATION_INVALID")

    if not isinstance(request["payload"], dict):
        raise ProtocolError("PAYLOAD_INVALID")

    _validate_json_value(request["payload"])

    if request["idempotency"] is not None:
        # V1 exposes only read operations. Mutation support remains disabled
        # until the canonical B4 durable idempotency owner is injected.
        raise ProtocolError("MUTATION_NOT_ENABLED")

    if operation in {
        "oidc.verify_access_token",
        "core001.identity.resolve",
    }:
        if (
            isinstance(request["context"], dict)
            and set(request["context"]) == {"correlationId"}
        ):
            validate_correlation_context(request["context"])
        else:
            validate_trusted_context(request["context"])
    else:
        validate_trusted_context(request["context"])

    replay_guard.claim(
        request["requestId"],
        request["nonce"],
        now_ms=current,
    )
    return request


def _uuid(value: Any, code: str) -> UUID:
    if not _is_uuid(value):
        raise ProtocolError(code)
    return UUID(value)


def _uuid_value(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str) and _is_uuid(value):
        return value
    raise ProtocolError("DOMAIN_RESULT_INVALID")


def _enum_value(value: Any, allowed: frozenset[str]) -> str:
    candidate = getattr(value, "value", value)
    if not isinstance(candidate, str) or candidate not in allowed:
        raise ProtocolError("DOMAIN_RESULT_INVALID")
    return candidate


def _map_domain_failure(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, DomainOperationError):
        code = (
            exc.code
            if exc.code in _DOMAIN_ERROR_CODES
            else "DOMAIN_EXECUTION_FAILED"
        )
        messages = {
            "ISSUER_NOT_ALLOWED": "The identity issuer is not configured for this runtime.",
            "DOMAIN_DEPENDENCY_UNAVAILABLE": "A required domain dependency is unavailable.",
            "DOMAIN_VALIDATION_FAILED": "The domain request was rejected.",
            "DOMAIN_RESULT_INVALID": "A canonical domain owner returned an invalid result.",
            "DOMAIN_OWNER_UNAVAILABLE": "A canonical domain owner is unavailable.",
            "TENANT_SCOPE_MISMATCH": "The requested tenant is outside the trusted context.",
            "ORGANIZATION_SCOPE_MISMATCH": "The requested organization is outside the trusted context.",
            "ACTOR_SCOPE_MISMATCH": "The requested actor is outside the trusted context.",
            "OPERATION_NOT_ALLOWED": "The requested domain operation is not enabled.",
            "ACCESS_TOKEN_INVALID": "The access token is invalid.",
            "OIDC_VERIFIER_UNAVAILABLE": "The identity verification service is unavailable.",
            "OIDC_TRUST_CONFIGURATION_INVALID": "The verified identity does not match the configured API trust boundary.",
            "TRUSTED_CONTEXT_STALE": "The canonical identity, tenant or membership changed after the trusted context was established.",
        }
        return code, messages[code]

    if isinstance(exc, (ConnectionError, TimeoutError)):
        return (
            "DOMAIN_DEPENDENCY_UNAVAILABLE",
            "A required domain dependency is unavailable.",
        )

    if isinstance(exc, (TypeError, ValueError)):
        return "DOMAIN_VALIDATION_FAILED", "The domain request was rejected."

    return "DOMAIN_EXECUTION_FAILED", "The domain operation failed."


class PythonDomainRuntime:
    """Thin transport adapter over injected existing Python domain owners."""

    def __init__(
        self,
        *,
        oidc_verifier: Any,
        identity_resolver: Any,
        tenant_resolver: Any,
        membership_resolver: Any,
        trusted_issuer: str,
        trusted_audience: str,
    ) -> None:
        required = (
            (oidc_verifier, "verify_access_token"),
            (identity_resolver, "resolve_external"),
            (tenant_resolver, "resolve_context"),
            (membership_resolver, "resolve_membership"),
        )

        if any(
            not callable(getattr(owner, method, None))
            for owner, method in required
        ):
            raise ValueError("Canonical Python domain-owner ports are incomplete.")

        if not _is_https_issuer(trusted_issuer):
            raise ValueError("The trusted OIDC issuer is invalid.")

        if (
            not isinstance(trusted_audience, str)
            or not trusted_audience
            or len(trusted_audience) > 512
            or trusted_audience != trusted_audience.strip()
            or any(
                ord(character) < 0x21 or 0x7F <= ord(character) <= 0x9F
                for character in trusted_audience
            )
        ):
            raise ValueError("The trusted OIDC audience is invalid.")

        self._oidc = oidc_verifier
        self._identity = identity_resolver
        self._tenant = tenant_resolver
        self._membership = membership_resolver
        self._trusted_issuer = trusted_issuer
        self._trusted_audience = trusted_audience

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        operation = request["operation"]
        payload = request["payload"]
        context = request["context"]

        if operation not in ALLOWED_OPERATIONS:
            raise DomainOperationError("OPERATION_NOT_ALLOWED")

        try:
            if operation == "oidc.verify_access_token":
                if set(payload) != {"accessToken"}:
                    raise ProtocolError("PAYLOAD_INVALID")

                token = payload["accessToken"]
                if (
                    not isinstance(token, str)
                    or not token
                    or len(token) > MAX_ACCESS_TOKEN_CHARS
                    or token != token.strip()
                    or any(
                        ord(character) < 0x21 or ord(character) == 0x7F
                        for character in token
                    )
                ):
                    raise ProtocolError("ACCESS_TOKEN_INVALID")

                try:
                    principal = self._oidc.verify_access_token(token)
                except Exception as exc:
                    code = getattr(exc, "code", None)
                    invalid_token_codes = {
                        "malformed_access_token",
                        "unsupported_token_algorithm",
                        "invalid_access_token_type",
                        "unsupported_critical_token_header",
                        "invalid_signing_key_id",
                        "invalid_access_token",
                    }
                    if code in invalid_token_codes:
                        raise DomainOperationError("ACCESS_TOKEN_INVALID") from None

                    # Unknown verifier failures are dependency failures, never proof
                    # that the caller supplied an invalid credential.
                    raise DomainOperationError("OIDC_VERIFIER_UNAVAILABLE") from None

                issuer = _safe_domain_text(
                    principal.issuer,
                    maximum=MAX_PROVIDER_CHARS,
                    code="DOMAIN_RESULT_INVALID",
                )
                subject = _safe_domain_text(
                    principal.subject,
                    maximum=MAX_SUBJECT_CHARS,
                    code="DOMAIN_RESULT_INVALID",
                )
                client_id = _safe_domain_text(
                    principal.client_id,
                    maximum=512,
                    code="DOMAIN_RESULT_INVALID",
                )
                token_id = _safe_domain_text(
                    principal.token_id,
                    maximum=255,
                    code="DOMAIN_RESULT_INVALID",
                )
                audiences = principal.audiences

                if (
                    not _is_https_issuer(issuer)
                    or issuer != self._trusted_issuer
                    or not isinstance(audiences, (tuple, list))
                    or not 1 <= len(audiences) <= 16
                ):
                    raise DomainOperationError("OIDC_TRUST_CONFIGURATION_INVALID")

                normalized_audiences = [
                    _safe_domain_text(
                        value,
                        maximum=2048,
                        code="DOMAIN_RESULT_INVALID",
                    )
                    for value in audiences
                ]

                if self._trusted_audience not in normalized_audiences:
                    raise DomainOperationError("OIDC_TRUST_CONFIGURATION_INVALID")

                return {
                    "issuer": issuer,
                    "subject": subject,
                    "audiences": normalized_audiences,
                    "clientId": client_id,
                    "tokenId": token_id,
                }

            if operation == "core001.identity.resolve":
                if set(payload) != {"provider", "subject"}:
                    raise ProtocolError("PAYLOAD_INVALID")

                provider = payload["provider"]
                subject = payload["subject"]

                if (
                    not _is_https_issuer(provider)
                    or provider != self._trusted_issuer
                    or not isinstance(subject, str)
                    or not subject
                    or len(subject) > MAX_SUBJECT_CHARS
                    or subject != subject.strip()
                    or any(
                        ord(character) < 0x20 or ord(character) == 0x7F
                        for character in subject
                    )
                ):
                    raise DomainOperationError("ISSUER_NOT_ALLOWED")

                result = self._identity.resolve_external(provider, subject)
                status = _enum_value(result.status, _IDENTITY_STATUSES)
                identity_id = (
                    None
                    if result.identity_id is None
                    else _uuid_value(result.identity_id)
                )
                reference_id = (
                    None
                    if result.reference_id is None
                    else _uuid_value(result.reference_id)
                )

                if status == "RESOLVED" and (
                    identity_id is None or reference_id is None
                ):
                    raise ProtocolError("DOMAIN_RESULT_INVALID")

                if context.get("actor") is not None:
                    if status != "RESOLVED" or identity_id is None:
                        raise DomainOperationError("TRUSTED_CONTEXT_STALE")
                    if identity_id != context["actor"]["identityId"]:
                        raise DomainOperationError("ACTOR_SCOPE_MISMATCH")

                return {
                    "status": status,
                    "identityId": identity_id,
                    "referenceId": reference_id,
                }

            if operation == "core001.tenant.resolve_context":
                if set(payload) != {"tenantId"}:
                    raise ProtocolError("PAYLOAD_INVALID")

                tenant_id = _uuid(payload["tenantId"], "TENANT_ID_INVALID")
                if str(tenant_id) != context["tenant"]["tenantId"]:
                    raise DomainOperationError("TENANT_SCOPE_MISMATCH")

                result = self._tenant.resolve_context(tenant_id)
                status = _enum_value(result.status, _TENANT_STATUSES)
                result_tenant_id = _uuid_value(result.tenant_id)

                if result_tenant_id != str(tenant_id):
                    raise ProtocolError("DOMAIN_RESULT_INVALID")

                revision = result.tenant_revision
                tenant_context = result.context

                if (
                    status != "RESOLVED"
                    or revision != context["tenant"]["tenantRevision"]
                ):
                    raise DomainOperationError("TRUSTED_CONTEXT_STALE")

                if status == "RESOLVED":
                    if (
                        type(revision) is not int
                        or revision < 1
                        or tenant_context is None
                    ):
                        raise ProtocolError("DOMAIN_RESULT_INVALID")

                    projected_context = {
                        "tenantStatus": _enum_value(
                            tenant_context.tenant_status,
                            frozenset({"ACTIVE", "RESTRICTED"}),
                        ),
                        "tenantKind": _safe_domain_text(
                            _enum_value(
                                tenant_context.tenant_kind,
                                frozenset({
                                    "BROKERAGE",
                                    "BUILDER",
                                    "ENTERPRISE",
                                    "PARTNER",
                                    "PLATFORM",
                                }),
                            ),
                            maximum=32,
                            code="DOMAIN_RESULT_INVALID",
                        ),
                        "operatingMode": _safe_domain_text(
                            _enum_value(
                                tenant_context.operating_mode,
                                frozenset({
                                    "OWNED_INTERNATIONAL_BROKERAGE",
                                    "BROKER_SAAS",
                                    "BUILDER_SAAS",
                                    "ENTERPRISE_WHITE_LABEL",
                                    "PLATFORM_API_PARTNER",
                                }),
                            ),
                            maximum=64,
                            code="DOMAIN_RESULT_INVALID",
                        ),
                    }
                else:
                    if revision is not None and (
                        type(revision) is not int or revision < 1
                    ):
                        raise ProtocolError("DOMAIN_RESULT_INVALID")
                    projected_context = None

                return {
                    "status": status,
                    "tenantId": result_tenant_id,
                    "tenantRevision": revision,
                    "context": projected_context,
                }

            if operation == "core001.membership.resolve":
                if set(payload) != {
                    "tenantId",
                    "organizationId",
                    "identityId",
                }:
                    raise ProtocolError("PAYLOAD_INVALID")

                tenant_id = _uuid(payload["tenantId"], "TENANT_ID_INVALID")
                organization_id = _uuid(
                    payload["organizationId"],
                    "ORGANIZATION_ID_INVALID",
                )
                identity_id = _uuid(
                    payload["identityId"],
                    "IDENTITY_ID_INVALID",
                )

                tenant_scope = context["tenant"]
                actor_scope = context["actor"]

                if str(tenant_id) != tenant_scope["tenantId"]:
                    raise DomainOperationError("TENANT_SCOPE_MISMATCH")
                if str(organization_id) != tenant_scope["organizationId"]:
                    raise DomainOperationError("ORGANIZATION_SCOPE_MISMATCH")
                if str(identity_id) != actor_scope["identityId"]:
                    raise DomainOperationError("ACTOR_SCOPE_MISMATCH")

                result = self._membership.resolve_membership(
                    tenant_id=tenant_id,
                    organization_id=organization_id,
                    identity_id=identity_id,
                )
                status = _enum_value(result.status, _MEMBERSHIP_STATUSES)

                returned_scope = (
                    _uuid_value(result.tenant_id),
                    _uuid_value(result.organization_id),
                    _uuid_value(result.identity_id),
                )
                requested_scope = (
                    str(tenant_id),
                    str(organization_id),
                    str(identity_id),
                )

                if returned_scope != requested_scope:
                    raise ProtocolError("DOMAIN_RESULT_INVALID")

                membership_id = (
                    None
                    if result.membership_id is None
                    else _uuid_value(result.membership_id)
                )
                revision = result.membership_revision

                if (
                    status != "RESOLVED"
                    or revision != tenant_scope["membershipRevision"]
                    or membership_id is None
                ):
                    raise DomainOperationError("TRUSTED_CONTEXT_STALE")

                if status == "RESOLVED":
                    if (
                        membership_id is None
                        or type(revision) is not int
                        or revision < 1
                    ):
                        raise ProtocolError("DOMAIN_RESULT_INVALID")
                elif revision is not None and (
                    type(revision) is not int or revision < 1
                ):
                    raise ProtocolError("DOMAIN_RESULT_INVALID")

                return {
                    "status": status,
                    "membershipId": membership_id,
                    "tenantId": requested_scope[0],
                    "organizationId": requested_scope[1],
                    "identityId": requested_scope[2],
                    "membershipRevision": revision,
                }

            raise DomainOperationError("OPERATION_NOT_ALLOWED")

        except (ProtocolError, DomainOperationError):
            raise
        except Exception as exc:
            code, _message = _map_domain_failure(exc)
            raise DomainOperationError(code) from None


def process_request(
    raw: bytes,
    runtime: PythonDomainRuntime,
    *,
    secret: bytes,
    replay_guard: ReplayGuard,
    now_ms: int | None = None,
) -> bytes:
    message = parse_json(raw, maximum=MAX_REQUEST_BYTES)
    request = verify_request(
        message,
        secret,
        now_ms=now_ms,
        replay_guard=replay_guard,
    )

    try:
        result = runtime.dispatch(request)
        if not isinstance(result, dict):
            raise ProtocolError("DOMAIN_RESULT_INVALID")

        _validate_json_value(result)
        response: dict[str, Any] = {
            "protocol": PROTOCOL_NAME,
            "version": PROTOCOL_VERSION,
            "messageType": "response",
            "runtimeId": RUNTIME_ID,
            "requestId": request["requestId"],
            "status": "success",
            "context": request["context"],
            "result": result,
        }

    except (DomainOperationError, ProtocolError) as exc:
        if isinstance(exc, DomainOperationError):
            code, message_text = _map_domain_failure(exc)
        else:
            code, message_text = (
                exc.code,
                "The runtime request was rejected.",
            )

        response = {
            "protocol": PROTOCOL_NAME,
            "version": PROTOCOL_VERSION,
            "messageType": "response",
            "runtimeId": RUNTIME_ID,
            "requestId": request["requestId"],
            "status": "failure",
            "context": request["context"],
            "error": {
                "code": code,
                "message": message_text,
                "retryable": code in {
                    "DOMAIN_DEPENDENCY_UNAVAILABLE",
                    "OIDC_VERIFIER_UNAVAILABLE",
                },
            },
        }

    signed = sign_message(secret, response)
    encoded = canonical_json(signed).encode("utf-8")
    if len(encoded) > MAX_RESPONSE_BYTES:
        raise ProtocolError("RESPONSE_SIZE_EXCEEDED")
    return encoded


__all__ = [
    "ALLOWED_OPERATIONS",
    "AUDIENCE",
    "DomainOperationError",
    "MAX_REQUEST_BYTES",
    "MAX_RESPONSE_BYTES",
    "PROTOCOL_NAME",
    "PROTOCOL_VERSION",
    "ProtocolError",
    "PythonDomainRuntime",
    "ReplayGuard",
    "RUNTIME_ID",
    "SERVICE_ID",
    "canonical_json",
    "parse_json",
    "process_request",
    "sign_message",
    "validate_correlation_context",
    "validate_trusted_context",
    "verify_request",
]
