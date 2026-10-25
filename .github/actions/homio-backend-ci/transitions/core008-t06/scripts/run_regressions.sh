#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
cd "$ROOT"

T06_TEST="REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/test_core008_t06_financial_audit_evidence.py"
FINANCIAL_DIR="REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial"
ACRL_DIR="REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl"

T06_LOG="$RUNNER_TEMP/core008-t06-focused.txt"
FINANCIAL_LOG="$RUNNER_TEMP/core008-financial-full.txt"
ACRL_LOG="$RUNNER_TEMP/acrl-full.txt"

python -m pytest -q -p no:cacheprovider "$T06_TEST" | tee "$T06_LOG"
python -m pytest -q -p no:cacheprovider "$FINANCIAL_DIR" | tee "$FINANCIAL_LOG"
python -m pytest -q -p no:cacheprovider "$ACRL_DIR" | tee "$ACRL_LOG"

read_pass_count() {
  local log_path="$1"
  local count

  count="$(
    grep -Eo '[0-9]+ passed' "$log_path" |
      tail -n 1 |
      awk '{print $1}' || true
  )"

  if [[ ! "$count" =~ ^[0-9]+$ ]] || [[ "$count" -lt 1 ]]; then
    echo "BLOCKED: no positive pytest pass count in $log_path" >&2
    return 1
  fi

  printf '%s' "$count"
}

T06_COUNT="$(read_pass_count "$T06_LOG")"
FINANCIAL_COUNT="$(read_pass_count "$FINANCIAL_LOG")"
ACRL_COUNT="$(read_pass_count "$ACRL_LOG")"

{
  echo "T06_TEST_COUNT=$T06_COUNT"
  echo "FINANCIAL_TEST_COUNT=$FINANCIAL_COUNT"
  echo "ACRL_TEST_COUNT=$ACRL_COUNT"
} >> "${GITHUB_ENV:?GITHUB_ENV is required}"

echo "T06_FOCUSED_TESTS_PASSED=$T06_COUNT"
echo "COMMISSION_FINANCIAL_TESTS_PASSED=$FINANCIAL_COUNT"
echo "COMPLETE_ACRL_TESTS_PASSED=$ACRL_COUNT"
