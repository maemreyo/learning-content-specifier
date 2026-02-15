#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
TOOL_PATH="$(resolve_python_tool manage_program_context.py)"
PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: python3/python is required to manage program context" >&2
    exit 1
fi

exec "$PYTHON_BIN" "$TOOL_PATH" --repo-root "$REPO_ROOT" "$@"
