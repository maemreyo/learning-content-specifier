---
description: Create or update the project learning-content charter and propagate governance changes.
handoffs:
  - label: Define Learning Unit
    agent: lcs.define
    prompt: Define a new learning unit from this charter.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --paths-only
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Load `.lcs/memory/charter.md` (or copy from `.lcs/templates/charter-template.md` if missing).
2. Resolve all placeholder fields with concrete governance content.
3. Version charter using semantic versioning:
   - MAJOR: breaking governance shifts
   - MINOR: new mandatory principle/section
   - PATCH: clarifications only
4. Propagate alignment updates to templates and commands under `.lcs/templates/`.
5. Validate:
   - no unresolved placeholder tokens
   - dates in `YYYY-MM-DD`
   - hard-gate principles are explicit and testable
6. Save charter and report version bump rationale.
