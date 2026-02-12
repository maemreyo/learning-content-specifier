#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv run python factory/scripts/python/build_contract_package.py --verify
else
  PYTHON_BIN="python3"
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
  fi
  "$PYTHON_BIN" factory/scripts/python/build_contract_package.py --verify
fi

echo "Contract sync verification passed"
