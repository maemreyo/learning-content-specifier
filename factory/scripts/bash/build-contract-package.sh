#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/common.sh"

BUILD_TOOL="$(resolve_python_tool build_contract_package.py)"
args=("$BUILD_TOOL" --repo-root "$REPO_ROOT")
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
