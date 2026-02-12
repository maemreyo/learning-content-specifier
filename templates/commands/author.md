---
description: Execute approved production sequence and author local output assets.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Validate hard gates before execution:
   - every rubric in `UNIT_DIR/rubrics/` has zero unchecked items
   - latest audit has no unresolved CRITICAL/HIGH blockers
3. If gates fail, stop and report blockers.
4. Load `sequence.md` and execute tasks in dependency order.
5. Write generated assets to `UNIT_DIR/outputs/` only.
6. Mark completed sequence tasks as `[X]` in `sequence.md`.
7. Emit final summary with produced files and remaining work.
