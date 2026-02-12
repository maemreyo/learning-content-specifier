#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-v9.9.9}"

AGENTS="claude codex copilot kilocode auggie roo" SCRIPTS="sh" tooling/ci/create-release-packages.sh "$VERSION"

check_zip_path() {
  local zip="$1" expected_path="$2"
  unzip -l "$zip" | awk '{print $4}' | grep -q "$expected_path"
}

for agent in claude codex copilot kilocode auggie roo; do
  zip=".genreleases/learning-content-specifier-template-${agent}-sh-${VERSION}.zip"
  [[ -f "$zip" ]] || { echo "Missing package: $zip"; exit 1; }

  case "$agent" in
    claude) check_zip_path "$zip" ".claude/commands/lcs.define.md" ;;
    codex) check_zip_path "$zip" ".codex/commands/lcs.define.md" ;;
    copilot) check_zip_path "$zip" ".github/agents/lcs.define.agent.md" ;;
    kilocode) check_zip_path "$zip" ".kilocode/rules/lcs.define.md" ;;
    auggie) check_zip_path "$zip" ".augment/rules/lcs.define.md" ;;
    roo) check_zip_path "$zip" ".roo/rules/lcs.define.md" ;;
  esac

  if unzip -l "$zip" | awk '{print $4}' | grep -q "\.lcs\.lcs/"; then
    echo "Invalid duplicated .lcs path in $zip"
    exit 1
  fi
done

contract_zip=".genreleases/lcs-contracts-${VERSION}.zip"
[[ -f "$contract_zip" ]] || { echo "Missing contract package: $contract_zip"; exit 1; }
check_zip_path "$contract_zip" "contracts/index.json"
check_zip_path "$contract_zip" "contracts/schemas/manifest.schema.json"
check_zip_path "$contract_zip" "contracts/docs/CONSUMER-API-V1.md"
check_zip_path "$contract_zip" "contracts/fixtures/golden_path_snapshot.json"

echo "Release packaging smoke checks passed"
