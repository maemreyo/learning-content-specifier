#!/usr/bin/env bash
set -euo pipefail

CORE_VERSION=$(python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('contracts/index.json').read_text(encoding='utf-8'))
print(payload.get('contract_version', '0.0.0'))
PY
)

if [[ -z "${CONSUMER_CONTRACT_VERSION:-}" ]]; then
  echo "Consumer contract version not provided; skipping explicit compatibility compare (core=$CORE_VERSION)"
  exit 0
fi

major() {
  local v="$1"
  if [[ "$v" =~ ^([0-9]+)\.[0-9]+\.[0-9]+$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo ""
  fi
}

CORE_MAJOR=$(major "$CORE_VERSION")
CONSUMER_MAJOR=$(major "$CONSUMER_CONTRACT_VERSION")

if [[ -z "$CORE_MAJOR" || -z "$CONSUMER_MAJOR" ]]; then
  echo "Invalid semver value: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION" >&2
  exit 1
fi

if [[ "$CORE_MAJOR" != "$CONSUMER_MAJOR" ]]; then
  echo "Contract major mismatch: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION" >&2
  exit 1
fi

echo "Consumer/core contract major compatible: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION"
