---
description: Convert sequence tasks into dependency-ordered GitHub issues.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --require-sequence --include-sequence
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -RequireSequence -IncludeSequence
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Run `{SCRIPT}` and parse `UNIT_DIR`.
2. Load `UNIT_DIR/sequence.md`.
3. Read remote URL from `git config --get remote.origin.url`.
4. Continue only if remote is a GitHub repository.
5. Create one issue per actionable sequence task, preserving dependencies and LO labels.
6. Report created issue links and any skipped tasks.
