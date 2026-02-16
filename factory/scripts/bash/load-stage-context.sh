#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
STAGE=""
INTENT=""
PROGRAM_OVERRIDE=""
UNIT_OVERRIDE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --stage)
            STAGE="${2:-}"
            shift 2
            ;;
        --intent)
            INTENT="${2:-}"
            shift 2
            ;;
        --program)
            PROGRAM_OVERRIDE="${2:-}"
            shift 2
            ;;
        --unit)
            UNIT_OVERRIDE="${2:-}"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 --stage <stage> [--intent <text>] [--program <id>] [--unit <id>] [--json]"
            exit 0
            ;;
        *)
            if [[ -z "$INTENT" ]]; then
                INTENT="$1"
            else
                INTENT="$INTENT $1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$STAGE" ]]; then
    echo "ERROR: --stage is required" >&2
    exit 1
fi

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
LOADER_TOOL="$(resolve_python_tool load_stage_context.py)"

args=(
  "$LOADER_TOOL"
  --repo-root "$REPO_ROOT"
  --stage "$STAGE"
)

if [[ -n "$INTENT" ]]; then
  args+=(--intent "$INTENT")
fi
if [[ -n "$PROGRAM_OVERRIDE" ]]; then
  args+=(--program "$PROGRAM_OVERRIDE")
fi
if [[ -n "$UNIT_OVERRIDE" ]]; then
  args+=(--unit "$UNIT_OVERRIDE")
fi
if [[ "$JSON_MODE" == "true" ]]; then
  args+=(--json)
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
