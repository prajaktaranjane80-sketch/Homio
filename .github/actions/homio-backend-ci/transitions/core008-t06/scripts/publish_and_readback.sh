#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
cd "$ROOT"

fail() {
  echo "PUBLISH BLOCKED: $1" >&2
  exit 1
}

for key in \
  EXPECTED_SHA \
  VERIFIED_CODE_SHA \
  ACTIONS_RUN_ID \
  ACTIONS_SERVER_URL \
  ACTIONS_REPOSITORY
do
  if [[ -z "${!key:-}" ]]; then
    fail "required environment variable is missing: $key"
  fi
done

if [[ "${GITHUB_REF:-}" != "refs/heads/reos-development" ]]; then
  fail "canonical branch is not reos-development"
fi

if [[ "${GITHUB_ACTOR:-}" != "prajaktaranjane80-sketch" ]]; then
  fail "transition actor is not the repository owner"
fi

if [[ "$EXPECTED_SHA" != "$VERIFIED_CODE_SHA" ]]; then
  fail "expected SHA and verified code SHA disagree"
fi

INITIAL_SHA="$(git rev-parse HEAD)"
if [[ "$INITIAL_SHA" != "$EXPECTED_SHA" ]]; then
  fail "HEAD changed after regression verification"
fi

git fetch --no-tags origin refs/heads/reos-development
PREFLIGHT_REMOTE_SHA="$(git rev-parse FETCH_HEAD)"

if [[ "$PREFLIGHT_REMOTE_SHA" != "$EXPECTED_SHA" ]]; then
  fail "canonical branch moved before transition publication"
fi

EXPECTED_TRACKED=(
  "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt"
  "REOS_CONTROL_CENTER/data/state.json"
  "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
)

ACTUAL_TRACKED="$(git diff --name-only | LC_ALL=C sort)"
EXPECTED_TRACKED_SORTED="$(
  printf '%s\n' "${EXPECTED_TRACKED[@]}" | LC_ALL=C sort
)"

if [[ "$ACTUAL_TRACKED" != "$EXPECTED_TRACKED_SORTED" ]]; then
  echo "PUBLISH BLOCKED: unexpected tracked changes." >&2
  echo "Expected:" >&2
  printf '%s\n' "$EXPECTED_TRACKED_SORTED" >&2
  echo "Actual:" >&2
  printf '%s\n' "$ACTUAL_TRACKED" >&2
  exit 1
fi

git -c core.whitespace=cr-at-eol diff --check

mapfile -t UNTRACKED_PATHS < <(
  git ls-files --others --exclude-standard | LC_ALL=C sort
)

if [[ "${#UNTRACKED_PATHS[@]}" -ne 2 ]]; then
  echo "PUBLISH BLOCKED: expected exactly the T06 evidence and one controller snapshot." >&2
  printf '%s\n' "${UNTRACKED_PATHS[@]}" >&2
  exit 1
fi

EVIDENCE_PATH="REOS_CONTROL_CENTER/evidence/CORE-008/T06-financial-audit-ci-evidence.md"
SNAPSHOT_PATH=""
EVIDENCE_FOUND="false"

for path in "${UNTRACKED_PATHS[@]}"; do
  if [[ "$path" == "$EVIDENCE_PATH" ]]; then
    EVIDENCE_FOUND="true"
  elif [[ "$path" =~ ^REOS_CONTROL_CENTER/snapshots/state_[0-9]{8}_[0-9]{6}_[0-9]{6}\.json$ ]]; then
    SNAPSHOT_PATH="$path"
  else
    fail "unexpected untracked path: $path"
  fi
done

if [[ "$EVIDENCE_FOUND" != "true" || -z "$SNAPSHOT_PATH" ]]; then
  fail "T06 evidence or controller snapshot is missing"
fi

python - "$SNAPSHOT_PATH" <<'PY'
import json
import sys
from pathlib import Path

from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

path = Path(sys.argv[1])
snapshot = json.loads(path.read_text(encoding="utf-8"))
stored_hash = snapshot.get("integrity", {}).get("sha256")

if not isinstance(stored_hash, str) or stored_hash != calculate_hash(snapshot):
    raise SystemExit("PUBLISH BLOCKED: controller snapshot integrity is invalid.")

print(f"SNAPSHOT INTEGRITY PASS: {path}")
PY

git add -- \
  REOS_CONTROL_CENTER/data/state.json \
  REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt \
  REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt \
  "$EVIDENCE_PATH" \
  "$SNAPSHOT_PATH"

