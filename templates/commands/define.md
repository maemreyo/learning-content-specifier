---
description: Create or update a learning unit brief from a natural language learning-content request.
handoffs:
  - label: Refine Unit Brief
    agent: lcs.refine
    prompt: Refine ambiguous areas in this brief.
    send: true
  - label: Build Learning Design
    agent: lcs.design
    prompt: Design the learning unit from this brief.
scripts:
  sh: scripts/bash/create-new-unit.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-unit.ps1 -Json "{ARGS}"
---

## User Input

```text
$ARGUMENTS
```

Use the input as the unit request. Do not ask the user to repeat it unless empty.

## Workflow

1. Run `{SCRIPT}` once to create/select the numbered unit directory and get JSON output.
2. Parse JSON: `UNIT_NAME`, `BRIEF_FILE`, `UNIT_NUM`.
3. Load `.lcs/templates/brief-template.md` and populate all mandatory sections.
4. Focus on:
   - audience and context
   - measurable learning outcomes
   - scope boundaries
   - content + accessibility requirements
   - success metrics and assumptions
5. Keep brief implementation-agnostic and learner-centric.
6. Save to `BRIEF_FILE`.
7. Report completion with unit name, file path, and suggested next command (`/lcs.refine` or `/lcs.design`).
