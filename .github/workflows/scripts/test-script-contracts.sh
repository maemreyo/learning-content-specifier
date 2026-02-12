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

tmp_nogit="$(pwd)/tmp-contract-test-$$"
mkdir -p "$tmp_nogit/.lcs/templates" "$tmp_nogit/specs"
cp templates/brief-template.md "$tmp_nogit/.lcs/templates/brief-template.md"
json_define=$(cd "$tmp_nogit" && bash "$ROOT/scripts/bash/create-new-unit.sh" --json "temporary unit for contract test")
uv run python3 - <<'PY' "$json_define"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["UNIT_NAME","BRIEF_FILE","UNIT_NUM"]:
    assert k in obj, f"missing {k}"
PY
uv run python3 - <<'PY' "$json_define"
import json,sys, pathlib
obj=json.loads(sys.argv[1])
brief_json = pathlib.Path(obj["BRIEF_FILE"]).with_suffix(".json")
assert brief_json.exists(), f"missing {brief_json}"
PY
rm -rf "$tmp_nogit"

json_setup=$(scripts/bash/setup-design.sh --json)
uv run python3 - <<'PY' "$json_setup"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["BRIEF_FILE","DESIGN_FILE","UNIT_DIR","BRANCH","HAS_GIT"]:
    assert k in obj, f"missing {k}"
assert isinstance(obj["HAS_GIT"], bool), "HAS_GIT must be bool"
PY
uv run python3 - <<'PY' "$UNIT_DIR/audit-report.json"
import json,sys
path=sys.argv[1]
obj=json.load(open(path))
obj["gate_decision"]="PASS"
obj["open_critical"]=0
obj["open_high"]=0
obj["findings"]=[]
json.dump(obj, open(path,"w"), indent=2)
PY
uv run python3 - <<'PY' "$UNIT_DIR/outputs/manifest.json"
import json,sys
path=sys.argv[1]
obj=json.load(open(path))
obj["gate_status"]={"decision":"PASS","open_critical":0,"open_high":0}
json.dump(obj, open(path,"w"), indent=2)
PY

contract_json=$(scripts/bash/validate-artifact-contracts.sh --json --unit-dir "$UNIT_DIR")
uv run python3 - <<'PY' "$contract_json"
import json,sys
obj=json.loads(sys.argv[1])
assert obj["STATUS"] == "PASS", obj
PY

json_paths=$(scripts/bash/check-workflow-prereqs.sh --json --paths-only --skip-branch-check)
uv run python3 - <<'PY' "$json_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in [
    "UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_HAS_GIT","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_BRIEF_JSON_FILE",
    "UNIT_DESIGN_FILE","UNIT_DESIGN_JSON_FILE","UNIT_SEQUENCE_FILE","UNIT_SEQUENCE_JSON_FILE",
    "UNIT_AUDIT_REPORT_FILE","UNIT_AUDIT_REPORT_JSON_FILE","UNIT_MANIFEST_FILE","UNIT_CHARTER_FILE"
]:
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

  pcontract=$(pwsh -NoLogo -NoProfile -File scripts/powershell/validate-artifact-contracts.ps1 -Json -UnitDir "$UNIT_DIR")
  python - <<'PY' "$pcontract"
import json,sys
obj=json.loads(sys.argv[1])
assert obj["STATUS"] == "PASS", obj
PY

  pjson_paths=$(pwsh -NoLogo -NoProfile -File scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -SkipBranchCheck)
  python - <<'PY' "$pjson_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in [
    "UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_HAS_GIT","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_BRIEF_JSON_FILE",
    "UNIT_DESIGN_FILE","UNIT_DESIGN_JSON_FILE","UNIT_SEQUENCE_FILE","UNIT_SEQUENCE_JSON_FILE",
    "UNIT_AUDIT_REPORT_FILE","UNIT_AUDIT_REPORT_JSON_FILE","UNIT_MANIFEST_FILE","UNIT_CHARTER_FILE"
]:
    assert k in obj, f"missing {k}"
PY

  pwsh -NoLogo -NoProfile -File scripts/powershell/validate-author-gates.ps1 -Json | uv run python3 - <<'PY'
import json,sys
obj=json.loads(sys.stdin.read())
assert obj["STATUS"] == "PASS"
PY
else
  echo "pwsh not found; skipping PowerShell contract checks" >&2
fi

echo "Script contract checks passed"
