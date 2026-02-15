#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
UNIT_DIR_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --unit-dir)
            UNIT_DIR_OVERRIDE="${2:-}"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--unit-dir <path>]"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$1'" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_unit_paths)"
VALIDATOR_TOOL="$(resolve_python_tool validate_artifact_contracts.py)"

UNIT_TARGET="$UNIT_DIR"
if [[ -n "$UNIT_DIR_OVERRIDE" ]]; then
    UNIT_TARGET="$UNIT_DIR_OVERRIDE"
fi

args=(
    "$VALIDATOR_TOOL"
    --repo-root "$REPO_ROOT"
    --unit-dir "$UNIT_TARGET"
)

if [[ "$JSON_MODE" == "true" ]]; then
    args+=(--json)
fi

if command -v uv >/dev/null 2>&1; then
    uv run --with jsonschema python "${args[@]}"
else
    PYTHON_BIN="python3"
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        PYTHON_BIN="python"
    fi
    "$PYTHON_BIN" "${args[@]}"
fi
