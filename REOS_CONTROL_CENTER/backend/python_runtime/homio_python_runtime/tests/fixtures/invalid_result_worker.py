from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys


def main() -> int:
    line = sys.stdin.readline(1_048_578)
    if not line.endswith("\n"):
        return 2

    request = json.loads(line)
    secret_value = os.environ.get("HOMIO_PYTHON_BRIDGE_SECRET", "")

    try:
        secret = bytes.fromhex(secret_value)
    except ValueError:
        return 3

    if len(secret) != 32:
        return 4

    response = {
        "protocol": "homio.python-domain-runtime",
        "version": 1,
        "messageType": "response",
        "runtimeId": "homio-python-runtime",
        "requestId": request.get("requestId"),
        "status": "success",
        "context": request.get("context"),
        "result": {
            "issuer": "https://issuer.example.test/",
            "subject": "untrusted-subject",
        },
    }

    canonical = json.dumps(
        response,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    response["signature"] = hmac.new(
        secret,
        canonical,
        hashlib.sha256,
    ).hexdigest()

    sys.stdout.write(
        json.dumps(
            response,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
