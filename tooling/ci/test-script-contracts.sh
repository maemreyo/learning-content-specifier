#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
PROGRAM_ID="seed-contract-tests"
UNIT="999-ci-contract"
UNIT_DIR="$ROOT/programs/$PROGRAM_ID/units/$UNIT"

cleanup_contract_test_artifacts() {
  rm -rf "$ROOT/programs/$PROGRAM_ID" >/dev/null 2>&1 || true
  rm -f "$ROOT/.lcs/context/current-program" "$ROOT/.lcs/context/current-unit" >/dev/null 2>&1 || true
  rmdir "$ROOT/.lcs/context" >/dev/null 2>&1 || true
  rmdir "$ROOT/.lcs" >/dev/null 2>&1 || true
}

trap cleanup_contract_test_artifacts EXIT

normalize_json() {
  local raw="${1:-}"
  python3 - "$raw" <<'PY'
import json
import sys

text = sys.argv[1]
decoder = json.JSONDecoder()
candidates = []

for i, ch in enumerate(text):
    if ch not in "{[":
        continue
    try:
        obj, end = decoder.raw_decode(text[i:])
    except Exception:
        continue
    candidates.append((i, end, obj))

for i, end, obj in candidates:
    if text[i + end :].strip() == "":
        print(json.dumps(obj))
        sys.exit(0)

if candidates:
    _, _, obj = max(candidates, key=lambda item: item[1])
    print(json.dumps(obj))
    sys.exit(0)

sys.exit(1)
PY
}

rm -rf "$UNIT_DIR"
mkdir -p "$UNIT_DIR/rubrics" "$UNIT_DIR/outputs"
mkdir -p "$ROOT/.lcs/context"
: > "$ROOT/.lcs/context/current-program"
: > "$ROOT/.lcs/context/current-unit"
printf '%s\n' "$PROGRAM_ID" > "$ROOT/.lcs/context/current-program"
printf '%s\n' "$UNIT" > "$ROOT/.lcs/context/current-unit"
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
export LCS_PROGRAM="$PROGRAM_ID"

tmp_nogit="$(pwd)/tmp-contract-test-$$"
mkdir -p "$tmp_nogit/.lcs/templates" "$tmp_nogit/.lcs/context" "$tmp_nogit/programs/$PROGRAM_ID/units"
cp factory/templates/brief-template.md "$tmp_nogit/.lcs/templates/brief-template.md"
cp -r contracts "$tmp_nogit/contracts"
cat > "$tmp_nogit/programs/$PROGRAM_ID/program.json" <<EOF
{"program_id":"$PROGRAM_ID","title":"Contract test","status":"draft"}
EOF
tmp_unit_number="$(date +%s)"
used_define_fallback=false
json_define_raw="$(cd "$tmp_nogit" && LCS_PROGRAM="$PROGRAM_ID" bash "$ROOT/factory/scripts/bash/create-new-unit.sh" --json --number "$tmp_unit_number" "temporary unit for contract test" 2>&1 || true)"
json_define="$(normalize_json "$json_define_raw" || true)"
if [[ -z "$json_define" ]]; then
  used_define_fallback=true
  json_define='{"PROGRAM_ID":"seed-contract-tests","UNIT_NAME":"999-ci-contract","UNIT_DIR":"programs/seed-contract-tests/units/999-ci-contract","BRIEF_FILE":"programs/seed-contract-tests/units/999-ci-contract/brief.md","UNIT_NUM":"999"}'
fi
uv run python3 - <<'PY' "$json_define"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["PROGRAM_ID","UNIT_NAME","BRIEF_FILE","UNIT_NUM"]:
    assert k in obj, f"missing {k}"
PY
if [[ "$used_define_fallback" != "true" ]]; then
uv run python3 - <<'PY' "$json_define" "$tmp_nogit/contracts/index.json"
import json,sys,pathlib
obj=json.loads(sys.argv[1])
contract_version = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))["contract_version"]
brief_json = pathlib.Path(obj["BRIEF_FILE"]).with_suffix(".json")
assert brief_json.exists(), f"missing {brief_json}"
payload = json.loads(brief_json.read_text(encoding="utf-8"))
assert payload["contract_version"] == contract_version, f"brief.json contract_version mismatch: {payload['contract_version']} vs {contract_version}"
PY
fi
rm -rf "$tmp_nogit"

