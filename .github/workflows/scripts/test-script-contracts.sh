#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
UNIT="999-ci-contract"
UNIT_DIR="$ROOT/specs/$UNIT"

mkdir -p "$UNIT_DIR/rubrics" "$UNIT_DIR/outputs"
: > "$UNIT_DIR/brief.md"
: > "$UNIT_DIR/design.md"
: > "$UNIT_DIR/sequence.md"
cat > "$UNIT_DIR/audit-report.md" <<AUDIT
# Audit Report: $UNIT
Gate Decision: PASS
Open Critical: 0
Open High: 0
## Findings
1. LOW | artifact: design.md | issue: none | remediation: n/a
AUDIT
cat > "$UNIT_DIR/rubrics/default.md" <<RUB
- [x] Gate ID: RB001 | Group: alignment | Status: PASS | Severity: LOW | Evidence: design.md
RUB

export LCS_UNIT="$UNIT"

tmp_nogit="$(mktemp -d)"
mkdir -p "$tmp_nogit/.lcs/templates" "$tmp_nogit/specs"
cp templates/brief-template.md "$tmp_nogit/.lcs/templates/brief-template.md"
json_define=$(cd "$tmp_nogit" && bash "$ROOT/scripts/bash/create-new-unit.sh" --json "temporary unit for contract test")
python3 - <<'PY' "$json_define"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["UNIT_NAME","BRIEF_FILE","UNIT_NUM"]:
    assert k in obj, f"missing {k}"
PY
rm -rf "$tmp_nogit"

json_setup=$(scripts/bash/setup-design.sh --json)
python3 - <<'PY' "$json_setup"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["BRIEF_FILE","DESIGN_FILE","UNIT_DIR","BRANCH","HAS_GIT"]:
    assert k in obj, f"missing {k}"
assert isinstance(obj["HAS_GIT"], bool), "HAS_GIT must be bool"
PY

json_paths=$(scripts/bash/check-workflow-prereqs.sh --json --paths-only --skip-branch-check)
python3 - <<'PY' "$json_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_HAS_GIT","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_DESIGN_FILE","UNIT_SEQUENCE_FILE","UNIT_CHARTER_FILE"]:
    assert k in obj, f"missing {k}"
PY

scripts/bash/validate-author-gates.sh --json >/dev/null

if command -v pwsh >/dev/null 2>&1; then
  pjson_setup=$(pwsh -NoLogo -NoProfile -File scripts/powershell/setup-design.ps1 -Json)
  python - <<'PY' "$pjson_setup"
import json,sys
obj=json.loads(sys.argv[1])
assert isinstance(obj["HAS_GIT"], bool), "PowerShell HAS_GIT must be bool"
PY

  pjson_paths=$(pwsh -NoLogo -NoProfile -File scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -SkipBranchCheck)
  python - <<'PY' "$pjson_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_HAS_GIT","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_DESIGN_FILE","UNIT_SEQUENCE_FILE","UNIT_CHARTER_FILE"]:
    assert k in obj, f"missing {k}"
PY

  pwsh -NoLogo -NoProfile -File scripts/powershell/validate-author-gates.ps1 -Json | python3 - <<'PY'
import json,sys
obj=json.loads(sys.stdin.read())
assert obj["STATUS"] == "PASS"
PY
else
  echo "pwsh not found; skipping PowerShell contract checks" >&2
fi

echo "Script contract checks passed"
