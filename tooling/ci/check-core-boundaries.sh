#!/usr/bin/env bash
set -euo pipefail

missing=0

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    missing=1
  fi
}

forbid_path() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "Forbidden path exists in core repo: $path" >&2
    missing=1
  fi
}

# Core/consumer boundary invariants.
forbid_path "scaffolds/lcs-output-consumer"
forbid_path "scripts/scaffold_output_consumer.py"
forbid_path "apps/teacher"
forbid_path "apps/learner"
forbid_path "services/bff"
forbid_path "services/workers"
forbid_path "packages/api-client"
forbid_path "packages/shared-ui"
forbid_path "packages/types"
require_file "factory/scripts/python/bootstrap_consumer.py"
require_file "factory/scripts/python/scaffold_tutoring_platform.py"
require_file "contracts/index.json"
require_file "contracts/consumer-contract-version.txt"

if rg -n --glob '!tooling/ci/check-core-boundaries.sh' "_learning-content-specifier/contracts|sync-contracts-from-specifier\\.sh" README.md docs factory tooling tests src >/dev/null 2>&1; then
  echo "Found forbidden sibling-path dependency tokens in core repo" >&2
  missing=1
fi

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

echo "Core boundary checks passed"
