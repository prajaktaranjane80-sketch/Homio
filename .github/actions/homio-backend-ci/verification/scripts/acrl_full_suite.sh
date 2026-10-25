#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl
