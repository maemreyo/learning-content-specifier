#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"

args=("$REPO_ROOT/scripts/build_contract_package.py" --repo-root "$REPO_ROOT")
if [[ $# -gt 0 ]]; then
    args+=("$@")
fi

if command -v uv >/dev/null 2>&1; then
    uv run python "${args[@]}"
else
    PYTHON_BIN="python3"
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        PYTHON_BIN="python"
    fi
    "$PYTHON_BIN" "${args[@]}"
fi
