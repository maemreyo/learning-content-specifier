---
description: Perform read-only cross-artifact audit across brief, design, and sequence.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## User Input

```text
$ARGUMENTS
```

## Goal

Detect quality and consistency gaps before authoring.

## Workflow

1. Run `{SCRIPT}` once and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load required artifacts:
   - `brief.md`
   - `design.md`
   - `sequence.md`
3. Validate:
   - LO coverage from brief -> design -> sequence
   - charter gate alignment
   - rubric readiness and unresolved risks
   - metadata contract consistency for `outputs/`
4. Output a markdown audit report (read-only analysis, no file edits unless user asks).
5. Severity levels: CRITICAL, HIGH, MEDIUM, LOW.
6. Recommend next actions; block `/lcs.author` when CRITICAL issues exist.
