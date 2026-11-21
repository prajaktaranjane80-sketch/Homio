#!/usr/bin/env python3
"""Verify the canonical rate-limit Lua script against a real Redis 8 service.

Only randomly named ephemeral CI keys are created. Production thresholds,
HMAC secrets and Redis key versions are not supplied or inferred here.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
RATE_LIMIT_SOURCE = (
    ROOT / "REOS_CONTROL_CENTER" / "backend" / "src" / "persistence"
    / "redis-rate-limit.ts"
)
SCRIPT_PATTERN = re.compile(
    r"export const REDIS_RATE_LIMIT_SCRIPT\s*=\s*`(?P<script>.*?)`\.trim\(\);",
    re.DOTALL,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_rate_limit_script() -> str:
    try:
        source = RATE_LIMIT_SOURCE.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Cannot read canonical Redis rate-limit owner: {RATE_LIMIT_SOURCE}") from exc
    matches = list(SCRIPT_PATTERN.finditer(source))
    require(len(matches) == 1,
            "Expected exactly one REDIS_RATE_LIMIT_SCRIPT owner in canonical TypeScript source.")
    script = matches[0].group("script").strip()
    require(bool(script) and "${" not in script and "`" not in script,
            "The canonical Redis rate-limit script is malformed.")
    for fragment in ("INCR", "PEXPIRE", "PTTL", "INVALID_RATE_LIMIT_ARGUMENTS"):
        require(fragment in script, f"Canonical Redis script is missing {fragment}.")
    return script


def run_redis(container_id: str, script: str, key: str,
              max_requests: int, window_ms: int) -> tuple[int, int, int]:
    command = [
        "docker", "exec", "-i", container_id, "redis-cli", "--raw",
        "EVAL", script, "1", key, str(max_requests), str(window_ms),
    ]
    result = subprocess.run(
        command, text=True, capture_output=True, check=False, timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Redis EVAL failed: {(result.stderr or result.stdout).strip()[:1000]}"
        )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    require(len(lines) == 3, f"Redis EVAL returned an invalid tuple: {lines}")
    try:
        values = tuple(int(value) for value in lines)
    except ValueError as exc:
        raise RuntimeError("Redis EVAL returned a non-integer result.") from exc
    require(values[0] in (0, 1) and values[1] >= 0 and values[2] >= 1,
            f"Redis EVAL returned out-of-contract values: {values}")
    return values  # type: ignore[return-value]


def redis_version(container_id: str) -> str:
    result = subprocess.run(
        ["docker", "exec", container_id, "redis-cli", "--raw", "INFO", "server"],
        text=True, capture_output=True, check=False, timeout=15,
    )
    require(result.returncode == 0, "Redis INFO server query failed.")
    match = re.search(r"(?m)^redis_version:([0-9]+\.[0-9]+\.[0-9]+)\s*$", result.stdout)
    require(match is not None and match.group(1).startswith("8."),
            "The integration service is not Redis 8.x.")
    return match.group(1)


def verify_shared_atomic_window(container_id: str, script: str) -> None:
    key = f"homio:ci:rate-limit:{secrets.token_hex(16)}"
    limit = 5
    window_ms = 5_000
    call_count = 24
    results: list[tuple[int, int, int]] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [
            executor.submit(run_redis, container_id, script, key, limit, window_ms)
            for _ in range(call_count)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    allowed = [item for item in results if item[0] == 1]
    denied = [item for item in results if item[0] == 0]
    require(len(allowed) == limit,
            f"Atomic distributed limit allowed {len(allowed)} calls; expected {limit}.")
    require(len(denied) == call_count - limit,
            f"Atomic distributed limit denied {len(denied)} calls; expected {call_count - limit}.")
    require(all(item[1] > 0 for item in results),
            "Redis rate-limit counter lost its expiry during concurrent access.")
    require(sorted(item[2] for item in results) == list(range(1, call_count + 1)),
            "Redis INCR sequence contains duplicates or missing increments.")


def verify_expiry(container_id: str, script: str) -> None:
    key = f"homio:ci:rate-limit-expiry:{secrets.token_hex(16)}"
    first = run_redis(container_id, script, key, 1, 500)
    require(first[0] == 1 and first[2] == 1,
            "The first request in a fresh Redis window was not allowed.")
    second = run_redis(container_id, script, key, 1, 500)
    require(second[0] == 0 and second[2] == 2,
            "The second request exceeded the configured one-request test window but was not denied.")
    time.sleep(0.65)
    after_expiry = run_redis(container_id, script, key, 1, 500)
    require(after_expiry[0] == 1 and after_expiry[2] == 1,
            "Redis rate-limit counter did not reset after its expiry.")


def self_test() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    for fragment in ("REDIS_RATE_LIMIT_SCRIPT", "ThreadPoolExecutor",
                     "redis_version", "verify_expiry", "secrets.token_hex"):
        require(fragment in source, f"Redis rate-limit verifier is missing {fragment}.")
    print("PASS: Redis 8 atomic rate-limit verifier contract.")


def main() -> int:
    if "--self-test" in sys.argv:
        self_test()
        return 0
    container_id = os.environ.get("REDIS_SERVICE_CONTAINER", "").strip()
    require(bool(container_id), "REDIS_SERVICE_CONTAINER is required in CI.")
    require(shutil.which("docker") is not None,
            "Docker CLI is required for Redis integration verification.")
    script = load_rate_limit_script()
    version = redis_version(container_id)
    verify_shared_atomic_window(container_id, script)
    verify_expiry(container_id, script)
    print(
        f"PASS: Redis {version} atomic shared-window enforcement, "
        "24 concurrent calls across independent clients, and TTL reset."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: Redis 8 rate-limit integration verification: {exc}", file=sys.stderr)
        raise SystemExit(1)