git -c core.whitespace=cr-at-eol diff --cached --check

STAGED="$(git diff --cached --name-only | LC_ALL=C sort)"
EXPECTED_STAGED="$(
  printf '%s\n' \
    "${EXPECTED_TRACKED[@]}" \
    "$EVIDENCE_PATH" \
    "$SNAPSHOT_PATH" |
    LC_ALL=C sort
)"

if [[ "$STAGED" != "$EXPECTED_STAGED" ]]; then
  echo "PUBLISH BLOCKED: staged paths differ from the approved transition allowlist." >&2
  echo "Expected:" >&2
  printf '%s\n' "$EXPECTED_STAGED" >&2
  echo "Actual:" >&2
  printf '%s\n' "$STAGED" >&2
  exit 1
fi

git \
  -c user.name='github-actions[bot]' \
  -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
  commit -m "chore(control-center): complete CORE-008-T06 via controller"

LOCAL_COMMIT="$(git rev-parse HEAD)"
PARENT_COMMIT="$(git rev-parse HEAD^)"

if [[ "$PARENT_COMMIT" != "$EXPECTED_SHA" ]]; then
  fail "transition commit parent is not the exact verified code commit"
fi

git push origin HEAD:refs/heads/reos-development
git fetch --no-tags origin refs/heads/reos-development
REMOTE_SHA="$(git rev-parse FETCH_HEAD)"

if [[ "$REMOTE_SHA" != "$LOCAL_COMMIT" ]]; then
  fail "canonical branch readback does not match the published transition commit"
fi

git show "$REMOTE_SHA:REOS_CONTROL_CENTER/data/state.json" \
  > "${RUNNER_TEMP:?RUNNER_TEMP is required}/reos-state-readback.json"

python - <<'PY'
import json
import os
from pathlib import Path

from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

state_path = Path(os.environ["RUNNER_TEMP"]) / "reos-state-readback.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

execution = state.get("execution", {})
gate = state.get("gate_plans", {}).get("CORE-008", {})
subtasks = {
    item.get("id"): item
    for item in gate.get("subtasks", [])
}
criteria = {
    item.get("id"): item.get("status")
    for item in gate.get("criteria_state", [])
}

expected_criteria = {
    "CORE-008-AC01": "PENDING",
    "CORE-008-AC02": "VERIFIED",
    "CORE-008-AC03": "VERIFIED",
    "CORE-008-AC04": "PENDING",
    "CORE-008-AC05": "PENDING",
    "CORE-008-AC06": "PENDING",
}

stored_hash = state.get("integrity", {}).get("sha256")
if not isinstance(stored_hash, str) or stored_hash != calculate_hash(state):
    raise SystemExit("CANONICAL READBACK FAILED: state integrity is invalid.")

assert execution.get("current_gate") == "CORE-008", execution
assert execution.get("current_subtask") == "CORE-008-T07", execution
assert gate.get("status") == "CURRENT", gate
assert (
    state.get("session", {}).get("last_handoff")
    == "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
)
assert subtasks.get("CORE-008-T05", {}).get("status") == "DONE", subtasks
assert subtasks.get("CORE-008-T06", {}).get("status") == "DONE", subtasks
assert subtasks.get("CORE-008-T07", {}).get("status") == "CURRENT", subtasks
assert criteria == expected_criteria, criteria

print(
    "CANONICAL READBACK PASS: "
    "T05=DONE; T06=DONE; T07=CURRENT; acceptance criteria unchanged."
)
PY

for path in \
  "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt" \
  "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt"
do
  git show "$REMOTE_SHA:$path" | grep -Fq 'CURRENT_SUBTASK=CORE-008-T07'
  git show "$REMOTE_SHA:$path" | grep -Fq \
    'CORE-008-T06|DONE|Implement financial audit and evidence'
  git show "$REMOTE_SHA:$path" | grep -Fq \
    'CORE-008-T07|CURRENT|Implement financial reporting hooks'
done

git show "$REMOTE_SHA:$EVIDENCE_PATH" |
  grep -Fq 'T06 implementation, focused tests, full financial and ACRL regressions'

git show "$REMOTE_SHA:$EVIDENCE_PATH" |
  grep -Fq "$VERIFIED_CODE_SHA"

git show "$REMOTE_SHA:$EVIDENCE_PATH" |
  grep -Fq "$ACTIONS_RUN_ID"

echo "TRANSITION_COMMIT=$LOCAL_COMMIT"
echo "CANONICAL_BRANCH_HEAD=$REMOTE_SHA"
echo "READBACK=PASS"
