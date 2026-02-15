# Follow-up UX Standards

This document defines how LCS command responses should present actionable next steps.

## Principles

- Always include a `Follow-up Tasks` section at the end of command responses.
- Prefer one primary next action and up to 2 secondary actions.
- Make actions executable immediately (exact prompt/command, no ambiguity).
- For multi-unit programs, include context switch prompts before unit-specific work:
  - `/lcs.programs activate --program <program-id> --unit <unit-id>`
- Avoid dead-ends: if a user cannot proceed, provide a concrete recovery step.

## Source Alignment

The standards align with established UX guidance that confirmation and empty states should tell users what to do next and provide clear primary actions:

- GOV.UK confirmation pages pattern: include "what happens next" and links users likely need next.
- Carbon empty states: explain next action clearly and include a direct primary action.
- Atlassian empty state guidance: recommend the best next step as a primary action, with optional secondary actions.

## LCS Implementation

- Use `/lcs.programs workflow-status` to generate pending-stage status and follow-up commands.
- `lcs.design` and `lcs.refine` must call workflow-status and present prioritized follow-up tasks.
- `lcs.redesign` is available for force-reset design regeneration on the active unit.
