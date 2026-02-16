---
description: Create or update the subject-level governance charter at .lcs/memory/charter.md.
argument-hint: "[subject governance updates or policy deltas]"
handoffs:
  - label: Update Active Program Charter
    agent: lcs.charter
    prompt: Update the currently active program charter using this governance context.
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --paths-only --skip-branch-check --stage charter
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -SkipBranchCheck -Stage charter
---

## Intent

Establish or amend subject governance source of truth in `.lcs/memory/charter.md`.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST maintain deterministic charter version lines: `Version`, `Ratified`, `Last Amended`.
- YOU MUST define hard-gate policy in testable language (objective criteria, not vague intent).
- YOU MUST propagate governance-impacting changes into templates under `.lcs/templates/`.
- YOU MUST NOT leave unresolved placeholders.
- YOU MUST NOT edit `programs/<program_id>/charter.md` in this command.

## Execution Steps

1. Run `{SCRIPT}` and parse `SUBJECT_CHARTER_FILE`.
2. Load existing subject charter or bootstrap from `.lcs/templates/charter-template.md`.
3. Integrate user intent and keep command chain references aligned.
4. Apply semver bump rationale:
   - MAJOR: governance-breaking change.
   - MINOR: new mandatory principle or gate.
   - PATCH: clarification only.
5. Save subject charter and summarize governance impact.

## Hard Gates

- Gate G-SCH-001: no placeholder tokens remain.
- Gate G-SCH-002: all dates use `YYYY-MM-DD`.
- Gate G-SCH-003: hard-gate criteria are operationally testable.

## Output Contract

- Primary artifact: `.lcs/memory/charter.md`.
- Report includes old/new version, amendment scope, and affected templates.
- Report MUST include a `Follow-up Tasks` section with exact prompts:
  - `/lcs.charter ...` for active program alignment,
  - `/lcs.programs list` to confirm target program context.
