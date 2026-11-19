from __future__ import annotations

import importlib
import os
from pathlib import Path
import re
import sys
from typing import BinaryIO

_PACKAGE_PARENT = Path(__file__).resolve().parents[1]
if str(_PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_PARENT))

from homio_python_runtime.protocol import (
    MAX_REQUEST_BYTES,
    ProtocolError,
    PythonDomainRuntime,
    ReplayGuard,
    process_request,
)

_FACTORY = re.compile(
    r"^(?P<module>[A-Za-z_][A-Za-z0-9_.]*)\:(?P<factory>[A-Za-z_][A-Za-z0-9_]*)$"
)
_SECRET = re.compile(r"^[0-9a-f]{64}$")


def run_worker(
    runtime: PythonDomainRuntime,
    *,
    secret: bytes,
    input_stream: BinaryIO,
    output_stream: BinaryIO,
    error_stream: BinaryIO,
) -> int:
    """Serve authenticated newline-delimited IPC; stdout is protocol-only."""
    replay_guard = ReplayGuard()

    while True:
        raw = input_stream.readline(MAX_REQUEST_BYTES + 2)
        if raw == b"":
            return 0

        if len(raw) > MAX_REQUEST_BYTES + 1 or not raw.endswith(b"\n"):
            error_stream.write(b"PYTHON_RUNTIME_MESSAGE_FRAMING_INVALID\n")
            error_stream.flush()
            return 2

        frame = raw[:-1]

        try:
            response = process_request(
                frame,
                runtime,
                secret=secret,
                replay_guard=replay_guard,
            )
        except ProtocolError as exc:
            # Never emit an unsigned response for an unauthenticated frame.
            error_stream.write(
                (f"PYTHON_RUNTIME_PROTOCOL_REJECTED:{exc.code}\n").encode("ascii")
            )
            error_stream.flush()
            return 3
        except Exception:
            # Do not print tracebacks or payload material across the IPC boundary.
            error_stream.write(b"PYTHON_RUNTIME_UNEXPECTED_FAILURE\n")
            error_stream.flush()
            return 6

        output_stream.write(response + b"\n")
        output_stream.flush()


def _is_allowed_owner_module(mode: str, module_name: str) -> bool:
    is_acrl = (
        module_name == "AUTONOMY_ENGINE.continuity.acrl"
        or module_name.startswith("AUTONOMY_ENGINE.continuity.acrl.")
    )
    is_domain_owner = module_name.startswith("AUTONOMY_ENGINE.") and not is_acrl
    is_test_fixture = module_name.startswith(
        "homio_python_runtime.tests.fixtures."
    )

    if mode == "production":
        return is_domain_owner
    if mode == "test":
        return is_domain_owner or is_test_fixture
    return False


def _load_runtime() -> PythonDomainRuntime:
    mode = os.environ.get("HOMIO_PYTHON_RUNTIME_MODE")
    factory_value = os.environ.get("HOMIO_PYTHON_RUNTIME_OWNER_FACTORY")
    match = _FACTORY.fullmatch(factory_value or "")

    if mode not in {"production", "test"} or match is None:
        raise RuntimeError("Python runtime owner composition is not configured.")

    module_name = match.group("module")
    factory_name = match.group("factory")

    if not _is_allowed_owner_module(mode, module_name):
        raise RuntimeError("Python runtime owner factory is outside its approved namespace.")

    module = importlib.import_module(module_name)
    factory = getattr(module, factory_name, None)

    if not callable(factory):
        raise RuntimeError("Python runtime owner factory is unavailable.")

    runtime = factory()
    if not isinstance(runtime, PythonDomainRuntime):
        raise RuntimeError("Python runtime owner factory returned an invalid runtime.")

    return runtime


def main() -> int:
    # Make the canonical Python domain package importable without changing cwd.
    control_center_root = Path(__file__).resolve().parents[3]
    if str(control_center_root) not in sys.path:
        sys.path.insert(0, str(control_center_root))

    secret_value = os.environ.get("HOMIO_PYTHON_BRIDGE_SECRET", "")
    if not _SECRET.fullmatch(secret_value):
        sys.stderr.write("PYTHON_RUNTIME_SERVICE_SECRET_INVALID\n")
        return 4

    try:
        runtime = _load_runtime()
    except Exception:
        sys.stderr.write("PYTHON_RUNTIME_OWNER_COMPOSITION_UNAVAILABLE\n")
        return 5

    return run_worker(
        runtime,
        secret=bytes.fromhex(secret_value),
        input_stream=sys.stdin.buffer,
        output_stream=sys.stdout.buffer,
        error_stream=sys.stderr.buffer,
    )


if __name__ == "__main__":
    raise SystemExit(main())
