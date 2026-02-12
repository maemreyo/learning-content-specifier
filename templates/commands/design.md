---
description: Generate learning design artifacts from the unit brief and charter.
handoffs:
  - label: Build Production Sequence
    agent: lcs.sequence
    prompt: Create a production sequence from design artifacts.
    send: true
  - label: Generate Rubric
    agent: lcs.rubric
    prompt: Generate hard-gate rubric for this unit.
scripts:
  sh: scripts/bash/setup-design.sh --json
  ps: scripts/powershell/setup-design.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Run `{SCRIPT}` and parse `BRIEF_FILE`, `DESIGN_FILE`, `UNIT_DIR`, `BRANCH`, `HAS_GIT`.
2. Load `BRIEF_FILE`, `.lcs/memory/charter.md`, and `.lcs/templates/design-template.md`.
3. Create/update:
   - `design.md`
   - `content-model.md`
   - `assessment-map.md`
   - `delivery-guide.md`
4. Enforce charter gates in design output:
   - objective-activity-assessment alignment
   - pedagogy consistency
   - accessibility/readability coverage
   - metadata completeness
5. Run `{AGENT_SCRIPT}` to refresh agent context from design metadata.
6. Report generated artifacts and any unresolved blockers.
