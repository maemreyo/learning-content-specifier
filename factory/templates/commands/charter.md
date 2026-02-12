---
description: Create or update the project learning-content charter and propagate governance changes.
handoffs:
  - label: Define Learning Unit
    agent: lcs.define
    prompt: Define a new learning unit from this charter.
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --paths-only --skip-branch-check
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -SkipBranchCheck
---

## Intent

Establish or amend the governance source of truth in `.lcs/memory/charter.md`.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST maintain a deterministic charter version line: `Version`, `Ratified`, `Last Amended`.
- YOU MUST define hard-gate policy in testable language (objective criteria, not vague intent).
- YOU MUST propagate governance-impacting changes into templates under `.lcs/templates/`.
- YOU MUST NOT leave unresolved placeholders.
- YOU MUST NOT require unit branch context for this command.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_REPO_ROOT`, `UNIT_CHARTER_FILE`.
2. Load existing charter or bootstrap from `.lcs/templates/charter-template.md`.
3. Integrate user intent and enforce command chain: `charter -> define -> refine -> design -> sequence -> rubric -> audit -> author -> issueize`.
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

- Primary artifact: `.lcs/memory/charter.md`.
- Report includes:
  - old/new version,
  - amendment scope,
  - affected factory/templates/commands.

## Examples

- Success: charter updated with explicit gate criteria and semver bump rationale.
- Fail: unresolved `[TODO]` governance token remains.