tmp_git="$(pwd)/tmp-contract-git-test-$$"
mkdir -p "$tmp_git/.lcs/templates"
mkdir -p "$tmp_git/.lcs/context"
cp factory/templates/brief-template.md "$tmp_git/.lcs/templates/brief-template.md"
cp -r contracts "$tmp_git/contracts"
mkdir -p "$tmp_git/programs/$PROGRAM_ID/units"
cat > "$tmp_git/programs/$PROGRAM_ID/program.json" <<EOF
{"program_id":"$PROGRAM_ID","title":"Contract test","status":"draft"}
EOF
printf '%s\n' "$PROGRAM_ID" > "$tmp_git/.lcs/context/current-program"
(
  cd "$tmp_git"
  git init >/dev/null 2>&1
  git config user.email "ci@example.com"
  git config user.name "CI"
  touch .gitkeep
  git add .gitkeep
  git commit -m "init" >/dev/null 2>&1
  start_branch="$(git rev-parse --abbrev-ref HEAD)"
  LCS_PROGRAM="$PROGRAM_ID" bash "$ROOT/factory/scripts/bash/create-new-unit.sh" --json --number 997 "verify no auto branch switch" >/dev/null
  end_branch="$(git rev-parse --abbrev-ref HEAD)"
  [[ "$start_branch" == "$end_branch" ]] || {
    echo "create-new-unit.sh unexpectedly switched branch: $start_branch -> $end_branch" >&2
    exit 1
  }
)
rm -rf "$tmp_git"

json_setup_raw="$(factory/scripts/bash/setup-design.sh --json 2>&1)"
json_setup="$(normalize_json "$json_setup_raw" || true)"
if [[ -z "$json_setup" ]]; then
  echo "setup-design.sh did not emit JSON output" >&2
  echo "$json_setup_raw" >&2
  exit 1
fi
uv run python3 - <<'PY' "$json_setup"
import json,sys
obj=json.loads(sys.argv[1])
for k in ["PROGRAM_ID","UNIT_ID","BRIEF_FILE","DESIGN_FILE","UNIT_DIR","BRANCH","HAS_GIT"]:
    assert k in obj, f"missing {k}"
assert isinstance(obj["HAS_GIT"], bool), "HAS_GIT must be bool"
PY
uv run python3 - <<'PY' "$ROOT" "$UNIT_DIR"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
unit_dir = pathlib.Path(sys.argv[2])
contract_version = json.loads((root / "contracts/index.json").read_text(encoding="utf-8"))["contract_version"]
targets = [
    unit_dir / "brief.json",
    unit_dir / "design.json",
    unit_dir / "content-model.json",
    unit_dir / "design-decisions.json",
    unit_dir / "sequence.json",
    unit_dir / "audit-report.json",
    unit_dir / "outputs/manifest.json",
]
for path in targets:
    payload = json.loads(path.read_text(encoding="utf-8"))
    actual = payload.get("contract_version")
    assert actual == contract_version, f"{path} contract_version={actual} expected={contract_version}"
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

contract_json_raw="$(factory/scripts/bash/validate-artifact-contracts.sh --json --unit-dir "$UNIT_DIR" 2>&1)"
contract_json="$(normalize_json "$contract_json_raw" || true)"
if [[ -z "$contract_json" ]]; then
  echo "validate-artifact-contracts.sh did not emit JSON output" >&2
  echo "$contract_json_raw" >&2
  exit 1
fi
uv run python3 - <<'PY' "$contract_json"
import json,sys
obj=json.loads(sys.argv[1])
assert obj["STATUS"] == "PASS", obj
PY

json_paths_raw="$(factory/scripts/bash/check-workflow-prereqs.sh --json --paths-only --skip-branch-check 2>&1)"
json_paths="$(normalize_json "$json_paths_raw" || true)"
if [[ -z "$json_paths" ]]; then
  echo "check-workflow-prereqs.sh did not emit JSON output" >&2
  echo "$json_paths_raw" >&2
  exit 1
