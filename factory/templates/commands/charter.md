---
description: Create or update the active learning-program charter and keep program context deterministic.
handoffs:
  - label: Update Subject Governance Charter
    agent: lcs.subject.charter
    prompt: Update subject-level governance charter in .lcs/memory/charter.md.
  - label: Define Learning Unit
    agent: lcs.define
    prompt: Define a new learning unit from this program charter.
scripts:
  sh: factory/scripts/bash/ensure-program-context.sh --json "{ARGS}"
  ps: factory/scripts/powershell/ensure-program-context.ps1 -Json "{ARGS}"
---

## Intent

Establish or amend the active program charter in `programs/<program_id>/charter.md`.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run `{SCRIPT}` exactly once to resolve/create active program context.
- YOU MUST maintain deterministic charter version lines: `Version`, `Ratified`, `Last Amended`.
- YOU MUST define hard-gate policy in testable language (objective criteria, not vague intent).
- YOU MUST generate/maintain `programs/<program_id>/roadmap.json` and `programs/<program_id>/roadmap.md` when program scope is multi-unit (>=8 study sessions, cadence-flexible).
- YOU MUST propagate governance-impacting changes into templates under `.lcs/templates/`.
- YOU MUST NOT leave unresolved placeholders.
- YOU MUST NOT edit `.lcs/memory/charter.md` in this command.

## Execution Steps

1. Run `{SCRIPT}` and parse `PROGRAM_ID`, `PROGRAM_DIR`, `PROGRAM_CHARTER_FILE`, `PROGRAM_ROADMAP_JSON_FILE`, `PROGRAM_ROADMAP_MD_FILE`, `TARGET_SESSIONS`, `DURATION_DAYS`, `EXPECTED_UNITS`, `SUBJECT_CHARTER_FILE`.
2. Load existing program charter or bootstrap from `.lcs/templates/charter-template.md`.
3. Integrate user intent and enforce command chain: `charter -> define -> refine -> design -> sequence -> rubric -> audit -> author`.
4. Apply semver bump rationale:
   - MAJOR: governance-breaking change.
   - MINOR: new mandatory principle or gate.
   - PATCH: clarification only.
5. Save charter and summarize governance impact.

## Hard Gates

- Gate G-CH-001: no placeholder tokens remain.
- Gate G-CH-002: all dates use `YYYY-MM-DD`.
- Gate G-CH-003: hard-gate criteria are operationally testable.

## Failure Modes

- Missing charter template: stop with actionable path.
- Invalid version/date format: stop and request correction.
- Unclear governance impact: stop and request explicit scope.

## Output Contract

- Primary artifact: `programs/<program_id>/charter.md`.
- Planning artifacts (when target scope >=8 study sessions): `programs/<program_id>/roadmap.json`, `programs/<program_id>/roadmap.md`.
- Context artifacts: `.lcs/context/current-program` set to active `program_id` and `.lcs/context/current-unit` cleared.
- Report includes:
  - `program_id`,
  - old/new version,
  - amendment scope,
  - affected `.lcs/templates/*` files.
- Report MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.programs workflow-status --program <program_id>`
  - `/lcs.define ...` for the first unit
  - `/lcs.programs activate --program <program_id> --unit <unit_id>` when continuing with existing units.

## Examples

- Success: program charter updated with explicit gate criteria and semver bump rationale.
- Fail: unresolved `[TODO]` governance token remains.
