#!/usr/bin/env bash
set -euo pipefail

pattern='lcs\.(constitution|specify|clarify|plan|tasks|implement|checklist|analyze|taskstoissues)|requires\.speckit_version|after_tasks|after_implement'

if rg -n --hidden --glob '!.git' --glob '!CHANGELOG.md' --glob '!extensions/RFC-EXTENSION-SYSTEM.md' --glob '!docs/plans/**' --glob '!docs/system/migration/**' --glob '!.github/workflows/scripts/legacy-token-guard.sh' "$pattern" README.md spec-driven.md docs templates scripts src .devcontainer .github/workflows extensions/template extensions/EXTENSION-API-REFERENCE.md extensions/EXTENSION-DEVELOPMENT-GUIDE.md extensions/EXTENSION-USER-GUIDE.md extensions/EXTENSION-PUBLISHING-GUIDE.md; then
  echo "Legacy tokens found outside allowlist"
  exit 1
fi

echo "Legacy token guard passed"