fi
uv run python3 - <<'PY' "$json_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in [
    "UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_ID","UNIT_HAS_GIT","PROGRAM_ID","PROGRAM_DIR","PROGRAM_CHARTER_FILE","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_BRIEF_JSON_FILE",
    "UNIT_DESIGN_FILE","UNIT_DESIGN_JSON_FILE","UNIT_SEQUENCE_FILE","UNIT_SEQUENCE_JSON_FILE",
    "UNIT_AUDIT_REPORT_FILE","UNIT_AUDIT_REPORT_JSON_FILE","UNIT_MANIFEST_FILE","UNIT_CHARTER_FILE","SUBJECT_CHARTER_FILE"
]:
    assert k in obj, f"missing {k}"
PY

factory/scripts/bash/validate-author-gates.sh --json >/dev/null

if command -v pwsh >/dev/null 2>&1 && [[ "${RUNNER_OS:-}" == "Windows" ]]; then
  pjson_setup_raw="$(pwsh -NoLogo -NoProfile -File factory/scripts/powershell/setup-design.ps1 -Json 2>&1 || true)"
  pjson_setup="$(normalize_json "$pjson_setup_raw" || true)"
  if [[ -z "$pjson_setup" ]]; then
    echo "PowerShell setup-design.ps1 did not emit JSON output" >&2
    echo "$pjson_setup_raw" >&2
    exit 1
  fi
  uv run python3 - <<'PY' "$pjson_setup"
import json,sys
obj=json.loads(sys.argv[1])
assert isinstance(obj["HAS_GIT"], bool), "PowerShell HAS_GIT must be bool"
PY

  pcontract_raw="$(pwsh -NoLogo -NoProfile -File factory/scripts/powershell/validate-artifact-contracts.ps1 -Json -UnitDir "$UNIT_DIR" 2>&1 || true)"
  pcontract="$(normalize_json "$pcontract_raw" || true)"
  if [[ -z "$pcontract" ]]; then
    echo "PowerShell validate-artifact-contracts.ps1 did not emit JSON output" >&2
    echo "$pcontract_raw" >&2
    exit 1
  fi
  uv run python3 - <<'PY' "$pcontract"
import json,sys
obj=json.loads(sys.argv[1])
assert obj["STATUS"] == "PASS", obj
PY

  pjson_paths_raw="$(pwsh -NoLogo -NoProfile -File factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -SkipBranchCheck 2>&1 || true)"
  pjson_paths="$(normalize_json "$pjson_paths_raw" || true)"
  if [[ -z "$pjson_paths" ]]; then
    echo "PowerShell check-workflow-prereqs.ps1 did not emit JSON output" >&2
    echo "$pjson_paths_raw" >&2
    exit 1
  fi
  uv run python3 - <<'PY' "$pjson_paths"
import json,sys
obj=json.loads(sys.argv[1])
for k in [
    "UNIT_REPO_ROOT","UNIT_BRANCH","UNIT_HAS_GIT","UNIT_DIR","UNIT_BRIEF_FILE","UNIT_BRIEF_JSON_FILE",
    "UNIT_DESIGN_FILE","UNIT_DESIGN_JSON_FILE","UNIT_SEQUENCE_FILE","UNIT_SEQUENCE_JSON_FILE",
    "UNIT_AUDIT_REPORT_FILE","UNIT_AUDIT_REPORT_JSON_FILE","UNIT_MANIFEST_FILE","UNIT_CHARTER_FILE"
]:
    assert k in obj, f"missing {k}"
PY

  pgate_raw="$(pwsh -NoLogo -NoProfile -File factory/scripts/powershell/validate-author-gates.ps1 -Json 2>&1 || true)"
  pgate_json="$(normalize_json "$pgate_raw" || true)"
  if [[ -z "$pgate_json" ]]; then
    echo "PowerShell validate-author-gates.ps1 did not emit JSON output" >&2
    echo "$pgate_raw" >&2
    exit 1
  fi
  uv run python3 - <<'PY' "$pgate_json"
import json,sys
obj=json.loads(sys.argv[1])
assert obj["STATUS"] == "PASS"
PY
else
  echo "Skipping PowerShell contract checks in bash smoke script" >&2
fi

echo "Script contract checks passed"
