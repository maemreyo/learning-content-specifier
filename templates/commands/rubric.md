---
description: Generate a hard-gate rubric for learning-content quality validation.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load `brief.md`, `design.md`, and `sequence.md` when available.
3. Create `UNIT_DIR/rubrics/` if missing.
4. Generate rubric file from `.lcs/templates/rubric-template.md`.
5. Tailor rubric checks to the unit context and keep IDs sequential.
6. Rubric MUST include these gate groups:
   - objective-activity-assessment alignment
   - pedagogy consistency
   - accessibility/readability
   - metadata completeness
7. Report created rubric path and total check items.
