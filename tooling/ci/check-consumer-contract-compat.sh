#!/usr/bin/env bash
set -euo pipefail

CONSUMER_VERSION_FILE_DEFAULT="contracts/consumer-contract-version.txt"

CORE_VERSION=$(python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('contracts/index.json').read_text(encoding='utf-8'))
print(payload.get('contract_version', '0.0.0'))
PY
)

major() {
  local v="$1"
  if [[ "$v" =~ ^([0-9]+)\.[0-9]+\.[0-9]+$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo ""
  fi
}

CONSUMER_CONTRACT_VERSION_VALUE="${CONSUMER_CONTRACT_VERSION:-}"
CONSUMER_VERSION_SOURCE="env:CONSUMER_CONTRACT_VERSION"

if [[ -z "$CONSUMER_CONTRACT_VERSION_VALUE" ]]; then
  if [[ -f "$CONSUMER_VERSION_FILE_DEFAULT" ]]; then
    CONSUMER_CONTRACT_VERSION_VALUE="$(tr -d '[:space:]' < "$CONSUMER_VERSION_FILE_DEFAULT")"
    CONSUMER_VERSION_SOURCE="$CONSUMER_VERSION_FILE_DEFAULT"
  fi
fi

if [[ -z "$CONSUMER_CONTRACT_VERSION_VALUE" ]]; then
  echo "Consumer contract version is required." >&2
  echo "Provide CONSUMER_CONTRACT_VERSION or maintain $CONSUMER_VERSION_FILE_DEFAULT." >&2
  exit 1
fi

CORE_MAJOR=$(major "$CORE_VERSION")
CONSUMER_MAJOR=$(major "$CONSUMER_CONTRACT_VERSION_VALUE")

if [[ -z "$CORE_MAJOR" || -z "$CONSUMER_MAJOR" ]]; then
  echo "Invalid semver value: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION_VALUE" >&2
  exit 1
fi

if [[ "$CORE_MAJOR" != "$CONSUMER_MAJOR" ]]; then
  echo "Contract major mismatch: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION_VALUE" >&2
  exit 1
fi

echo "Consumer/core contract major compatible: core=$CORE_VERSION consumer=$CONSUMER_CONTRACT_VERSION_VALUE (source=$CONSUMER_VERSION_SOURCE)"
