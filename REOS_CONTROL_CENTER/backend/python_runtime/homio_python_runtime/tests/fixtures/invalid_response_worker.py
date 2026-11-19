from __future__ import annotations

import json
import sys


def main() -> int:
    line = sys.stdin.readline(1_048_578)
    if not line.endswith("\n"):
        return 2

    request = json.loads(line)
    response = {
        "protocol": "homio.python-domain-runtime",
        "version": 1,
        "messageType": "response",
        "runtimeId": "homio-python-runtime",
        "requestId": request.get("requestId"),
        "status": "success",
        "context": request.get("context"),
        "result": {"forged": True},
        "signature": "0" * 64,
    }
    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
